"""
WindSight - UK Wind Power Forecast Analytics Platform
Backend configuration and settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Elexon BMRS API base URL
    ELEXON_API_BASE: str = "https://data.elexon.co.uk/bmrs/api/v1"
    
    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://*.vercel.app",
    ]
    
    # Data scope: January 2026
    DATA_START_DATE: str = "2026-01-01"
    DATA_END_DATE: str = "2026-01-31"
    
    # Cache TTL in seconds (5 minutes)
    CACHE_TTL: int = 300
    CACHE_DIR: str = "data_cache"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
