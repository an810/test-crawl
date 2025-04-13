from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add the scripts directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from SaveLinkBatdongsan import scrape_links
from ScraperBatdongsan import scrape_data

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
    'batdongsan_scraping',
    default_args=default_args,
    description='Scrape batdongsan.com.vn data',
    schedule_interval='0 0 * * *',  # Run daily at midnight
    catchup=False
)

# Task 1: Save Links
save_links_task = PythonOperator(
    task_id='save_links',
    python_callable=scrape_links,
    dag=dag,
)

# Task 2: Scrape Data
scrape_data_task = PythonOperator(
    task_id='scrape_data',
    python_callable=scrape_data,
    dag=dag,
)

# Set task dependencies
save_links_task >> scrape_data_task 