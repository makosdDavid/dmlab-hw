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
OPENWEATHER_FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
OPENWEATHER_ONECALL_URL = "http://api.openweathermap.org/data/2.5/onecall"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "dmlab")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")

if "<db_password>" in MONGO_URI and MONGO_DB_PASSWORD:
    MONGO_URI = MONGO_URI.replace("<db_password>", MONGO_DB_PASSWORD)

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("Connected to MongoDB Atlas successfully!")
    
    db = client[MONGO_DB_NAME]
    weather_collection = db["weather"]
    solar_collection = db["solar"]
    forecast_collection = db["forecast"]
    cities_collection = db["cities"]
    # New collection for historical daily summaries
    historical_weather_collection = db["historical_weather"]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

# Default cities if none in DB
DEFAULT_CITIES = [
    {"id": 3054643, "name": "Budapest", "country": "HU"},  # Added Budapest as first city
    {"id": 719819, "name": "Debrecen", "country": "HU"},  # Added more Hungarian cities
    {"id": 715429, "name": "Szeged", "country": "HU"},
    {"id": 3050434, "name": "Pécs", "country": "HU"},
    {"id": 3052009, "name": "Győr", "country": "HU"},
    {"id": 264371, "name": "Athens", "country": "GR"},
    {"id": 2759794, "name": "Amsterdam", "country": "NL"},
    {"id": 2988507, "name": "Paris", "country": "FR"},
    {"id": 3117735, "name": "Madrid", "country": "ES"},
    {"id": 2950159, "name": "Berlin", "country": "DE"}
]

# Initialize cities collection if empty
def initialize_cities():
    if cities_collection.count_documents({}) == 0:
        print("Initializing default cities...")
        cities_collection.insert_many(DEFAULT_CITIES)
        print(f"Added {len(DEFAULT_CITIES)} default cities")

def get_all_cities():
    return list(cities_collection.find({}, {"_id": 0}))

def fetch_weather_data(city_id=None, city_name=None, country_code=None):
    url = OPENWEATHER_API_URL
    
    if city_id:
        params = {
            'id': city_id,
            'appid': OPENWEATHER_API_KEY,  
            'units': 'metric'
        }
    elif city_name and country_code:
        params = {
            'q': f"{city_name},{country_code}",
            'appid': OPENWEATHER_API_KEY,  
            'units': 'metric'
        }
    else:
        print("Either city_id or city_name and country_code must be provided")
        return None
        
    try: 
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        city_info = {
            'id': data['id'],
            'name': data['name'],
            'country': data['sys']['country']
        }
        
        weather_data = {
            'datetime': datetime.now(),
            'city_id': data['id'],
            'city_name': data['name'],
            'country': data['sys']['country'],
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'cloud_cover': data.get('clouds', {}).get('all', 0),
            'precipitation': data.get('rain', {}).get('1h', 0),
            'description': data['weather'][0]['description'],
            'solar_irradiance': estimate_solar_irradiance(data)
        }
        
        result = weather_collection.insert_one(weather_data)
        
        print(f"Weather data collected for {weather_data['city_name']} at {weather_data['datetime']}")
        print(f"Temperature: {weather_data['temperature']}°C")
        print(f"Wind speed: {weather_data['wind_speed']} m/s")
        print(f"Precipitation: {weather_data['precipitation']} mm")
        print(f"Est. solar irradiance: {weather_data['solar_irradiance']} W/m²")
        
        # Add to daily summary if not already added today
        add_to_daily_summary(weather_data)
        
        return weather_data

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def add_to_daily_summary(weather_data):
    """Store daily weather summaries for historical data tracking"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check if we already have a summary for today
    existing_summary = historical_weather_collection.find_one({
        'date': today,
        'city_id': weather_data['city_id']
    })
    
    if existing_summary:
        # Update existing summary with new measurements
        measurements = existing_summary.get('measurements', [])
        measurements.append({
            'datetime': weather_data['datetime'],
            'temperature': weather_data['temperature'],
            'humidity': weather_data['humidity'],
            'wind_speed': weather_data['wind_speed'],
            'cloud_cover': weather_data['cloud_cover'],
            'precipitation': weather_data['precipitation'],
            'solar_irradiance': weather_data['solar_irradiance']
        })
        
        # Calculate new min/max/avg values
        temperatures = [m['temperature'] for m in measurements]
        humidity_values = [m['humidity'] for m in measurements]
        wind_speeds = [m['wind_speed'] for m in measurements]
        
        # Update summary document
        historical_weather_collection.update_one(
            {'_id': existing_summary['_id']},
            {'$set': {
                'measurements': measurements,
                'measurement_count': len(measurements),
                'max_temp': max(temperatures),
                'min_temp': min(temperatures),
                'avg_temp': sum(temperatures) / len(temperatures),
                'max_humidity': max(humidity_values),
                'min_humidity': min(humidity_values),
                'avg_humidity': sum(humidity_values) / len(humidity_values),
                'max_wind': max(wind_speeds),
                'min_wind': min(wind_speeds),
                'avg_wind': sum(wind_speeds) / len(wind_speeds),
                'last_updated': datetime.now()
            }}
        )
    else:
        # Create new daily summary
        historical_weather_collection.insert_one({
            'date': today,
            'city_id': weather_data['city_id'],
            'city_name': weather_data['city_name'],
            'country': weather_data['country'],
            'measurements': [{
                'datetime': weather_data['datetime'],
                'temperature': weather_data['temperature'],
                'humidity': weather_data['humidity'],
                'wind_speed': weather_data['wind_speed'],
                'cloud_cover': weather_data['cloud_cover'],
                'precipitation': weather_data['precipitation'],
                'solar_irradiance': weather_data['solar_irradiance']
            }],
            'measurement_count': 1,
            'max_temp': weather_data['temperature'],
            'min_temp': weather_data['temperature'],
            'avg_temp': weather_data['temperature'],
            'max_humidity': weather_data['humidity'],
            'min_humidity': weather_data['humidity'],
            'avg_humidity': weather_data['humidity'],
            'max_wind': weather_data['wind_speed'],
            'min_wind': weather_data['wind_speed'],
            'avg_wind': weather_data['wind_speed'],
            'created_at': datetime.now(),
            'last_updated': datetime.now()
        })
        
        print(f"Created new daily summary for {weather_data['city_name']} on {today.strftime('%Y-%m-%d')}")

def fetch_5day_forecast(city_id=None, city_name=None, country_code=None):
    """Fetch 5-day weather forecast and store it"""
    url = OPENWEATHER_FORECAST_URL
    
    if city_id:
        params = {
            'id': city_id,
            'appid': OPENWEATHER_API_KEY,  
            'units': 'metric'
        }
    elif city_name and country_code:
        params = {
            'q': f"{city_name},{country_code}",
            'appid': OPENWEATHER_API_KEY,  
            'units': 'metric'
        }
    else:
        print("Either city_id or city_name and country_code must be provided")
        return None
        
    try: 
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        city_info = {
            'id': data['city']['id'],
            'name': data['city']['name'],
            'country': data['city']['country']
        }
        
        forecast_entries = []
        for forecast in data['list']:
            forecast_time = datetime.fromtimestamp(forecast['dt'])
            forecast_data = {
                'datetime': forecast_time,
                'city_id': city_info['id'],
                'city_name': city_info['name'],
                'country': city_info['country'],
                'temperature': forecast['main']['temp'],
                'humidity': forecast['main']['humidity'],
                'wind_speed': forecast['wind']['speed'],
                'cloud_cover': forecast.get('clouds', {}).get('all', 0),
                'precipitation': forecast.get('rain', {}).get('3h', 0),
                'description': forecast['weather'][0]['description'],
                'source': 'forecast_api',
                'prediction_time': datetime.now()
            }
            forecast_entries.append(forecast_data)
        
        # Store in forecast collection
        if forecast_entries:
            forecast_collection.insert_many(forecast_entries)
            print(f"Stored {len(forecast_entries)} forecast entries for {city_info['name']}")
        
        return forecast_entries

    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return None

def get_historical_daily_summaries(city_id, days=365):
    """Retrieve historical daily summaries for a city"""
    try:
        # Get summaries for the last X days
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)
        
        summaries = list(historical_weather_collection.find({
            'city_id': city_id,
            'date': {'$gte': start_date}
        }).sort('date', -1))
        
        print(f"Retrieved {len(summaries)} historical daily summaries for city ID {city_id}")
        return summaries
    except Exception as e:
        print(f"Error retrieving historical summaries: {e}")
        return []

def estimate_solar_irradiance(weather_data):
    """
    Enhanced solar irradiance estimation based on cloud cover, time of day,
    and latitude/longitude for more accurate solar panel production simulation.
    """
    cloud_cover = weather_data.get('clouds', {}).get('all', 0)
    
    now = datetime.now()
    hour = now.hour
    
    # Get latitude for more accurate solar calculation
    lat = weather_data.get('coord', {}).get('lat', 40.0)  # Default to mid-latitude
    
    # Calculate day of year for seasonal adjustment
    day_of_year = now.timetuple().tm_yday
    
    # Seasonal adjustment
    seasonal_factor = 1.0 + 0.3 * math.sin((day_of_year - 81) / 365 * 2 * math.pi)
    
    # Day/night cycle
    if hour < 6 or hour > 18:
        time_factor = 0.0
    else:
        time_factor = math.sin(math.pi * (hour - 6) / 12)
    
    # Latitude adjustment (more sun near equator)
    latitude_factor = 1.0 - abs(lat) / 90 * 0.3
    
    max_irradiance = 1000 * seasonal_factor * latitude_factor
    
    min_cloud_factor = 0.2  
    cloud_factor = max(min_cloud_factor, 1 - (cloud_cover / 100))
    
    base_irradiance = int(max_irradiance * time_factor * cloud_factor)
    
    # Ensure reasonable daytime values
    if 6 <= hour <= 18 and base_irradiance < 50 and time_factor > 0.2:
        base_irradiance = 50 + int(time_factor * 100)
    
    return base_irradiance

def simulate_solar_panel_data(city_id=None):
    """
    Simulate solar panel production based on latest weather data.
    """
    # Get the latest weather data for the specified city
    query = {}
    if city_id:
        query = {"city_id": city_id}
        
    latest_weather = weather_collection.find_one(query, sort=[('datetime', -1)])
    
    if not latest_weather:
        print("No weather data available!")
        return None

    irradiance = latest_weather['solar_irradiance']
    temperature = latest_weather['temperature']
    city_id = latest_weather['city_id']
    city_name = latest_weather['city_name']
    
    # Typical home solar installation (5kW)
    system_capacity = 5.0  # kW
    
    # Solar panel efficiency factors
    base_efficiency = 0.20  # 20% efficiency
    
    # Temperature factor (efficiency drops 0.5% per degree above 25°C)
    temp_adjustment = max(0, temperature - 25) * 0.005
    adjusted_efficiency = base_efficiency * (1 - temp_adjustment)
    
    # Calculate production
    standard_test_irradiance = 1000  # W/m²
    
    min_daytime_production = 0.1
    hour = datetime.now().hour
    is_daytime = 6 <= hour <= 18
    
    raw_production = (irradiance / standard_test_irradiance) * system_capacity * adjusted_efficiency
    
    if is_daytime and raw_production < min_daytime_production and irradiance > 0:
        production = min_daytime_production + (irradiance / 1000)
    else:
        production = raw_production
    
    # Assume 60% of production is fed back to the grid
    feed_in = production * 0.6
    
    solar_data = {
        'datetime': datetime.now(),
        'city_id': city_id,
        'city_name': city_name,
        'production': round(production, 2),
        'feed_in': round(feed_in, 2),
        'efficiency': round(adjusted_efficiency * 100, 2),
        'panel_temperature': round(temperature + 15 * (irradiance / 1000), 1)
    }

    result = solar_collection.insert_one(solar_data)
    
    print(f"Solar panel data simulated for {city_name} at {solar_data['datetime']}")
    print(f"Production: {solar_data['production']} kW")
    print(f"Feed-in: {solar_data['feed_in']} kW")
    print(f"Efficiency: {solar_data['efficiency']}%")
    
    return solar_data

def collect_data_for_all_cities():
    cities = get_all_cities()
    results = []
    
    for city in cities:
        print(f"Collecting data for {city['name']}, {city['country']}...")
        weather_data = fetch_weather_data(city_id=city['id'])
        
        # Only fetch forecast once per day to avoid API limits
        should_fetch_forecast = True
        latest_forecast = forecast_collection.find_one(
            {'city_id': city['id'], 'source': 'forecast_api'},
            sort=[('prediction_time', -1)]
        )
        if latest_forecast and latest_forecast['prediction_time'] > datetime.now() - timedelta(hours=12):
            should_fetch_forecast = False
        
        if should_fetch_forecast:
            forecast_data = fetch_5day_forecast(city_id=city['id'])
        
        if weather_data:
            solar_data = simulate_solar_panel_data(city_id=city['id'])
            results.append({
                'city': city['name'],
                'weather': weather_data is not None,
                'solar': solar_data is not None,
                'forecast': should_fetch_forecast
            })
            
    return results

def main():
    """Main function to run the data collection process"""
    print("Data collector starting...")
    
    # Initialize cities if needed
    initialize_cities()
    
    while True:
        print("\n===== Collecting data for all cities =====")
        results = collect_data_for_all_cities()
        
        for result in results:
            status = "✓" if result['weather'] and result['solar'] else "✗"
            print(f"[{status}] {result['city']}")
      
        collection_interval = 60  # 1 minute for testing
        print(f"Waiting {collection_interval} seconds before next collection...")
        time.sleep(collection_interval)

if __name__ == "__main__":
    main()