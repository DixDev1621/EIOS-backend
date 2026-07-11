"""
Authentication and authorization.

Supabase issues HS256-signed JWTs to authenticated users. This module
verifies those tokens on protected routes and exposes role-based
dependencies (citizen / researcher / officer / admin) driven by the
`role` claim stored in Supabase's `user_metadata` / `app_metadata` and
mirrored into our own `profiles` table (see supabase/schema.sql).
"""

from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import get_settings

security_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str
    email: Optional[str] = None
    role: str = "citizen"


ROLE_HIERARCHY = {
    "citizen": 0,
    "researcher": 1,
    "officer": 2,
    "admin": 3,
}


def _decode_token(token: str) -> dict:
    settings = get_settings()
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth is not configured on the server (missing SUPABASE_JWT_SECRET).",
        )
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[CurrentUser]:
    """Optional auth: returns None for anonymous (public/citizen-tier) requests."""
    if credentials is None:
        return None
    payload = _decode_token(credentials.credentials)
    app_meta = payload.get("app_metadata", {}) or {}
    return CurrentUser(
        user_id=payload["sub"],
        email=payload.get("email"),
        role=app_meta.get("role", "citizen"),
    )


async def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    payload = _decode_token(credentials.credentials)
    app_meta = payload.get("app_metadata", {}) or {}
    return CurrentUser(
        user_id=payload["sub"],
        email=payload.get("email"),
        role=app_meta.get("role", "citizen"),
    )


def require_role(minimum_role: str):
    """Dependency factory: require_role('officer') etc."""

    async def dependency(user: CurrentUser = Depends(require_user)) -> CurrentUser:
        if ROLE_HIERARCHY.get(user.role, 0) < ROLE_HIERARCHY.get(minimum_role, 99):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{minimum_role}' role or higher.",
            )
        return user

    return dependency
