import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Lazy-load processor so the server binds to PORT before heavy ML training
processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data and train models AFTER the server starts listening."""
    global processor
    from data_processor import DataProcessor
    processor = DataProcessor()
    print("Application startup complete.")
    yield
    print("Application shutdown.")

app = FastAPI(title="AQI Research Lab API", lifespan=lifespan)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint acts as entry point for index.html
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# Define request model for predictions
class WeatherInput(BaseModel):
    t2m: float  # Temperature (K)
    d2m: float  # Dewpoint Temp (K)
    sp: float   # Surface Pressure (Pa)
    blh: float  # Boundary Layer Height (m)
    wind_speed: float
    city: str = 'all' # Optional city for customized prediction

@app.get("/api/summary/{city}")
def get_summary(city: str):
    """Returns top-level stats (Avg AQI, etc.) filtered by optional city."""
    stats = processor.get_summary_stats(city)
    if "error" in stats:
        raise HTTPException(status_code=500, detail=stats["error"])
    return stats

@app.get("/api/cities")
def get_cities():
    """Returns list of available cities."""
    return {"cities": processor.get_cities()}

@app.get("/api/timeseries/{city}")
def get_timeseries(city: str):
    """Returns daily AQI and meteorological data for Chart.js."""
    data = processor.get_timeseries(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/api/analytics/{city}/monthly")
def get_analytics_monthly(city: str):
    data = processor.get_monthly_seasonality(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/api/analytics/{city}/distribution")
def get_analytics_distribution(city: str):
    data = processor.get_aqi_distribution(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/api/analytics/{city}/correlation")
def get_analytics_correlation(city: str):
    data = processor.get_correlation(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.post("/api/predict")
def predict_aqi(input_data: WeatherInput):
    """A POST endpoint that takes weather variables and returns an AQI prediction."""
    try:
        prediction = processor.predict_aqi(
            t2m=input_data.t2m,
            d2m=input_data.d2m,
            sp=input_data.sp,
            blh=input_data.blh,
            wind_speed=input_data.wind_speed,
            city=input_data.city
        )
        return {"predicted_aqi": prediction, "model_used": input_data.city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files *after* explicit routes using prefix /static (or just mount the directory for relative imports)
# It's better to structure standard static mounting this way:
app.mount("/", StaticFiles(directory="static", html=True), name="static")
