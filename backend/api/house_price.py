# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, Field
# import numpy as np
# from model_loader import ModelLoader
# from typing import Literal

# router = APIRouter()
# model_loader = ModelLoader()

# # List of districts in Hanoi
# HANOI_DISTRICTS = [
#     "Ba Dinh", "Bac Tu Liem", "Cau Giay", "Dong Da", "Ha Dong",
#     "Hai Ba Trung", "Hoan Kiem", "Hoang Mai", "Long Bien", "Nam Tu Liem",
#     "Tay Ho", "Thanh Xuan", "Ba Vi", "Chuong My", "Dan Phuong",
#     "Dong Anh", "Gia Lam", "Hoai Duc", "Me Linh", "My Duc",
#     "Phu Xuyen", "Phuc Tho", "Quoc Oai", "Soc Son", "Son Tay",
#     "Thach That", "Thanh Oai", "Thanh Tri", "Thuong Tin", "Ung Hoa"
# ]

# class HouseFeatures(BaseModel):
#     area: float = Field(..., description="Area of the property in square meters", gt=0)
#     number_of_bedrooms: int = Field(..., description="Number of bedrooms", ge=0)
#     number_of_toilets: int = Field(..., description="Number of toilets", ge=0)
#     legal: Literal["red_book", "pink_book", "other"] = Field(..., description="Type of legal document")
#     lat: float = Field(..., description="Latitude coordinate", ge=20.5, le=21.5)  # Hanoi's latitude range
#     lon: float = Field(..., description="Longitude coordinate", ge=105.0, le=106.0)  # Hanoi's longitude range
#     district: str = Field(..., description="District in Hanoi")

#     model_config = {
#         "json_schema_extra": {
#             "example": {
#                 "area": 100.5,
#                 "number_of_bedrooms": 3,
#                 "number_of_toilets": 2,
#                 "legal": "red_book",
#                 "lat": 21.0285,
#                 "lon": 105.8542,
#                 "district": "Cau Giay"
#             }
#         }
#     }

#     def validate_district(self):
#         if self.district not in HANOI_DISTRICTS:
#             raise ValueError(f"District must be one of: {', '.join(HANOI_DISTRICTS)}")

# @router.post("/predict")
# async def predict_house_price(features: HouseFeatures):
#     try:
#         # Validate district
#         features.validate_district()
        
#         model = model_loader.get_model()
        
#         # Convert legal status to numerical value
#         legal_mapping = {
#             "red_book": 2,
#             "pink_book": 1,
#             "other": 0
#         }
        
#         # Convert district to numerical value (one-hot encoding would be handled by the model)
#         district_index = HANOI_DISTRICTS.index(features.district)
        
#         # Convert input features to numpy array
#         input_features = np.array([[
#             features.area,
#             features.bedrooms,
#             features.toilets,
#             legal_mapping[features.legal],
#             features.latitude,
#             features.longitude,
#             district_index
#         ]])
        
#         # Make prediction
#         prediction = model.predict(input_features)[0]
        
#         return {
#             "predicted_price": float(prediction),
#             "input_features": features.model_dump(),
#             "price_per_sqm": float(prediction / features.area)
#         }
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e)) 