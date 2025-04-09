from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
import os

def save_data(url_data, data):
    url_tsv_file = "/Users/ducan/Documents/test/data/batdongsan_url.tsv"
    data_tsv_file = "/Users/ducan/Documents/test/data/batdongsan.tsv"

    url_df = pd.DataFrame([url_data])
    data_df = pd.DataFrame([data])

    def write_with_header(df, file_path):
        write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
        df.to_csv(file_path, sep='\t', index=False, mode='a', header=write_header)

    if url_data is not None:
        write_with_header(url_df, url_tsv_file)
    if data is not None:    
        write_with_header(data_df, data_tsv_file)


def convert_date_format(date_str: str) -> str:
    try:
        # Convert from DD/MM/YYYY to YYYY-MM-DD
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        # If the date is not in the expected format, return None or a default value
        return None

def extract_number_from_text(text: str):
    if text:
        match = re.search(r'\d+', text)
        if match:
            return int(match.group(0))
    return None

def extract_id_from_url(url: str):
    pattern = r'pr\d+'
    match = re.search(pattern, url)
    if match:
        return match.group(0)
    else:
        return None


def scrape_data(url, max_retries=5):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    attempts = 0
    soup = None
    
    while attempts < max_retries:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        if soup.find_all('div', class_='re__pr-short-info-item js__pr-config-item'):
            break
        attempts += 1

    if attempts == max_retries:
        print(f"Failed to load page after {max_retries} attempts: {url}")
        driver.quit()
        return None, None


    # html_content = driver.page_source
    # soup = BeautifulSoup(html_content, 'html.parser')

    url_data = {
        "id": "",
        "url": url,
        "status": 0,
        "source_id": 1,
        "source_name": "batdongsan.com.vn",
        "posted_date": "",
        "due_date": "",
        "updated_date": datetime.now().strftime('%Y-%m-%d')
    }

    data = {
        "Tên": None,
        "url_id": None,
        "Diện tích": None,
        "Mặt tiền": None,
        "Mức giá": None,
        "Hướng nhà": None,
        "Số phòng ngủ": None,
        "Số phòng tắm, vệ sinh": None,
        "Nội thất": None,
        "Pháp lý": None,
        "lat": None,
        "lon": None,
        "Địa chỉ": None,
        "Quận": None,
        "Thành phố": None
    }

    # Process url data
    date_body = soup.find_all('div', class_='re__pr-short-info-item js__pr-config-item')
    for item in date_body:
        title_span = item.find('span', class_='title')
        value_span = item.find('span', class_='value')
        if title_span and value_span:
            title = title_span.text.strip()
            value = value_span.text.strip()
            if title == "Ngày đăng":
                url_data["posted_date"] = convert_date_format(value)
            elif title == "Ngày hết hạn":
                url_data["due_date"] = convert_date_format(value)

    # Extract id from url
    url_data["id"] = extract_id_from_url(url)


    # Process real estate data
    address = soup.find('span', class_='re__pr-short-description js__pr-address')
    data["Địa chỉ"] = address.text.strip() if address else None

    # Get coordinates (lat, lon)
    map_section = soup.find('div', class_='re__section re__pr-map js__section js__li-other')
    if map_section:
        iframe = map_section.find('iframe', {'data-src': True})
        if iframe and iframe.has_attr('data-src'):
            match = re.search(r'q=([-+]?\d*\.\d+),([-+]?\d*\.\d+)', iframe['data-src'])
            if match:
                data["lat"] = match.group(1)
                data["lon"] = match.group(2)

    # Extract city, district, and title from tabs
    tabs = soup.find_all('a', class_='re__link-se')
    for tab in tabs:
        level_value = tab.get('level')
        if level_value == "2":
            data["Thành phố"] = tab.text.strip()
        elif level_value == "3":
            data["Quận"] = tab.text.strip()
        elif level_value == "4":
            data["Tên"] = tab.text.strip()


    section_body = soup.find('div', class_='re__pr-specs-content-v2 js__other-info')

    # Process real estate specifications (e.g., area, price)
    section_body = soup.find('div', class_='re__pr-specs-content-v2 js__other-info')
    if section_body:
        specs_items = section_body.find_all('div', class_='re__pr-specs-content-item')
        for item in specs_items:
            title = item.find('span', class_='re__pr-specs-content-item-title').text.strip()
            value = item.find('span', class_='re__pr-specs-content-item-value').text.strip()
            if title in data:
                data[title] = value

    key_mapping = {
        "Tên": "title",
        "Diện tích": "area",
        "Mặt tiền": "width",
        "Mức giá": "price",
        "Hướng nhà": "direction",
        "Số phòng ngủ": "number_of_bedrooms",
        "Số phòng tắm, vệ sinh": "number_of_toilets",
        "Nội thất": "furniture",
        "Pháp lý": "legal",
        "Địa chỉ": "address",
        "Quận": "district",
        "Thành phố": "province"
    }
    data = {key_mapping.get(old_key, old_key): value for old_key, value in data.items()}

    # Extract number of bedrooms and toilets (if any)
    # data["number_of_bedrooms"] = extract_number_from_text(data.get("number_of_bedrooms", ""))
    # data["number_of_toilets"] = extract_number_from_text(data.get("number_of_toilets", ""))
    data["url_id"] = url_data["id"]

    if data["title"] is not None: 
        url_data["status"] = 1
    else:
        data = None
    

    # Close the browser
    driver.quit()

    print(url_data)
    print(data)
    # Save data to the database
    save_data(url_data, data)

    return url_data, data


if __name__ == '__main__':
    input_file = "/Users/ducan/Documents/test/data/batdongsan_links.txt"  

    with open(input_file, 'r', encoding='utf-8') as file:
        links = file.read().splitlines()

    for link in links:
        print(f"Scraping data from: {link}")
        try:
            scrape_data(link)
        except Exception as e:
            print(f"Error scraping {link}: {e}")
    print("Scraping completed.")     