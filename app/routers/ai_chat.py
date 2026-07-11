"""
AI query endpoints.

Backs the "AI Chat" surface in the brief:
  - "Why is <district> polluted today?"        -> /ai/explain
  - "What happens if truck traffic reduces..."  -> /ai/simulate-traffic
  - "Which districts are most vulnerable..."    -> /ai/vulnerable-districts

See app.services.chat_service for why these are deterministic/auditable
rather than routed through a general-purpose LLM.
"""

from fastapi import APIRouter, HTTPException, Query

from app.services import chat_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/explain")
async def explain(district: str = Query(..., description="District name, e.g. 'Chennai'")):
    result = await chat_service.explain_pollution(district)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/simulate-traffic")
async def simulate_traffic(
    district: str = Query(..., description="District name"),
    reduction_pct: float = Query(20.0, ge=1, le=100, description="Percent reduction in traffic volume"),
):
    result = await chat_service.simulate_traffic_reduction(district, reduction_pct)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/vulnerable-districts")
async def vulnerable_districts(top_n: int = Query(5, ge=1, le=200)):
    return await chat_service.most_vulnerable_districts(top_n)
