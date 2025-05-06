import os
import time
import json
import math
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "efp_db")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")

if "<db_password>" in MONGO_URI and MONGO_DB_PASSWORD:
    MONGO_URI = MONGO_URI.replace("<db_password>", MONGO_DB_PASSWORD)

try:
    client = MongoClient(MONGO_URI)
    # Test connection
    client.admin.command('ping')
    print("Connected to MongoDB Atlas successfully!")
    
    db = client[MONGO_DB_NAME]
    weather_collection = db["weather"]
    solar_collection = db["solar"]
    forecast_collection = db["forecast"]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")


forecasts = []


def get_data(days=7):
    threshold_date = datetime.now() - timedelta(days=days)
    try:
        weather_data = list(weather_collection.find({"datetime": {"$gte": threshold_date}}))
        solar_data = list(solar_collection.find({"datetime": {"$gte": threshold_date}}))
        #testing print
        print(f"Retrieved {len(weather_data)} weather records and {len(solar_data)} solar records")

        return weather_data, solar_data
    except Exception as e:
        print(f"Error retrieving data from MongoDB: {e}")
        return [], []

 
def create_forecast(hours=24):
    # Create energy consumption forecast based on weather and solar data
    weather_data, solar_data = get_data(days=7)

    if not weather_data or not solar_data:
        print("No weather or solar data, no forecast for you mister!")
        return []
    
    # Calculate total solar production
    latest_weather = weather_data[-1] if weather_data else None
    latest_solar = solar_data[-1] if solar_data else None

    if not latest_weather or not latest_solar: 
        print("No latest weather or solar data!")
        return []
    

    for hour in range(24):
        forecast_time = datetime.now() + timedelta(hours=hour)
        hour_of_day = forecast_time.hour

         # Simple rules for base consumption based on time of day
        if 7 <= hour_of_day < 9 or 17 <= hour_of_day < 21:  # Morning or evening 
            base_consumption = 45.0  # kWh
        elif 22 <= hour_of_day or hour_of_day < 6:  # Night
            base_consumption = 25.0  # kWh
        else:  # Day
            base_consumption = 35.0  # kWh

        # Temperature adjustment (higher at extremes)
        # Lets say 21°C is optimal, consumption increases away from this
        optimal_temp = 21
        temp_adjustment = abs(latest_weather['temperature'] - optimal_temp) * 0.5
        
        predicted_consumption = base_consumption + temp_adjustment
        
        # Solar production (simplified, based on hour of day)
        if 6 <= hour_of_day < 20:  # Daylight hours
            # Simplified solar production curve
            solar_factor = math.sin(math.pi * (hour_of_day - 6) / 14)
            solar_production = latest_solar['production'] * solar_factor
            feed_in = latest_solar['feed_in'] * solar_factor
        else:
            solar_production = 0.0
            feed_in = 0.0
        
        # Create forecast doc
        forecast = {
            'datetime': forecast_time,
            'predicted_consumption': round(predicted_consumption, 2),
            'solar_production': round(solar_production, 2),
            'feed_in': round(feed_in, 2)
        }
        
        forecasts.append(forecast)
    
    return forecasts

def store_forecast(forecast):

    if not forecast: 
        return 0

    try: 
        creation_time = datetime.now()
        for forecast in forecasts:
            forecast['forecast_created_at'] = creation_time
        
        result = forecast_collection.insert_many(forecasts)
        print(f"Stored {len(result.inserted_ids)} forecast documents")
        return len(result.inserted_ids)
    except Exception as e:
        print(f"Error storing forecast: {e}")
        return 0
 
   
def process_data():
    print("\n===== Creating energy consumption forecast =====") # fency decorat
    
    forecast = create_forecast(hours=24)

    if forecasts:
        store_forecast(forecasts)
    
    # test print
    for i, forecast in enumerate(forecasts[:3]):
            print(f"Hour {i+1}: {forecast['datetime']}")
            print(f"  Predicted consumption: {forecast['predicted_consumption']} kWh")
            print(f"  Solar production: {forecast['solar_production']} kW")
            print(f"  Feed-in: {forecast['feed_in']} kW")
    
    return len(forecasts)

def main():
    print("Data processor starting...")
    
    while True:
        process_data()
        processing_interval = 60  # 1 minute for testing
        
        #testing print
        print(f"\nWaiting {processing_interval} seconds before next processing...")
        time.sleep(processing_interval)

if __name__ == "__main__":
    main()