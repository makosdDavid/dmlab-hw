# Energy Consumption Forecast Project

This project provides a full-stack application for forecasting energy consumption and monitoring solar panel production. It includes a FastAPI backend with MongoDB integration and an Angular frontend for data visualization.

## Project Structure

```
efp/
├── server/                 # Backend code
│   ├── api/                # FastAPI server
│   ├── data_collector/     # Data collection scripts
│   └── data_processor/     # Data processing and forecasting
├── ui/                     # Angular frontend
│   ├── src/                # Angular source code
│   └── ...                 # Angular configuration
├── .env                    # Environment variables
└── requirements.txt        # Python dependencies
```

## Setup

### Backend Setup

1. **MongoDB Setup:**
   - Create a MongoDB Atlas account or use a local MongoDB instance
   - Get your connection string from MongoDB Atlas
   - Update the `.env` file with your MongoDB connection string and password

2. **Environment Variables:**
   Create a `.env` file in the project root with the following variables:
   ```
   MONGO_URI=mongodb+srv://makosdaviddev:<db_password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority
   MONGO_DB_PASSWORD=your_actual_mongodb_atlas_password
   ```

3. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. **Install Node.js Dependencies:**
   ```bash
   cd ui
   npm install
   ```

## Running the Application

### Run the Backend

1. **Start the API Server:**
   ```bash
   cd server/api
   python server.py
   ```

2. **Generate Demo Data:**
   ```bash
   cd server/data_processor
   python processor.py
   ```

### Run the Frontend

1. **Start the Angular Development Server:**
   ```bash
   cd ui
   ng serve
   ```

2. **View the Application:**
   Open a browser and navigate to `http://localhost:4200/`

## API Endpoints

- `GET /api/health` - API and database health check
- `GET /api/weather` - Get recent weather data
- `GET /api/solar` - Get recent solar panel data
- `GET /api/forecast` - Get energy consumption forecasts
- `POST /api/process` - Trigger data processing and forecast generation

## Features

- Real-time weather data display
- Solar panel production monitoring
- Energy consumption forecasting
- Interactive data visualization
- Responsive dashboard

## Technologies Used

- **Backend:**
  - Python
  - FastAPI
  - MongoDB
  - PyMongo

- **Frontend:**
  - Angular 17
  - TypeScript
  - Chart.js
  - Angular Material

## Development

### Adding New Features

1. **Backend:**
   - Add new endpoints in `server/api/server.py`
   - Add data processing logic in `server/data_processor/processor.py`

2. **Frontend:**
   - Add new components in `ui/src/app/components/`
   - Update the dashboard in `ui/src/app/components/dashboard/`
   - Add API service methods in `ui/src/app/services/api.service.ts`

