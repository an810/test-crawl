from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add the scripts directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the scraper function
from ScraperBatdongsan import scrape_data

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the test DAG
dag = DAG(
    'batdongsan_test_scraping',
    default_args=default_args,
    description='Test DAG for BatDongSan scraper',
    schedule_interval=timedelta(hours=1),  # Run every hour for testing
    start_date=datetime(2025, 4, 14),
    catchup=False,
    tags=['test', 'scraper', 'batdongsan'],
)

# Define the test scraping task
def test_scrape_data_task():
    """
    Task to test the scraper functionality
    """
    try:
        result = scrape_data(use_multiprocessing=False)
        if not result:
            raise Exception("Scraping failed")
        return "Scraping test completed successfully"
    except Exception as e:
        raise Exception(f"Error in test_scrape_data_task: {str(e)}")

# Create the test task
test_scrape_task = PythonOperator(
    task_id='test_scrape_data',
    python_callable=test_scrape_data_task,
    dag=dag,
)

# Set task dependencies (none in this case, as we only have one task)
test_scrape_task 