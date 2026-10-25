"""WindSight Serverless Function - /api/comparison"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.main import get_comparison

app = FastAPI(title="WindSight Comparison API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/comparison")
@app.get("/api/comparison")
async def handle_comparison(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
):
    return await get_comparison(date_from=date_from, date_to=date_to)
