import os
import time
import json
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD", "")

if "<db_password>" in MONGO_URI and MONGO_DB_PASSWORD:
    MONGO_URI = MONGO_URI.replace("<db_password>", MONGO_DB_PASSWORD)

mongo_client = MongoClient(MONGO_URI)

try:
    mongo_client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

db = mongo_client["energy_db"]
weather_collection = db["weather_data"]
solar_collection = db["solar_data"]
forecast_collection = db["forecast_data"]

def get_weather_data(limit: int = 10) -> Generator[Dict[str, Any], None, None]:
    cursor = weather_collection.find().sort("datetime", pymongo.DESCENDING).limit(limit)
    
    for doc in cursor:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        if 'datetime' in doc and isinstance(doc['datetime'], datetime):
            doc['datetime'] = doc['datetime'].isoformat()
            
        yield doc

def get_solar_data(limit: int = 10) -> Generator[Dict[str, Any], None, None]:
    cursor = solar_collection.find().sort("datetime", pymongo.DESCENDING).limit(limit)
    
    for doc in cursor:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        if 'datetime' in doc and isinstance(doc['datetime'], datetime):
            doc['datetime'] = doc['datetime'].isoformat()
            
        yield doc

def get_forecast_data(hours: int = 24) -> Generator[Dict[str, Any], None, None]:
    latest_forecast = forecast_collection.find_one(
        sort=[("prediction_time", pymongo.DESCENDING)]
    )
    
    if not latest_forecast:
        return
        
    prediction_time = latest_forecast.get("prediction_time")
    
    cursor = forecast_collection.find(
        {"prediction_time": prediction_time}
    ).sort("datetime", pymongo.ASCENDING).limit(hours)
    
    for doc in cursor:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        if 'datetime' in doc and isinstance(doc['datetime'], datetime):
            doc['datetime'] = doc['datetime'].isoformat()
            
        if 'prediction_time' in doc and isinstance(doc['prediction_time'], datetime):
            doc['prediction_time'] = doc['prediction_time'].isoformat()
            
        yield doc

def generate_forecast() -> int:
    current_time = datetime.now().replace(year=2024)
    
    latest_weather = list(get_weather_data(1))
    if not latest_weather:
        print("No weather data available for forecast generation")
        return 0
        
    latest_solar = list(get_solar_data(1))
    if not latest_solar:
        print("No solar data available for forecast generation")
        return 0
    
    forecast_hours = 24
    forecasts = []
    
    for hour in range(forecast_hours):
        forecast_time = current_time + timedelta(hours=hour)
        
        base_consumption = 20 + 15 * math.sin(hour / 24 * 2 * math.pi)
        weather_factor = 1.0
        
        if latest_weather:
            try:
                temp = float(latest_weather[0]['temperature'])
                weather_factor = 1.0 + 0.05 * max(0, temp - 20)
            except (KeyError, ValueError, TypeError):
                pass
                
        consumption = base_consumption * weather_factor * (0.9 + 0.2 * random.random())
        
        base_production = 0
        if 6 <= forecast_time.hour <= 18:
            hour_factor = 1.0 - abs(forecast_time.hour - 12) / 6
            base_production = 30 * hour_factor
            
            cloud_factor = 1.0
            if latest_weather and 'cloud_cover' in latest_weather[0]:
                try:
                    cloud_cover = float(latest_weather[0]['cloud_cover'])
                    cloud_factor = 1.0 - (cloud_cover / 100) * 0.8
                except (ValueError, TypeError):
                    pass
                    
            base_production *= cloud_factor
        
        production = base_production * (0.85 + 0.3 * random.random())
        
        net_consumption = consumption - production
        
        confidence = 0.95 - (hour / forecast_hours) * 0.4
        
        forecasts.append({
            "datetime": forecast_time,
            "prediction_time": current_time,
            "consumption": round(consumption, 2),
            "production": round(production, 2),
            "net_consumption": round(net_consumption, 2),
            "confidence": round(confidence, 2),
            "source": "simple_model_v1"
        })
    
    if forecasts:
        forecast_collection.insert_many(forecasts)
        
    return len(forecasts)

def store_weather_data(weather_data: Dict[str, Any]) -> str:
    if 'datetime' in weather_data and isinstance(weather_data['datetime'], str):
        try:
            weather_data['datetime'] = datetime.fromisoformat(weather_data['datetime'])
        except ValueError:
            weather_data['datetime'] = datetime.now().replace(year=2024)
    
    result = weather_collection.insert_one(weather_data)
    return str(result.inserted_id)

def store_solar_data(solar_data: Dict[str, Any]) -> str:
    if 'datetime' in solar_data and isinstance(solar_data['datetime'], str):
        try:
            solar_data['datetime'] = datetime.fromisoformat(solar_data['datetime'])
        except ValueError:
            solar_data['datetime'] = datetime.now().replace(year=2024)
    
    result = solar_collection.insert_one(solar_data)
    return str(result.inserted_id)

def store_forecast(forecast_data: List[Dict[str, Any]]) -> int:
    current_time = datetime.now().replace(year=2024)
    
    for forecast in forecast_data:
        if 'prediction_time' not in forecast:
            forecast['prediction_time'] = current_time
            
        if 'datetime' in forecast and isinstance(forecast['datetime'], str):
            try:
                forecast['datetime'] = datetime.fromisoformat(forecast['datetime'])
            except ValueError:
                index = forecast_data.index(forecast)
                forecast['datetime'] = current_time + timedelta(hours=index)
    
    if forecast_data:
        result = forecast_collection.insert_many(forecast_data)
        return len(result.inserted_ids)
    return 0
    current_time = datetime.now().replace(year=2024)
    
    weather_descriptions = [
        "Clear sky", "Partly cloudy", "Cloudy", "Light rain", "Heavy rain",
        "Thunderstorm", "Foggy", "Snowy", "Windy"
    ]
    
    weather_data = {
        "datetime": current_time,
        "temperature": round(random.uniform(15, 35), 1),
        "humidity": round(random.uniform(30, 90), 1),
        "wind_speed": round(random.uniform(0, 20), 1),
        "cloud_cover": round(random.uniform(0, 100), 1),
        "description": random.choice(weather_descriptions),
        "location": "Default City"
    }
    
    store_weather_data(weather_data)
    print(f"Created demo weather data: {weather_data}")
    
    solar_status = ["Optimal", "Good", "Degraded", "Maintenance Required", "Error"]
    
    solar_data = {
        "datetime": current_time,
        "energy_produced": round(random.uniform(5, 25), 2),
        "efficiency": round(random.uniform(0.4, 0.9), 2),
        "panel_temperature": round(random.uniform(20, 60), 1),
        "solar_irradiance": round(random.uniform(200, 1000), 0),
        "status": random.choice(solar_status)
    }
    
    store_solar_data(solar_data)
    print(f"Created demo solar data: {solar_data}")
    
    forecast_count = generate_forecast()
    print(f"Generated {forecast_count} forecast records")


