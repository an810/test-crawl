import os
import joblib
from xgboost import XGBRegressor

# Create checkpoint directory if it doesn't exist
os.makedirs('models/checkpoint', exist_ok=True)

# Load the trained model
model = XGBRegressor(random_state=42)

# Save the model in two formats for flexibility
model.save_model('models/checkpoint/xgb_model.json')
joblib.dump(model, 'models/checkpoint/xgb_model.joblib')

print("Model saved successfully in both JSON and joblib formats in models/checkpoint/") 