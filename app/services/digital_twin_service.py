"""
Digital Twin service.

A "digital twin" of a district is formalized here as three explicit,
clearly-separated layers, all built from real data already served
elsewhere in the API (this module composes, it does not introduce new
data sources):

  - CURRENT   : live sensor-equivalent readings (AQI, weather, fires) --
                the twin's present state
  - HISTORICAL: the last 48h of observed PM2.5/weather -- the twin's
                short-term memory, used to contextualize "current"
  - PREDICTED : the ML forecast + SHAP explainability -- the twin's
                projection of its own near-future state
  - META      : health score + recommendations -- the twin's derived
                interpretation layer

This layered shape is what lets a frontend (or another system) treat a
district as a persistent, queryable "twin" object rather than a single
flat API response, and is the same shape that would back a live
WebSocket/Realtime feed (see `docs/DIGITAL_TWIN.md` for how to wire
Supabase Realtime on top of the `predictions` and `alerts` tables for
push updates instead of polling this endpoint).
"""

import asyncio

from app.services import open_meteo_service, firms_service, ml_service
from app.services.aqi_calculator import compute_aqi
from app.services.health_score_service import compute_health_score
from app.services.recommendation_service import (
    recommendations_for_aqi, recommendations_for_heat, recommendations_for_fires,
)


async def get_twin_snapshot(district: dict) -> dict:
    lat, lon = district["lat"], district["lon"]

    current_aq_task = open_meteo_service.fetch_current_air_quality(lat, lon)
    current_wx_task = open_meteo_service.fetch_current_weather(lat, lon)
    fire_task = firms_service.fetch_fire_alerts(lat, lon, radius_deg=1.0, days=2)
    forecast_task = ml_service.get_district_forecast(lat, lon)

    current_aq, current_wx, fires, forecast = await asyncio.gather(
        current_aq_task, current_wx_task, fire_task, forecast_task
    )

    current = current_aq.get("current", {})
    current_wx_now = current_wx.get("current", {})

    aqi_result = compute_aqi(
        pm25=current.get("pm2_5"),
        pm10=current.get("pm10"),
        no2=current.get("nitrogen_dioxide"),
        so2=current.get("sulphur_dioxide"),
        co_mg_m3=(current.get("carbon_monoxide") or 0) / 1000 if current.get("carbon_monoxide") else None,
        o3=current.get("ozone"),
    )

    health = compute_health_score(
        aqi=aqi_result.aqi if aqi_result else None,
        apparent_temp_c=current_wx_now.get("apparent_temperature"),
        humidity_pct=current_wx_now.get("relative_humidity_2m"),
        fire_detection_count=len(fires.get("detections", [])),
    )

    recs = []
    if aqi_result:
        recs += recommendations_for_aqi(aqi_result.aqi, aqi_result.category)
    if current_wx_now.get("apparent_temperature") is not None:
        recs += recommendations_for_heat(current_wx_now["apparent_temperature"])
    recs += recommendations_for_fires(len(fires.get("detections", [])))

    # Trim the last 48h from the hourly series already fetched for "current"
    # (Open-Meteo's forecast endpoint includes recent history in `hourly`).
    hourly_time = current_aq.get("hourly", {}).get("time", [])
    hourly_pm25 = current_aq.get("hourly", {}).get("pm2_5", [])
    historical_window = list(zip(hourly_time, hourly_pm25))[-48:]

    return {
        "district": {"code": district["code"], "name": district["name"], "state_code": district.get("state_code")},
        "current": {
            "aqi": aqi_result.aqi if aqi_result else None,
            "category": aqi_result.category if aqi_result else None,
            "dominant_pollutant": aqi_result.dominant_pollutant if aqi_result else None,
            "pollutants_raw": current,
            "weather": current_wx_now,
            "active_fires": len(fires.get("detections", [])),
        },
        "historical": {
            "window_hours": len(historical_window),
            "pm25_series": [{"time": t, "pm25": v} for t, v in historical_window],
        },
        "predicted": forecast,
        "meta": {
            "health_score": health.__dict__,
            "recommendations": [r.__dict__ for r in recs],
        },
    }
