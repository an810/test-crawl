from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
import os
import tempfile
import shutil
from multiprocessing import Pool, Lock, Manager
import time
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define output directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def ensure_directories_exist():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info(f"Created directory: {DATA_DIR}")

def save_data(lock, url_data, data):
    """Save scraped data to TSV files"""
    url_file = os.path.join(DATA_DIR, "hn_nhatot_url.tsv")
    data_file = os.path.join(DATA_DIR, "hn_nhatot.tsv")

    with lock:
        # Save URL data
        url_df = pd.DataFrame([url_data])
        url_df.to_csv(url_file, mode='a', header=not os.path.exists(url_file), 
                     sep='\t', index=False, encoding='utf-8')

        # Save property data if available
        if data:
            data_df = pd.DataFrame([data])
            data_df.to_csv(data_file, mode='a', header=not os.path.exists(data_file), 
                          sep='\t', index=False, encoding='utf-8')

def extract_id_from_url(url):
    """Extract item ID from URL"""
    match = re.search(r'/(\d+)\.htm', url)
    return match.group(1) if match else None

def load_crawled_ids(file_path):
    """Load already crawled IDs from TSV file"""
    if not os.path.exists(file_path):
        return set()
    df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
    return set(df['id'].astype(str))

def scrape_one_url(args):
    """Scrape a single URL"""
    url, lock, crawled_ids = args
    driver = None
    user_data_dir = None

    try:
        # Create temporary user data directory
        user_data_dir = tempfile.mkdtemp()
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page load
        time.sleep(random.uniform(2, 4))
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # Check for error pages
        if 'Please try again later!' in soup.find('body').get_text():
            driver.refresh()
            time.sleep(random.uniform(2, 4))
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

        if soup.find('div', class_='NotFound_warning__dwnf5'):
            return

        # Try to click "Xem thêm" button if exists
        try:
            button = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Xem thêm')]"))
            )
            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)
        except TimeoutException:
            logging.info(f"No 'Xem thêm' button found on {url}")

        # Extract item ID
        item_id = extract_id_from_url(url)
        if not item_id:
            return

        # Prepare URL data
        url_data = {
            "id": item_id,
            "url": url,
            "status": 0,
            "source_id": 3,  # Unique ID for nhatot
            "source_name": "nhatot.com",
            "posted_date": "",
            "due_date": "",
            "updated_date": datetime.now().strftime('%Y-%m-%d')
        }

        # Prepare property data
        data = {
            "title": None,
            "url_id": url_data["id"],
            "area": None,
            "width": None,
            "price": None,
            "direction": None,
            "number_of_bedrooms": None,
            "number_of_toilets": None,
            "furniture": None,
            "legal": None,
            "lat": None,
            "lon": None,
            "address": None,
            "district": None,
            "province": None
        }

        # Extract title
        title_tag = soup.find('h1', class_='AdDecriptionVeh_adTitle__vEuKD')
        data["title"] = title_tag.text.strip() if title_tag else None

        # Extract price
        price_span = soup.find('span', class_='AdDecriptionVeh_price__u_N83')
        data["price"] = price_span.text.split('-')[0].strip() if price_span else None

        # Extract address
        address_tag = soup.find('div', class_='media-body media-middle AdParam_address__5wp1F AdParam_addressClickable__coDWA')
        if address_tag:
            span = address_tag.find('span', class_='fz13')
            if span:
                sub = span.find('span', class_='AdParam_addressClickableLoadMap__FLeKT')
                if sub:
                    sub.extract()
                data["address"] = span.text.strip()

        # Extract province and district
        if data["address"]:
            match_city = re.search(r',\s*([^,]+)$', data["address"])
            if match_city:
                data["province"] = match_city.group(1).strip()
            match_district = re.search(r'(Quận|Huyện|Thị xã)\s*([^,]+)', data["address"])
            if match_district:
                data["district"] = match_district.group(2).strip()

        # Extract coordinates
        for tag in soup.find_all('script'):
            text = str(tag)
            if "longitude" in text and "latitude" in text:
                lon_match = re.search(r'longitude":([\d\.\-]+)', text)
                lat_match = re.search(r'latitude":([\d\.\-]+)', text)
                if lon_match and lat_match:
                    data["lon"] = lon_match.group(1)
                    data["lat"] = lat_match.group(1)
                break

        # Extract property specifications
        specs_items = soup.find_all('div', class_='media-body media-middle')
        label_map = {
            "Diện tích đất": "area",
            "Chiều ngang": "width",
            "Hướng cửa chính": "direction",
            "Số phòng ngủ": "number_of_bedrooms",
            "Số phòng vệ sinh": "number_of_toilets",
            "Tình trạng nội thất": "furniture",
            "Giấy tờ pháp lý": "legal"
        }

        for item in specs_items:
            parts = item.get_text(strip=True).split(':')
            if len(parts) == 2:
                label, value = parts[0].strip(), parts[1].strip()
                key = label_map.get(label)
                if key:
                    data[key] = value

        url_data["status"] = 1 if data["title"] else 0
        if not data["title"]:
            data = None

        save_data(lock, url_data, data)

    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
    finally:
        if driver:
            driver.quit()
        if user_data_dir:
            shutil.rmtree(user_data_dir)

def scrape_data(use_multiprocessing=False):
    """Main function to scrape all URLs"""
    try:
        ensure_directories_exist()
        
        # Read URLs from file
        file_path = os.path.join(DATA_DIR, 'hn_nhatot_links.txt')
        with open(file_path, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip() and 'nhatot.com' in line]

        logging.info(f"Found {len(urls)} URLs to scrape")

        if use_multiprocessing:
            # Use multiprocessing for parallel scraping
            # Use multiprocessing for parallel scraping
            with Pool() as pool:
                manager = Manager()
                lock = manager.Lock()
                crawled_ids = load_crawled_ids(os.path.join(DATA_DIR, "hn_nhatot_url.tsv"))
                
                args = [(url, lock, crawled_ids) for url in urls]
                pool.map(scrape_one_url, args)
        else:
            # Single process scraping
            lock = Lock()
            crawled_ids = load_crawled_ids(os.path.join(DATA_DIR, "hn_nhatot_url.tsv"))
            
            for url in urls:
                item_id = extract_id_from_url(url)
                if item_id in crawled_ids:
                    logging.info(f"[Skipped] Already crawled: {url}")
                    continue
                
                try:
                    scrape_one_url((url, lock, crawled_ids))
                    crawled_ids.add(item_id)
                except Exception as e:
                    logging.error(f"Error scraping {url}: {e}")
                    continue

        logging.info("✅ Scraping completed successfully")
        return True

    except Exception as e:
        logging.error(f"Error in scrape_data: {e}")
        return False

if __name__ == "__main__":
    # This block only runs if the script is executed directly
    scrape_data(use_multiprocessing=True)