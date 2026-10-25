"""WindSight Serverless Function - /api/forecasts"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.main import get_forecasts

app = FastAPI(title="WindSight Forecasts API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/forecasts")
@app.get("/api/forecasts")
async def handle_forecasts(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
):
    return await get_forecasts(date_from=date_from, date_to=date_to)
