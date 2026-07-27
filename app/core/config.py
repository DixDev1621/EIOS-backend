"""
Application configuration.

All secrets and environment-specific values are read from environment
variables (see .env.example). Nothing is hardcoded here.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "India Environmental Intelligence OS"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # --- External data providers ---
    # Open-Meteo: free, no API key required for non-commercial use.
    OPEN_METEO_AIR_QUALITY_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"

    # NASA FIRMS: free MAP_KEY from https://firms.modis.gov/api/map_key/
    NASA_FIRMS_MAP_KEY: str = ""
    NASA_FIRMS_BASE_URL: str = "https://firms.modis.gov/api/area/csv"

    # Optional: WAQI ground-station token from https://aqicn.org/data-platform/token/
    WAQI_TOKEN: str = ""

    # --- Cache ---
    CACHE_TTL_SECONDS: int = 900  # 15 minutes, matches typical provider refresh cadence

    # --- Open-Meteo request throttling & retry ---
    # Open-Meteo's free tier rate-limits aggressively under burst load (e.g.
    # a homepage that fans out to ~65 concurrent district requests). These
    # settings cap how many requests we make in parallel and how we recover
    # from 429 responses, without touching any API route or response shape.
    OPEN_METEO_MAX_CONCURRENT_REQUESTS: int = 5
    OPEN_METEO_MAX_RETRIES: int = 3
    OPEN_METEO_RETRY_BASE_SECONDS: float = 1.0

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 120

    # --- Auth ---
    JWT_ALGORITHM: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()
