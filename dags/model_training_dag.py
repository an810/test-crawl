from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
import sys
import os
import logging

# Add the scripts directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from train_price_model import train_price_model
from train_recommendation_model import train_recommendation_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Set task dependencies
[wait_for_batdongsan, wait_for_nhatot] >> [train_price, train_recommendation] 