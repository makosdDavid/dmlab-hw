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
    cities_collection = db["cities"]
    engineer_predictions_collection = db["engineer_predictions"]
    insurance_predictions_collection = db["insurance_predictions"]
    tourist_predictions_collection = db["tourist_predictions"]
    historic_accuracy_collection = db["historic_accuracy"]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

app = Flask(__name__)
CORS(app)

@app.route('/')
def root():
    return jsonify({"message": "Welcome to the Energy Forecast API"})

@app.route('/cities')
def get_cities():
    try:
        cities = list(cities_collection.find({}, {"_id": 0}))
        return jsonify(cities)
    except Exception as e:
        return jsonify({"error": f"Error retrieving cities: {str(e)}"}), 500

@app.route('/weather')
def get_weather():
    try:
        days = int(request.args.get('days', 1))
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        threshold_date = datetime.now() - timedelta(days=days)
        query = {"datetime": {"$gte": threshold_date}}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        weather_data = list(weather_collection.find(query, {"_id": 0}).sort("datetime", -1))
        
        for data in weather_data:
            data['datetime'] = data['datetime'].isoformat()
        
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving weather data: {str(e)}"}), 500

@app.route('/solar')
def get_solar():
    try:
        days = int(request.args.get('days', 1))
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        threshold_date = datetime.now() - timedelta(days=days)
        query = {"datetime": {"$gte": threshold_date}}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        solar_data = list(solar_collection.find(query, {"_id": 0}).sort("datetime", -1))
        
        for data in solar_data:
            data['datetime'] = data['datetime'].isoformat()
        
        return jsonify(solar_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving solar data: {str(e)}"}), 500

@app.route('/forecast')
def get_forecast():
    try:
        hours = int(request.args.get('hours', 24))
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        forecast_type = request.args.get('type', 'day')
        
        # Build query
        query = {"forecast_type": forecast_type}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        # Find latest forecast for this city and type
        latest_forecast = forecast_collection.find_one(
            query,
            sort=[("prediction_time", -1)]
        )
        
        if not latest_forecast:
            return jsonify({"error": "No forecast data available"}), 404
        
        # Get latest prediction time
        latest_creation_time = latest_forecast["prediction_time"]
        query["prediction_time"] = latest_creation_time
        
        forecasts = list(forecast_collection.find(
            query,
            {"_id": 0}
        ).sort("datetime", 1).limit(hours))
        
        for forecast in forecasts:
            forecast['datetime'] = forecast['datetime'].isoformat()
            forecast['prediction_time'] = forecast['prediction_time'].isoformat()
        
        return jsonify(forecasts)
    except Exception as e:
        return jsonify({"error": f"Error retrieving forecast data: {str(e)}"}), 500

@app.route('/accuracy')
def get_accuracy():
    try:
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        # Build query
        query = {}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        # Get latest accuracy data
        accuracy_data = list(historic_accuracy_collection.find(
            query,
            {"_id": 0}
        ).sort("datetime", -1))
        
        if not accuracy_data:
            return jsonify({"error": "No accuracy data available"}), 404
        
        for data in accuracy_data:
            data['datetime'] = data['datetime'].isoformat()
        
        return jsonify(accuracy_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving accuracy data: {str(e)}"}), 500

@app.route('/predictions/engineer')
def get_engineer_predictions():
    try:
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        # Build query
        query = {}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        # Get latest predictions
        prediction = engineer_predictions_collection.find_one(query, {"_id": 0})
        
        if not prediction:
            return jsonify({"error": "No engineer predictions available"}), 404
        
        prediction['datetime'] = prediction['datetime'].isoformat()
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": f"Error retrieving engineer predictions: {str(e)}"}), 500

@app.route('/predictions/insurance')
def get_insurance_predictions():
    try:
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        # Build query
        query = {}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        # Get latest predictions
        prediction = insurance_predictions_collection.find_one(query, {"_id": 0})
        
        if not prediction:
            return jsonify({"error": "No insurance predictions available"}), 404
        
        prediction['datetime'] = prediction['datetime'].isoformat()
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": f"Error retrieving insurance predictions: {str(e)}"}), 500

@app.route('/predictions/tourist')
def get_tourist_predictions():
    try:
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        # Build query
        query = {}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        # Get latest predictions
        prediction = tourist_predictions_collection.find_one(query, {"_id": 0})
        
        if not prediction:
            return jsonify({"error": "No tourist predictions available"}), 404
        
        prediction['datetime'] = prediction['datetime'].isoformat()
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": f"Error retrieving tourist predictions: {str(e)}"}), 500

@app.route('/process', methods=['POST'])
def trigger_processing():
    try:
        from data_processor.processor import process_all_cities
        
        results = process_all_cities()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500

@app.route('/health')
def health_check():
    try:
        client.admin.command('ping')
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": f"disconnected: {str(e)}"}), 500

@app.route('/historical')
def get_historical_weather():
    try:
        days = int(request.args.get('days', 365))  # Default to 1 year
        city_id = request.args.get('city_id')
        city_name = request.args.get('city_name')
        
        # Build query
        query = {}
        
        if city_id:
            query["city_id"] = int(city_id)
        elif city_name:
            query["city_name"] = city_name
        
        # Find historical daily summaries
        threshold_date = datetime.now() - timedelta(days=days)
        query["date"] = {"$gte": threshold_date}
        
        historical_data = list(db["historical_weather"].find(
            query,
            {"_id": 0, "measurements": 0}  # Exclude measurements to reduce response size
        ).sort("date", -1))
        
        for data in historical_data:
            data['date'] = data['date'].isoformat()
            if 'created_at' in data:
                data['created_at'] = data['created_at'].isoformat()
            if 'last_updated' in data:
                data['last_updated'] = data['last_updated'].isoformat()
        
        return jsonify(historical_data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving historical weather data: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=True)
