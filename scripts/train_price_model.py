import mlflow
import mlflow.xgboost
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_price_model():
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri("http://localhost:5000")
        
        # Load data
        df = pd.read_csv("cleaning/output/processed_data.tsv", sep="\t")
        
        # Prepare features and target
        X = df.drop(['price', 'title', 'province', 'url_id'], axis=1)
        y = df['price']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=128)
        
        # Start MLflow run
        with mlflow.start_run(run_name="price_prediction_model"):
            # Create and train model
            model = XGBRegressor(random_state=42)
            model.fit(X_train, y_train)
            
            # Make predictions and evaluate
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            mape = mean_absolute_percentage_error(y_test, y_pred)
            
            # Log parameters
            mlflow.log_params({
                "random_state": 42,
                "test_size": 0.2
            })
            
            # Log metrics
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("r2", r2)
            mlflow.log_metric("mape", mape)
            
            # Log model
            mlflow.xgboost.log_model(model, "price_prediction_model")
            
            # Register model if it's better than the current production model
            try:
                current_model = mlflow.xgboost.load_model("models:/price_prediction_model/Production")
                current_mae = mean_absolute_error(y_test, current_model.predict(X_test))
                if mae < current_mae:
                    mlflow.register_model(
                        model_uri=f"runs:/{mlflow.active_run().info.run_id}/price_prediction_model",
                        name="price_prediction_model"
                    )
                    mlflow.xgboost.log_model(model, "price_prediction_model", registered_model_name="price_prediction_model")
                    logger.info("New price prediction model registered as it performs better")
                else:
                    logger.info("Current price prediction model performs better, keeping it")
            except:
                # If no production model exists, register this one
                mlflow.register_model(
                    model_uri=f"runs:/{mlflow.active_run().info.run_id}/price_prediction_model",
                    name="price_prediction_model"
                )
                logger.info("First price prediction model registered")
            
            return True
            
    except Exception as e:
        logger.error(f"Error in train_price_model: {str(e)}")
        return False

if __name__ == "__main__":
    train_price_model() 