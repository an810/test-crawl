import mlflow
import mlflow.sklearn
import mlflow.xgboost
import pandas as pd
from flask import Flask, request, jsonify
from mlflow.tracking import MlflowClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_best_model_version(model_name):
    """Get the best performing model version based on metrics."""
    client = MlflowClient()
    try:
        # Get all versions of the model
        versions = client.search_model_versions(f"name='{model_name}'")
        
        if not versions:
            logger.warning(f"No versions found for model {model_name}")
            return None
            
        # Get versions that were registered as production
        production_versions = [v for v in versions if v.current_stage == 'Production']
        if not production_versions:
            logger.warning(f"No production version found for model {model_name}")
            return None
        
        # Get metrics for each version
        best_version = None
        best_metric = float('inf') if model_name == "price_prediction_model" else float('inf')
        
        for version in production_versions:
            try:
                # Get the run that created this model version
                run = client.get_run(version.run_id)
                
                # Get metrics based on model type
                if model_name == "price_prediction_model":
                    # For price prediction, we want to minimize MAE
                    metric = run.data.metrics.get('mae', float('inf'))
                    if metric < best_metric:
                        best_metric = metric
                        best_version = version
                else:  # recommendation_model
                    # For recommendation, we want to minimize MSE
                    metric = run.data.metrics.get('mse', float('inf'))
                    if metric < best_metric:
                        best_metric = metric
                        best_version = version
                        
            except Exception as e:
                logger.warning(f"Error getting metrics for version {version.version}: {str(e)}")
                continue
        
        if best_version:
            logger.info(f"Selected {model_name} version {best_version.version} with metric {best_metric}")
            return best_version
        else:
            logger.warning(f"No valid metrics found for {model_name}")
            # Fallback to latest version if no metrics available
            return max(production_versions, key=lambda x: x.version)
            
    except Exception as e:
        logger.error(f"Error getting best model version: {str(e)}")
        return None

def load_models():
    """Load the best versions of both models."""
    global recommendation_model, price_prediction_model
    
    # Load recommendation model
    rec_model = get_best_model_version("recommendation_model")
    if rec_model:
        recommendation_model = mlflow.sklearn.load_model(f"models:/recommendation_model/{rec_model.version}")
        logger.info(f"Loaded recommendation model version {rec_model.version}")
    else:
        raise Exception("No recommendation model available")
    
    # Load price prediction model
    price_model = get_best_model_version("price_prediction_model")
    if price_model:
        price_prediction_model = mlflow.xgboost.load_model(f"models:/price_prediction_model/{price_model.version}")
        logger.info(f"Loaded price prediction model version {price_model.version}")
    else:
        raise Exception("No price prediction model available")

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Load the models
try:
    load_models()
except Exception as e:
    logger.error(f"Error loading models: {str(e)}")
    raise

@app.route('/predict-price', methods=['POST'])
def predict_price():
    try:
        data = request.get_json()
        features = pd.DataFrame([data])
        prediction = price_prediction_model.predict(features)
        return jsonify({
            'predicted_price': float(prediction[0])
        })
    except Exception as e:
        logger.error(f"Error in predict_price: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        user_pref = data.get('user_preferences', {})
        features = pd.DataFrame([data.get('property_features', {})])
        
        # Get prediction from model
        predicted_score = recommendation_model.predict(features)[0]
        
        return jsonify({
            'recommendation_score': float(predicted_score),
            'user_preferences': user_pref
        })
    except Exception as e:
        logger.error(f"Error in recommend: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/reload-models', methods=['POST'])
def reload_models():
    """Endpoint to reload models with the latest versions."""
    try:
        load_models()
        return jsonify({'message': 'Models reloaded successfully'})
    except Exception as e:
        logger.error(f"Error reloading models: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) 