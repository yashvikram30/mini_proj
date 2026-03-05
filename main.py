import os
import threading
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Background initialization ──────────────────────────────────────
# The server MUST bind to $PORT instantly. Heavy data loading and
# ML model training runs in a background thread so Railway's health
# check passes immediately.

processor = None
_init_error = None

def _init_processor():
    global processor, _init_error
    try:
        from data_processor import DataProcessor
        processor = DataProcessor()
        print("✅ Processor ready — all models trained.")
    except Exception as e:
        _init_error = str(e)
        print(f"❌ Processor init failed: {e}")

threading.Thread(target=_init_processor, daemon=True).start()

# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(title="AQI Research Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Diagnostic endpoint (shows what's happening on Railway) ─────────
@app.get("/health")
def health():
    import glob
    cwd = os.getcwd()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_name = "aqi_era5_daily_2015_2019_clean.csv"
    csv_in_cwd = os.path.exists(os.path.join(cwd, csv_name))
    csv_in_script_dir = os.path.exists(os.path.join(script_dir, csv_name))
    all_files = glob.glob(os.path.join(script_dir, "*"))

    return {
        "status": "ok" if processor else ("error" if _init_error else "loading"),
        "init_error": _init_error,
        "processor_ready": processor is not None,
        "data_loaded": processor.df is not None if processor else False,
        "data_rows": len(processor.df) if processor and processor.df is not None else 0,
        "data_load_error": getattr(processor, '_load_error', None) if processor else None,
        "cwd": cwd,
        "script_dir": script_dir,
        "csv_in_cwd": csv_in_cwd,
        "csv_in_script_dir": csv_in_script_dir,
    }

# ── Root ────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# ── Models ──────────────────────────────────────────────────────────
class WeatherInput(BaseModel):
    t2m: float
    d2m: float
    sp: float
    blh: float
    wind_speed: float
    city: str = "all"

# ── Helper: guard against requests before processor is ready ───────
def _require_processor():
    if _init_error:
        raise HTTPException(status_code=500, detail=f"Startup error: {_init_error}")
    if processor is None:
        raise HTTPException(status_code=503, detail="Server is still loading data. Please retry in a few seconds.")

# ── API Endpoints ───────────────────────────────────────────────────
@app.get("/api/summary/{city}")
def get_summary(city: str):
    _require_processor()
    stats = processor.get_summary_stats(city)
    if "error" in stats:
        raise HTTPException(status_code=500, detail=stats["error"])
    return stats

@app.get("/api/cities")
def get_cities():
    _require_processor()
    return {"cities": processor.get_cities()}

@app.get("/api/timeseries/{city}")
def get_timeseries(city: str):
    _require_processor()
    data = processor.get_timeseries(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/api/analytics/{city}/monthly")
def get_analytics_monthly(city: str):
    _require_processor()
    data = processor.get_monthly_seasonality(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/api/analytics/{city}/distribution")
def get_analytics_distribution(city: str):
    _require_processor()
    data = processor.get_aqi_distribution(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/api/analytics/{city}/correlation")
def get_analytics_correlation(city: str):
    _require_processor()
    data = processor.get_correlation(city)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.post("/api/predict")
def predict_aqi(input_data: WeatherInput):
    _require_processor()
    try:
        prediction = processor.predict_aqi(
            t2m=input_data.t2m,
            d2m=input_data.d2m,
            sp=input_data.sp,
            blh=input_data.blh,
            wind_speed=input_data.wind_speed,
            city=input_data.city,
        )
        return {"predicted_aqi": prediction, "model_used": input_data.city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Static files (must be LAST) ────────────────────────────────────
app.mount("/", StaticFiles(directory="static", html=True), name="static")
