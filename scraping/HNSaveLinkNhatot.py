import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_FILE = "/home/ducan/Documents/anmd/test-crawl/data/hn_nhatot_links.txt"
ERROR_FILE = "/home/ducan/Documents/anmd/test-crawl/data/hn_nhatot_error_links.txt"
BASE_URL = "https://www.nhatot.com"
PAGE_PATH = "/mua-ban-bat-dong-san-ha-noi?price=7000000000-30000000000&page="

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def clear_file(file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.truncate(0)


def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(options=options)


def get_page_with_retries(driver, url, retries=5, delay=3):
    for attempt in range(retries):
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/mua-ban-'][href$='.htm']"))
            )
            time.sleep(random.uniform(1, 2))  # nhẹ hơn
            return driver.page_source
        except Exception as e:
            logging.warning(f"[Attempt {attempt+1}] Failed to get page: {e}")
            time.sleep(delay)
    return None


def write_links(file_path, links):
    clear_file(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(link + '\n')
    logging.info(f"✅ Written {len(links)} links to {file_path}")


def get_page_links(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    if soup.find('div', class_='NotFound_content__KtIbC'):
        return None

    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/mua-ban-') and '.htm' in href:
            full_url = base_url + href
            
            links.add(full_url)
    logging.info(f"Found {len(links)} links on the page.")
    return links


def scrape_links():
    all_links = set()

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            all_links.update(f.read().splitlines())

    error_urls = []
    driver = create_driver()
    page_index = 1

    try:
        while page_index < 10:
            full_url = BASE_URL + PAGE_PATH + str(page_index)
            logging.info(f"[Scraping] {full_url}")
            html_content = get_page_with_retries(driver, full_url)

            if not html_content:
                error_urls.append(full_url)
                break  # Optional: or continue depending on tolerance
            page_links = get_page_links(html_content, BASE_URL)

            if page_links is None:
                logging.warning(f"[Stop] Page {page_index} is empty or not found.")
                break

            all_links.update(page_links)

            if page_index % 10 == 0:
                write_links(OUTPUT_FILE, all_links)

            page_index += 1
            time.sleep(1)

    finally:
        driver.quit()

    write_links(OUTPUT_FILE, all_links)

    if error_urls:
        with open(ERROR_FILE, 'w', encoding='utf-8') as ef:
            for url in error_urls:
                ef.write(url + '\n')
        logging.warning(f"❌ Failed to scrape {len(error_urls)} pages. Logged in {ERROR_FILE}")

    logging.info("✅ Scraping completed.")


if __name__ == "__main__":
    scrape_links()
