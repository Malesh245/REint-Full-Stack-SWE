"""
WindSight - Elexon BMRS API client service
Fetches wind generation actuals (FUELHH) and forecasts (WINDFOR) with:
- High-concurrency async batching
- Automatic disk caching for instantaneous responses
- Resilient retries and timeout handling
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Reusable async HTTP client
_client: Optional[httpx.AsyncClient] = None

# Multi-location cache directory resolution
def _resolve_cache_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data_cache",
        Path(settings.CACHE_DIR),
        Path(__file__).resolve().parent.parent / "data_cache",
    ]
    for c in candidates:
        if c.exists() and any(c.glob("*.json")):
            return c
    p = Path(settings.CACHE_DIR)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p

CACHE_PATH = _resolve_cache_dir()


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.ELEXON_API_BASE,
            timeout=httpx.Timeout(45.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=30),
            follow_redirects=True,
        )
    return _client


async def close_http_client():
    """Close the shared HTTP client."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


def _get_cache_file(category: str, key: str) -> Path:
    """Return cache file path for given category and key."""
    safe_key = key.replace(":", "_").replace("/", "_")
    return CACHE_PATH / f"{category}_{safe_key}.json"


def _read_disk_cache(category: str, key: str) -> Optional[list]:
    """Read cached JSON data from disk if it exists."""
    cache_file = _get_cache_file(category, key)
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Cache read error for {cache_file}: {e}")
    return None


def _write_disk_cache(category: str, key: str, data: list):
    """Write data to disk cache."""
    cache_file = _get_cache_file(category, key)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Cache write error for {cache_file}: {e}")


async def _fetch_single_day_actuals(
    client: httpx.AsyncClient,
    date_str: str,
    sem: asyncio.Semaphore,
) -> list[dict]:
    """Fetch FUELHH actuals for a single date with caching and retries."""
    cached = _read_disk_cache("fuelhh", date_str)
    if cached is not None:
        return cached

    params = {
        "settlementDateFrom": date_str,
        "settlementDateTo": date_str,
        "fuelType": "WIND",
    }

    async with sem:
        for attempt in range(3):
            try:
                response = await client.get("/datasets/FUELHH/stream", params=params)
                response.raise_for_status()
                data = response.json()
                if data:
                    _write_disk_cache("fuelhh", date_str, data)
                return data
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning(f"Attempt {attempt+1} failed for FUELHH {date_str}: {e}")
                if attempt < 2:
                    await asyncio.sleep(1.0 * (attempt + 1))
        logger.error(f"Failed to fetch FUELHH for {date_str} after 3 attempts")
        return []


async def fetch_wind_actuals(date_from: str, date_to: str) -> list[dict]:
    """
    Fetch actual wind generation data from FUELHH dataset concurrently.
    """
    client = await get_http_client()
    current = datetime.strptime(date_from, "%Y-%m-%d")
    end = datetime.strptime(date_to, "%Y-%m-%d")

    dates = []
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    sem = asyncio.Semaphore(10)
    tasks = [_fetch_single_day_actuals(client, d, sem) for d in dates]
    results = await asyncio.gather(*tasks)

    all_records = []
    for day_records in results:
        all_records.extend(day_records)

    logger.info(f"Total FUELHH records fetched: {len(all_records)} across {len(dates)} days")
    return all_records


async def _fetch_single_day_forecast(
    client: httpx.AsyncClient,
    start_dt: datetime,
    end_dt: datetime,
    sem: asyncio.Semaphore,
) -> list[dict]:
    """Fetch WINDFOR forecasts for a single chunk with caching and retries."""
    key = start_dt.strftime("%Y-%m-%d")
    cached = _read_disk_cache("windfor", key)
    if cached is not None:
        return cached

    params = {
        "publishDateTimeFrom": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishDateTimeTo": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    async with sem:
        for attempt in range(3):
            try:
                response = await client.get("/datasets/WINDFOR/stream", params=params)
                response.raise_for_status()
                data = response.json()
                if data:
                    _write_disk_cache("windfor", key, data)
                return data
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning(f"Attempt {attempt+1} failed for WINDFOR {key}: {e}")
                if attempt < 2:
                    await asyncio.sleep(1.0 * (attempt + 1))
        logger.error(f"Failed to fetch WINDFOR for {key} after 3 attempts")
        return []


async def fetch_wind_forecasts(publish_from: str, publish_to: str) -> list[dict]:
    """
    Fetch wind generation forecast data from WINDFOR dataset concurrently.
    """
    client = await get_http_client()
    current = datetime.fromisoformat(publish_from.replace("Z", "+00:00"))
    end = datetime.fromisoformat(publish_to.replace("Z", "+00:00"))

    chunks = []
    while current < end:
        chunk_end = min(current + timedelta(days=1), end)
        chunks.append((current, chunk_end))
        current = chunk_end

    sem = asyncio.Semaphore(8)
    tasks = [_fetch_single_day_forecast(client, c_start, c_end, sem) for c_start, c_end in chunks]
    results = await asyncio.gather(*tasks)

    all_records = []
    for chunk_records in results:
        all_records.extend(chunk_records)

    logger.info(f"Total WINDFOR records fetched: {len(all_records)} across {len(chunks)} chunks")
    return all_records
