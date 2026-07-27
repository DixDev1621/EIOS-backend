"""
India Environmental Intelligence OS -- FastAPI backend entrypoint.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.routers import states, districts, alerts, search, ai_chat, auth, national

configure_logging()
logger = logging.getLogger("eios")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Environmental Intelligence Operating System for Tamil Nadu -- "
        "real-time air quality (CPCB AQI methodology), weather, active fire "
        "detections, ML forecasting with SHAP explainability, and a "
        "rule-based recommendation engine, all built on live public data."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. This has been logged."},
    )


app.include_router(national.router, prefix=settings.API_V1_PREFIX)
app.include_router(states.router, prefix=settings.API_V1_PREFIX)
app.include_router(districts.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
