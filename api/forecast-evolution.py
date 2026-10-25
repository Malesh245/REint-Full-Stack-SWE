"""WindSight Serverless Function - /api/forecast-evolution"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.main import get_forecast_evolution

app = FastAPI(title="WindSight Forecast Evolution API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/forecast-evolution")
@app.get("/api/forecast-evolution")
async def handle_evolution(target_date: str = Query(...)):
    return await get_forecast_evolution(target_date=target_date)
