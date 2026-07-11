"""Shared Pydantic response models."""

from typing import Optional
from pydantic import BaseModel


class DistrictSummary(BaseModel):
    code: str
    name: str
    headquarters: str
    lat: float
    lon: float
    area_km2: float
    population: int


class AQIResponse(BaseModel):
    aqi: Optional[float]
    category: Optional[str]
    color: Optional[str]
    dominant_pollutant: Optional[str]
    sub_indices: dict
    pollutants_raw: dict
    as_of: Optional[str] = None


class WeatherResponse(BaseModel):
    temperature_c: Optional[float]
    apparent_temperature_c: Optional[float]
    humidity_pct: Optional[float]
    wind_speed_kmh: Optional[float]
    wind_direction_deg: Optional[float]
    precipitation_mm: Optional[float]
    surface_pressure_hpa: Optional[float]
    daily_forecast: list = []


class HealthScoreResponse(BaseModel):
    score: float
    air_quality_component: float
    weather_stress_component: float
    fire_load_component: float
    inputs: dict


class RecommendationItem(BaseModel):
    audience: str
    severity: str
    action: str
    basis: str


class ErrorResponse(BaseModel):
    detail: str
