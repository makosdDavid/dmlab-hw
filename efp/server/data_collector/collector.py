import os 
import time
import requests
import json
import math 
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_CITY_ID = os.getenv("OPENWEATHER_CITY_ID", 3054643)
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

def fetch_weather_data():
    url = OPENWEATHER_API_URL
    params = {
        'id': OPENWEATHER_CITY_ID,
        'appid': OPENWEATHER_API_KEY,  
        'units': 'metric'
    }

    try: 
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        weather_data = {
            'datetime': datetime.now(),
            'temperature': data['main']['temp'],
            'wind_speed': data['wind']['speed'],
            'precipitation': data.get('rain', {}).get('1h', 0),
            'solar_irradiance': estimate_solar_irradiance(data)
        }
        
        result = weather_collection.insert_one(weather_data)
        
        #testing print
        print(f"Weather data collected at {weather_data['datetime']}")
        print(f"Temperature: {weather_data['temperature']}°C")
        print(f"Wind speed: {weather_data['wind_speed']} m/s")
        print(f"Precipitation: {weather_data['precipitation']} mm")
        print(f"Est. solar irradiance: {weather_data['solar_irradiance']} W/m²")
        
        return weather_data

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def estimate_solar_irradiance(weather_data):
    """
    Estimate solar irradiance based on cloud cover and time of day.
    """
    # Get cloud cover percentage (0-100)
    cloud_cover = weather_data.get('clouds', {}).get('all', 0)
    
    now = datetime.now()
    hour = now.hour
    
    # Rough time-of-day factor (0.0 to 1.0)
    # Max at noon (12), zero at night
    if hour < 6 or hour > 18:  # Night time
        time_factor = 0.0
    else:
        time_factor = math.sin(math.pi * (hour - 6) / 12)
    
    # max irradiance (1000 W/m²) * time factor * cloud factor
    max_irradiance = 1000
    cloud_factor = 1 - (cloud_cover / 100)
    
    return int(max_irradiance * time_factor * cloud_factor)

def simulate_solar_panel_data():
    """
    Simulate solar panel production based on latest weather data.
    """
    # Get the most recent weather data
    latest_weather = weather_collection.find_one(sort=[('datetime', -1)])
    
    if not latest_weather:
        print("No weather data!")
        return None

    irradiance = latest_weather['solar_irradiance']
    temperature = latest_weather['temperature']
    
    # Typical home solar installation (5kW)
    system_capacity = 5.0  # kW
    
    # Solar panel efficiency factors
    base_efficiency = 0.20  # 20% efficiency
    
    # Temperature factor (efficiency drops 0.5% per degree above 25°C)
    temp_adjustment = max(0, temperature - 25) * 0.005
    adjusted_efficiency = base_efficiency * (1 - temp_adjustment)
    
    # Calculate production
    standard_test_irradiance = 1000  # W/m²
    production = (irradiance / standard_test_irradiance) * system_capacity * adjusted_efficiency
    
    # Assume 60% of production is fed back to the grid
    feed_in = production * 0.6
    
    solar_data = {
        'datetime': datetime.now(),
        'production': round(production, 2),
        'feed_in': round(feed_in, 2)
    }
    
    # Save to MongoDB
    result = solar_collection.insert_one(solar_data)
    
    #testing print
    print(f"Solar panel data simulated at {solar_data['datetime']}")
    print(f"Production: {solar_data['production']} kW")
    print(f"Feed-in: {solar_data['feed_in']} kW")
    
    return solar_data

def main():
    """Main function to run the data collection process"""
    print("Data collector starting...")
    
    while True:
        print("\n===== Collecting new data =====")
        weather_data = fetch_weather_data()
        
        if weather_data:
            solar_data = simulate_solar_panel_data()
        
        # In a production system, we would use a proper scheduler
        collection_interval = 60  # seconds (1 minute for testing)
        #testing print
        print(f"Waiting {collection_interval} seconds before next collection...")
        time.sleep(collection_interval)

if __name__ == "__main__":
    main()