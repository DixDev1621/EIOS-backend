"""
State-level endpoints.

Generalized to serve all 36 Indian states/UTs at the summary level (see
app/data/registry.py). Full live overview (per-district AQI aggregation)
is available for every state in `registry.LIVE_DISTRICT_DATASETS` --
Tamil Nadu, Kerala and Delhi in this build. Requesting the overview for
a state without district data returns a clear 404 explaining that, rather
than a fabricated/empty overview.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.data import registry
from app.services import open_meteo_service
from app.services.aqi_calculator import compute_aqi

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/states", tags=["states"])


@router.get("")
async def list_states():
    return {"states": registry.list_states(), "count": len(registry.list_states())}


@router.get("/{state_code}")
async def get_state(state_code: str):
    state = registry.get_state(state_code)
    if not state:
        raise HTTPException(404, f"'{state_code}' is not a recognized Indian state/UT code.")

    districts = registry.LIVE_DISTRICT_DATASETS.get(state_code.upper())
    return {
        **state,
        "districts": [
            {"code": d["code"], "name": d["name"], "headquarters": d["headquarters"]}
            for d in districts
        ] if districts else [],
    }


async def _district_quick_status(district) -> dict:
    try:
        aq = await open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
        current = aq.get("current", {})
        aqi_result = compute_aqi(
            pm25=current.get("pm2_5"),
            pm10=current.get("pm10"),
            no2=current.get("nitrogen_dioxide"),
            so2=current.get("sulphur_dioxide"),
            o3=current.get("ozone"),
        )
        return {
            "code": district["code"],
            "name": district["name"],
            "lat": district["lat"],
            "lon": district["lon"],
            "aqi": aqi_result.aqi if aqi_result else None,
            "category": aqi_result.category if aqi_result else None,
            "color": aqi_result.color if aqi_result else None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed quick status for %s: %s", district["name"], exc)
        return {
            "code": district["code"], "name": district["name"],
            "lat": district["lat"], "lon": district["lon"],
            "aqi": None, "category": None, "color": None,
        }


@router.get("/{state_code}/overview")
async def get_state_overview(state_code: str):
    """
    Live state summary: per-district AQI fetched concurrently. Only
    available for states with a wired-in district dataset -- see
    app/data/registry.py -- since a "state overview" of a single blended
    point (the capital) would be misleading for anything district-level.
    """
    state = registry.get_state(state_code)
    if not state:
        raise HTTPException(404, f"'{state_code}' is not a recognized Indian state/UT code.")

    districts = registry.LIVE_DISTRICT_DATASETS.get(state_code.upper())
    if not districts:
        raise HTTPException(
            404,
            f"District-level live data is not yet wired in for {state['name']}. "
            f"Currently live: {', '.join(registry.LIVE_DISTRICT_DATASETS.keys())}. "
            f"See docs/ROADMAP.md for how to add a new state.",
        )

    statuses = await asyncio.gather(*(_district_quick_status(d) for d in districts))
    valid = [s for s in statuses if s["aqi"] is not None]
    valid_sorted = sorted(valid, key=lambda s: s["aqi"], reverse=True)

    avg_aqi = round(sum(s["aqi"] for s in valid) / len(valid), 1) if valid else None

    return {
        "state": state,
        "average_aqi": avg_aqi,
        "districts_reporting": len(valid),
        "districts_total": len(districts),
        "most_polluted": valid_sorted[:5],
        "least_polluted": list(reversed(valid_sorted))[:5],
        "all_districts": statuses,
    }


@router.get("/meta/live")
async def live_states():
    """Which states currently have full district-level live data wired in."""
    return {
        "live_state_codes": list(registry.LIVE_DISTRICT_DATASETS.keys()),
        "live_district_count": len(registry.all_live_districts()),
        "total_states_in_registry": len(registry.INDIA_STATES),
    }
