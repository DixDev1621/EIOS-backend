"""
Open-Meteo integration.

Open-Meteo (https://open-meteo.com) provides free, keyless access to:
  - Air Quality API   : PM2.5, PM10, NO2, SO2, CO, O3, plus forecast
  - Weather API       : temperature, humidity, wind, precipitation
  - Historical Archive : multi-year hourly reanalysis data, used to
                          train the forecasting model in ml_service.py

No API key is required for non-commercial use, which makes it the
default provider for this project. If you later obtain a WAQI ground
station token, `waqi_service.py` can be layered in as a cross-check on
ground-truth monitoring stations.

Request throttling & resilience:
  - All outbound requests share one global `asyncio.Semaphore`, capping
    concurrent Open-Meteo calls (default 5) so a page that fans out to
    dozens of districts queues its requests instead of firing them all
    at once and tripping Open-Meteo's rate limiter.
  - HTTP 429 responses are retried automatically with exponential
    backoff (1s, 2s, 4s -- 3 retries by default) before giving up.
  - Every fetch goes through `cached_with_fallback`: if a fresh fetch
    ultimately fails after retries, the most recent successfully-fetched
    value for that exact location is served instead of raising, so one
    provider hiccup never has to fail an endpoint that depends on it.
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import Any

import httpx

from app.core.cache import cached_with_fallback
from app.core.config import get_settings

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# Global concurrency limit across every Open-Meteo call made by this
# process, regardless of which endpoint/service function triggered it.
_settings_for_semaphore = get_settings()
_OPEN_METEO_SEMAPHORE = asyncio.Semaphore(_settings_for_semaphore.OPEN_METEO_MAX_CONCURRENT_REQUESTS)


async def _get_json(url: str, params: dict[str, Any]) -> dict:
    """
    Fetch JSON from an Open-Meteo endpoint, queued behind the global
    concurrency semaphore and retried with exponential backoff on 429s.
    """
    settings = get_settings()
    max_retries = settings.OPEN_METEO_MAX_RETRIES
    base_delay = settings.OPEN_METEO_RETRY_BASE_SECONDS

    async with _OPEN_METEO_SEMAPHORE:
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                rate_limited = exc.response.status_code == 429
                if rate_limited and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        "Open-Meteo rate limited (429) on %s. Retrying in %.0fs (attempt %d/%d).",
                        url, delay, attempt + 1, max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

    # Unreachable in practice (the loop above always returns or raises),
    # but keeps the function's control flow explicit for type checkers.
    raise RuntimeError(f"Open-Meteo request to {url} failed after {max_retries} retries")


async def fetch_current_air_quality(lat: float, lon: float) -> dict:
    """Current + hourly air quality for one point. Cached per-district."""
    settings = get_settings()

    async def _fetch():
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone,us_aqi",
            "hourly": "pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone",
            "timezone": "Asia/Kolkata",
            "forecast_days": 3,
        }
        return await _get_json(settings.OPEN_METEO_AIR_QUALITY_URL, params)

    key = f"aq:{lat:.3f}:{lon:.3f}"
    return await cached_with_fallback(key, settings.CACHE_TTL_SECONDS, _fetch)


async def fetch_current_weather(lat: float, lon: float) -> dict:
    """Current + hourly + 7-day daily forecast weather for one point."""
    settings = get_settings()

    async def _fetch():
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
                        "wind_speed_10m,wind_direction_10m,weather_code,surface_pressure",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation_probability",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,"
                     "precipitation_probability_max",
            "timezone": "Asia/Kolkata",
            "forecast_days": 7,
        }
        return await _get_json(settings.OPEN_METEO_FORECAST_URL, params)

    key = f"wx:{lat:.3f}:{lon:.3f}"
    return await cached_with_fallback(key, settings.CACHE_TTL_SECONDS, _fetch)


async def fetch_historical_air_quality(lat: float, lon: float, days_back: int = 60) -> dict:
    """
    Historical hourly air quality, used as ML training data.
    Cached for 12 hours since historical data doesn't change intraday.
    """
    settings = get_settings()
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days_back)

    async def _fetch():
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "timezone": "Asia/Kolkata",
        }
        return await _get_json(settings.OPEN_METEO_AIR_QUALITY_URL, params)

    key = f"aq-hist:{lat:.3f}:{lon:.3f}:{days_back}"
    return await cached_with_fallback(key, 12 * 3600, _fetch)


async def fetch_historical_weather(lat: float, lon: float, days_back: int = 60) -> dict:
    settings = get_settings()
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days_back)

    async def _fetch():
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "timezone": "Asia/Kolkata",
        }
        return await _get_json(settings.OPEN_METEO_ARCHIVE_URL, params)

    key = f"wx-hist:{lat:.3f}:{lon:.3f}:{days_back}"
    return await cached_with_fallback(key, 12 * 3600, _fetch)
