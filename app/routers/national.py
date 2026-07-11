"""
National endpoints.

This is the "Digital Twin of India" front door: a live, composed view
across every state that currently has district-level data wired in
(Tamil Nadu, Kerala, Delhi -- see app/data/registry.py), plus the
per-district Digital Twin snapshot (current/historical/predicted/meta).
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.data import registry
from app.services import open_meteo_service
from app.services.aqi_calculator import compute_aqi
from app.services.digital_twin_service import get_twin_snapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/national", tags=["national"])


async def _quick_status(district: dict) -> dict:
    try:
        aq = await open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
        current = aq.get("current", {})
        aqi_result = compute_aqi(
            pm25=current.get("pm2_5"), pm10=current.get("pm10"), no2=current.get("nitrogen_dioxide"),
        )
        return {
            "code": district["code"], "name": district["name"], "state_code": district["state_code"],
            "lat": district["lat"], "lon": district["lon"],
            "aqi": aqi_result.aqi if aqi_result else None,
            "category": aqi_result.category if aqi_result else None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("National quick status failed for %s: %s", district["name"], exc)
        return {
            "code": district["code"], "name": district["name"], "state_code": district["state_code"],
            "lat": district["lat"], "lon": district["lon"], "aqi": None, "category": None,
        }


@router.get("/overview")
async def national_overview():
    """
    Live cross-state summary across every state with wired-in district
    data. Grows automatically as more states are added to
    registry.LIVE_DISTRICT_DATASETS -- no changes needed here.
    """
    live_districts = registry.all_live_districts()
    statuses = await asyncio.gather(*(_quick_status(d) for d in live_districts))
    valid = [s for s in statuses if s["aqi"] is not None]
    valid_sorted = sorted(valid, key=lambda s: s["aqi"], reverse=True)

    avg_aqi = round(sum(s["aqi"] for s in valid) / len(valid), 1) if valid else None

    return {
        "states_total_in_registry": len(registry.INDIA_STATES),
        "states_with_live_data": list(registry.LIVE_DISTRICT_DATASETS.keys()),
        "districts_total_live": len(live_districts),
        "districts_reporting": len(valid),
        "average_aqi": avg_aqi,
        "most_polluted": valid_sorted[:10],
        "least_polluted": list(reversed(valid_sorted))[:10],
        "all_states": registry.list_states(),
    }


@router.get("/twin/{identifier}")
async def digital_twin(identifier: str):
    """Composed Digital Twin snapshot (current + historical + predicted + meta) for one district."""
    district = registry.get_district_by_code(identifier) or registry.get_district_by_name(identifier)
    if district is None:
        raise HTTPException(404, f"District '{identifier}' not found in any live state.")
    return await get_twin_snapshot(district)
