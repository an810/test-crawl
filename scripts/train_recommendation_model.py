import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_recommendation_model():
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri("http://localhost:5000")
        
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
            # Create and train pipeline
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
            ])
            
            pipeline.fit(X_train, y_train)
            
            # Make predictions and evaluate
            y_pred = pipeline.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            
            # Log parameters
            mlflow.log_params({
                "n_estimators": 100,
                "random_state": 42,
                "test_size": 0.2
            })
            
            # Log metrics
            mlflow.log_metric("mse", mse)
            
            # Log model
            mlflow.sklearn.log_model(pipeline, "recommendation_model")
            
            # Register model if it's better than the current production model
            try:
                current_model = mlflow.sklearn.load_model("models:/recommendation_model/Production")
                current_mse = mean_squared_error(y_test, current_model.predict(X_test))
                if mse < current_mse:
                    mlflow.register_model(
                        model_uri=f"runs:/{mlflow.active_run().info.run_id}/recommendation_model",
                        name="recommendation_model"
                    )
                    mlflow.sklearn.log_model(pipeline, "recommendation_model", registered_model_name="recommendation_model")
                    logger.info("New recommendation model registered as it performs better")
                else:
                    logger.info("Current recommendation model performs better, keeping it")
            except:
                # If no production model exists, register this one
                mlflow.register_model(
                    model_uri=f"runs:/{mlflow.active_run().info.run_id}/recommendation_model",
                    name="recommendation_model"
                )
                logger.info("First recommendation model registered")
            
            return True
            
    except Exception as e:
        logger.error(f"Error in train_recommendation_model: {str(e)}")
        return False

if __name__ == "__main__":
    train_recommendation_model() 