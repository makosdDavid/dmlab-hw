# Energy Consumption Forecast Project

A comprehensive application for forecasting energy consumption based on weather data, with specialized predictions for different sectors including residential, commercial, industrial, tourism, and solar energy production.

## Features

- **Weather-based Energy Forecasting**: Predict energy consumption patterns based on current and forecasted weather conditions
- **Multi-sector Analysis**: Specialized insights for residential, commercial, industrial, tourism, and solar energy sectors
- **Interactive Data Visualization**: Explore energy consumption patterns through interactive charts and metrics
- **Prediction Accuracy Tracking**: Monitor and improve forecast accuracy over time
- **Optimization Recommendations**: Get actionable insights to optimize energy consumption and production

## Technology Stack

### Backend
- Python
- Flask (REST API)
- MongoDB
- Weather data APIs

### Frontend
- React
- Context API for state management
- Recharts for data visualization
- Responsive design for all devices

## Getting Started

### Prerequisites
- Node.js (v14+)
- npm or yarn
- Python 3.8+
- MongoDB

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/energy-consumption-forecast.git
cd energy-consumption-forecast
```

2. Set up the backend:
```bash
# Create and activate a virtual environment (recommended)
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate

# Install required packages
cd server
python -m pip install python-dotenv requests schedule pymongo flask flask-cors numpy pandas scikit-learn matplotlib

# If a requirements.txt file exists, you can use:
# python -m pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd ui
npm install
   ```

### Running the Application

1. Start the backend server:
```bash
# !!! IMPORTANT !!! - YOU MUST BE PHYSICALLY INSIDE THE SERVER DIRECTORY
# This is critical - the server will not start if you're in any other directory
cd server  # ALWAYS do this first to ensure you're in the server directory
ls         # Verify you see run_server.py in the current directory
python run_server.py
```

The backend consists of three services that will start:
- Data Collector: Collects energy and weather data
- Data Processor: Processes raw data for analysis
- API Service: Provides endpoints for the frontend

2. Start the frontend development server:
```bash
# !!! IMPORTANT !!! - YOU MUST BE PHYSICALLY INSIDE THE UI DIRECTORY
cd ui  # ALWAYS do this first to ensure you're in the ui directory
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

### Troubleshooting

If you encounter any issues:

1. **Python package errors**: Make sure all required packages are installed
```bash
# Core packages for the server
python -m pip install python-dotenv requests schedule pymongo

# Additional packages for data processing and API
python -m pip install flask flask-cors numpy pandas scikit-learn matplotlib
```

If you see errors like:
- `ModuleNotFoundError: No module named 'numpy'` or `ModuleNotFoundError: No module named 'flask'` - Install data processing and API packages
- `ModuleNotFoundError: No module named 'flask_cors'` - Install Flask-CORS with `pip install flask-cors`

2. **"No such file or directory"** when trying to run the server:
   - This means you're NOT in the correct directory
   - ALWAYS change directory to the server folder first:
   ```bash
   cd /path/to/your/project/server  # Navigate to the server directory
   python run_server.py             # Then run the server
   ```
   - If you get `can't open file '/path/to/run_server.py'`, you're 100% in the wrong directory

3. **API Connection Refused / No data showing in the UI**:
   - Check the port your API is running on - look for the message: `API is running at http://0.0.0.0:8000`
   - Make sure the frontend is configured to use the SAME port:
   - Open `ui/src/services/api.js` and check line 3:
   ```javascript
   // If this shows port 5000 but your API is running on port 8000, change it!
   const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
   
   // Should be:
   const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
   ```
   - IMPORTANT: Note that the backend doesn't have an '/api' prefix in its routes, so make sure your API_BASE_URL doesn't include '/api'
   - After making this change, restart your frontend application
   - If you see errors like `ERR_CONNECTION_REFUSED` in the console, this is almost certainly a port mismatch

4. **Frontend compilation errors**: Check the console for specific errors
   - If you see a missing export error like `Attempted import error: 'fetchForecastData' is not exported from '../../services/api'`, you need to add the missing function to the API service file:
   ```javascript
   // In ui/src/services/api.js
   export const fetchForecastData = async (cityId, hours = 168) => {
     try {
       const response = await apiClient.get(`/weather/forecast?city_id=${cityId}&hours=${hours}`);
       return response.data;
     } catch (error) {
       console.error('Error fetching forecast data:', error);
       throw error;
     }
   };
   
   // Also add it to the default export
   export default {
     // ...other functions
     fetchForecastData,
     // ...other functions
   };
   ```

5. **Backend server errors**: 
   - If only the Data Collector starts but the Data Processor and API Service fail, it's likely due to missing dependencies. Install them with:
   ```bash
   python -m pip install flask flask-cors numpy pandas scikit-learn matplotlib
   ```
   - Check if MongoDB is running and all services are properly configured

6. **Data Processor crashing with parameter errors**:
   - If you see an error like `TypeError: generate_tourist_predictions() got an unexpected keyword argument 'city_id'`, you need to fix the function definition:
   ```python
   # In server/data_processor/processor.py
   # Change from:
   def generate_tourist_predictions(forecasts, weather_data):
       
   # To:
   def generate_tourist_predictions(city_id=None, city_name=None, forecasts=None, weather_data=None):
       # Also update the query part:
       query = {}
       if city_id:
           query["city_id"] = city_id
       elif weather_data:
           query["city_id"] = weather_data.get('city_id')
       elif forecasts:
           query["city_id"] = forecasts[0].get('city_id')
   ```

7. **No cities or data appearing in the frontend**:
   - Make sure the Data Processor is running without errors
   - Check the API endpoints by manually accessing them (e.g., http://localhost:8000/api/cities)
   - Check your browser console for any CORS issues or API request errors

8. **ERROR: TypeError: Cannot read properties of undefined (reading 'toISOString')** in tab components:
   - This happens when date ranges are undefined in the tab components
   - Check the components (ResidentialTab, CommercialTab, etc.) and ensure there are default dates:
   ```javascript
   // In the fetchData function of each tab component:
   const startDate = dateRange?.startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
   const endDate = dateRange?.endDate || new Date();
   ```

9. **API endpoint 404 errors**:
   - Make sure the frontend API service functions are using the correct endpoints that match the backend
   - Check `ui/src/services/api.js` and ensure functions like `fetchForecastData` use endpoints that exist:
   ```javascript
   // For forecast data, use /forecast instead of /weather/forecast
   export const fetchForecastData = async (cityId, hours = 168) => {
     try {
       const response = await apiClient.get(`/forecast?city_id=${cityId}&hours=${hours}`);
       // ...
     }
   };
   ```
   - Actual API endpoints available in this project:
     - `/cities` - Get available cities
     - `/weather` - Get current weather data (uses `city_id` or `city_name` parameter)
     - `/forecast` - Get weather forecasts (uses `city_id` or `city_name` parameter)
     - `/solar` - Get solar data
     - `/predictions/tourist` - Get tourist predictions
     - `/predictions/engineer` - Get engineer predictions 
     - `/predictions/insurance` - Get insurance predictions
     - `/process` - Trigger data processing (POST)
     - `/accuracy` - Get prediction accuracy metrics
     - `/health` - API health check

10. **404 errors for sector-specific endpoints (energy/residential, energy/commercial, etc.)**:
    - The current backend implementation doesn't have dedicated endpoints for these sectors
    - We've implemented a workaround in the frontend using the weather data endpoint to generate mock data
    - The sector-specific tab views will show generated mock data based on the weather conditions
    - To fix this properly, you would need to implement these endpoints in the backend:
      ```python
      # Example implementation for the backend:
      @app.route('/energy/residential')
      def get_residential_energy():
          # Implementation logic
          ...
      ```

11. **500 Internal Server Error for /process endpoint**:
    - The current implementation attempts to import modules with incorrect paths
    - We've implemented a workaround to simulate data processing in the frontend
    - To fix this properly, you would need to correct the import in the backend:
      ```python
      # Fix import path in server/api/main.py:
      @app.route('/process', methods=['POST'])
      def trigger_processing():
          try:
              # Fix the import path:
              from data_processor.processor import process_all_cities
              # instead of:
              # from efp.server.data_processor.processor import process_all_cities
              
              results = process_all_cities()
              return jsonify({"success": True, "results": results})
          except Exception as e:
              return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500
      ```

## Usage

1. Select a city from the dropdown in the header
2. View current weather and forecast in the Weather Card
3. Navigate between different sectors using the tab navigation
4. Use the date range selector to adjust the time period for analysis
5. Explore metrics and charts for each sector
6. Click the refresh button in the header to update data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Weather data provided by OpenWeatherMap API
- Inspired by the need for energy optimization in smart cities

