from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from house_price import router as house_price_router


app = FastAPI(
    title="House Price Prediction API",
    description="API for predicting house prices using machine learning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(house_price_router, prefix="/api/v1/house-price", tags=["house-price"])

@app.get("/")
async def root():
    return {"message": "Welcome to House Price Prediction API"} 
