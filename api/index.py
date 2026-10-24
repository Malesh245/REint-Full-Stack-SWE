"""
WindSight - Vercel Serverless Function Entrypoint
Exposes the FastAPI application to Vercel's Python runtime
"""
import sys
import os

# Ensure backend directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from backend.app.main import app
except ImportError:
    from app.main import app

handler = app
