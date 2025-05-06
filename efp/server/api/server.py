import typing

original_evaluate = typing.ForwardRef._evaluate
def patched_evaluate(self, globalns, localns, recursive_guard=None):
    if recursive_guard is None:
        recursive_guard = set()
    return original_evaluate(self, globalns, localns, recursive_guard)

typing.ForwardRef._evaluate = patched_evaluate

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent))
from data_processor.processor import (
    generate_forecast, 
    get_weather_data, 
    get_solar_data, 
    get_forecast_data
)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD", "")
if "<db_password>" in MONGO_URI and MONGO_DB_PASSWORD:
    MONGO_URI = MONGO_URI.replace("<db_password>", MONGO_DB_PASSWORD)

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["energy_db"]
weather_collection = db["weather_data"]
solar_collection = db["solar_data"]
forecast_collection = db["forecast_data"]
app = FastAPI(title="Energy Consumption API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: Optional[str] = None

class WeatherData(BaseModel):
    _id: Optional[str] = None
    datetime: datetime
    temperature: float
    humidity: float
    wind_speed: float
    cloud_cover: float
    description: str
    location: Optional[str] = None

class SolarPanelData(BaseModel):
    _id: Optional[str] = None
    datetime: datetime
    energy_produced: float
    efficiency: float
    panel_temperature: float
    solar_irradiance: float
    status: str

class ForecastData(BaseModel):
    _id: Optional[str] = None
    datetime: datetime
    prediction_time: Optional[datetime] = None
    consumption: float
    production: float
    net_consumption: float
    confidence: float
    source: Optional[str] = None

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    try:
        mongo_client.admin.command('ping')
        return HealthResponse(status="healthy", message="Connected to MongoDB")
    except Exception as e:
        return HealthResponse(status="error", message=f"Database error: {str(e)}")

@app.get("/api/weather", response_model=List[WeatherData])
async def get_weather(limit: int = 10):
    try:
        weather_data = list(get_weather_data(limit))
        return weather_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving weather data: {str(e)}")

@app.get("/api/solar", response_model=List[SolarPanelData])
async def get_solar(limit: int = 10):
    try:
        solar_data = list(get_solar_data(limit))
        return solar_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving solar data: {str(e)}")

@app.get("/api/forecast", response_model=List[ForecastData])
async def get_forecast(hours: int = 24):
    try:
        forecast_data = list(get_forecast_data(hours))
        return forecast_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving forecast data: {str(e)}")

@app.post("/api/process")
async def process_data():
    try:
        result = generate_forecast()
        return {"success": True, "message": "Processing completed", "forecast_count": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True) 