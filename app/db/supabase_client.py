"""
Supabase client factory.

Two clients are exposed:
  - `get_supabase()`         anon key, RLS-enforced, safe for read paths
                              that should respect row-level security.
  - `get_supabase_admin()`   service-role key, bypasses RLS. Used only by
                              trusted server-side jobs (data ingestion,
                              writing computed predictions/alerts).

Both are None if Supabase credentials are not configured, so the API can
still run (e.g. in local dev hitting only Open-Meteo/FIRMS) without a
Supabase project attached.
"""

from functools import lru_cache
from typing import Optional

from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Optional[Client]:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache
def get_supabase_admin() -> Optional[Client]:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
