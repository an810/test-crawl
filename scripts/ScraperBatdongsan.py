from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
import os
import tempfile
import shutil
from multiprocessing import Pool, Lock, Manager
import time


def save_data(lock, url_data, data):
    url_tsv_file = "/home/ducan/Documents/anmd/test-crawl/data/batdongsan_url.tsv"
    data_tsv_file = "/home/ducan/Documents/anmd/test-crawl/data/batdongsan.tsv"

    url_df = pd.DataFrame([url_data])
    data_df = pd.DataFrame([data])

    def write_with_header(df, file_path):
        write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
        with lock:
            df.to_csv(file_path, sep='\t', index=False, mode='a', header=write_header)

    if url_data is not None:
        write_with_header(url_df, url_tsv_file)
    if data is not None:
        write_with_header(data_df, data_tsv_file)


def convert_date_format(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        return None


def extract_id_from_url(url: str):
    match = re.search(r'pr\d+', url)
    return match.group(0) if match else None


def create_driver(user_data_dir):
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    # chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(options=chrome_options)


def scrape_one_url(args):
    url, lock, crawled_ids = args
    item_id = extract_id_from_url(url)
    if item_id in crawled_ids:
        print(f"[Skipped] Already crawled: {url}")
        return

    print(f"[Scraping] {url}")
    user_data_dir = tempfile.mkdtemp()
    driver = None
    try:
        driver = create_driver(user_data_dir)

        max_retries = 5
        success = False
        soup = None

        for attempt in range(max_retries):
            try:
                driver.get(url)
            except Exception as e:
                print(f"[Error] Failed to connect to {url}: {e}")
                return
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            if soup.find('div', class_='re__pr-short-info-item js__pr-config-item'):
                success = True
                break
            print(f"[Retry {attempt+1}] Retrying load for {url}")
            time.sleep(1)

        if not success:
            print(f"[Timeout] Failed to load key content: {url}")
            return

        url_data = {
            "id": item_id,
            "url": url,
            "status": 0,
            "source_id": 1,
            "source_name": "batdongsan.com.vn",
            "posted_date": "",
            "due_date": "",
            "updated_date": datetime.now().strftime('%Y-%m-%d')
        }

        data = {
            "title": None,
            "url_id": item_id,
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

        for item in soup.find_all('div', class_='re__pr-short-info-item js__pr-config-item'):
            title_span = item.find('span', class_='title')
            value_span = item.find('span', class_='value')
            if title_span and value_span:
                title = title_span.text.strip()
                value = value_span.text.strip()
                if title == "Ngày đăng":
                    url_data["posted_date"] = convert_date_format(value)
                elif title == "Ngày hết hạn":
                    url_data["due_date"] = convert_date_format(value)

        address = soup.find('span', class_='re__pr-short-description js__pr-address')
        data["address"] = address.text.strip() if address else None

        map_section = soup.find('div', class_='re__section re__pr-map js__section js__li-other')
        if map_section:
            iframe = map_section.find('iframe', {'data-src': True})
            if iframe and iframe.has_attr('data-src'):
                match = re.search(r'q=([-+]?\d*\.\d+),([-+]?\d*\.\d+)', iframe['data-src'])
                if match:
                    data["lat"] = match.group(1)
                    data["lon"] = match.group(2)

        for tab in soup.find_all('a', class_='re__link-se'):
            level = tab.get('level')
            if level == "2":
                data["province"] = tab.text.strip()
            elif level == "3":
                data["district"] = tab.text.strip()
            elif level == "4":
                data["title"] = tab.text.strip()

        specs = soup.find('div', class_='re__pr-specs-content-v2 js__other-info')
        if specs:
            for item in specs.find_all('div', class_='re__pr-specs-content-item'):
                title = item.find('span', class_='re__pr-specs-content-item-title').text.strip()
                value = item.find('span', class_='re__pr-specs-content-item-value').text.strip()
                key_map = {
                    "Diện tích": "area",
                    "Mặt tiền": "width",
                    "Mức giá": "price",
                    "Hướng nhà": "direction",
                    "Số phòng ngủ": "number_of_bedrooms",
                    "Số phòng tắm, vệ sinh": "number_of_toilets",
                    "Nội thất": "furniture",
                    "Pháp lý": "legal"
                }
                if title in key_map:
                    data[key_map[title]] = value

        url_data["status"] = 1 if data["title"] else 0
        if not data["title"]:
            data = None

        save_data(lock, url_data, data)

    except Exception as e:
        print(f"[Unhandled Error] Failed to scrape {url}: {e}")
    finally:
        if driver:
            driver.quit()
        shutil.rmtree(user_data_dir)


def load_crawled_ids(tsv_file_path):
    if not os.path.exists(tsv_file_path):
        return set()
    df = pd.read_csv(tsv_file_path, sep='\t', usecols=["id"])
    return set(df["id"].astype(str))


# if __name__ == '__main__':
#     input_file = "/home/ducan/Documents/anmd/test-crawl/data/batdongsan_links.txt"
#     url_tsv_file = "/home/ducan/Documents/anmd/test-crawl/data/batdongsan_url.tsv"

#     crawled_ids = load_crawled_ids(url_tsv_file)

#     with open(input_file, 'r', encoding='utf-8') as file:
#         links = file.read().splitlines()

#     with Manager() as manager:
#         lock = manager.Lock()
#         shared_ids = manager.list(crawled_ids)

#         jobs = [(url, lock, shared_ids) for url in links]

#         with Pool(processes=5) as pool:  # Adjust number of processes based on your system
#             pool.map(scrape_one_url, jobs)

#     print("✅ Scraping completed.")

def scrape_data():
    """
    Main scraping function that can be called by the Airflow DAG
    """
    try:
        # Read links from file
        with open('/opt/airflow/data/batdongsan_links.txt', 'r', encoding='utf-8') as f:
            urls = f.read().splitlines()

        # Initialize list to store all property data
        all_properties = []
        
        # Process each URL
        for url in urls:
            try:
                property_data = scrape_property_data(url)
                all_properties.append(property_data)
                time.sleep(random.uniform(1, 3))  # Random delay between requests
            except Exception as e:
                logging.error(f"Error scraping {url}: {e}")
                continue

        # Convert to DataFrame and save
        df = pd.DataFrame(all_properties)
        output_path = '/opt/airflow/data/batdongsan_data.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logging.info(f"Successfully scraped {len(all_properties)} properties")
        return True

    except Exception as e:
        logging.error(f"Error in scrape_data: {e}")
        return False

if __name__ == "__main__":
    # This block only runs if the script is executed directly
    scrape_data()