import os
import time
import json
import base64
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.firefox import GeckoDriverManager
import subprocess

# ---- Load config ----
with open("config.json", "r") as f:
    CONFIG = json.load(f)

OUTPUT_DIR = CONFIG["output_dir"]
USER_DATA_DIR = CONFIG["user_data_dir"]
PROFILE_NAME = CONFIG["profile_name"]
CLEANUP_MODE = CONFIG.get("cleanup_mode", "gentle")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(name):
    name = name.replace(":", "-").replace("/", "-").replace("?", "")
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()

def create_driver():
    opts = FirefoxOptions()
    opts.add_argument("--width=1280")
    opts.add_argument("--height=800")
    # opts.add_argument("--headless")  # Optional

    # Load profile if needed
    profile_path = os.path.join(USER_DATA_DIR, PROFILE_NAME)
    if os.path.isdir(profile_path):
        opts.profile = profile_path

    # Load Firefox extension if provided
    extension_path = CONFIG.get("firefox_extension_path")
    if extension_path and os.path.exists(extension_path):
        profile = webdriver.FirefoxProfile()
        profile.add_extension(extension=extension_path)
        service = FirefoxService(executable_path=GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=opts, firefox_profile=profile)

    # No extension case
    service = FirefoxService(executable_path=GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=opts)

def gentle_cleanup(driver):
    js = """
        const style = document.createElement('style');
        style.innerHTML = `
            body {
                font-family: Georgia, serif;
                line-height: 1.6;
            }
            img, iframe, video {
                max-width: 100%;
                height: auto;
            }
            .caption, figcaption, [class*='caption'] {
                display: block;
                font-size: 0.9em;
                color: #555;
                text-align: center;
                margin-top: 0.3em;
            }
        `;
        document.head.appendChild(style);

        const selectors = [
            '[class*="popup"]', '[id*="popup"]',
            '[class*="overlay"]', '[id*="overlay"]',
            '[class*="modal"]', '[id*="modal"]',
            '[class*="cookie"]', '[id*="cookie"]',
            '[class*="subscribe"]', '[id*="subscribe"]'
        ];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });

        document.body.style.overflow = 'auto';
    """
    driver.execute_script(js)

def isolate_main_content(driver):
    js = """
        function zap(selectors) {
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        }

        zap([
            'header', 'footer', 'nav', 'aside',
            '[class*="sidebar"]', '[id*="sidebar"]',
            '[class*="popup"]', '[id*="popup"]',
            '[class*="overlay"]', '[id*="overlay"]',
            '[class*="modal"]', '[id*="modal"]',
            '[class*="ad"]', '[id*="ad"]',
            '[class*="cookie"]', '[id*="cookie"]',
            '[class*="banner"]', '[id*="banner"]',
            '[class*="StickyVideo"]', '[id*="StickyVideo"]',
            '[class*="VideoHub"]', '[id*="VideoHub"]',
            'iframe[src*="video"]', 'iframe[src*="youtube"]',
            'video', 'figure[class*="video"]', 'div[class*="video"]'
        ]);

        let main = document.querySelector("main") ||
                   document.querySelector('[role="main"]') ||
                   document.querySelector('[class*="article"]') ||
                   document.querySelector('[class*="story"]') ||
                   document.querySelector('[class*="content"]');

        if (main) {
            document.body.innerHTML = "";
            document.body.appendChild(main.cloneNode(true));
            document.body.style.margin = "2em";
            document.body.style.fontFamily = "Georgia, serif";
            document.body.style.lineHeight = "1.6";
            document.body.style.background = "white";
        } else {
            console.warn("[WARN] No main content found.");
        }

        document.querySelectorAll("*").forEach(el => {
            const style = window.getComputedStyle(el);
            if (["fixed", "sticky"].includes(style.position)) {
                el.style.display = "none";
            }
        });
    """
    driver.execute_script(js)

def fix_layout(driver):
    js = '''
        const style = document.createElement('style');
        style.innerHTML = `
            * {
                box-sizing: border-box !important;
                max-width: 100% !important;
                word-wrap: break-word !important;
            }

            body {
                margin: 0 auto;
                padding: 2em;
                font-family: Georgia, serif;
                font-size: 16px;
                line-height: 1.6;
                background: white;
                max-width: 700px;
            }

            img, video, iframe {
                max-width: 100% !important;
                height: auto !important;
            }

            figure {
                margin-bottom: 1.5em;
            }

            figcaption, .caption, [class*="caption"] {
                display: block;
                font-size: 0.9em;
                color: #555;
                margin-top: 0.3em;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    '''
    driver.execute_script(js)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_welcome():
    print("Welcome to RemarkablePageScribe! Enter a URL to save as a ReMarkable PDF.")
    print("Type 'q' or 'quit' to exit.\n")

def main():
    driver = create_driver()

    while True:
        clear_console()
        print_welcome()
        url = input("Paste URL: ").strip()
        if url.lower() in {"q", "quit"}:
            break
        try:
            print(f"[OPENING] {url}")
            driver.get(url)

            title = driver.title or "webpage"
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = sanitize_filename(f"{timestamp}_{title}") + ".pdf"
            filepath = os.path.join(OUTPUT_DIR, filename)

            print(f"[SAVING PDF] → {filepath}")

            if CLEANUP_MODE == "aggressive":
                print("[DEBUG] Using aggressive cleanup...")
                isolate_main_content(driver)
                print("[DEBUG] Isolated main content")
                fix_layout(driver)
                print("[DEBUG] Applied fix_layout")
            else:
                print("[DEBUG] Using gentle cleanup...")
                gentle_cleanup(driver)

            # Firefox workaround: Use print dialog to save PDF or use pyautogui to automate
            print("[INFO] Please manually print the page to PDF using Firefox's print dialog.")
            input("Press Enter after saving the PDF...")

            print("[DONE]\n")
            time.sleep(2)

        except Exception as e:
            print(f"[ERROR] Failed to process: {e}\n")

    driver.quit()
    print("Goodbye!")

if __name__ == "__main__":
    main()
