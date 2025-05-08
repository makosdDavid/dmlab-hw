import React, { useEffect, useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import { fetchWeatherData, fetchForecastData } from '../../services/api';
import './WeatherCard.css';

const WeatherCard = () => {
  const { selectedCity } = useAppContext();
  const [currentWeather, setCurrentWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedCity) return;

      try {
        setLoading(true);
        setError(null);

        // Fetch current weather
        const weatherData = await fetchWeatherData(selectedCity.id, 1);
        if (weatherData && weatherData.length > 0) {
          setCurrentWeather(weatherData[0]);
        }

        // Fetch 7-day forecast
        const forecastData = await fetchForecastData(selectedCity.id, 24 * 7);
        
        // Group forecast by day
        const groupedForecast = groupForecastByDay(forecastData);
        setForecast(groupedForecast);
      } catch (err) {
        console.error('Error fetching weather data:', err);
        setError('Failed to load weather data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedCity]);

  // Helper function to group forecast data by day
  const groupForecastByDay = (forecastData) => {
    if (!forecastData || !Array.isArray(forecastData) || forecastData.length === 0) {
      return [];
    }
    
    const grouped = {};
    
    forecastData.forEach(item => {
      // Handle different date formats from the API
      const date = new Date(item.datetime || item.date);
      const dateKey = date.toISOString().split('T')[0];
      
      if (!grouped[dateKey]) {
        grouped[dateKey] = {
          date,
          dayName: getDayName(date),
          temperatures: [],
          conditions: [],
          precipitation: 0
        };
      }
      
      // Handle different property names from different endpoints
      const temp = item.temperature || item.temp;
      if (temp !== undefined) grouped[dateKey].temperatures.push(temp);
      
      const description = item.description || item.weather_description || 'Unknown';
      if (description) grouped[dateKey].conditions.push(description);
      
      const precipitation = item.precipitation || item.rain || 0;
      if (precipitation) {
        grouped[dateKey].precipitation += precipitation;
      }
    });
    
    // Calculate min, max temperature and most frequent condition for each day
    return Object.values(grouped).map(day => {
      // Make sure we have temperature data
      if (day.temperatures.length === 0) {
        day.temperatures = [20]; // Default fallback value
      }
      
      const minTemp = Math.min(...day.temperatures);
      const maxTemp = Math.max(...day.temperatures);
      const avgTemp = day.temperatures.reduce((a, b) => a + b, 0) / day.temperatures.length;
      
      // Find most frequent condition
      const conditionCounts = {};
      day.conditions.forEach(condition => {
        conditionCounts[condition] = (conditionCounts[condition] || 0) + 1;
      });
      
      const mainCondition = day.conditions.length > 0 
        ? Object.entries(conditionCounts).sort((a, b) => b[1] - a[1])[0][0]
        : 'Unknown';
      
      return {
        date: day.date,
        dayName: day.dayName,
        minTemp: Math.round(minTemp),
        maxTemp: Math.round(maxTemp),
        avgTemp: Math.round(avgTemp),
        condition: mainCondition,
        precipitation: Math.round(day.precipitation * 10) / 10
      };
    }).slice(0, 7); // Limit to 7 days
  };

  // Helper function to get day name
  const getDayName = (date) => {
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    }
  };

  // Helper to get weather icon based on condition
  const getWeatherIcon = (condition) => {
    const conditionLower = condition ? condition.toLowerCase() : '';
    
    if (conditionLower.includes('clear') || conditionLower.includes('sun')) {
      return '☀️';
    } else if (conditionLower.includes('cloud')) {
      return '☁️';
    } else if (conditionLower.includes('rain') || conditionLower.includes('drizzle')) {
      return '🌧️';
    } else if (conditionLower.includes('snow')) {
      return '❄️';
    } else if (conditionLower.includes('thunder') || conditionLower.includes('storm')) {
      return '⛈️';
    } else if (conditionLower.includes('fog') || conditionLower.includes('mist')) {
      return '🌫️';
    } else {
      return '🌤️';
    }
  };

  if (loading) {
    return (
      <div className="weather-card loading">
        <div className="loading-indicator">Loading weather data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-card error">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!currentWeather) {
    return (
      <div className="weather-card no-data">
        <div className="no-data-message">No weather data available</div>
      </div>
    );
  }

  return (
    <div className="weather-card">
      <div className="current-weather">
        <div className="weather-header">
          <h2>Current Weather</h2>
          <div className="weather-location">{selectedCity.name}, {selectedCity.country}</div>
          <div className="weather-time">
            {new Date(currentWeather.datetime).toLocaleString()}
          </div>
        </div>
        
        <div className="weather-content">
          <div className="weather-icon-temp">
            <div className="weather-icon">{getWeatherIcon(currentWeather.description)}</div>
            <div className="weather-temp">{Math.round(currentWeather.temperature)}°C</div>
          </div>
          
          <div className="weather-details">
            <div className="weather-condition">{currentWeather.description}</div>
            <div className="weather-metrics">
              <div className="metric">
                <span className="metric-label">Humidity:</span>
                <span className="metric-value">{currentWeather.humidity}%</span>
              </div>
              <div className="metric">
                <span className="metric-label">Wind:</span>
                <span className="metric-value">{currentWeather.wind_speed} m/s</span>
              </div>
              {currentWeather.precipitation > 0 && (
                <div className="metric">
                  <span className="metric-label">Precipitation:</span>
                  <span className="metric-value">{currentWeather.precipitation} mm</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="forecast">
        <h3>Weekly Forecast</h3>
        <div className="forecast-days">
          {forecast.map((day, index) => (
            <div key={index} className="forecast-day">
              <div className="day-name">{day.dayName}</div>
              <div className="day-icon">{getWeatherIcon(day.condition)}</div>
              <div className="day-temp">
                <span className="max-temp">{day.maxTemp}°</span>
                <span className="min-temp">{day.minTemp}°</span>
              </div>
              {day.precipitation > 0 && (
                <div className="day-precip">{day.precipitation} mm</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WeatherCard; 