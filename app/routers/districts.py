"""District-level endpoints -- the core of the District detail page."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.data import registry
from app.services import open_meteo_service, firms_service, ml_service
from app.services.aqi_calculator import compute_aqi
from app.services.health_score_service import compute_health_score
from app.services.recommendation_service import (
    recommendations_for_aqi, recommendations_for_heat, recommendations_for_fires,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/districts", tags=["districts"])


@router.get("")
async def list_districts(state: str | None = None):
    if state:
        districts = registry.LIVE_DISTRICT_DATASETS.get(state.upper())
        if districts is None:
            raise HTTPException(404, f"No live district data for state '{state}'.")
        return {"districts": districts, "count": len(districts), "state": state.upper()}

    all_districts = registry.all_live_districts()
    return {"districts": all_districts, "count": len(all_districts)}


def _resolve_district(identifier: str):
    d = registry.get_district_by_code(identifier) or registry.get_district_by_name(identifier)
    if d is None:
        raise HTTPException(
            404,
            f"District '{identifier}' not found. Live district data currently covers: "
            f"{', '.join(registry.LIVE_DISTRICT_DATASETS.keys())}. Use a district name or its code.",
        )
    return d


@router.get("/{identifier}")
async def get_district(identifier: str):
    return _resolve_district(identifier)


@router.get("/{identifier}/aqi")
async def district_aqi(identifier: str):
    district = _resolve_district(identifier)
    aq = await open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
    current = aq.get("current", {})
    result = compute_aqi(
        pm25=current.get("pm2_5"),
        pm10=current.get("pm10"),
        no2=current.get("nitrogen_dioxide"),
        so2=current.get("sulphur_dioxide"),
        co_mg_m3=(current.get("carbon_monoxide") or 0) / 1000 if current.get("carbon_monoxide") else None,
        o3=current.get("ozone"),
    )
    if result is None:
        raise HTTPException(503, "Live pollutant data unavailable from provider right now.")
    return {
        "district": district["name"],
        "aqi": result.aqi,
        "category": result.category,
        "color": result.color,
        "dominant_pollutant": result.dominant_pollutant,
        "sub_indices": result.sub_indices,
        "pollutants_raw": current,
        "hourly": aq.get("hourly", {}),
        "as_of": current.get("time"),
    }


@router.get("/{identifier}/weather")
async def district_weather(identifier: str):
    district = _resolve_district(identifier)
    wx = await open_meteo_service.fetch_current_weather(district["lat"], district["lon"])
    current = wx.get("current", {})
    return {
        "district": district["name"],
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction_deg": current.get("wind_direction_10m"),
        "precipitation_mm": current.get("precipitation"),
        "surface_pressure_hpa": current.get("surface_pressure"),
        "as_of": current.get("time"),
        "hourly": wx.get("hourly", {}),
        "daily_forecast": wx.get("daily", {}),
    }


@router.get("/{identifier}/fires")
async def district_fires(identifier: str):
    district = _resolve_district(identifier)
    return await firms_service.fetch_fire_alerts(district["lat"], district["lon"], radius_deg=1.0, days=3)


@router.get("/{identifier}/forecast")
async def district_forecast(identifier: str):
    district = _resolve_district(identifier)
    result = await ml_service.get_district_forecast(district["lat"], district["lon"])
    return {"district": district["name"], **result}


@router.get("/{identifier}/health-score")
async def district_health_score(identifier: str):
    district = _resolve_district(identifier)
    aq_task = open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
    wx_task = open_meteo_service.fetch_current_weather(district["lat"], district["lon"])
    fire_task = firms_service.fetch_fire_alerts(district["lat"], district["lon"], radius_deg=0.5, days=2)
    aq, wx, fire = await asyncio.gather(aq_task, wx_task, fire_task)

    aqi_result = compute_aqi(
        pm25=aq.get("current", {}).get("pm2_5"),
        pm10=aq.get("current", {}).get("pm10"),
        no2=aq.get("current", {}).get("nitrogen_dioxide"),
    )
    breakdown = compute_health_score(
        aqi=aqi_result.aqi if aqi_result else None,
        apparent_temp_c=wx.get("current", {}).get("apparent_temperature"),
        humidity_pct=wx.get("current", {}).get("relative_humidity_2m"),
        fire_detection_count=len(fire.get("detections", [])),
    )
    return {"district": district["name"], **breakdown.__dict__}


@router.get("/{identifier}/recommendations")
async def district_recommendations(identifier: str):
    district = _resolve_district(identifier)
    aq_task = open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
    wx_task = open_meteo_service.fetch_current_weather(district["lat"], district["lon"])
    fire_task = firms_service.fetch_fire_alerts(district["lat"], district["lon"], radius_deg=0.5, days=2)
    aq, wx, fire = await asyncio.gather(aq_task, wx_task, fire_task)

    recs = []
    aqi_result = compute_aqi(
        pm25=aq.get("current", {}).get("pm2_5"),
        pm10=aq.get("current", {}).get("pm10"),
        no2=aq.get("current", {}).get("nitrogen_dioxide"),
    )
    if aqi_result:
        recs += recommendations_for_aqi(aqi_result.aqi, aqi_result.category)

    apparent_temp = wx.get("current", {}).get("apparent_temperature")
    if apparent_temp is not None:
        recs += recommendations_for_heat(apparent_temp)

    recs += recommendations_for_fires(len(fire.get("detections", [])))

    return {"district": district["name"], "recommendations": [r.__dict__ for r in recs]}


@router.get("/{identifier}/dashboard")
async def district_dashboard(identifier: str):
    """
    Single call powering the full District detail page: AQI, weather,
    fires, health score and recommendations fetched concurrently.
    """
    district = _resolve_district(identifier)
    aq_task = open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
    wx_task = open_meteo_service.fetch_current_weather(district["lat"], district["lon"])
    fire_task = firms_service.fetch_fire_alerts(district["lat"], district["lon"], radius_deg=1.0, days=3)
    aq, wx, fire = await asyncio.gather(aq_task, wx_task, fire_task)

    current_aq = aq.get("current", {})
    current_wx = wx.get("current", {})

    aqi_result = compute_aqi(
        pm25=current_aq.get("pm2_5"),
        pm10=current_aq.get("pm10"),
        no2=current_aq.get("nitrogen_dioxide"),
        so2=current_aq.get("sulphur_dioxide"),
        co_mg_m3=(current_aq.get("carbon_monoxide") or 0) / 1000 if current_aq.get("carbon_monoxide") else None,
        o3=current_aq.get("ozone"),
    )
    breakdown = compute_health_score(
        aqi=aqi_result.aqi if aqi_result else None,
        apparent_temp_c=current_wx.get("apparent_temperature"),
        humidity_pct=current_wx.get("relative_humidity_2m"),
        fire_detection_count=len(fire.get("detections", [])),
    )

    recs = []
    if aqi_result:
        recs += recommendations_for_aqi(aqi_result.aqi, aqi_result.category)
    if current_wx.get("apparent_temperature") is not None:
        recs += recommendations_for_heat(current_wx["apparent_temperature"])
    recs += recommendations_for_fires(len(fire.get("detections", [])))

    return {
        "district": district,
        "aqi": {
            "value": aqi_result.aqi if aqi_result else None,
            "category": aqi_result.category if aqi_result else None,
            "color": aqi_result.color if aqi_result else None,
            "dominant_pollutant": aqi_result.dominant_pollutant if aqi_result else None,
            "sub_indices": aqi_result.sub_indices if aqi_result else {},
            "pollutants_raw": current_aq,
        },
        "weather": {
            "temperature_c": current_wx.get("temperature_2m"),
            "apparent_temperature_c": current_wx.get("apparent_temperature"),
            "humidity_pct": current_wx.get("relative_humidity_2m"),
            "wind_speed_kmh": current_wx.get("wind_speed_10m"),
            "wind_direction_deg": current_wx.get("wind_direction_10m"),
            "precipitation_mm": current_wx.get("precipitation"),
            "daily_forecast": wx.get("daily", {}),
        },
        "fires": fire,
        "health_score": breakdown.__dict__,
        "recommendations": [r.__dict__ for r in recs],
        "as_of": current_aq.get("time") or current_wx.get("time"),
    }
