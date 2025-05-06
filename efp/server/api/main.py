import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "dmlab")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

if "<db_password>" in MONGO_URI and MONGO_DB_PASSWORD:
    MONGO_URI = MONGO_URI.replace("<db_password>", MONGO_DB_PASSWORD)

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("Connected to MongoDB Atlas successfully from API!")
    db = client[MONGO_DB_NAME]
    weather_collection = db["weather"]
    solar_collection = db["solar"]
    forecast_collection = db["forecast"]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

app = Flask(__name__)
CORS(app)

@app.route('/')
def root():
    return jsonify({"message": "Welcome to the Energy Forecast API"})

@app.route('/weather')
def get_weather():
    try:
        days = int(request.args.get('days', 1))
        threshold_date = datetime.now() - timedelta(days=days)
        
        weather_data = list(weather_collection.find(
            {"datetime": {"$gte": threshold_date}},
            {"_id": 0}
        ).sort("datetime", -1))
        
        for data in weather_data:
            data['datetime'] = data['datetime'].isoformat()
        
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving weather data: {str(e)}"}), 500

@app.route('/solar')
def get_solar():
    try:
        days = int(request.args.get('days', 1))
        threshold_date = datetime.now() - timedelta(days=days)
        
        solar_data = list(solar_collection.find(
            {"datetime": {"$gte": threshold_date}},
            {"_id": 0}
        ).sort("datetime", -1))
        
        for data in solar_data:
            data['datetime'] = data['datetime'].isoformat()
        
        return jsonify(solar_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving solar data: {str(e)}"}), 500

@app.route('/forecast')
def get_forecast():
    try:
        hours = int(request.args.get('hours', 24))
        
        latest_forecast = forecast_collection.find_one(
            sort=[("forecast_created_at", -1)]
        )
        
        if not latest_forecast:
            return jsonify({"error": "No forecast data available"}), 404
        
        latest_creation_time = latest_forecast["forecast_created_at"]
        forecasts = list(forecast_collection.find(
            {"forecast_created_at": latest_creation_time},
            {"_id": 0}
        ).sort("datetime", 1).limit(hours))
        
        for forecast in forecasts:
            forecast['datetime'] = forecast['datetime'].isoformat()
            forecast['forecast_created_at'] = forecast['forecast_created_at'].isoformat()
        
        return jsonify(forecasts)
    except Exception as e:
        return jsonify({"error": f"Error retrieving forecast data: {str(e)}"}), 500

@app.route('/health')
def health_check():
    try:
        client.admin.command('ping')
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": f"disconnected: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=True)
