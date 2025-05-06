import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

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
app = Flask(__name__)
CORS(app)

@app.route("/api/health")
def health_check():
    try:
        mongo_client.admin.command('ping')
        return jsonify({"status": "healthy", "message": "Connected to MongoDB"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500

@app.route("/api/weather")
def get_weather_route():
    try:
        limit = request.args.get('limit', default=10, type=int)
        weather_data = list(get_weather_data(limit))
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving weather data: {str(e)}"}), 500

@app.route("/api/solar")
def get_solar_route():
    try:
        limit = request.args.get('limit', default=10, type=int)
        solar_data = list(get_solar_data(limit))
        return jsonify(solar_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving solar data: {str(e)}"}), 500

@app.route("/api/forecast")
def get_forecast_route():
    try:
        hours = request.args.get('hours', default=24, type=int)
        forecast_data = list(get_forecast_data(hours))
        return jsonify(forecast_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving forecast data: {str(e)}"}), 500

@app.route("/api/process", methods=["POST"])
def process_data():
    try:
        result = generate_forecast()
        return jsonify({"success": True, "message": "Processing completed", "forecast_count": result})
    except Exception as e:
        return jsonify({"error": f"Error processing data: {str(e)}"}), 500

if __name__ == "__main__":
    print("Starting Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False) 