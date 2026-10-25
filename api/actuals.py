"""WindSight Serverless Function - /api/actuals"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.main import get_actuals

app = FastAPI(title="WindSight Actuals API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/actuals")
@app.get("/api/actuals")
async def handle_actuals(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
):
    return await get_actuals(date_from=date_from, date_to=date_to)
