import os
import time
import logging
import requests
import json
from tqdm import tqdm
from typing import List, Set, Optional, Dict, Tuple
from threading import Lock

class NhatotScraper:
    
    def __init__(
        self,
        output_file: str = "/opt/airflow/data/hn_nhatot_links.txt",
        error_file: str = "/opt/airflow/data/hn_nhatot_error_links.txt",
        base_url: str = "https://www.nhatot.com",
        region_v2: int = 12000,  # Hanoi region
        cg: int = 1000,  # Real estate category
        save_interval: int = 10,
        retry_attempts: int = 5,
        retry_delay: int = 3
    ):
        
        self.output_file = output_file
        self.error_file = error_file
        self.base_url = base_url
        self.region_v2 = region_v2
        self.cg = cg
        self.save_interval = save_interval
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.all_links = set()
        self.error_urls = []
        self.links_lock = Lock()
        self.error_urls_lock = Lock()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        os.makedirs(os.path.dirname(error_file), exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("NhatotScraper")
    
    def clear_file(self, file_path: str) -> None:
        """Clear the contents of a file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.truncate(0)
        self.logger.info(f"Cleared file: {file_path}")

    def write_links(self, file_path: str, links: Set[str]) -> None:
        """Write links to a file"""
        self.clear_file(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            for link in sorted(links):
                f.write(link + '\n')
        self.logger.info(f"✅ Written {len(links)} links to {file_path}")

    def get_api_data(self, start_partition: int, page: int) -> Optional[Dict]:
        """Fetch data from Nhatot API with retry mechanism"""
        api_gateway = 'https://gateway.chotot.com/v1/public/ad-listing?region_v2={}&cg={}&o={}&page={}&st=s,k&limit=20&w=1&key_param_included=true'
        api_url = api_gateway.format(self.region_v2, self.cg, start_partition, page)
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(api_url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
        
        self.logger.error(f"Failed to fetch data from API after {self.retry_attempts} attempts: {api_url}")
        with self.error_urls_lock:
            self.error_urls.append(f"API request failed for page {page}: {api_url}")
        return None

    def load_existing_links(self) -> None:
        """Load existing links from the output file if it exists"""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                self.all_links.update(f.read().splitlines())
            self.logger.info(f"Loaded {len(self.all_links)} existing links")

    def scrape_links(self) -> bool:
        """Main function to scrape property links from Nhatot"""
        self.load_existing_links()
        self.error_urls = []

        # Get initial data to determine total number of pages
        initial_data = self.get_api_data(0, 1)
        if not initial_data:
            self.logger.error("Failed to get initial data from API")
            return False

        total_news = initial_data['total']
        max_pages = total_news // 20 + 1
        self.logger.info(f"Total listings: {total_news}, Max pages: {max_pages}")

        # Process each page
        for page_th in tqdm(range(1, max_pages + 1)):
            start_partition = (page_th - 1) * 20
            data = self.get_api_data(start_partition, page_th)

            if not data:
                continue

            if len(data.get('ads', [])) != 0:
                with self.links_lock:
                    for item in data['ads']:
                        list_id = item['list_id']
                        link = f"{self.base_url}/mua-ban-bat-dong-san/{list_id}.htm"
                        self.all_links.add(link)

            # Save progress every save_interval pages
            if page_th % self.save_interval == 0:
                self.write_links(self.output_file, self.all_links)
                time.sleep(1)  # Small delay to prevent overwhelming the API

        # Final save of all links
        self.write_links(self.output_file, self.all_links)

        # Log any errors
        if self.error_urls:
            with open(self.error_file, 'w', encoding='utf-8') as ef:
                for url in self.error_urls:
                    ef.write(url + '\n')
            self.logger.warning(f"❌ Failed to scrape {len(self.error_urls)} pages. Logged in {self.error_file}")

        self.logger.info("✅ Scraping completed.")
        return True

    def run(self) -> bool:
        """Main entry point for the scraper"""
        return self.scrape_links()


def scrape_links(
    output_file: str = "/opt/airflow/data/hn_nhatot_links.txt",
    error_file: str = "/opt/airflow/data/hn_nhatot_error_links.txt",
    base_url: str = "https://www.nhatot.com",
    region_v2: int = 12000,
    cg: int = 1000
):
    """Function to be used as an Airflow task"""
    scraper = NhatotScraper(
        output_file=output_file,
        error_file=error_file,
        base_url=base_url,
        region_v2=region_v2,
        cg=cg
    )
    return scraper.run()


if __name__ == "__main__":
    scrape_links() 