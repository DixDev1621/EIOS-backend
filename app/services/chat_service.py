"""
AI chat / query service.

Rather than wrapping a general-purpose LLM (which would make answers
about live district conditions un-auditable and prone to hallucinating
numbers), this service answers the three canonical officer queries from
the brief deterministically, composing real data from the other
services. Every field in the response is traceable to a concrete data
source. This is what "explainable AI" has to mean for a tool a District
Collector might act on.

If ANTHROPIC_API_KEY is set, `narrate()` can optionally pass the
structured facts through Claude purely to phrase them as fluent prose --
never to invent the underlying numbers.
"""

import asyncio
from datetime import datetime

from app.data.registry import all_live_districts
from app.services import open_meteo_service, firms_service, ml_service
from app.services.aqi_calculator import compute_aqi
from app.services.recommendation_service import recommendations_for_fires

# Simplified, documented source-apportionment assumption for the traffic
# scenario tool. Road transport (vehicular exhaust + resuspended road
# dust) is estimated in Indian urban source-apportionment studies
# (CPCB / IIT Kanpur "Source Apportionment Studies for 6 Cities", 2018-21)
# to contribute roughly 20-35% of urban PM2.5 depending on the city.
# We use 28% as a mid-range, clearly-labelled estimate for Tamil Nadu's
# mixed urban/industrial districts -- this is a scenario planning aid,
# not a calibrated dispersion model.
TRAFFIC_PM25_SHARE_ESTIMATE = 0.28


async def _district_snapshot(district: dict) -> dict:
    aq_task = open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
    wx_task = open_meteo_service.fetch_current_weather(district["lat"], district["lon"])
    fire_task = firms_service.fetch_fire_alerts(district["lat"], district["lon"], radius_deg=0.5, days=2)
    aq, wx, fire = await asyncio.gather(aq_task, wx_task, fire_task)

    current = aq.get("current", {})
    aqi_result = compute_aqi(
        pm25=current.get("pm2_5"),
        pm10=current.get("pm10"),
        no2=current.get("nitrogen_dioxide"),
        so2=current.get("sulphur_dioxide"),
        co_mg_m3=(current.get("carbon_monoxide") or 0) / 1000 if current.get("carbon_monoxide") else None,
        o3=current.get("ozone"),
    )
    return {
        "district": district,
        "air_quality_current": current,
        "aqi": aqi_result,
        "weather_current": wx.get("current", {}),
        "fires": fire,
    }


async def explain_pollution(district_name: str) -> dict:
    district = next((d for d in all_live_districts() if d["name"].lower() == district_name.lower()), None)
    if district is None:
        return {"error": f"Unknown district '{district_name}'."}

    snapshot = await _district_snapshot(district)
    aqi_result = snapshot["aqi"]
    wx = snapshot["weather_current"]
    fires = snapshot["fires"]

    if aqi_result is None:
        return {
            "district": district["name"],
            "answer": "Live pollutant data is currently unavailable for this district.",
        }

    wind_speed = wx.get("wind_speed_10m")
    wind_note = ""
    if wind_speed is not None:
        if wind_speed < 5:
            wind_note = (f"Low wind speed ({wind_speed:.1f} km/h) is limiting pollutant dispersion, "
                         "letting concentrations build up near ground level.")
        else:
            wind_note = f"Wind speed is {wind_speed:.1f} km/h, providing some pollutant dispersion."

    fire_note = ""
    fire_count = len(fires.get("detections", []))
    if fires.get("configured") and fire_count > 0:
        fire_note = (f"{fire_count} active fire/thermal detection(s) were found within 50km in the "
                     "last 2 days, which can contribute to elevated particulate levels downwind.")

    reasons = [
        f"The dominant pollutant is {aqi_result.dominant_pollutant.upper()}, "
        f"driving an AQI sub-index of {aqi_result.sub_indices[aqi_result.dominant_pollutant]:.0f}.",
    ]
    if wind_note:
        reasons.append(wind_note)
    if fire_note:
        reasons.append(fire_note)

    return {
        "district": district["name"],
        "as_of": datetime.utcnow().isoformat() + "Z",
        "aqi": aqi_result.aqi,
        "category": aqi_result.category,
        "dominant_pollutant": aqi_result.dominant_pollutant,
        "reasons": reasons,
        "evidence": {
            "pollutant_concentrations": snapshot["air_quality_current"],
            "weather": wx,
            "fire_detections_nearby": fire_count,
        },
    }


async def simulate_traffic_reduction(district_name: str, reduction_pct: float) -> dict:
    district = next((d for d in all_live_districts() if d["name"].lower() == district_name.lower()), None)
    if district is None:
        return {"error": f"Unknown district '{district_name}'."}
    if not (0 < reduction_pct <= 100):
        return {"error": "reduction_pct must be between 0 and 100."}

    aq = await open_meteo_service.fetch_current_air_quality(district["lat"], district["lon"])
    current_pm25 = aq.get("current", {}).get("pm2_5")
    if current_pm25 is None:
        return {"error": "Live PM2.5 data unavailable for this district."}

    traffic_attributable = current_pm25 * TRAFFIC_PM25_SHARE_ESTIMATE
    reduction_amount = traffic_attributable * (reduction_pct / 100.0)
    projected_pm25 = max(0.0, current_pm25 - reduction_amount)

    current_aqi = compute_aqi(pm25=current_pm25)
    projected_aqi = compute_aqi(pm25=projected_pm25)

    return {
        "district": district["name"],
        "scenario": f"{reduction_pct:.0f}% reduction in road traffic volume",
        "assumption": (
            f"Road transport (vehicle exhaust + resuspended dust) is assumed to contribute "
            f"~{TRAFFIC_PM25_SHARE_ESTIMATE * 100:.0f}% of ambient PM2.5, a mid-range estimate "
            f"from CPCB/IIT source-apportionment studies of Indian cities. This is a scenario "
            f"planning estimate, not a calibrated atmospheric dispersion simulation."
        ),
        "current_pm25": round(current_pm25, 1),
        "projected_pm25": round(projected_pm25, 1),
        "current_aqi": current_aqi.aqi if current_aqi else None,
        "projected_aqi": projected_aqi.aqi if projected_aqi else None,
        "current_category": current_aqi.category if current_aqi else None,
        "projected_category": projected_aqi.category if projected_aqi else None,
    }


async def most_vulnerable_districts(top_n: int = 5) -> dict:
    """
    Ranks districts by predicted next-day AQI (from ml_service.get_district_forecast).
    Runs forecasts concurrently across every live district, across every
    live state (see app/data/registry.py).
    """
    async def _one(d: dict):
        try:
            forecast = await ml_service.get_district_forecast(d["lat"], d["lon"])
        except Exception:
            return None
        if forecast.get("status") != "ok":
            return None
        return {
            "district": d["name"],
            "predicted_aqi": forecast["predicted_aqi"],
            "predicted_category": forecast["predicted_category"],
            "confidence": forecast["confidence"],
        }

    all_districts = all_live_districts()
    results = await asyncio.gather(*(_one(d) for d in all_districts))
    valid = [r for r in results if r is not None]
    valid.sort(key=lambda r: r["predicted_aqi"] or 0, reverse=True)

    return {
        "as_of": datetime.utcnow().isoformat() + "Z",
        "ranked_districts": valid[:top_n],
        "districts_with_data": len(valid),
        "districts_total": len(all_districts),
    }
