# Air Quality Research Lab

An ultra-modern, decoupled Python web application for analyzing Air Quality (AQI) and Meteorological (ERA5) data. Built with an "Apple-style" minimalist aesthetic.

## Features
- **Data Engine**: Automated cleaning, missing value interpolation, and feature engineering.
- **Advanced Analytics**: Real-time aggregated KPIs, monthly seasonality charting, health category distributions, and meteorological correlations.
- **City-Level Predictive AI**: Dynamically trains 5 distinct RandomForestRegressor models on startup (Global + 4 specific cities) to accurately forecast AQI based on deeply localized weather patterns.
- **Pure Minimalist Frontend**: A completely bespoke Vanilla HTML/CSS/JS frontend utilizing Chart.js, CSS Grids, and Feather icons for an ultra-fast, lightweight user interface without the constraints of a UI framework.
- **FastAPI Backend**: High-performance REST API handling the machine learning inference and data aggregation.

## Architecture
- `main.py`: The FastAPI application server and API endpoints (`/api/summary`, `/api/timeseries`, `/api/predict`, `/api/analytics`).
- `data_processor.py`: The core engine for loading the dataset, calculating analytics, and housing the machine learning pipeline.
- `static/`: The Vanilla frontend (HTML, CSS, JS).
  - `index.html` & `script.js`: The primary dashboard with timeseries tracking and the AI predictor form.
  - `analytics.html` & `analytics.js`: The advanced insights dashboard.
  - `style.css`: The bespoke monochrome design system.

## Local Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Data Requirements**:
   Ensure `aqi_era5_daily_2015_2019_clean.csv` is present in the root directory.

3. **Run the Application**:
   ```bash
   python3 -m uvicorn main:app --reload
   ```
   Navigate to `http://localhost:8000`.

## Deployment Options

Since this is a decoupled FastAPI application serving static files, deployment is extremely straightforward.

### Option A: Render (Easiest)
This repository includes a `render.yaml` Blueprint.
1. Push your code to a GitHub repository.
2. Sign into [Render.com](https://render.com) and create a new **Blueprint Instance**.
3. Point it to your repository. Render will automatically detect the Python environment, install the `requirements.txt`, and start the Uvicorn server.

### Option B: Docker
This repository includes a `Dockerfile`.
1. Build the image:
   ```bash
   docker build -t aqi-research-lab .
   ```
2. Run the container:
   ```bash
   docker run -d -p 8000:8000 aqi-research-lab
   ```

### Option C: Railway / Heroku
FastAPI integrates natively with standard PaaS providers. Simply link your GitHub repo and configure the start command to be: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
