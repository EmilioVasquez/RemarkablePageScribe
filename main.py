import os
import time
import random
import base64
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service  # not needed with Selenium Manager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
# from webdriver_manager.chrome import ChromeDriverManager  # <-- removed, caused bad path
from bs4 import BeautifulSoup
from datetime import datetime

# ----- Configuration -----
BASE_URL       = "https://www.theatlantic.com"
LATEST_URL     = f"{BASE_URL}/latest/"
OUTPUT_DIR     = r"C:\Users\efv\Desktop\news_scrapers\RemarkablePageScribe\downloads"
TRACK_FILE     = "downloaded_articles.txt"
USER_DATA_DIR  = r"C:\temp\chrome_test"
PROFILE_NAME   = "Default"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----- Logging Setup -----
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file_path = os.path.join(LOG_DIR, f"scraper_{timestamp_str}.log")

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clear any existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# File handler
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)

# Console (stream) handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("=== Script Start ===")

def sanitize_filename(name):
    name = name.replace(":", " - ").replace("/", "-").replace("?", "").replace('"', '').replace(".", "")
    keep = (" ", "-", "_", "[", "]")
    cleaned = "".join(c for c in name if c.isalnum() or c in keep)
    return cleaned.strip().replace("  ", " ")  # collapse double spaces

def create_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    opts.add_argument(f"--profile-directory={PROFILE_NAME}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--headless=new")  # Comment this out to see browser

    # === FIX: Use Selenium Manager instead of webdriver_manager ===
    # This avoids the WinError 193 from picking a non-executable file.
    return webdriver.Chrome(options=opts)

def act_human(driver):
    height = driver.execute_script("return document.body.scrollHeight")
    for pos in range(0, height, random.randint(300, 800)):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(random.uniform(0.5, 1.5))
    elems = driver.find_elements(By.CSS_SELECTOR, "img, a.LandingRiver_titleLink__nUImQ")
    if elems:
        el = random.choice(elems)
        try:
            ActionChains(driver).move_to_element(el).perform()
            time.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            logging.warning(f"Hovering failed: {e}")

def extract_article_metadata(driver):
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-flatplan-title="true"]'))
        )
    except:
        logging.warning("Timed out waiting for article content to load.")

    soup = BeautifulSoup(driver.page_source, "html.parser")

    def sel_text(q):
        el = soup.select_one(q)
        return el.get_text(strip=True) if el else "Unknown"

    def sel_attr(q, attr):
        el = soup.select_one(q)
        return el.get(attr) if el and el.has_attr(attr) else None

    section = sel_text('[data-flatplan-rubric="true"]')
    title   = sel_text('[data-flatplan-title="true"]')
    author  = sel_text('[data-flatplan-author-link="true"]')
    iso     = sel_attr('time[data-flatplan-timestamp="true"]', "datetime") or ""
    timestamp = iso.rstrip("Z").replace(":", "-") if iso else "UnknownDate"

    logging.info(f"Metadata -> Section: {section}, Title: {title}, Author: {author}, Time: {timestamp}")
    return section, title, author, timestamp

def save_page_as_pdf(driver, output_path):
    time.sleep(random.uniform(2, 5))
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
    logging.info(f"Saved PDF to: {output_path}")

def load_downloaded_articles():
    if not os.path.exists(TRACK_FILE):
        return set()
    with open(TRACK_FILE) as f:
        return set(line.strip() for line in f)

def mark_article_downloaded(url):
    with open(TRACK_FILE, "a") as f:
        f.write(url + "\n")  # <-- FIX: real newline
    logging.info(f"Marked as downloaded: {url}")

def get_article_links(driver):
    driver.get(LATEST_URL)
    time.sleep(random.uniform(5, 15))
    act_human(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = list({a["href"] for a in soup.select("a.LandingRiver_titleLink__nUImQ[href^='https://']")})
    logging.info(f"Found {len(links)} article links.")
    return links

def main():
    seen = load_downloaded_articles()
    driver = create_driver()

    links = get_article_links(driver)

    for url in links:
        if url in seen:
            logging.info(f"[SKIP] Already downloaded: {url}")
            continue

        try:
            logging.info(f"[NAVIGATE] {url}")
            driver.get(url)
            act_human(driver)

            section, title, author, timestamp = extract_article_metadata(driver)
            raw_name = f"{timestamp} [{section}] {title} - {author}"
            filename = sanitize_filename(raw_name) + ".pdf"
            outpath  = os.path.join(OUTPUT_DIR, filename)

            save_page_as_pdf(driver, outpath)
            mark_article_downloaded(url)

            driver.get(LATEST_URL)
            wait = random.uniform(5, 15)
            logging.info(f"[WAIT] Sleeping for {wait:.1f}s before next article")
            time.sleep(wait)

        except Exception as e:
            logging.error(f"[ERROR] Could not process {url}: {e}")

    driver.quit()
    logging.info("=== Script End ===")

if __name__ == "__main__":
    main()
