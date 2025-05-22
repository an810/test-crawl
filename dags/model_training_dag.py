from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
import sys
import os
import logging
import requests

# Add the scripts directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from train_price_model import train_price_model
from train_recommendation_model import train_recommendation_model
from prepare_data import prepare_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_model_reload():
    """Trigger the backend to reload models"""
    try:
        response = requests.post('http://localhost:5001/reload-models')
        response.raise_for_status()
        logger.info("Successfully triggered model reload")
        return True
    except Exception as e:
        logger.error(f"Error triggering model reload: {str(e)}")
        return False

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'model_training',
    default_args=default_args,
    description='Train ML models after both scraping DAGs complete',
    schedule_interval=timedelta(days=1),  # Run daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Prevent multiple runs at the same time
    tags=['model', 'training']
)

# Wait for BatDongSan scraping to complete
wait_for_batdongsan = ExternalTaskSensor(
    task_id='wait_for_batdongsan',
    external_dag_id='batdongsan_scraping',
    external_task_id='process_data',
    mode='reschedule',
    timeout=3600,  # 1 hour timeout
    dag=dag
)

# Wait for Nhatot scraping to complete
wait_for_nhatot = ExternalTaskSensor(
    task_id='wait_for_nhatot',
    external_dag_id='nhatot_scraping',
    external_task_id='process_data',
    mode='reschedule',
    timeout=3600,  # 1 hour timeout
    dag=dag
)

# Add data preparation task
prepare_data_task = PythonOperator(
    task_id='prepare_data',
    python_callable=prepare_data,
    dag=dag
)

# Define training tasks
train_price = PythonOperator(
    task_id='train_price_model',
    python_callable=train_price_model,
    dag=dag
)

train_recommendation = PythonOperator(
    task_id='train_recommendation_model',
    python_callable=train_recommendation_model,
    dag=dag
)

# Add model reload task
reload_models = PythonOperator(
    task_id='reload_models',
    python_callable=trigger_model_reload,
    dag=dag
)

# Set task dependencies
[wait_for_batdongsan, wait_for_nhatot] >> prepare_data_task >> [train_price, train_recommendation] >> reload_models 