"""
NASA FIRMS (Fire Information for Resource Management System) integration.

Provides real active fire/thermal-anomaly detections from the VIIRS and
MODIS satellites, used for forest fire and crop-residue-burning alerts.

Requires a free MAP_KEY: https://firms.modis.gov/api/map_key/ (instant,
email-based signup, no cost). Without a key configured, this service
returns an empty result set with a clear `configured: false` flag rather
than fabricating alerts -- the platform must never invent fire events.
"""

import csv
import io
import logging

import httpx

from app.core.cache import cached
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# VIIRS NOAA-20, 375m resolution, best balance of coverage/precision for FIRMS area API
SOURCE = "VIIRS_NOAA20_NRT"


async def fetch_fire_alerts(lat: float, lon: float, radius_deg: float = 1.0, days: int = 2) -> dict:
    """
    Fire detections within a bounding box around (lat, lon) over the
    last `days` days. Returns {"configured": bool, "detections": [...]}.
    """
    settings = get_settings()

    if not settings.NASA_FIRMS_MAP_KEY:
        return {
            "configured": False,
            "detections": [],
            "message": "NASA_FIRMS_MAP_KEY is not set. Get a free key at "
                       "https://firms.modis.gov/api/map_key/ and add it to your .env "
                       "to enable live fire detection.",
        }

    west, south, east, north = lon - radius_deg, lat - radius_deg, lon + radius_deg, lat + radius_deg
    bbox = f"{west:.4f},{south:.4f},{east:.4f},{north:.4f}"
    url = f"{settings.NASA_FIRMS_BASE_URL}/{settings.NASA_FIRMS_MAP_KEY}/{SOURCE}/{bbox}/{days}"

    async def _fetch():
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            reader = csv.DictReader(io.StringIO(response.text))
            detections = []
            for row in reader:
                try:
                    detections.append({
                        "lat": float(row["latitude"]),
                        "lon": float(row["longitude"]),
                        "brightness_k": float(row.get("bright_ti4", row.get("brightness", 0)) or 0),
                        "confidence": row.get("confidence", "n/a"),
                        "acquired_date": row.get("acq_date"),
                        "acquired_time": row.get("acq_time"),
                        "frp_mw": float(row["frp"]) if row.get("frp") else None,
                        "day_night": row.get("daynight"),
                    })
                except (ValueError, KeyError):
                    continue
            return {"configured": True, "detections": detections}

    key = f"firms:{lat:.2f}:{lon:.2f}:{radius_deg}:{days}"
    return await cached(key, 3600, _fetch)  # fire data refreshes ~hourly at source
