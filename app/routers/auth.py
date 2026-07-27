"""
Auth endpoints.

Actual credential storage and password handling is delegated entirely
to Supabase Auth -- this router is a thin, documented proxy so the
frontend has a single backend base URL to talk to, plus a `/me`
endpoint that verifies the resulting JWT. No passwords or sessions are
ever handled or stored by this service directly.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, require_user
from app.db.supabase_client import get_supabase
from app.schemas.auth import SignUpRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def sign_up(payload: SignUpRequest):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase is not configured on this server.")
    try:
        result = client.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {"data": {"full_name": payload.full_name, "role": payload.requested_role}},
        })
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, str(exc))
    return {"user_id": result.user.id if result.user else None, "message": "Check your email to confirm your account."}


@router.post("/login")
async def login(payload: LoginRequest):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase is not configured on this server.")
    try:
        result = client.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(401, "Invalid email or password.")
    return {
        "access_token": result.session.access_token if result.session else None,
        "refresh_token": result.session.refresh_token if result.session else None,
        "user_id": result.user.id if result.user else None,
    }


@router.get("/me")
async def me(user: CurrentUser = Depends(require_user)):
    return user
