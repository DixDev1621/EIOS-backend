"""
Sliding-window rate limiter, keyed by client IP.

In-memory implementation suitable for a single-instance deployment.
For horizontally-scaled production deployments, back this with Redis
(INCR + EXPIRE) instead of the local dict -- the interface below stays
the same, only `_hits` needs to move to Redis.
"""

import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings

_hits: dict[str, deque] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        limit = settings.RATE_LIMIT_PER_MINUTE
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = _hits[client_ip]

        while window and now - window[0] > 60:
            window.popleft()

        if len(window) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please slow down and try again shortly.",
                    "limit_per_minute": limit,
                },
            )

        window.append(now)
        return await call_next(request)
