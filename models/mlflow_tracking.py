import mlflow
import mlflow.sklearn
import mlflow.xgboost
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
from xgboost import XGBRegressor
import joblib
import os

# Set MLflow tracking URI (you can change this to your preferred location)
mlflow.set_tracking_uri("http://localhost:5000")

def train_recommendation_model():
    # Load data
    df = pd.read_csv("cleaning/output/processed_data.tsv", sep="\t")
    
    # Preprocess
    features = ['price', 'area', 'number_of_bedrooms', 'number_of_toilets', 'district', 'legal']
    df_clean = df.dropna(subset=features + ['url_id']).copy()
    
    # Define user preference
    user_pref = {
        'price': 14,
        'area': 70,
        'number_of_bedrooms': 3,
        'number_of_toilets': 3,
        'district': [1, 2, 3],
        'legal': 2,
    }
    
    # Compute similarity score
    def compute_similarity_score(row, pref):
        score = 0
        score += abs(row['price'] - pref['price']) / pref['price']
        score += abs(row['area'] - pref['area']) / pref['area']
        score += abs(row['number_of_bedrooms'] - pref['number_of_bedrooms']) / (pref['number_of_bedrooms'] + 1)
        score += abs(row['number_of_toilets'] - pref['number_of_toilets']) / (pref['number_of_toilets'] + 1)
        
        preferred_districts = pref['district'] if isinstance(pref['district'], list) else [pref['district']]
        score += 0 if row['district'] in preferred_districts else 1
        
        legal_diff = abs(row['legal'] - pref['legal'])
        score += 0 if legal_diff == 0 else (0.5 if legal_diff == 1 else 1)
        
        return 1 / (1 + score)
    
    df_clean['score'] = df_clean.apply(lambda row: compute_similarity_score(row, user_pref), axis=1)
    
    # Prepare data for training
    X = df_clean[features]
    y = df_clean['score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Start MLflow run
    with mlflow.start_run(run_name="recommendation_model"):
        # Log parameters
        mlflow.log_params({
            "n_estimators": 100,
            "random_state": 42,
            "test_size": 0.2
        })
        
        # Create and train pipeline
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
        ])
        
        pipeline.fit(X_train, y_train)
        
        # Make predictions and evaluate
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("mse", mse)
        
        # Log model
        mlflow.sklearn.log_model(pipeline, "recommendation_model")
        
        # Save model locally
        os.makedirs('models/saved', exist_ok=True)
        model_path = 'models/saved/recommendation_model.joblib'
        joblib.dump(pipeline, model_path)
        
        print(f"Recommendation model saved and logged to MLflow")
        return pipeline

def train_price_prediction_model():
    # Load data
    df = pd.read_csv('cleaning/output/processed_data.tsv', sep='\t')
    
    # Prepare features and target
    X = df.drop(['price', 'title', 'province', 'url_id'], axis=1)
    y = df['price']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=128)
    
    # Start MLflow run
    with mlflow.start_run(run_name="price_prediction_model"):
        # Log parameters
        mlflow.log_params({
            "random_state": 42,
            "test_size": 0.2
        })
        
        # Create and train model
        model = XGBRegressor(random_state=42)
        model.fit(X_train, y_train)
        
        # Make predictions and evaluate
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mape", mape)
        
        # Log model
        mlflow.xgboost.log_model(model, "price_prediction_model")
        
        # Save model locally
        os.makedirs('models/saved', exist_ok=True)
        model_path = 'models/saved/xgb_model.joblib'
        joblib.dump(model, model_path)
        
        print(f"Price prediction model saved and logged to MLflow")
        return model

if __name__ == "__main__":
    # Train both models
    recommendation_model = train_recommendation_model()
    price_prediction_model = train_price_prediction_model()
    
    print("Both models have been trained and logged to MLflow") 