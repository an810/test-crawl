 import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.sklearn
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report
from evidently.test_suite import TestSuite
from evidently.test_preset import DataStabilityTestPreset
import xgboost as xgb
from datetime import datetime
import os

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

def load_and_prepare_data():
    """Load and prepare the data for training"""
    # Read the processed data
    df = pd.read_csv('../cleaning/output/processed_data.tsv', sep='\t')
    
    # Assuming the last column is the target variable
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

def train_model(X_train, y_train):
    """Train XGBoost model with MLflow tracking"""
    with mlflow.start_run():
        # Log parameters
        params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'objective': 'reg:squarederror'
        }
        mlflow.log_params(params)
        
        # Train model
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)
        
        # Log model
        mlflow.sklearn.log_model(model, "model")
        
        return model

def evaluate_data_drift(reference_data, current_data):
    """Evaluate data drift using Evidently AI"""
    drift_report = Report(metrics=[DataDriftPreset()])
    drift_report.run(reference_data=reference_data, current_data=current_data)
    
    # Save drift report
    drift_report.save_html("data_drift_report.html")
    
    # Run data stability tests
    stability_suite = TestSuite(tests=[DataStabilityTestPreset()])
    stability_suite.run(reference_data=reference_data, current_data=current_data)
    stability_suite.save_html("data_stability_report.html")

def main():
    # Load and prepare data
    X_train, X_test, y_train, y_test, scaler = load_and_prepare_data()
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Create reference and current datasets for drift detection
    reference_data = pd.DataFrame(X_train, columns=[f'feature_{i}' for i in range(X_train.shape[1])])
    current_data = pd.DataFrame(X_test, columns=[f'feature_{i}' for i in range(X_test.shape[1])])
    
    # Evaluate data drift
    evaluate_data_drift(reference_data, current_data)
    
    # Save the scaler
    import joblib
    joblib.dump(scaler, 'scaler.joblib')
    
    print("Training completed successfully!")
    print("MLflow tracking server: http://localhost:5000")
    print("Data drift report: data_drift_report.html")
    print("Data stability report: data_stability_report.html")

if __name__ == "__main__":
    main()