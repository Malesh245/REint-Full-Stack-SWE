"""WindSight Serverless Function - /api/accuracy"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.main import get_accuracy

app = FastAPI(title="WindSight Accuracy API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/accuracy")
@app.get("/api/accuracy")
async def handle_accuracy(
    date_from: str = Query(default=None),
    date_to: str = Query(default=None),
    group_by: str = Query(default=None),
):
    return await get_accuracy(date_from=date_from, date_to=date_to, group_by=group_by)
