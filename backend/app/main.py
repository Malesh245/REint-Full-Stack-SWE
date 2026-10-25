"""
WindSight - UK Wind Power Forecast Analytics Platform
FastAPI Backend Server

Provides REST API endpoints for:
- Wind generation actuals (from Elexon FUELHH dataset)
- Wind generation forecasts (from Elexon WINDFOR dataset)
- Forecast accuracy analytics and error metrics
- Comparison timeseries data for visualization
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.elexon_client import (
    fetch_wind_actuals,
    fetch_wind_forecasts,
    close_http_client,
)
from app.services.analytics import (
    process_actuals,
    process_forecasts,
    get_day_ahead_forecasts,
    compute_accuracy_metrics,
    build_comparison_timeseries,
    build_error_distribution,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# In-memory cache for API responses
_cache: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("WindSight backend starting up...")
    yield
    logger.info("WindSight backend shutting down...")
    await close_http_client()


app = FastAPI(
    title="WindSight API",
    description="UK Wind Power Forecast Analytics Platform - Powered by Elexon BMRS",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from prefix and kwargs."""
    parts = [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return f"{prefix}:{'|'.join(parts)}"


@app.get("/")
@app.get("/api")
@app.get("/health")
@app.get("/api/health")
async def root():
    """Health check endpoint."""
    return {
        "service": "WindSight API",
        "status": "healthy",
        "version": "1.0.0",
        "data_scope": f"{settings.DATA_START_DATE} to {settings.DATA_END_DATE}",
    }


@app.get("/api/actuals")
@app.get("/actuals")
async def get_actuals(
    date_from: str = Query(
        default=None,
        description="Start date (YYYY-MM-DD). Defaults to 2026-01-01",
    ),
    date_to: str = Query(
        default=None,
        description="End date (YYYY-MM-DD). Defaults to 2026-01-31",
    ),
):
    """
    Get actual wind generation data for the specified date range.
    Returns hourly aggregated MW values from the FUELHH dataset.
    """
    date_from = date_from or settings.DATA_START_DATE
    date_to = date_to or settings.DATA_END_DATE
    
    cache_key = _cache_key("actuals", date_from=date_from, date_to=date_to)
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        raw_data = await fetch_wind_actuals(date_from, date_to)
        df = process_actuals(raw_data)
        
        result = {
            "data": df.to_dict(orient="records") if not df.empty else [],
            "meta": {
                "date_from": date_from,
                "date_to": date_to,
                "n_records": len(df),
                "source": "Elexon BMRS FUELHH (WIND)",
                "resolution": "hourly (aggregated from 30-min)",
            },
        }
        
        # Convert timestamps to ISO strings
        for record in result["data"]:
            if "timestamp" in record:
                record["timestamp"] = record["timestamp"].isoformat()
        
        _cache[cache_key] = result
        return result
        
    except Exception as e:
        logger.error(f"Error fetching actuals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecasts")
@app.get("/forecasts")
async def get_forecasts(
    date_from: str = Query(
        default=None,
        description="Start publish date (YYYY-MM-DD). Defaults to 2026-01-01",
    ),
    date_to: str = Query(
        default=None,
        description="End publish date (YYYY-MM-DD). Defaults to 2026-01-31",
    ),
):
    """
    Get wind generation forecast data for the specified date range.
    Returns all forecast vintages from the WINDFOR dataset.
    """
    date_from = date_from or settings.DATA_START_DATE
    date_to = date_to or settings.DATA_END_DATE
    
    # Fetch WINDFOR starting 2 days prior so D-1 day-ahead forecasts exist for early dates
    start_dt = datetime.strptime(date_from, "%Y-%m-%d")
    publish_from = (start_dt - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
    publish_to = f"{date_to}T23:59:59Z"
    
    cache_key = _cache_key("forecasts", date_from=date_from, date_to=date_to)
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        raw_data = await fetch_wind_forecasts(publish_from, publish_to)
        df = process_forecasts(raw_data)
        
        # Get day-ahead forecasts specifically
        day_ahead_df = get_day_ahead_forecasts(df)
        
        # Filter to requested delivery date range
        import pandas as pd
        start_utc = pd.to_datetime(date_from, utc=True)
        end_utc = pd.to_datetime(date_to, utc=True) + pd.Timedelta(days=1)
        
        if not df.empty:
            df = df[(df["timestamp"] >= start_utc) & (df["timestamp"] < end_utc)]
        if not day_ahead_df.empty:
            day_ahead_df = day_ahead_df[(day_ahead_df["timestamp"] >= start_utc) & (day_ahead_df["timestamp"] < end_utc)]
        
        # Convert timestamps to strings
        forecast_records = []
        for _, row in df.iterrows():
            forecast_records.append({
                "timestamp": row["timestamp"].isoformat(),
                "forecast_mw": row["forecast_mw"],
                "publish_time": row["publish_time"].isoformat(),
            })
        
        day_ahead_records = []
        for _, row in day_ahead_df.iterrows():
            day_ahead_records.append({
                "timestamp": row["timestamp"].isoformat(),
                "forecast_mw": row["forecast_mw"],
                "publish_time": row["publish_time"].isoformat(),
                "lead_hours": round(row["lead_hours"], 1),
            })
        
        result = {
            "all_forecasts": forecast_records,
            "day_ahead": day_ahead_records,
            "meta": {
                "date_from": date_from,
                "date_to": date_to,
                "n_all_forecasts": len(forecast_records),
                "n_day_ahead": len(day_ahead_records),
                "source": "Elexon BMRS WINDFOR",
                "resolution": "hourly",
                "publish_times_per_day": "~8 (03:30, 05:30, 08:30, 10:30, 12:30, 16:30, 19:30, 23:30 UTC)",
            },
        }
        
        _cache[cache_key] = result
        return result
        
    except Exception as e:
        logger.error(f"Error fetching forecasts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comparison")
@app.get("/comparison")
async def get_comparison(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
):
    """
    Get merged actuals vs day-ahead forecast comparison timeseries.
    Ideal for line chart visualization showing forecast accuracy over time.
    """
    date_from = date_from or settings.DATA_START_DATE
    date_to = date_to or settings.DATA_END_DATE
    
    cache_key = _cache_key("comparison", date_from=date_from, date_to=date_to)
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # Fetch both datasets
        actuals_raw = await fetch_wind_actuals(date_from, date_to)
        
        start_dt = datetime.strptime(date_from, "%Y-%m-%d")
        publish_from = (start_dt - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
        publish_to = f"{date_to}T23:59:59Z"
        forecasts_raw = await fetch_wind_forecasts(publish_from, publish_to)
        
        # Process
        actuals_df = process_actuals(actuals_raw)
        forecasts_df = process_forecasts(forecasts_raw)
        day_ahead_df = get_day_ahead_forecasts(forecasts_df)
        
        # Filter to requested delivery range
        import pandas as pd
        start_utc = pd.to_datetime(date_from, utc=True)
        end_utc = pd.to_datetime(date_to, utc=True) + pd.Timedelta(days=1)
        if not actuals_df.empty:
            actuals_df = actuals_df[(actuals_df["timestamp"] >= start_utc) & (actuals_df["timestamp"] < end_utc)]
        if not day_ahead_df.empty:
            day_ahead_df = day_ahead_df[(day_ahead_df["timestamp"] >= start_utc) & (day_ahead_df["timestamp"] < end_utc)]
        
        # Build comparison timeseries
        timeseries = build_comparison_timeseries(actuals_df, day_ahead_df)
        
        result = {
            "timeseries": timeseries,
            "meta": {
                "date_from": date_from,
                "date_to": date_to,
                "n_points": len(timeseries),
            },
        }
        
        _cache[cache_key] = result
        return result
        
    except Exception as e:
        logger.error(f"Error building comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accuracy")
@app.get("/accuracy")
async def get_accuracy(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    group_by: str = Query(
        default=None,
        description="Grouping: 'hour_of_day', 'day', or 'week'",
    ),
):
    """
    Get forecast accuracy metrics (MAE, RMSE, MAPE, Bias).
    Optionally group by hour_of_day, day, or week.
    """
    date_from = date_from or settings.DATA_START_DATE
    date_to = date_to or settings.DATA_END_DATE
    
    cache_key = _cache_key(
        "accuracy", date_from=date_from, date_to=date_to, group_by=str(group_by)
    )
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # Fetch both datasets
        actuals_raw = await fetch_wind_actuals(date_from, date_to)
        
        start_dt = datetime.strptime(date_from, "%Y-%m-%d")
        publish_from = (start_dt - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
        publish_to = f"{date_to}T23:59:59Z"
        forecasts_raw = await fetch_wind_forecasts(publish_from, publish_to)
        
        # Process
        actuals_df = process_actuals(actuals_raw)
        forecasts_df = process_forecasts(forecasts_raw)
        day_ahead_df = get_day_ahead_forecasts(forecasts_df)
        
        # Filter to requested delivery range
        import pandas as pd
        start_utc = pd.to_datetime(date_from, utc=True)
        end_utc = pd.to_datetime(date_to, utc=True) + pd.Timedelta(days=1)
        if not actuals_df.empty:
            actuals_df = actuals_df[(actuals_df["timestamp"] >= start_utc) & (actuals_df["timestamp"] < end_utc)]
        if not day_ahead_df.empty:
            day_ahead_df = day_ahead_df[(day_ahead_df["timestamp"] >= start_utc) & (day_ahead_df["timestamp"] < end_utc)]
        
        # Compute metrics
        metrics = compute_accuracy_metrics(actuals_df, day_ahead_df, group_by)
        
        # Build error distribution
        distribution = build_error_distribution(actuals_df, day_ahead_df)
        
        result = {
            "metrics": metrics,
            "error_distribution": distribution,
            "meta": {
                "date_from": date_from,
                "date_to": date_to,
                "group_by": group_by,
                "forecast_type": "day-ahead (latest before D-1 09:00 UTC gate closure)",
            },
        }
        
        _cache[cache_key] = result
        return result
        
    except Exception as e:
        logger.error(f"Error computing accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast-evolution")
@app.get("/forecast-evolution")
async def get_forecast_evolution(
    target_date: str = Query(
        description="Target delivery date (YYYY-MM-DD)",
        default="2026-01-15",
    ),
):
    """
    Get the evolution of forecasts for a specific delivery date.
    Shows how the forecast changed across publish times (forecast vintages).
    Useful for understanding how forecast accuracy improves closer to delivery.
    """
    cache_key = _cache_key("evolution", target_date=target_date)
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # Fetch forecasts published up to 3 days before the target date
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        publish_from = (dt - timedelta(days=3)).strftime("%Y-%m-%dT00:00:00Z")
        publish_to = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        
        forecasts_raw = await fetch_wind_forecasts(publish_from, publish_to)
        forecasts_df = process_forecasts(forecasts_raw)
        
        # Filter to only target date delivery hours
        target_start = f"{target_date}T00:00:00+00:00"
        target_end = f"{target_date}T23:00:00+00:00"
        
        mask = (
            (forecasts_df["timestamp"] >= target_start) & 
            (forecasts_df["timestamp"] <= target_end)
        )
        target_forecasts = forecasts_df[mask].copy()
        
        # Also fetch actuals for comparison
        actuals_raw = await fetch_wind_actuals(target_date, target_date)
        actuals_df = process_actuals(actuals_raw)
        
        # Build evolution data: group by publish_time
        evolution = []
        for publish_time, group in target_forecasts.groupby("publish_time"):
            records = []
            for _, row in group.iterrows():
                records.append({
                    "timestamp": row["timestamp"].isoformat(),
                    "forecast_mw": row["forecast_mw"],
                })
            evolution.append({
                "publish_time": publish_time.isoformat(),
                "forecasts": records,
            })
        
        # Actuals
        actual_records = []
        for _, row in actuals_df.iterrows():
            ts = row["timestamp"]
            if hasattr(ts, 'isoformat'):
                ts_str = ts.isoformat()
            else:
                ts_str = str(ts)
            actual_records.append({
                "timestamp": ts_str,
                "actual_mw": row["actual_mw"],
            })
        
        result = {
            "target_date": target_date,
            "evolution": evolution,
            "actuals": actual_records,
            "meta": {
                "n_vintages": len(evolution),
                "n_actual_points": len(actual_records),
            },
        }
        
        _cache[cache_key] = result
        return result
        
    except Exception as e:
        logger.error(f"Error building forecast evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/cache")
@app.delete("/cache")
async def clear_cache():
    """Clear the in-memory cache."""
    global _cache
    _cache = {}
    return {"status": "cache cleared"}
