"""
Search endpoint.

Searches all 36 states/UTs by name, plus every live district (currently
Tamil Nadu, Kerala, Delhi -- see app/data/registry.py). Factory,
power-plant, hospital and school point layers are part of the documented
roadmap (see docs/ROADMAP.md) but are intentionally NOT included as
fake/sample points in this build -- wiring them up requires a licensed
point-of-interest dataset, which is a data-sourcing decision for the
deploying agency, not something to fabricate here.
"""

from fastapi import APIRouter

from app.data import registry

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(q: str):
    query = q.strip()
    if not query:
        return {"results": []}

    matches = registry.search_all(query)
    results = [
        {"type": "state", "name": s["name"], "code": s["code"], "district_data_available": s["district_data_available"]}
        for s in matches["states"]
    ] + [
        {
            "type": "district", "name": d["name"], "code": d["code"], "state_code": d["state_code"],
            "headquarters": d["headquarters"], "lat": d["lat"], "lon": d["lon"],
        }
        for d in matches["districts"]
    ]

    return {"query": q, "results": results, "count": len(results)}
