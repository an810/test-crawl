import os
import time
import logging
import requests
import json
from tqdm import tqdm

OUTPUT_FILE = "/Users/ducan/Documents/test/data/hn_nhatot_links.txt"
ERROR_FILE = "/Users/ducan/Documents/test/data/hn_nhatot_error_links.txt"
BASE_URL = "https://www.nhatot.com"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_file(file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.truncate(0)

def write_links(file_path, links):
    clear_file(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(link + '\n')
    logging.info(f"✅ Written {len(links)} links to {file_path}")

def get_api_data(region_v2, cg, start_partition, page):
    api_gateway = 'https://gateway.chotot.com/v1/public/ad-listing?region_v2={}&cg={}&o={}&page={}&st=s,k&limit=20&w=1&key_param_included=true'
    api_url = api_gateway.format(region_v2, cg, start_partition, page)
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching data from API: {e}")
        return None

def scrape_links():
    all_links = set()
    error_urls = []

    # Load existing links if file exists
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            all_links.update(f.read().splitlines())

    # API parameters
    region_v2 = 12000  # Hanoi region
    cg = 1000  # Real estate category
    page = 1

    # Get initial data to determine total number of pages
    initial_data = get_api_data(region_v2, cg, 0, page)
    if not initial_data:
        logging.error("Failed to get initial data from API")
        return

    total_news = initial_data['total']
    max_pages = total_news // 20 + 1
    logging.info(f"Total listings: {total_news}, Max pages: {max_pages}")

    # Process each page
    for page_th in tqdm(range(1, max_pages + 1)):
        start_partition = (page_th - 1) * 20
        data = get_api_data(region_v2, cg, start_partition, page_th)

        if not data:
            error_urls.append(f"API request failed for page {page_th}")
            continue

        if len(data.get('ads', [])) != 0:
            for item in data['ads']:
                list_id = item['list_id']
                link = f"{BASE_URL}/mua-ban-bat-dong-san/{list_id}.htm"
                all_links.add(link)

        # Save progress every 10 pages
        if page_th % 10 == 0:
            write_links(OUTPUT_FILE, all_links)
            time.sleep(1)  # Small delay to prevent overwhelming the API

    # Final save of all links
    write_links(OUTPUT_FILE, all_links)

    # Log any errors
    if error_urls:
        with open(ERROR_FILE, 'w', encoding='utf-8') as ef:
            for url in error_urls:
                ef.write(url + '\n')
        logging.warning(f"❌ Failed to scrape {len(error_urls)} pages. Logged in {ERROR_FILE}")

    logging.info("✅ Scraping completed.")

if __name__ == "__main__":
    scrape_links()
