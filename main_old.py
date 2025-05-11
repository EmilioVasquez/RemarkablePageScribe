import os
import time
import json
import base64
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import subprocess

# ---- Load config ----
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Directory where we save the PDF
OUTPUT_DIR = CONFIG["output_dir"]

# Location where Chrome profile is located. This allows the user to sign in and stay signed in to any website of their choosing.
# NOTE: Find where your chrome.exe is located and run the below line in CMD:
# "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\temp\chrome_test"
# A Chrome window will pop up. Sign in to the sites you like.
USER_DATA_DIR = CONFIG["user_data_dir"]
PROFILE_NAME = CONFIG["profile_name"]

# Make output directory if it doesn't exist.
os.makedirs(OUTPUT_DIR, exist_ok=True)


def sanitize_filename(name):
    name = name.replace(":", "-").replace("/", "-").replace("?", "")
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()





def create_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    opts.add_argument(f"--profile-directory={PROFILE_NAME}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--headless=new")
    opts.add_argument("--log-level=3")
    opts.add_argument("--disable-logging")
    opts.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    service.log_output = subprocess.DEVNULL  # Only suppress ChromeDriver logs

    return webdriver.Chrome(service=service, options=opts)




def create_driverv1():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    opts.add_argument(f"--profile-directory={PROFILE_NAME}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--headless=new")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def act_human(driver):
    height = driver.execute_script("return document.body.scrollHeight")
    for pos in range(0, height, random.randint(300, 800)):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(random.uniform(0.3, 1.0))
    elems = driver.find_elements(By.CSS_SELECTOR, "img, a")
    if elems:
        el = random.choice(elems)
        try:
            ActionChains(driver).move_to_element(el).perform()
        except:
            pass

def remove_popups(driver):
    js_cleanup = """
        // Remove common overlays and modals
        const selectors = [
            '[id*="popup"]',
            '[class*="popup"]',
            '[id*="overlay"]',
            '[class*="overlay"]',
            '[class*="modal"]',
            '[id*="modal"]',
            '[class*="newsletter"]',
            '[id*="subscribe"]',
            '[class*="subscribe"]',
            '[id*="cookie"]',
            '[class*="cookie"]'
        ];
        for (let sel of selectors) {
            document.querySelectorAll(sel).forEach(el => el.remove());
        }

        // Prevent scrolling lock (common on modals)
        document.body.style.overflow = 'auto';
    """
    driver.execute_script(js_cleanup)



def fix_layout(driver):
    css_fix = '''
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

            figcaption, .caption, [class*="caption"], .MediaCaption__text {
                display: block;
                font-size: 0.9em;
                color: #555;
                margin-top: 0.3em;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    '''
    driver.execute_script(css_fix)



def fix_layoutv1(driver):
    css_fix = '''
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
        `;
        document.head.appendChild(style);
    '''
    driver.execute_script(css_fix)



def isolate_main_content(driver):
    js_ap_hardcore_cleanup = """
        // Helper to remove elements by selector
        function zap(selectors) {
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        }

        // Remove common clutter
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

        // Try to isolate main content
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
        }

        // As a final punch: hide any floating/fixed elements
        document.querySelectorAll("*").forEach(el => {
            const style = window.getComputedStyle(el);
            if (["fixed", "sticky"].includes(style.position)) {
                el.style.display = "none";
            }
        });
    """
    driver.execute_script(js_ap_hardcore_cleanup)




def save_page_as_pdf(driver, output_path):
    #time.sleep(2)
    pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "paperWidth": 5.8,
        "paperHeight": 8.3,
        "marginTop": 0.4,
        "marginBottom": 0.4,
        "marginLeft": 0.4,
        "marginRight": 0.4,
        "scale": 0.9,
    })["data"]
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(pdf_data))


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_welcome():
    print("Welcome to RemarkablePageScribe! Enter a URL to save as a ReMarkable PDF.")
    print("Type 'q' or 'quit' to exit.\n")
    print('URL:')




def main():
    driver = create_driver()

    while True:
        # Clear console.
        clear_console()
        # Print welcome message.
        print_welcome()

        # Get URL from user
        url = input("Paste URL: ").strip()
        if url.lower() in {"q", "quit"}:
            break
        try:
            print(f"[OPENING] {url}")
            driver.get(url)
            #act_human(driver)

            title = driver.title or "webpage"
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = sanitize_filename(f"{timestamp}_{title}") + ".pdf"
            filepath = os.path.join(OUTPUT_DIR, filename)

            print(f"[SAVING PDF] → {filepath}")
            #remove_popups(driver)
            isolate_main_content(driver)
            fix_layout(driver)
            save_page_as_pdf(driver, filepath)

            print("[DONE]\n")

            time.sleep(2)
            os.system("cls")
        except Exception as e:
            print(f"[ERROR] Failed to process: {e}\n")

    driver.quit()
    print("Goodbye!")


if __name__ == "__main__":
    main()
