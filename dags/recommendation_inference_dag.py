from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import pandas as pd
import numpy as np
import joblib
import telegram
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine
from typing import Tuple, List

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'recommendation_inference',
    default_args=default_args,
    description='DAG for running recommendation model inference and sending notifications',
    schedule_interval='0 0 * * *',  # Run daily at midnight
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

def load_model():
    """Load the trained recommendation model"""
    try:
        model = joblib.load('/path/to/your/model.joblib')
        return model
    except Exception as e:
        raise Exception(f"Error loading model: {str(e)}")

def load_user_data() -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Load user data and notification preferences from database"""
    try:
        # Get database connection details from Airflow Variables
        db_connection = Variable.get("DB_CONNECTION_STRING")
        engine = create_engine(db_connection)
        
        # Load user data for inference
        user_data_query = """
        SELECT user_id, feature1, feature2, feature3 
        FROM users 
        WHERE last_inference_date < CURRENT_DATE
        """
        user_data = pd.read_sql(user_data_query, engine)
        
        # Load notification preferences
        notification_query = """
        SELECT user_id, email, telegram_chat_id, notification_type
        FROM user_notifications
        WHERE is_active = true
        """
        notification_prefs = pd.read_sql(notification_query, engine)
        
        # Split users by notification preference
        email_users = notification_prefs[
            notification_prefs['notification_type'].isin(['email', 'both'])
        ]['email'].tolist()
        
        telegram_users = notification_prefs[
            notification_prefs['notification_type'].isin(['telegram', 'both'])
        ]['telegram_chat_id'].tolist()
        
        return user_data, email_users, telegram_users
    except Exception as e:
        raise Exception(f"Error loading user data: {str(e)}")

def run_inference(model, user_data):
    """Run inference on user data"""
    try:
        predictions = model.predict(user_data)
        return predictions
    except Exception as e:
        raise Exception(f"Error during inference: {str(e)}")

def send_telegram_notifications(predictions, telegram_users):
    """Send notifications via Telegram bot to multiple users"""
    try:
        bot_token = Variable.get("TELEGRAM_BOT_TOKEN")
        bot = telegram.Bot(token=bot_token)
        
        message = f"Recommendation Model Inference Results:\n"
        message += f"Total predictions made: {len(predictions)}\n"
        message += f"Timestamp: {datetime.now()}"
        
        for chat_id in telegram_users:
            try:
                bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                print(f"Failed to send Telegram message to {chat_id}: {str(e)}")
                continue
    except Exception as e:
        raise Exception(f"Error in Telegram notification system: {str(e)}")

def send_email_notifications(predictions, email_users):
    """Send notifications via email to multiple users"""
    try:
        smtp_server = Variable.get("SMTP_SERVER")
        smtp_port = int(Variable.get("SMTP_PORT"))
        sender_email = Variable.get("SENDER_EMAIL")
        sender_password = Variable.get("SENDER_PASSWORD")
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['Subject'] = "Recommendation Model Inference Results"
        
        body = f"""
        Recommendation Model Inference Results:
        
        Total predictions made: {len(predictions)}
        Timestamp: {datetime.now()}
        
        Best regards,
        Your Recommendation System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            
            for email in email_users:
                try:
                    msg['To'] = email
                    server.send_message(msg)
                except Exception as e:
                    print(f"Failed to send email to {email}: {str(e)}")
                    continue
    except Exception as e:
        raise Exception(f"Error in email notification system: {str(e)}")

def run_inference_pipeline():
    """Main pipeline function that orchestrates the entire process"""
    try:
        # Load model
        model = load_model()
        
        # Load user data and notification preferences
        user_data, email_users, telegram_users = load_user_data()
        
        # Run inference
        predictions = run_inference(model, user_data)
        
        return {
            'predictions': predictions,
            'email_users': email_users,
            'telegram_users': telegram_users
        }
    except Exception as e:
        raise Exception(f"Pipeline failed: {str(e)}")

# Define the tasks
inference_task = PythonOperator(
    task_id='run_inference_pipeline',
    python_callable=run_inference_pipeline,
    dag=dag,
)

telegram_notification_task = PythonOperator(
    task_id='send_telegram_notifications',
    python_callable=lambda **context: send_telegram_notifications(
        context['task_instance'].xcom_pull(task_ids='run_inference_pipeline')['predictions'],
        context['task_instance'].xcom_pull(task_ids='run_inference_pipeline')['telegram_users']
    ),
    dag=dag,
)

email_notification_task = PythonOperator(
    task_id='send_email_notifications',
    python_callable=lambda **context: send_email_notifications(
        context['task_instance'].xcom_pull(task_ids='run_inference_pipeline')['predictions'],
        context['task_instance'].xcom_pull(task_ids='run_inference_pipeline')['email_users']
    ),
    dag=dag,
)

# Set task dependencies
inference_task >> [telegram_notification_task, email_notification_task] 