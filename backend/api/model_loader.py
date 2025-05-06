import joblib
import os
from pathlib import Path

class ModelLoader:
    def __init__(self):
        self.model = None
        self.model_path = Path(__file__).parent.parent.parent / "models" / "checkpoint" / "house_price_model.joblib"
        
    def load_model(self):
        """Load the pre-trained model from the checkpoint directory"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        
        try:
            self.model = joblib.load(self.model_path)
            return self.model
        except Exception as e:
            raise Exception(f"Error loading model: {str(e)}")
    
    def get_model(self):
        """Get the loaded model, load it if not already loaded"""
        if self.model is None:
            self.load_model()
        return self.model 