from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
import sys
import os
import logging

# Add the scripts directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the scraping modules
from scraping.HNSaveLinkNhatot import scrape_links as save_links
from scraping.HNScraperNhatot import scrape_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'hn_nhatot_scraping',
    default_args=default_args,
    description='DAG for scraping and processing Hanoi Nhatot data',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 4, 14),
    catchup=False,
    tags=['scraper', 'nhatot', 'hanoi'],
)

# Task 1: Save Links
def save_links_task():
    try:
        # Use the HNSaveLinkNhatot module to scrape links
        save_links()
        logger.info("Successfully completed save_links_task")
    except Exception as e:
        logger.error(f"Error in save_links_task: {e}")
        raise

save_links_operator = PythonOperator(
    task_id='save_links',
    python_callable=save_links_task,
    dag=dag,
    retries=2,
    retry_delay=timedelta(minutes=10)
)

# Task 2: Scrape Data
def scrape_data_task():
    try:
        result = scrape_data(use_multiprocessing=False)
        if not result:
            raise Exception("Scraping failed")
        return "Scraping completed successfully"
    except Exception as e:
        raise Exception(f"Error in scrape_data_task: {str(e)}")

scrape_task = PythonOperator(
    task_id='scrape_data',
    python_callable=scrape_data_task,
    dag=dag,
)

# Set task dependencies
save_links_operator >> scrape_task 