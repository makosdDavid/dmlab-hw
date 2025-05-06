# Energy Forecast Project (EFP)

A microservice-based application for forecasting energy consumption based on weather data and solar panel production.

## Components

- Data Collector: Fetches weather and solar panel data
- Data Processor: Processes data and creates forecasts
- REST API: Serves data to frontend applications
- Angular Frontend: Dashboard for visualizing forecasts

## Technology Choices

### API Framework: Flask vs FastAPI

Originally, we planned to use FastAPI for the REST API component due to its automatic documentation, type validation, and async capabilities. However, we encountered compatibility issues with Python 3.13:

- FastAPI newer versions (0.109.0+) depend on Pydantic 2.x, which requires Rust compilation
- FastAPI older versions (0.95.x) have issues with Python 3.13's typing system implementation
- The specific error encountered was: `TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'`

As a result, we switched to Flask 2.3.3, which:
- Works well with Python 3.13 without requiring Rust compilation
- Provides sufficient functionality for our REST API needs
- Has mature middleware support through Flask-CORS and other extensions
- Is easier to set up and configure in environments without development tools

This choice ensures better compatibility across different development environments while still providing all the necessary functionality for the API.

## Setup Instructions

1. Clone the repository
2. Copy .env.example to .env and fill in your API keys
3. Run with Docker Compose: `docker-compose up --build`
4. Access the dashboard at http://localhost:4200
5. Access the API at http://localhost:8000

