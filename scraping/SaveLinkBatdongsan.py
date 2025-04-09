from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import random
import logging

def get_page_with_retries(driver, url, retries=10, delay=10):
    for attempt in range(retries): 
        try:
            driver.get(url)
            return driver.page_source
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception(f"Failed to load page after {retries} attempts: {url}")


def clear_file(file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.truncate(0)  

def scrape_links():
    output_file = "/Users/ducan/Documents/test/data/batdongsan_links.txt"
    error_file = "/Users/ducan/Documents/test/data/batdongsan_error_links.txt"
    
    unscraped_links = set()
    with open(output_file, 'r', encoding='utf-8') as existing_links_file:
        existing_links = existing_links_file.read().splitlines()
        unscraped_links.update(existing_links)
    sourceUrl = 'https://batdongsan.com.vn/nha-dat-ban'
    path = "?gtn=7-ty&gcn=30-ty"
    filter_path = "?gtn=7-ty&gcn=30-ty"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)


    page_index = 0

    while page_index < 3058:
        page_index += 1
        driver = webdriver.Chrome(options=chrome_options)
        page_path = "/p" + str(page_index)
        full_path = sourceUrl + page_path + filter_path
        driver.get(full_path)
        print(full_path)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # Tìm tất cả các phần tử <a> với class 'js__product-link-for-product-id'
        links = soup.find_all('a', class_='js__product-link-for-product-id')
        print(f"Number of links found on page {page_index}: {len(links)}")

        if len(links) == 0:
            with open(error_file, 'a', encoding='utf-8') as ef:
                ef.write(full_path + '\n')
                print("Writing error link: " + full_path)

        for link in links:
            if link.get('data-product-id') == "0":
                continue
            href = link.get('href')
            unscraped_links.add(sourceUrl + href)

        if page_index % 10 == 0:
            clear_file(output_file)
            with open(output_file, 'a', encoding='utf-8') as linksfile:
                for link in unscraped_links:
                    linksfile.write(link + '\n')
            print(f"Links have been written to {output_file}")

        driver.quit()


    print("Retrying error URLs...")

    # if not os.path.exists(error_file):
    #     print("No error file found. Done.")
    #     return

    with open(error_file, 'r', encoding='utf-8') as ef:
        error_urls = ef.read().splitlines()

    remaining_errors = []

    for url in error_urls:
        success = False
        for attempt in range(5):
            print(f"Retrying ({attempt+1}/5): {url}")
            driver = webdriver.Chrome(options=chrome_options)
            try:
                driver.get(url)
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                links = soup.find_all('a', class_='js__product-link-for-product-id')

                if links:
                    print(f"✅ Success on attempt {attempt+1}: Found {len(links)} links.")
                    for link in links:
                        if link.get('data-product-id') == "0":
                            continue
                        href = link.get('href')
                        unscraped_links.add(sourceUrl + href)
                    success = True
                    driver.quit()
                    break  # Exit retry loop
                else:
                    print("No links found.")
                driver.quit()
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                driver.quit()
                time.sleep(3)

        if not success:
            remaining_errors.append(url)

    # Write updated error file
    with open(error_file, 'w', encoding='utf-8') as ef:
        for url in remaining_errors:
            ef.write(url + '\n')
    print(f"Retry complete. {len(remaining_errors)} failed pages remaining in {error_file}.")

    # Final save of all collected links
    clear_file(output_file)
    with open(output_file, 'w', encoding='utf-8') as linksfile:
        for link in unscraped_links:
            linksfile.write(link + '\n')

    print(f"Final links written to {output_file}")

if __name__ == "__main__":
    scrape_links()
