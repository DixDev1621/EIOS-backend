"""
Alerts endpoint.

Alerts are DERIVED live from current conditions across all districts
(no synthetic/static alert data). Severe-AQI and heatwave alerts come
from the same Open-Meteo feeds as the rest of the platform; forest-fire
alerts come from NASA FIRMS. If Supabase is configured, computed alerts
are also upserted into the `alerts` table so the frontend's realtime
subscription and historical alert log both work; without Supabase the
endpoint still functions statelessly.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.data import registry
from app.db.supabase_client import get_supabase_admin
from app.services import open_meteo_service, firms_service
from app.services.aqi_calculator import compute_aqi

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])

HEATWAVE_THRESHOLD_C = 40.0
SEVERE_AQI_THRESHOLD = 300.0


async def _check_district(district) -> list[dict]:
    alerts: list[dict] = []

    try:
        aq_task = open_meteo_service.fetch_current_air_quality(
            district["lat"], district["lon"]
        )
        wx_task = open_meteo_service.fetch_current_weather(
            district["lat"], district["lon"]
        )
        fire_task = firms_service.fetch_fire_alerts(
            district["lat"], district["lon"], radius_deg=1.0, days=2
        )

        aq, wx, fire = await asyncio.gather(aq_task, wx_task, fire_task)

        current_aq = aq.get("current", {})
        aqi_result = compute_aqi(
            pm25=current_aq.get("pm2_5"),
            pm10=current_aq.get("pm10"),
        )

        if aqi_result and aqi_result.aqi >= SEVERE_AQI_THRESHOLD:
            alerts.append(
                {
                    "type": "air_quality",
                    "severity": "severe" if aqi_result.aqi >= 400 else "warning",
                    "district": district["name"],
                    "message": f"AQI at {aqi_result.aqi:.0f} ({aqi_result.category}) in {district['name']}.",
                    "value": aqi_result.aqi,
                }
            )

        apparent_temp = wx.get("current", {}).get("apparent_temperature")

        if apparent_temp is not None and apparent_temp >= HEATWAVE_THRESHOLD_C:
            alerts.append(
                {
                    "type": "heatwave",
                    "severity": "severe" if apparent_temp >= 45 else "warning",
                    "district": district["name"],
                    "message": f"Apparent temperature at {apparent_temp:.1f}°C in {district['name']}.",
                    "value": apparent_temp,
                }
            )

        fire_detections = fire.get("detections", [])

        if fire_detections:
            alerts.append(
                {
                    "type": "forest_fire",
                    "severity": "warning"
                    if len(fire_detections) < 5
                    else "severe",
                    "district": district["name"],
                    "message": f"{len(fire_detections)} active fire detection(s) near {district['name']}.",
                    "value": len(fire_detections),
                }
            )

    except Exception as exc:
        logger.warning("Alert check failed for %s: %s", district["name"], exc)

    return alerts


@router.get("")
async def get_active_alerts(state: str | None = None):
    if state:
        districts = registry.LIVE_DISTRICT_DATASETS.get(state.upper())

        if districts is None:
            raise HTTPException(
                404,
                f"No live district data for state '{state}'.",
            )
    else:
        districts = registry.all_live_districts()

    results = await asyncio.gather(*(_check_district(d) for d in districts))
    all_alerts = [a for sub in results for a in sub]

    admin = get_supabase_admin()

    if admin is not None and all_alerts:
        try:
            admin.table("alerts").insert(all_alerts).execute()
        except Exception:
            logger.exception("Failed to persist alerts to Supabase")

    severity_order = {
        "severe": 0,
        "warning": 1,
    }

    all_alerts.sort(
        key=lambda a: severity_order.get(a["severity"], 2)
    )

    return {
        "count": len(all_alerts),
        "alerts": all_alerts,
        "thresholds": {
            "heatwave_apparent_temp_c": HEATWAVE_THRESHOLD_C,
            "severe_aqi": SEVERE_AQI_THRESHOLD,
        },
    }