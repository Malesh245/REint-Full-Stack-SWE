"""
WindSight - UK Wind Power Forecast Analytics Platform
Backend configuration and settings
"""
import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Elexon BMRS API base URL
    ELEXON_API_BASE: str = os.getenv("ELEXON_API_BASE", "https://data.elexon.co.uk/bmrs/api/v1")
    
    # CORS settings
    CORS_ORIGINS: list[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://*.vercel.app",
        "*"
    ])
    
    # Data scope: January 2026
    DATA_START_DATE: str = os.getenv("DATA_START_DATE", "2026-01-01")
    DATA_END_DATE: str = os.getenv("DATA_END_DATE", "2026-01-31")
    
    # Cache TTL in seconds (5 minutes)
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    CACHE_DIR: str = os.getenv("CACHE_DIR", "data_cache")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

