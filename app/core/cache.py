"""
TTL cache used to avoid re-fetching from external providers (Open-Meteo,
NASA FIRMS) on every request. Falls back to an in-process cache; if
REDIS_URL is set the same interface can be backed by Redis for
multi-worker deployments (see `RedisCache` below).
"""

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

_store: dict[str, tuple[float, Any]] = {}
# Last successfully fetched value per key, kept indefinitely (never expired,
# only ever overwritten by a newer successful fetch). Used by
# `cached_with_fallback` so a provider outage or rate limit never has to
# turn into a hard failure if we have *any* prior good value to serve.
_last_good: dict[str, Any] = {}
_lock = asyncio.Lock()


async def cached(key: str, ttl_seconds: int, fetcher: Callable[[], Awaitable[Any]]) -> Any:
    now = time.time()
    async with _lock:
        entry = _store.get(key)
        if entry and entry[0] > now:
            return entry[1]

    value = await fetcher()

    async with _lock:
        _store[key] = (now + ttl_seconds, value)
    return value


async def cached_with_fallback(key: str, ttl_seconds: int, fetcher: Callable[[], Awaitable[Any]]) -> Any:
    """
    Same TTL-cache behavior as `cached`, with one addition: if the fresh
    fetch fails (after the caller's own retries are exhausted), the most
    recent successfully-fetched value for this key is returned instead of
    raising, so a single provider hiccup never has to fail the endpoint.
    Only raises if the fetch fails AND no prior good value exists yet.
    """
    now = time.time()
    async with _lock:
        entry = _store.get(key)
        if entry and entry[0] > now:
            return entry[1]

    try:
        value = await fetcher()
    except Exception as exc:  # noqa: BLE001
        async with _lock:
            if key in _last_good:
                logger.warning(
                    "cached_with_fallback: fetch failed for '%s' (%s); serving last known good value.",
                    key, exc,
                )
                return _last_good[key]
        raise

    async with _lock:
        _store[key] = (now + ttl_seconds, value)
        _last_good[key] = value
    return value


def invalidate(key: str) -> None:
    _store.pop(key, None)
    _last_good.pop(key, None)


def stats() -> dict:
    return {"keys_cached": len(_store), "keys_with_fallback_value": len(_last_good)}
