import os
import time
import json
import math
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "dmlab")
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

db = mongo_client[MONGO_DB_NAME]
weather_collection = db["weather"]
solar_collection = db["solar"]
forecast_collection = db["forecast"]
cities_collection = db["cities"]
historic_accuracy_collection = db["historic_accuracy"]
engineer_predictions_collection = db["engineer_predictions"]
insurance_predictions_collection = db["insurance_predictions"]

def get_weather_data(city_id=None, limit: int = 10) -> Generator[Dict[str, Any], None, None]:
    query = {}
    if city_id:
        query["city_id"] = city_id
        
    cursor = weather_collection.find(query).sort("datetime", pymongo.DESCENDING).limit(limit)
    
    for doc in cursor:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        if 'datetime' in doc and isinstance(doc['datetime'], datetime):
            doc['datetime'] = doc['datetime'].isoformat()
            
        yield doc

def get_solar_data(city_id=None, limit: int = 10) -> Generator[Dict[str, Any], None, None]:
    query = {}
    if city_id:
        query["city_id"] = city_id
        
    cursor = solar_collection.find(query).sort("datetime", pymongo.DESCENDING).limit(limit)
    
    for doc in cursor:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        if 'datetime' in doc and isinstance(doc['datetime'], datetime):
            doc['datetime'] = doc['datetime'].isoformat()
            
        yield doc

def get_forecast_data(city_id=None, hours: int = 24) -> Generator[Dict[str, Any], None, None]:
    query = {}
    if city_id:
        query["city_id"] = city_id
    
    # Find the latest prediction time
    latest_forecast = forecast_collection.find_one(
        query, sort=[("prediction_time", pymongo.DESCENDING)]
    )
    
    if not latest_forecast:
        return
        
    prediction_time = latest_forecast.get("prediction_time")
    
    # Update query to include prediction time
    query["prediction_time"] = prediction_time
    
    cursor = forecast_collection.find(
        query
    ).sort("datetime", pymongo.ASCENDING).limit(hours)
    
    for doc in cursor:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        if 'datetime' in doc and isinstance(doc['datetime'], datetime):
            doc['datetime'] = doc['datetime'].isoformat()
            
        if 'prediction_time' in doc and isinstance(doc['prediction_time'], datetime):
            doc['prediction_time'] = doc['prediction_time'].isoformat()
            
        yield doc

def get_cities():
    """Get list of cities from database"""
    return list(cities_collection.find({}, {"_id": 0}))

def generate_forecast(city_id=None, city_name=None, timeframe="day") -> int:
    """Generate forecasts for the specified city and timeframe (day, month, year)"""
    current_time = datetime.now()
    
    # Determine query for finding latest weather data
    query = {}
    if city_id:
        query["city_id"] = city_id
    elif city_name:
        query["city_name"] = city_name
    
    # Get latest weather and solar data for the city
    latest_weather = weather_collection.find_one(query, sort=[('datetime', -1)])
    if not latest_weather:
        print(f"No weather data available for forecast generation")
        return 0
        
    latest_solar = solar_collection.find_one(query, sort=[('datetime', -1)])
    if not latest_solar:
        print(f"No solar data available for forecast generation")
        return 0
    
    # Calculate forecast hours based on timeframe
    if timeframe == "day":
        forecast_hours = 24
    elif timeframe == "month":
        forecast_hours = 24 * 30
    elif timeframe == "year":
        forecast_hours = 24 * 365
    elif timeframe == "5years":
        forecast_hours = 24 * 365 * 5
    elif timeframe == "10years":
        forecast_hours = 24 * 365 * 10
    else:
        forecast_hours = 24  # Default to day
    
    # Generate hourly forecasts
    forecasts = []
    
    for hour in range(forecast_hours):
        forecast_time = current_time + timedelta(hours=hour)
        
        # Basic consumption model with daily and seasonal patterns
        hour_of_day = forecast_time.hour
        day_of_year = forecast_time.timetuple().tm_yday
        
        # Daily cycle - peaking in morning and evening
        daily_factor = 1.0 + 0.3 * math.sin((hour_of_day + 6) / 24 * 2 * math.pi) + 0.2 * math.sin((hour_of_day + 18) / 24 * 2 * math.pi)
        
        # Seasonal cycle - more energy use in winter and summer
        seasonal_factor = 1.0 + 0.2 * math.cos((day_of_year / 365) * 2 * math.pi)
        
        # Base consumption pattern 
        base_consumption = 20 * daily_factor * seasonal_factor
        
        # Weather influence
        temp = latest_weather.get('temperature', 20)
        wind_speed = latest_weather.get('wind_speed', 0)
        
        # Temperature effect (more consumption at temperature extremes)
        temp_factor = 1.0 + 0.05 * abs(temp - 22)
        
        # Add randomness based on forecast distance in time
        randomness_factor = 1.0 + (hour / forecast_hours) * 0.5
        randomness = (0.9 + 0.2 * random.random() * randomness_factor)
        
        # Calculate consumption
        consumption = base_consumption * temp_factor * randomness
        
        # Solar production forecast
        base_production = 0
        if 6 <= forecast_time.hour <= 18:
            hour_factor = 1.0 - abs(forecast_time.hour - 12) / 6
            
            # Add seasonal variation to solar production
            seasonal_sun_factor = 1.0 + 0.4 * math.sin((day_of_year - 172) / 365 * 2 * math.pi)
            
            base_production = 40 * hour_factor * seasonal_sun_factor
                
            # Weather impact on solar production
            if latest_weather and 'cloud_cover' in latest_weather:
                cloud_cover = float(latest_weather.get('cloud_cover', 0))
                cloud_factor = 1.0 - (cloud_cover / 100) * 0.8
                base_production *= cloud_factor
        
        # Randomize production with declining certainty over time
        production_randomness = 1.0 + (hour / forecast_hours) * 0.6
        production = base_production * (0.85 + 0.3 * random.random() * production_randomness)
        
        # Ensure reasonable production during daytime
        if 6 <= forecast_time.hour <= 18 and production < 0.5 and base_production > 0:
            production = 0.5 + (hour_factor * 2)
        
        # Calculate net consumption
        net_consumption = consumption - production
        
        # Calculate confidence (decreases with time)
        confidence = 0.98 - (hour / forecast_hours) * 0.8
        
        # Create forecast entry
        forecasts.append({
            "datetime": forecast_time,
            "prediction_time": current_time,
            "city_id": latest_weather.get('city_id'),
            "city_name": latest_weather.get('city_name'),
            "consumption": round(consumption, 2),
            "production": round(production, 2),
            "net_consumption": round(net_consumption, 2),
            "confidence": round(confidence, 2),
            "forecast_type": timeframe,
            "source": "advanced_model_v2"
        })
    
    if forecasts:
        # Insert forecasts into database
        forecast_collection.insert_many(forecasts)
        
        # Generate predictions for different stakeholders
        if timeframe == "day":
            generate_engineer_predictions(city_id=latest_weather.get('city_id'), city_name=latest_weather.get('city_name'), forecasts=forecasts, weather_data=latest_weather, solar_data=latest_solar)
            generate_insurance_predictions(city_id=latest_weather.get('city_id'), city_name=latest_weather.get('city_name'), forecasts=forecasts, weather_data=latest_weather)
            generate_tourist_predictions(city_id=latest_weather.get('city_id'), city_name=latest_weather.get('city_name'), forecasts=forecasts, weather_data=latest_weather)
    
    return len(forecasts)

def generate_historical_accuracy(city_id=None, city_name=None):
    """Generate historical accuracy metrics by comparing past forecasts to actual weather data"""
    
    print("Generating historical accuracy metrics...")
    
    try:
        # Determine query for finding forecast and weather data
        query = {}
        if city_id:
            query["city_id"] = city_id
        elif city_name:
            query["city_name"] = city_name
        
        # Get all cities if none specified
        if not city_id and not city_name:
            cities = list(cities_collection.find({}, {"_id": 0}))
        else:
            cities = list(cities_collection.find(query, {"_id": 0}))
        
        accuracy_records = []
    
        for city in cities:
            city_id = city["id"]
            city_query = {"city_id": city_id}
            
            # Find all prediction times for this city
            prediction_times = forecast_collection.distinct('prediction_time', city_query)
            prediction_times.sort(reverse=True)  # Most recent first
            
            # Track accuracy metrics for different timeframes
            day_forecast_count = 0
            day_forecast_errors = 0
            week_forecast_count = 0 
            week_forecast_errors = 0
            month_forecast_count = 0
            month_forecast_errors = 0
            year_forecast_count = 0
            year_forecast_errors = 0
            
            now = datetime.now()
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(days=7)
            one_month_ago = now - timedelta(days=30)
            one_year_ago = now - timedelta(days=365)
            
            # Find weather data for verification (past 1 year)
            weather_data = list(
                weather_collection.find(
                    {**city_query, "datetime": {"$gte": one_year_ago}}
                ).sort("datetime", 1)
            )
            
            if not weather_data:
                print(f"No weather data available for accuracy calculation for {city['name']}")
                continue
                
            # Create lookup table for quick access to actual weather data
            actual_data = {}
            for data in weather_data:
                # Round to nearest hour for comparison with forecast times
                hour_key = data["datetime"].replace(minute=0, second=0, microsecond=0).isoformat()
                actual_data[hour_key] = data
            
            # Analyze each prediction time
            for prediction_time in prediction_times:
                if prediction_time < one_year_ago:
                    continue  # Skip old predictions outside our comparison window
                
                # Retrieve forecasts made at this prediction time
                forecasts = list(
                    forecast_collection.find(
                        {**city_query, "prediction_time": prediction_time}
                    ).sort("datetime", 1)
                )
                
                for forecast in forecasts:
                    forecast_time = forecast["datetime"]
                    
                    # Skip future forecasts that we can't verify yet
                    if forecast_time > now:
                        continue
                    
                    # Round to nearest hour
                    forecast_hour = forecast_time.replace(minute=0, second=0, microsecond=0)
                    hour_key = forecast_hour.isoformat()
                    
                    # Find actual weather at forecasted time
                    actual = actual_data.get(hour_key)
                    if not actual:
                        # Try to find closest hour
                        closest_hour = min(
                            actual_data.keys(),
                            key=lambda d: abs(datetime.fromisoformat(d) - forecast_hour)
                        ) if actual_data else None
                        
                        if closest_hour and abs(datetime.fromisoformat(closest_hour) - forecast_hour) < timedelta(hours=2):
                            actual = actual_data[closest_hour]
                        else:
                            continue  # No matching actual data found
                    
                    # Calculate forecast errors (percentage deviation from actual)
                    temp_error = abs(forecast["temperature"] - actual["temperature"]) / max(1, abs(actual["temperature"])) * 100
                    
                    # Skip extreme outliers that might skew results
                    if temp_error > 100:
                        continue
                    
                    # Determine which timeframe this belongs to
                    forecast_age = now - prediction_time
                    
                    if forecast_age <= timedelta(days=1):
                        day_forecast_count += 1
                        day_forecast_errors += temp_error
                    
                    if forecast_age <= timedelta(days=7):
                        week_forecast_count += 1
                        week_forecast_errors += temp_error
                    
                    if forecast_age <= timedelta(days=30):
                        month_forecast_count += 1
                        month_forecast_errors += temp_error
                    
                    year_forecast_count += 1
                    year_forecast_errors += temp_error
            
            # Calculate average error percentages
            day_accuracy = max(0, 100 - (day_forecast_errors / day_forecast_count if day_forecast_count > 0 else 0))
            week_accuracy = max(0, 100 - (week_forecast_errors / week_forecast_count if week_forecast_count > 0 else 0))
            month_accuracy = max(0, 100 - (month_forecast_errors / month_forecast_count if month_forecast_count > 0 else 0))
            year_accuracy = max(0, 100 - (year_forecast_errors / year_forecast_count if year_forecast_count > 0 else 0))
            
            # Create accuracy record
            accuracy_record = {
                "datetime": now,
                "city_id": city_id,
                "city_name": city["name"],
                "country": city["country"],
                "day_accuracy": round(day_accuracy, 2),
                "week_accuracy": round(week_accuracy, 2),
                "month_accuracy": round(month_accuracy, 2),
                "year_accuracy": round(year_accuracy, 2),
                "day_forecast_count": day_forecast_count,
                "week_forecast_count": week_forecast_count,
                "month_forecast_count": month_forecast_count,
                "year_forecast_count": year_forecast_count
            }
            
            # Insert into database
            historic_accuracy_collection.insert_one(accuracy_record)
            accuracy_records.append(accuracy_record)
            
            print(f"Generated accuracy metrics for {city['name']}:")
            print(f"  1-day accuracy: {accuracy_record['day_accuracy']}% (based on {day_forecast_count} forecasts)")
            print(f"  1-week accuracy: {accuracy_record['week_accuracy']}% (based on {week_forecast_count} forecasts)")
            print(f"  1-month accuracy: {accuracy_record['month_accuracy']}% (based on {month_forecast_count} forecasts)")
            print(f"  1-year accuracy: {accuracy_record['year_accuracy']}% (based on {year_forecast_count} forecasts)")
        
        return accuracy_records
    
    except Exception as e:
        print(f"Error generating historical accuracy: {e}")
        return []

def generate_engineer_predictions(city_id=None, city_name=None, forecasts=None, weather_data=None, solar_data=None):
    """Generate specialized predictions for solar panel engineers with enhanced analysis"""
    try:
        print("Generating engineer predictions...")
        
        # Determine query for finding data
        query = {}
        if city_id:
            query["city_id"] = city_id
        elif city_name:
            query["city_name"] = city_name
        
        # Get the city
        city = cities_collection.find_one({"id": city_id} if city_id else {"name": city_name})
        if not city:
            print(f"City not found for engineer predictions")
            return None
        
        # Get weather and solar data from last year if not provided
        if not weather_data or not solar_data:
            one_year_ago = datetime.now() - timedelta(days=365)
            weather_data = list(
                weather_collection.find(
                    {**query, "datetime": {"$gte": one_year_ago}}
                ).sort("datetime", 1)
            )
            solar_data = list(
                solar_collection.find(
                    {**query, "datetime": {"$gte": one_year_ago}}
                ).sort("datetime", 1)
            )
        
        # Get forecasts if not provided
        if not forecasts:
            latest_prediction = forecast_collection.find_one(
                {**query}, sort=[("prediction_time", -1)]
            )
            
            if latest_prediction:
                prediction_time = latest_prediction["prediction_time"]
                forecasts = list(
                    forecast_collection.find(
                        {**query, "prediction_time": prediction_time}
                    ).sort("datetime", 1)
                )
        
        # Process historical solar data to generate insights
        if not solar_data:
            print(f"No solar data available for engineer predictions for {city['name']}")
            return None
            
        # Calculate daily solar panel performance
        daily_performance = {}
        for data in solar_data:
            date_key = data["datetime"].strftime("%Y-%m-%d")
            
            if date_key not in daily_performance:
                daily_performance[date_key] = {
                    "date": data["datetime"].date(),
                    "production_values": [],
                    "efficiency_values": [],
                    "temperature_values": []
                }
            
            daily_performance[date_key]["production_values"].append(data["production"])
            daily_performance[date_key]["efficiency_values"].append(data["efficiency"])
            daily_performance[date_key]["temperature_values"].append(data["panel_temperature"])
        
        # Calculate averages for each day
        daily_averages = []
        for date_key, performance in daily_performance.items():
            avg_production = sum(performance["production_values"]) / len(performance["production_values"])
            avg_efficiency = sum(performance["efficiency_values"]) / len(performance["efficiency_values"])
            avg_temperature = sum(performance["temperature_values"]) / len(performance["temperature_values"])
            
            daily_averages.append({
                "date": performance["date"].isoformat(),
                "avg_production": round(avg_production, 2),
                "avg_efficiency": round(avg_efficiency, 2),
                "avg_panel_temperature": round(avg_temperature, 1)
            })
        
        # Sort by date
        daily_averages.sort(key=lambda x: x["date"])
        
        # Calculate monthly performance metrics
        monthly_performance = {}
        for data in solar_data:
            month_key = data["datetime"].strftime("%Y-%m")
            
            if month_key not in monthly_performance:
                monthly_performance[month_key] = {
                    "year": data["datetime"].year,
                    "month": data["datetime"].month,
                    "month_name": data["datetime"].strftime("%B"),
                    "production_sum": 0,
                    "production_count": 0,
                    "efficiency_sum": 0,
                    "efficiency_count": 0,
                    "high_production_hours": 0,
                    "measurement_hours": 0
                }
            
            monthly_performance[month_key]["production_sum"] += data["production"]
            monthly_performance[month_key]["production_count"] += 1
            
            monthly_performance[month_key]["efficiency_sum"] += data["efficiency"]
            monthly_performance[month_key]["efficiency_count"] += 1
            
            monthly_performance[month_key]["measurement_hours"] += 1
            
            # Count hours with high production (>80% of system capacity)
            if data["production"] > 4.0:  # 80% of 5kW system
                monthly_performance[month_key]["high_production_hours"] += 1
        
        # Calculate monthly averages
        monthly_averages = []
        for month_key, performance in monthly_performance.items():
            avg_production = performance["production_sum"] / performance["production_count"] if performance["production_count"] > 0 else 0
            avg_efficiency = performance["efficiency_sum"] / performance["efficiency_count"] if performance["efficiency_count"] > 0 else 0
            
            # Calculate peak performance ratio (actual high production hours vs theoretical maximum)
            # Estimate maximum potential hours based on month (very rough estimate)
            month = performance["month"]
            # Potential sunny hours varies by month (northern hemisphere)
            potential_peak_hours = {
                1: 8, 2: 9, 3: 10, 4: 12, 5: 13, 6: 14,
                7: 14, 8: 13, 9: 12, 10: 10, 11: 9, 12: 8
            }
            days_in_month = 30  # Approximation
            potential_hours = potential_peak_hours[month] * days_in_month
            performance_ratio = performance["high_production_hours"] / potential_hours if potential_hours > 0 else 0
            
            monthly_averages.append({
                "year_month": month_key,
                "month_name": performance["month_name"],
                "year": performance["year"],
                "month": performance["month"],
                "avg_production": round(avg_production, 2),
                "avg_efficiency": round(avg_efficiency, 2),
                "high_production_hours": performance["high_production_hours"],
                "performance_ratio": round(performance_ratio * 100, 1)  # As percentage
            })
        
        # Sort by year and month
        monthly_averages.sort(key=lambda x: (x["year"], x["month"]))
        
        # Calculate yearly averages if we have enough data
        yearly_averages = {}
        for data in monthly_averages:
            year = data["year"]
            if year not in yearly_averages:
                yearly_averages[year] = {
                    "production_sum": 0,
                    "months_count": 0,
                    "efficiency_sum": 0,
                    "high_production_hours": 0
                }
            
            yearly_averages[year]["production_sum"] += data["avg_production"]
            yearly_averages[year]["efficiency_sum"] += data["avg_efficiency"]
            yearly_averages[year]["months_count"] += 1
            yearly_averages[year]["high_production_hours"] += data["high_production_hours"]
        
        yearly_avg_data = []
        for year, data in yearly_averages.items():
            if data["months_count"] > 0:
                yearly_avg_data.append({
                    "year": year,
                    "avg_production": round(data["production_sum"] / data["months_count"], 2),
                    "avg_efficiency": round(data["efficiency_sum"] / data["months_count"], 2),
                    "high_production_hours": data["high_production_hours"]
                })
        
        # Find optimal maintenance schedule
        # Strategy: recommend maintenance before high-production months
        now = datetime.now()
        current_month = now.month
        
        # Sort months by average production
        sorted_months = sorted(monthly_averages, key=lambda x: x["avg_production"], reverse=True)
        high_production_months = [m for m in sorted_months if m["avg_production"] > 3.0]  # Threshold for high production
        
        maintenance_recommendations = []
        
        # Recommend maintenance before high production periods
        for month_data in high_production_months:
            # Calculate the month before this high production month
            maintenance_month = month_data["month"] - 1 if month_data["month"] > 1 else 12
            
            # Only recommend if it's in the future
            if (maintenance_month > current_month) or (month_data["year"] > now.year):
                maintenance_month_name = datetime(2020, maintenance_month, 1).strftime("%B")
                production_month_name = month_data["month_name"]
                
                recommendation = {
                    "maintenance_month": maintenance_month,
                    "maintenance_month_name": maintenance_month_name,
                    "production_month": month_data["month"],
                    "production_month_name": production_month_name,
                    "expected_production": month_data["avg_production"],
                    "recommendation": f"Schedule maintenance in {maintenance_month_name} before high production period in {production_month_name}"
                }
                
                # Check if this month is already in recommendations
                if not any(r["maintenance_month"] == maintenance_month for r in maintenance_recommendations):
                    maintenance_recommendations.append(recommendation)
        
        # If we couldn't generate any maintenance recommendations, add a generic one
        if not maintenance_recommendations:
            next_maintenance_month = (current_month + 2) % 12 or 12  # Two months from now
            maintenance_month_name = datetime(2020, next_maintenance_month, 1).strftime("%B")
            
            maintenance_recommendations.append({
                "maintenance_month": next_maintenance_month,
                "maintenance_month_name": maintenance_month_name,
                "recommendation": f"Schedule routine maintenance in {maintenance_month_name}"
            })
        
        # Calculate panel efficiency insights
        efficiency_insights = {}
        
        # Find average efficiency trends
        monthly_efficiencies = [(m["month"], m["avg_efficiency"]) for m in monthly_averages]
        
        # Check if efficiency is declining
        if len(monthly_efficiencies) >= 3:
            recent_months = sorted(monthly_efficiencies[-3:])
            if recent_months[0][1] > recent_months[-1][1]:
                efficiency_trend = "declining"
                efficiency_decline_rate = (recent_months[0][1] - recent_months[-1][1]) / recent_months[0][1] * 100
            elif recent_months[0][1] < recent_months[-1][1]:
                efficiency_trend = "improving"
                efficiency_decline_rate = 0
            else:
                efficiency_trend = "stable"
                efficiency_decline_rate = 0
        else:
            efficiency_trend = "unknown"
            efficiency_decline_rate = 0
        
        # Calculate average efficiency
        all_efficiencies = [data["efficiency"] for data in solar_data]
        avg_efficiency = sum(all_efficiencies) / len(all_efficiencies) if all_efficiencies else 0
        
        # Calculate performance ratio
        total_high_production_hours = sum(month["high_production_hours"] for month in monthly_averages)
        total_potential_hours = sum(30 * potential_peak_hours[month["month"]] for month in monthly_averages)
        overall_performance_ratio = total_high_production_hours / total_potential_hours if total_potential_hours > 0 else 0
        
        # Calculate expected panel lifespan based on efficiency trend
        base_lifespan_years = 25  # Standard solar panel lifespan
        if efficiency_trend == "declining" and efficiency_decline_rate > 0:
            # Adjust lifespan based on decline rate
            yearly_decline = efficiency_decline_rate * 4  # Extrapolate to yearly decline
            if yearly_decline > 10:  # If declining more than 10% per year
                lifespan_adjustment = -5
            elif yearly_decline > 5:  # If declining 5-10% per year
                lifespan_adjustment = -3
            else:
                lifespan_adjustment = -1
        elif efficiency_trend == "stable":
            lifespan_adjustment = 0
        else:
            lifespan_adjustment = 2
        
        expected_lifespan = base_lifespan_years + lifespan_adjustment
        
        efficiency_insights = {
            "avg_efficiency": round(avg_efficiency, 2),
            "efficiency_trend": efficiency_trend,
            "annual_decline_rate": round(efficiency_decline_rate, 2) if efficiency_trend == "declining" else 0,
            "performance_ratio": round(overall_performance_ratio * 100, 1),  # As percentage
            "expected_lifespan": expected_lifespan
        }
        
        # Generate short-term production forecast
        production_forecast = []
        if forecasts:
            now = datetime.now()
            for i in range(7):  # 7-day forecast
                target_date = now + timedelta(days=i)
                day_forecasts = [f for f in forecasts if f["datetime"].date() == target_date.date()]
                
                if day_forecasts:
                    # Calculate expected solar production based on forecast
                    day_production = []
                    for forecast in day_forecasts:
                        hour = forecast["datetime"].hour
                        
                        # Skip night hours
                        if hour < 6 or hour > 18:
                            continue
                            
                        # Estimate production based on weather data
                        cloud_cover = forecast.get("cloud_cover", 50)
                        temperature = forecast.get("temperature", 20)
                        
                        # Calculate hour factor (peak at noon)
                        hour_factor = 1.0 - abs(hour - 12) / 6
                        
                        # Calculate cloud factor (less clouds = more production)
                        cloud_factor = 1.0 - (cloud_cover / 100) * 0.8
                        
                        # Calculate temperature factor (efficiency drops at high temps)
                        temp_adjustment = max(0, temperature - 25) * 0.005
                        temp_factor = 1.0 - temp_adjustment
                        
                        # Estimate production for this hour
                        hour_production = 5.0 * hour_factor * cloud_factor * temp_factor
                        
                        day_production.append(hour_production)
                    
                    # Calculate daily total
                    daily_total = sum(day_production)
                    daily_avg = sum(day_production) / len(day_production) if day_production else 0
                    
                    production_forecast.append({
                        "date": target_date.date().isoformat(),
                        "day_name": target_date.strftime("%A"),
                        "estimated_production": round(daily_total, 2),
                        "hourly_avg": round(daily_avg, 2),
                        "expected_efficiency": round(avg_efficiency * (1 - 0.002 * (target_date.day)), 2)  # Slight degradation over time
                    })
        
        # Create the final prediction record
        engineer_prediction = {
        "datetime": datetime.now(),
            "city_id": city["id"],
            "city_name": city["name"],
            "country": city["country"],
            "daily_performance": daily_averages[-30:] if len(daily_averages) > 30 else daily_averages,  # Last 30 days
            "monthly_performance": monthly_averages,
            "yearly_performance": yearly_avg_data,
            "maintenance_recommendations": maintenance_recommendations,
            "efficiency_insights": efficiency_insights,
            "production_forecast": production_forecast,
            "summary": {
                "avg_daily_production": round(sum(d["avg_production"] for d in daily_averages) / len(daily_averages), 2) if daily_averages else 0,
                "best_production_month": max(monthly_averages, key=lambda x: x["avg_production"])["month_name"] if monthly_averages else "Unknown",
                "worst_production_month": min(monthly_averages, key=lambda x: x["avg_production"])["month_name"] if monthly_averages else "Unknown",
                "performance_category": "Excellent" if (efficiency_insights["performance_ratio"] > 80) else
                                       "Good" if (efficiency_insights["performance_ratio"] > 70) else
                                       "Average" if (efficiency_insights["performance_ratio"] > 60) else
                                       "Below Average" if (efficiency_insights["performance_ratio"] > 50) else
                                       "Poor"
            }
    }
    
    # Store in database
        # First delete any existing predictions for this city
        engineer_predictions_collection.delete_many(query)
        
        # Insert new prediction
        result = engineer_predictions_collection.insert_one(engineer_prediction)
        
        print(f"Generated engineer predictions for {city['name']}")
        print(f"  Performance category: {engineer_prediction['summary']['performance_category']}")
        print(f"  Average daily production: {engineer_prediction['summary']['avg_daily_production']} kW")
        print(f"  Best production month: {engineer_prediction['summary']['best_production_month']}")
        print(f"  Expected panel lifespan: {efficiency_insights['expected_lifespan']} years")
        
        return engineer_prediction
        
    except Exception as e:
        print(f"Error generating engineer predictions: {e}")
        return None

def generate_insurance_predictions(city_id=None, city_name=None, forecasts=None, weather_data=None):
    """Generate specialized predictions for insurance companies with enhanced risk assessment"""
    try:
        print("Generating insurance predictions...")
        
        # Determine query for finding data
        query = {}
        if city_id:
            query["city_id"] = city_id
        elif city_name:
            query["city_name"] = city_name
        
        # Get the city
        city = cities_collection.find_one({"id": city_id} if city_id else {"name": city_name})
        if not city:
            print(f"City not found for insurance predictions")
            return None
        
        # Get historical weather data from last year if not provided
        if not weather_data:
            three_years_ago = datetime.now() - timedelta(days=365*3)
            weather_data = list(
                weather_collection.find(
                    {**query, "datetime": {"$gte": three_years_ago}}
                ).sort("datetime", 1)
            )
        
        # Get forecasts if not provided
        if not forecasts:
            latest_prediction = forecast_collection.find_one(
                {**query}, sort=[("prediction_time", -1)]
            )
            
            if latest_prediction:
                prediction_time = latest_prediction["prediction_time"]
                forecasts = list(
                    forecast_collection.find(
                        {**query, "prediction_time": prediction_time}
                    ).sort("datetime", 1)
                )
        
        # Define thresholds for extreme weather
        extreme_weather_thresholds = {
            "high_temp": 35,  # °C
            "low_temp": -10,  # °C
            "high_wind": 15,  # m/s (~54 km/h)
            "heavy_rain": 30,  # mm/day
            "snow": -2,  # °C (temperature where precipitation is likely snow)
            "hail": {"temp_min": 15, "temp_max": 30, "humidity_min": 60}  # Conditions favorable for hail
        }
        
        # Analysis of extreme weather events from historical data
        extreme_events = {
            "high_temp_days": 0,
            "low_temp_days": 0,
            "high_wind_hours": 0,
            "heavy_rain_days": 0,
            "potential_snow_days": 0,
            "potential_hail_days": 0,
            "extreme_days": 0,  # Days with any extreme condition
            "days_analyzed": 0
        }
        
        # Track daily extremes
        daily_extremes = {}
        for data in weather_data:
            date_key = data["datetime"].strftime("%Y-%m-%d")
            
            if date_key not in daily_extremes:
                daily_extremes[date_key] = {
                    "date": data["datetime"].date(),
                    "max_temp": -100,
                    "min_temp": 100,
                    "max_wind": 0,
                    "total_rain": 0,
                    "has_extreme": False
                }
            
            # Update daily extremes
            daily_extremes[date_key]["max_temp"] = max(daily_extremes[date_key]["max_temp"], data["temperature"])
            daily_extremes[date_key]["min_temp"] = min(daily_extremes[date_key]["min_temp"], data["temperature"])
            daily_extremes[date_key]["max_wind"] = max(daily_extremes[date_key]["max_wind"], data["wind_speed"])
            
            if "precipitation" in data:
                daily_extremes[date_key]["total_rain"] += data["precipitation"]
            
            # Check for high wind in this hour
            if data["wind_speed"] >= extreme_weather_thresholds["high_wind"]:
                extreme_events["high_wind_hours"] += 1
            
            # Check for potential hail conditions
            if (extreme_weather_thresholds["hail"]["temp_min"] <= data["temperature"] <= extreme_weather_thresholds["hail"]["temp_max"] and
                data.get("humidity", 0) >= extreme_weather_thresholds["hail"]["humidity_min"]):
                daily_extremes[date_key]["potential_hail"] = True
        
        # Calculate statistics from daily extremes
        for date_key, extremes in daily_extremes.items():
            extreme_events["days_analyzed"] += 1
            
            # Check for high temperature days
            if extremes["max_temp"] >= extreme_weather_thresholds["high_temp"]:
                extreme_events["high_temp_days"] += 1
                extremes["has_extreme"] = True
            
            # Check for low temperature days
            if extremes["min_temp"] <= extreme_weather_thresholds["low_temp"]:
                extreme_events["low_temp_days"] += 1
                extremes["has_extreme"] = True
            
            # Check for heavy rain days
            if extremes["total_rain"] >= extreme_weather_thresholds["heavy_rain"]:
                extreme_events["heavy_rain_days"] += 1
                extremes["has_extreme"] = True
            
            # Check for potential snow days
            if extremes["min_temp"] <= extreme_weather_thresholds["snow"]:
                extreme_events["potential_snow_days"] += 1
                extremes["has_extreme"] = True
            
            # Check for potential hail days
            if extremes.get("potential_hail", False):
                extreme_events["potential_hail_days"] += 1
                extremes["has_extreme"] = True
            
            # Count total extreme days
            if extremes["has_extreme"]:
                extreme_events["extreme_days"] += 1
        
        # Calculate extreme weather probabilities
        days_in_year = 365
        extreme_probabilities = {
            "high_temp_probability": round(extreme_events["high_temp_days"] / extreme_events["days_analyzed"] * 100, 2) if extreme_events["days_analyzed"] > 0 else 0,
            "low_temp_probability": round(extreme_events["low_temp_days"] / extreme_events["days_analyzed"] * 100, 2) if extreme_events["days_analyzed"] > 0 else 0,
            "heavy_rain_probability": round(extreme_events["heavy_rain_days"] / extreme_events["days_analyzed"] * 100, 2) if extreme_events["days_analyzed"] > 0 else 0,
            "snow_probability": round(extreme_events["potential_snow_days"] / extreme_events["days_analyzed"] * 100, 2) if extreme_events["days_analyzed"] > 0 else 0,
            "hail_probability": round(extreme_events["potential_hail_days"] / extreme_events["days_analyzed"] * 100, 2) if extreme_events["days_analyzed"] > 0 else 0,
            "any_extreme_probability": round(extreme_events["extreme_days"] / extreme_events["days_analyzed"] * 100, 2) if extreme_events["days_analyzed"] > 0 else 0
        }
        
        # Calculate expected days per year for each extreme
        expected_days = {
            "high_temp_days_per_year": round(extreme_probabilities["high_temp_probability"] * days_in_year / 100, 1),
            "low_temp_days_per_year": round(extreme_probabilities["low_temp_probability"] * days_in_year / 100, 1),
            "heavy_rain_days_per_year": round(extreme_probabilities["heavy_rain_probability"] * days_in_year / 100, 1),
            "snow_days_per_year": round(extreme_probabilities["snow_probability"] * days_in_year / 100, 1),
            "hail_days_per_year": round(extreme_probabilities["hail_probability"] * days_in_year / 100, 1),
            "extreme_days_per_year": round(extreme_probabilities["any_extreme_probability"] * days_in_year / 100, 1)
        }
        
        # Analyze seasonal patterns
        seasonal_data = {
            "winter": {"months": [12, 1, 2], "extreme_days": 0, "total_days": 0},
            "spring": {"months": [3, 4, 5], "extreme_days": 0, "total_days": 0},
            "summer": {"months": [6, 7, 8], "extreme_days": 0, "total_days": 0},
            "autumn": {"months": [9, 10, 11], "extreme_days": 0, "total_days": 0}
        }
        
        # Assign extreme days to seasons
        for date_key, extremes in daily_extremes.items():
            date = datetime.strptime(date_key, "%Y-%m-%d")
            month = date.month
            
            # Determine season
            season = next((s for s, data in seasonal_data.items() if month in data["months"]), None)
            
            if season:
                seasonal_data[season]["total_days"] += 1
                if extremes["has_extreme"]:
                    seasonal_data[season]["extreme_days"] += 1
        
        # Calculate seasonal probabilities
        seasonal_probabilities = {}
        for season, data in seasonal_data.items():
            if data["total_days"] > 0:
                probability = data["extreme_days"] / data["total_days"] * 100
                seasonal_probabilities[season] = round(probability, 2)
            else:
                seasonal_probabilities[season] = 0
        
        # Determine highest risk season
        highest_risk_season = max(seasonal_probabilities.items(), key=lambda x: x[1])
        
        # Calculate estimated damage costs
        # These are simplified estimates based on typical insurance payouts
        avg_damage_costs = {
            "high_temp_damage": 500,  # €/event (e.g., AC failures, heat stress)
            "low_temp_damage": 1500,  # €/event (e.g., pipe bursts, heating failures)
            "high_wind_damage": 3000,  # €/event (e.g., roof damage, fallen trees)
            "heavy_rain_damage": 5000,  # €/event (e.g., flooding, water damage)
            "snow_damage": 2000,  # €/event (e.g., roof collapse, ice damage)
            "hail_damage": 4000   # €/event (e.g., vehicle damage, window breakage)
        }
        
        # Calculate annual expected damage
        annual_damage_estimate = (
            expected_days["high_temp_days_per_year"] * avg_damage_costs["high_temp_damage"] +
            expected_days["low_temp_days_per_year"] * avg_damage_costs["low_temp_damage"] +
            (extreme_events["high_wind_hours"] / 24 / extreme_events["days_analyzed"] * days_in_year) * avg_damage_costs["high_wind_damage"] +
            expected_days["heavy_rain_days_per_year"] * avg_damage_costs["heavy_rain_damage"] +
            expected_days["snow_days_per_year"] * avg_damage_costs["snow_damage"] +
            expected_days["hail_days_per_year"] * avg_damage_costs["hail_damage"]
        )
        
        # Generate short-term risk forecast (7 days)
        risk_forecast = []
        if forecasts:
            now = datetime.now()
            for i in range(7):
                target_date = now + timedelta(days=i)
                day_forecasts = [f for f in forecasts if f["datetime"].date() == target_date.date()]
                
                if day_forecasts:
                    # Calculate daily extremes from forecast
                    forecast_max_temp = max(f["temperature"] for f in day_forecasts)
                    forecast_min_temp = min(f["temperature"] for f in day_forecasts)
                    forecast_max_wind = max(f["wind_speed"] for f in day_forecasts)
                    forecast_precipitation = sum(f.get("precipitation", 0) for f in day_forecasts)
                    
                    # Determine risk factors
                    risk_factors = []
                    risk_level = "Low"
                    
                    if forecast_max_temp >= extreme_weather_thresholds["high_temp"]:
                        risk_factors.append("High temperature")
                        risk_level = "Medium"
                    
                    if forecast_min_temp <= extreme_weather_thresholds["low_temp"]:
                        risk_factors.append("Low temperature")
                        risk_level = "Medium"
                    
                    if forecast_max_wind >= extreme_weather_thresholds["high_wind"]:
                        risk_factors.append("High wind")
                        risk_level = "High"
                    
                    if forecast_precipitation >= extreme_weather_thresholds["heavy_rain"]:
                        risk_factors.append("Heavy rain")
                        risk_level = "High"
                    
                    if forecast_min_temp <= extreme_weather_thresholds["snow"] and forecast_precipitation > 0:
                        risk_factors.append("Potential snow")
                        risk_level = "Medium"
                    
                    # Check for hail conditions
                    has_hail_conditions = any(
                        (extreme_weather_thresholds["hail"]["temp_min"] <= f["temperature"] <= extreme_weather_thresholds["hail"]["temp_max"] and
                         f.get("humidity", 0) >= extreme_weather_thresholds["hail"]["humidity_min"] and
                         f.get("precipitation", 0) > 0)
                        for f in day_forecasts
                    )
                    
                    if has_hail_conditions:
                        risk_factors.append("Potential hail")
                        risk_level = "High"
                    
                    # Generate damage estimate for this day
                    damage_estimate = 0
                    if "High temperature" in risk_factors:
                        damage_estimate += avg_damage_costs["high_temp_damage"]
                    if "Low temperature" in risk_factors:
                        damage_estimate += avg_damage_costs["low_temp_damage"]
                    if "High wind" in risk_factors:
                        damage_estimate += avg_damage_costs["high_wind_damage"]
                    if "Heavy rain" in risk_factors:
                        damage_estimate += avg_damage_costs["heavy_rain_damage"]
                    if "Potential snow" in risk_factors:
                        damage_estimate += avg_damage_costs["snow_damage"]
                    if "Potential hail" in risk_factors:
                        damage_estimate += avg_damage_costs["hail_damage"]
                    
                    risk_forecast.append({
                        "date": target_date.date().isoformat(),
                        "day_name": target_date.strftime("%A"),
                        "risk_level": risk_level,
                        "risk_factors": risk_factors,
                        "max_temp": round(forecast_max_temp, 1),
                        "min_temp": round(forecast_min_temp, 1),
                        "max_wind": round(forecast_max_wind, 1),
                        "precipitation": round(forecast_precipitation, 1),
                        "potential_damage_estimate": round(damage_estimate, 2)
                    })
        
        # Create insurance prediction record
        insurance_prediction = {
        "datetime": datetime.now(),
            "city_id": city["id"],
            "city_name": city["name"],
            "country": city["country"],
            "extreme_event_probabilities": extreme_probabilities,
            "expected_extreme_days": expected_days,
            "seasonal_risk": {
                "winter_probability": seasonal_probabilities["winter"],
                "spring_probability": seasonal_probabilities["spring"],
                "summer_probability": seasonal_probabilities["summer"],
                "autumn_probability": seasonal_probabilities["autumn"],
                "highest_risk_season": highest_risk_season[0],
                "highest_risk_probability": highest_risk_season[1]
            },
            "damage_estimates": {
                "annual_damage_estimate": round(annual_damage_estimate, 2),
                "average_event_costs": avg_damage_costs
            },
            "risk_forecast": risk_forecast,
            "summary": {
                "risk_level": "High" if extreme_probabilities["any_extreme_probability"] > 30 else
                             "Medium" if extreme_probabilities["any_extreme_probability"] > 15 else
                             "Low",
                "primary_risks": [
                    k.replace("_probability", "") for k, v in extreme_probabilities.items()
                    if v > 5 and k != "any_extreme_probability"
                ],
                "expected_annual_extreme_days": round(expected_days["extreme_days_per_year"]),
                "recommended_coverage_level": "Premium" if annual_damage_estimate > 50000 else
                                             "Enhanced" if annual_damage_estimate > 20000 else
                                             "Standard"
            }
    }
    
    # Store in database
        # First delete any existing predictions for this city
        insurance_predictions_collection.delete_many(query)
        
        # Insert new prediction
        result = insurance_predictions_collection.insert_one(insurance_prediction)
        
        print(f"Generated insurance predictions for {city['name']}")
        print(f"  Risk level: {insurance_prediction['summary']['risk_level']}")
        print(f"  Annual extreme day expectation: {insurance_prediction['summary']['expected_annual_extreme_days']} days")
        print(f"  Estimated annual damage: €{round(annual_damage_estimate)}")
        print(f"  Recommended coverage: {insurance_prediction['summary']['recommended_coverage_level']}")
        
        return insurance_prediction
        
    except Exception as e:
        print(f"Error generating insurance predictions: {e}")
        return None

def generate_tourist_predictions(city_id=None, city_name=None, forecasts=None, weather_data=None):
    """Generate specialized predictions for tourists with enhanced features"""
    try:
        print("Generating tourist predictions...")
        
        # Determine query for finding data
        query = {}
        if city_id:
            query["city_id"] = city_id
        elif weather_data:
            query["city_id"] = weather_data.get('city_id')
        elif forecasts:
            query["city_id"] = forecasts[0].get('city_id')
        
        # Get the city
        city = cities_collection.find_one(query)
        if not city:
            print(f"City not found for tourist predictions")
            return None
        
        # Get historical weather data from last 12 months
        one_year_ago = datetime.now() - timedelta(days=365)
        weather_data = list(
            weather_collection.find(
                {**query, "datetime": {"$gte": one_year_ago}}
            ).sort("datetime", 1)
        )
        
        # Get the most recent forecast
        latest_prediction = forecast_collection.find_one(
            {**query}, sort=[("prediction_time", -1)]
        )
        if latest_prediction:
            prediction_time = latest_prediction["prediction_time"]
            forecasts = list(
                forecast_collection.find(
                    {**query, "prediction_time": prediction_time}
                ).sort("datetime", 1)
            )
        
        # Calculate monthly averages to determine seasonal patterns
        monthly_data = {}
        for month in range(1, 13):
            monthly_data[month] = {
                "temp_sum": 0,
                "temp_count": 0,
                "rain_sum": 0,
                "rain_count": 0,
                "sunshine_hours": 0,
                "sunshine_count": 0,
                "days_with_rain": 0,
                "comfort_index": 0,
                "wind_sum": 0,
                "cloud_cover_sum": 0
            }
        
        # Process historical weather data to get monthly statistics
        for data in weather_data:
            month = data["datetime"].month
            monthly_data[month]["temp_sum"] += data["temperature"]
            monthly_data[month]["temp_count"] += 1
            
            monthly_data[month]["wind_sum"] += data["wind_speed"]
            monthly_data[month]["cloud_cover_sum"] += data["cloud_cover"]
            
            if "precipitation" in data and data["precipitation"] > 0:
                monthly_data[month]["rain_sum"] += data["precipitation"]
                monthly_data[month]["rain_count"] += 1
                
                # Track days with rain (count only once per day)
                day_key = data["datetime"].strftime("%Y-%m-%d")
                monthly_data[month]["days_with_rain"] += 1
            
            # Estimate sunshine hours based on solar irradiance
            if "solar_irradiance" in data and data["solar_irradiance"] > 0:
                # If irradiance is above threshold, count as sunshine
                if data["solar_irradiance"] > 200:  # Threshold for "sunny"
                    monthly_data[month]["sunshine_hours"] += 1
                monthly_data[month]["sunshine_count"] += 1
        
        # Calculate monthly averages and find optimal periods
        months = []
        for month in range(1, 13):
            if monthly_data[month]["temp_count"] > 0:
                avg_temp = monthly_data[month]["temp_sum"] / monthly_data[month]["temp_count"]
                avg_wind = monthly_data[month]["wind_sum"] / monthly_data[month]["temp_count"]
                avg_cloud = monthly_data[month]["cloud_cover_sum"] / monthly_data[month]["temp_count"]
                
                # Calculate rainfall probability
                rain_days = monthly_data[month]["days_with_rain"]
                rain_probability = rain_days / 30 * 100  # Approximate days in a month
                
                # Calculate average rainfall when it rains
                avg_rainfall = monthly_data[month]["rain_sum"] / monthly_data[month]["rain_count"] if monthly_data[month]["rain_count"] > 0 else 0
                
                # Calculate sunshine hours 
                sunshine_hours = monthly_data[month]["sunshine_hours"]
                
                # Calculate comfort index (higher is better)
                # Ideal: ~22°C temperature, low rainfall probability, low wind, high sunshine
                temp_comfort = max(0, 100 - abs(avg_temp - 22) * 5)  # Optimal around 22°C
                rain_comfort = max(0, 100 - rain_probability)  # Less rain is better
                wind_comfort = max(0, 100 - avg_wind * 10)  # Less wind is better
                sunshine_comfort = min(100, sunshine_hours / 5)  # More sunshine is better
                
                comfort_index = (temp_comfort * 0.4 + rain_comfort * 0.2 + wind_comfort * 0.1 + sunshine_comfort * 0.3)
                
                months.append({
                    "month": month,
                    "month_name": datetime(2020, month, 1).strftime("%B"),
                    "avg_temperature": round(avg_temp, 1),
                    "rainfall_probability": round(rain_probability, 1),
                    "avg_rainfall": round(avg_rainfall, 1),
                    "estimated_sunshine_hours": round(sunshine_hours, 1),
                    "comfort_index": round(comfort_index, 1)
                })
        
        # Sort months by comfort index
        months.sort(key=lambda x: x["comfort_index"], reverse=True)
        
        optimal_periods = months[:3]  # Top 3 months
        worst_periods = months[-3:]   # Bottom 3 months
        
        # Calculate overall statistics
        avg_yearly_rainfall = sum(month["avg_rainfall"] * month["rainfall_probability"] / 100 for month in months)
        avg_yearly_sunshine = sum(month["estimated_sunshine_hours"] for month in months)
        
        # Find months with highest rainfall probability
        rainy_months = sorted(months, key=lambda x: x["rainfall_probability"], reverse=True)[:3]
        
        # Generate short-term forecast (7 days)
        short_term_forecast = []
        if forecasts:
            now = datetime.now()
            for i in range(7):
                target_date = now + timedelta(days=i)
                day_forecasts = [f for f in forecasts if f["datetime"].date() == target_date.date()]
                
                if day_forecasts:
                    # Calculate daily averages
                    avg_temp = sum(f["temperature"] for f in day_forecasts) / len(day_forecasts)
                    avg_wind = sum(f["wind_speed"] for f in day_forecasts) / len(day_forecasts)
                    has_precipitation = any(f.get("precipitation", 0) > 0 for f in day_forecasts)
                    
                    # Calculate comfort for this day
                    temp_comfort = max(0, 100 - abs(avg_temp - 22) * 5)
                    wind_comfort = max(0, 100 - avg_wind * 10)
                    rain_comfort = 0 if has_precipitation else 100
                    
                    day_comfort = (temp_comfort * 0.5 + wind_comfort * 0.2 + rain_comfort * 0.3)
                    
                    short_term_forecast.append({
                        "date": target_date.date().isoformat(),
                        "day_name": target_date.strftime("%A"),
                        "avg_temperature": round(avg_temp, 1),
                        "has_precipitation": has_precipitation,
                        "comfort_index": round(day_comfort, 1),
                        "recommendation": "Ideal for tourism" if day_comfort > 75 else
                                         "Good conditions" if day_comfort > 60 else
                                         "Acceptable conditions" if day_comfort > 40 else
                                         "Not recommended"
                    })
        
        # Create tourist prediction record
        tourism_prediction = {
        "datetime": datetime.now(),
            "city_id": city["id"],
            "city_name": city["name"],
            "country": city["country"],
            "optimal_periods": optimal_periods,
            "worst_periods": worst_periods,
            "rainfall_patterns": {
                "yearly_average": round(avg_yearly_rainfall, 1),
                "rainy_months": [m["month_name"] for m in rainy_months],
                "rainy_months_data": rainy_months
            },
            "sunshine_hours": {
                "yearly_average": round(avg_yearly_sunshine, 1),
                "monthly_data": sorted(months, key=lambda x: x["month"])
            },
            "short_term_forecast": short_term_forecast,
            "general_recommendation": "Optimal visiting periods: " + ", ".join([m["month_name"] for m in optimal_periods])
    }
    
    # Store in database
        # First delete any existing predictions for this city
        db["tourist_predictions"].delete_many(query)
        
        # Insert new prediction
        result = db["tourist_predictions"].insert_one(tourism_prediction)
        
        print(f"Generated tourist predictions for {city['name']}")
        print(f"  Optimal visiting periods: {', '.join([m['month_name'] for m in optimal_periods])}")
        print(f"  Yearly sunshine hours (est.): {round(avg_yearly_sunshine, 1)}")
        print(f"  Yearly average rainfall: {round(avg_yearly_rainfall, 1)} mm")
        
        return tourism_prediction
        
    except Exception as e:
        print(f"Error generating tourist predictions: {e}")
        return None

def process_all_cities():
    """Process data for all cities to generate forecasts and specialized predictions"""
    cities = get_cities()
    results = {}
    
    for city in cities:
        city_id = city["id"]
        city_name = city["name"]
        print(f"Processing data for {city_name}...")
        
        # Get recent weather and solar data for this city
        one_year_ago = datetime.now() - timedelta(days=365)
        
        weather_data = list(
            weather_collection.find(
                {"city_id": city_id, "datetime": {"$gte": one_year_ago}}
            ).sort("datetime", 1)
        )
        
        solar_data = list(
            solar_collection.find(
                {"city_id": city_id, "datetime": {"$gte": one_year_ago}}
            ).sort("datetime", 1)
        )
        
        # Generate forecasts for different timeframes
        day_forecasts = generate_forecast(city_id=city_id, timeframe="day")
        month_forecasts = generate_forecast(city_id=city_id, timeframe="month")
        
        # Get the latest forecasts for specialized predictions
        latest_forecasts = list(
            forecast_collection.find(
                {"city_id": city_id, "forecast_type": "day"}
            ).sort("datetime", 1)
        )
        
        # Generate specialized predictions
        engineer_predictions = generate_engineer_predictions(
            city_id=city_id, 
            forecasts=latest_forecasts,
            weather_data=weather_data,
            solar_data=solar_data
        )
        
        insurance_predictions = generate_insurance_predictions(
            city_id=city_id,
            forecasts=latest_forecasts,
            weather_data=weather_data
        )
        
        tourist_predictions = generate_tourist_predictions(
            city_id=city_id,
            city_name=city_name,
            forecasts=latest_forecasts,
            weather_data=weather_data
        )
        
        # Calculate historical accuracy
        accuracy_metrics = generate_historical_accuracy(city_id=city_id)
        
        results[city_name] = {
            "forecasts_generated": day_forecasts > 0 and month_forecasts > 0,
            "engineer_predictions": engineer_predictions is not None,
            "insurance_predictions": insurance_predictions is not None,
            "tourist_predictions": tourist_predictions is not None,
            "accuracy_calculated": len(accuracy_metrics) > 0 if isinstance(accuracy_metrics, list) else False
        }
    
    return results

def main():
    """Main function to run the forecast processor"""
    print("Forecast processor starting...")
    
    while True:
        print("\n===== Processing forecasts for all cities =====")
        results = process_all_cities()
        
        for city, result in results.items():
            print(f"[✓] {city}:")
            for key, value in result.items():
                if isinstance(value, bool):
                    print(f"  {key}: {'Yes' if value else 'No'}")
                else:
                    print(f"  {key}: {value}")
        
        process_interval = 60  # 1 minute for testing
        print(f"Waiting {process_interval} seconds before next processing...")
        time.sleep(process_interval)

if __name__ == "__main__":
    main()


