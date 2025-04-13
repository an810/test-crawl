from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import random
import logging
import os
from typing import List, Set, Optional

class BatDongSanScraper:
    """
    A class to scrape property links from BatDongSan website.
    Designed to be used in DAGs and other workflow systems.
    """
    
    def __init__(
        self,
        output_file: str = "/opt/airflow/data/batdongsan_links.txt",
        error_file: str = "/opt/airflow/data/batdongsan_error_links.txt",
        base_url: str = "https://batdongsan.com.vn/nha-dat-ban",
        filter_path: str = "?gtn=7-ty&gcn=30-ty",
        max_pages: int = 3058,
        save_interval: int = 10,
        retry_attempts: int = 5,
        retry_delay: int = 3
    ):
        """
        Initialize the scraper with configurable parameters.
        
        Args:
            output_file: Path to save the scraped links
            error_file: Path to save error URLs
            base_url: Base URL for the website
            filter_path: Filter parameters for the URL
            max_pages: Maximum number of pages to scrape
            save_interval: How often to save progress (in pages)
            retry_attempts: Number of retry attempts for failed URLs
            retry_delay: Delay between retries in seconds
        """
        self.output_file = output_file
        self.error_file = error_file
        self.base_url = base_url
        self.filter_path = filter_path
        self.max_pages = max_pages
        self.save_interval = save_interval
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.unscraped_links = set()
        self.chrome_options = self._setup_chrome_options()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        os.makedirs(os.path.dirname(error_file), exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("BatDongSanScraper")
    
    def _setup_chrome_options(self) -> Options:
        """Set up Chrome options for headless browsing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        return chrome_options
    
    def get_page_with_retries(self, driver: webdriver.Chrome, url: str, retries: int = 10, delay: int = 10) -> str:
        """
        Get a page with retry logic.
        
        Args:
            driver: Selenium WebDriver instance
            url: URL to fetch
            retries: Number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            Page source as string
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(retries): 
            try:
                driver.get(url)
                return driver.page_source
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(delay)
        raise Exception(f"Failed to load page after {retries} attempts: {url}")
    
    def clear_file(self, file_path: str) -> None:
        """Clear the contents of a file."""
        with open(file_path, 'w', encoding='utf-8') as file:
            file.truncate(0)
    
    def load_existing_links(self) -> None:
        """Load existing links from the output file if it exists."""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as existing_links_file:
                existing_links = existing_links_file.read().splitlines()
                self.unscraped_links.update(existing_links)
                self.logger.info(f"Loaded {len(existing_links)} existing links")
    
    def save_links(self) -> None:
        """Save all collected links to the output file."""
        self.clear_file(self.output_file)
        with open(self.output_file, 'w', encoding='utf-8') as linksfile:
            for link in self.unscraped_links:
                linksfile.write(link + '\n')
        self.logger.info(f"Saved {len(self.unscraped_links)} links to {self.output_file}")
    
    def scrape_page(self, page_index: int) -> List[str]:
        """
        Scrape links from a single page.
        
        Args:
            page_index: Page number to scrape
            
        Returns:
            List of error URLs if any
        """
        error_urls = []
        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            page_path = f"/p{page_index}"
            full_path = f"{self.base_url}{page_path}{self.filter_path}"
            
            self.logger.info(f"Scraping page {page_index}: {full_path}")
            html_content = self.get_page_with_retries(driver, full_path)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all product links
            links = soup.find_all('a', class_='js__product-link-for-product-id')
            self.logger.info(f"Found {len(links)} links on page {page_index}")
            
            if len(links) == 0:
                error_urls.append(full_path)
                with open(self.error_file, 'a', encoding='utf-8') as ef:
                    ef.write(full_path + '\n')
                self.logger.warning(f"No links found on page {page_index}, added to error file")
            
            for link in links:
                if link.get('data-product-id') == "0":
                    continue
                href = link.get('href')
                self.unscraped_links.add(self.base_url + href)
                
        except Exception as e:
            self.logger.error(f"Error scraping page {page_index}: {e}")
            error_urls.append(full_path)
        finally:
            if driver:
                driver.quit()
                
        return error_urls
    
    def scrape_all_pages(self) -> None:
        """Scrape all pages and save links periodically."""
        self.load_existing_links()
        error_urls = []
        
        for page_index in range(1, self.max_pages + 1):
            page_errors = self.scrape_page(page_index)
            error_urls.extend(page_errors)
            
            # Save progress periodically
            if page_index % self.save_interval == 0:
                self.save_links()
                self.logger.info(f"Progress saved at page {page_index}")
        
        # Final save
        self.save_links()
        
        # Save error URLs
        if error_urls:
            with open(self.error_file, 'w', encoding='utf-8') as ef:
                for url in error_urls:
                    ef.write(url + '\n')
            self.logger.info(f"Saved {len(error_urls)} error URLs to {self.error_file}")
    
    def retry_error_urls(self) -> None:
        """Retry scraping URLs that previously failed."""
        if not os.path.exists(self.error_file):
            self.logger.info("No error file found. Nothing to retry.")
            return
            
        with open(self.error_file, 'r', encoding='utf-8') as ef:
            error_urls = ef.read().splitlines()
            
        if not error_urls:
            self.logger.info("No error URLs to retry.")
            return
            
        self.logger.info(f"Retrying {len(error_urls)} error URLs...")
        remaining_errors = []
        
        for url in error_urls:
            success = False
            for attempt in range(self.retry_attempts):
                self.logger.info(f"Retrying ({attempt+1}/{self.retry_attempts}): {url}")
                driver = None
                try:
                    driver = webdriver.Chrome(options=self.chrome_options)
                    html_content = self.get_page_with_retries(driver, url)
                    soup = BeautifulSoup(html_content, 'html.parser')
                    links = soup.find_all('a', class_='js__product-link-for-product-id')
                    
                    if links:
                        self.logger.info(f"✅ Success on attempt {attempt+1}: Found {len(links)} links.")
                        for link in links:
                            if link.get('data-product-id') == "0":
                                continue
                            href = link.get('href')
                            self.unscraped_links.add(self.base_url + href)
                        success = True
                        break
                    else:
                        self.logger.warning("No links found.")
                        
                except Exception as e:
                    self.logger.error(f"Error fetching {url}: {e}")
                finally:
                    if driver:
                        driver.quit()
                        
                if not success:
                    time.sleep(random.uniform(1, self.retry_delay))
                    
            if not success:
                remaining_errors.append(url)
                
        # Write updated error file
        with open(self.error_file, 'w', encoding='utf-8') as ef:
            for url in remaining_errors:
                ef.write(url + '\n')
                
        self.logger.info(f"Retry complete. {len(remaining_errors)} failed pages remaining in {self.error_file}.")
        
        # Save all collected links
        self.save_links()
    
    def run(self) -> None:
        """Run the complete scraping process."""
        self.scrape_all_pages()
        self.retry_error_urls()
        self.logger.info("Scraping process completed.")


def scrape_links(
    output_file: str = "/opt/airflow/data/batdongsan_links.txt",
    error_file: str = "/opt/airflow/data/batdongsan_error_links.txt",
    base_url: str = "https://batdongsan.com.vn/nha-dat-ban",
    filter_path: str = "?gtn=7-ty&gcn=30-ty",
    max_pages: int = 3058
) -> None:
    """
    Convenience function to run the scraper with default settings.
    This function can be imported and used in DAGs.
    
    Args:
        output_file: Path to save the scraped links
        error_file: Path to save error URLs
        base_url: Base URL for the website
        filter_path: Filter parameters for the URL
        max_pages: Maximum number of pages to scrape
    """
    scraper = BatDongSanScraper(
        output_file=output_file,
        error_file=error_file,
        base_url=base_url,
        filter_path=filter_path,
        max_pages=max_pages
    )
    scraper.run()


if __name__ == "__main__":
    scrape_links()
