"""
cache_layer.py
──────────────
Caches expensive external API results (Google Geocoding, Places,
OSMnx road network) so repeat or nearby scoring requests don't
re-trigger billed API calls.

Why this matters:
A single score_site() call fires ~15-25 Google Places API requests.
At ~$0.032/call that's $0.30-$0.50 per score, every single time,
even for the *same* address. Most of that data doesn't change
day-to-day (competitor density, nearby anchors, road network).

Strategy:
- Geocoding: cache by normalized address string. TTL 365 days
  (coordinates of a real address never change).
- Places-based scores (demand, footfall, competition, catchment,
  spending): cache by a rounded lat/lng "grid cell" (~100m) +
  brand_type + signal type. TTL 60 days — competitor landscape
  shifts slowly, not daily.
- Accessibility (OSMnx road network): cache by grid cell only
  (brand-independent). TTL 180 days — roads rarely change.

Storage:
- Primary: Supabase table `score_cache` (shared across all users —
  this is the whole point, two different users scoring a nearby
  address both benefit).
- Fallback: local JSON file in tempdir, same pattern as persistence.py,
  for when Supabase isn't configured (e.g. local dev).

Usage:
    from cache_layer import cache_get, cache_set, grid_key

    key = grid_key(lat, lng, precision=3) + f":competition:{brand_type}"
    cached = cache_get(key, max_age_days=60)
    if cached is not None:
        return cached["score"], cached["details"]
    # ... do the expensive API call ...
    cache_set(key, {"score": score, "details": details})
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

_LOCAL_CACHE_PATH = os.path.join(tempfile.gettempdir(), "siteiq_score_cache.json")

# In-process memory cache so that within a SINGLE score_site() call,
# or across a few calls in the same Streamlit session, we don't even
# hit Supabase/disk repeatedly.
_MEMORY_CACHE: dict[str, dict] = {}


# ── Supabase client (lazy, optional) ───────────────────────────────
def _get_client():
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning("Cache: Supabase client unavailable: %s", e)
        return None


# ── Key helpers ─────────────────────────────────────────────────────
def grid_key(lat: float, lng: float, precision: int = 3) -> str:
    """
    Rounds lat/lng to a grid cell so nearby addresses share a cache
    entry. precision=3 ≈ 110m at the equator (close enough at
    Gujarat's latitude for "same micro-market" purposes).
    """
    return f"{round(lat, precision)},{round(lng, precision)}"


def address_key(address: str) -> str:
    """Normalized cache key for geocoding lookups."""
    norm = re.sub(r"\s+", " ", address.strip().lower())
    return "geo:" + hashlib.md5(norm.encode()).hexdigest()


# ── Local file fallback ─────────────────────────────────────────────
def _load_local() -> dict:
    try:
        if os.path.exists(_LOCAL_CACHE_PATH):
            with open(_LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Cache: local load failed: %s", e)
    return {}


def _save_local(data: dict) -> None:
    try:
        with open(_LOCAL_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning("Cache: local save failed: %s", e)


def _local_get(key: str, max_age_days: float) -> Optional[Any]:
    store = _load_local()
    entry = store.get(key)
    if not entry:
        return None
    if time.time() - entry.get("ts", 0) > max_age_days * 86400:
        return None
    return entry.get("value")


def _local_set(key: str, value: Any) -> None:
    store = _load_local()
    store[key] = {"ts": time.time(), "value": value}
    # Keep file from growing unbounded — drop oldest if too large
    if len(store) > 5000:
        oldest = sorted(store.items(), key=lambda kv: kv[1].get("ts", 0))
        for k, _ in oldest[:1000]:
            store.pop(k, None)
    _save_local(store)


# ── Public API ───────────────────────────────────────────────────────
def cache_get(key: str, max_age_days: float = 60) -> Optional[Any]:
    """Returns cached value if present and fresh, else None."""
    # 1. Memory cache (fastest, same-process)
    mem = _MEMORY_CACHE.get(key)
    if mem and (time.time() - mem["ts"] <= max_age_days * 86400):
        return mem["value"]

    # 2. Supabase (shared across all users/sessions)
    client = _get_client()
    if client:
        try:
            res = (
                client.table("score_cache")
                .select("data, created_at")
                .eq("cache_key", key)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows:
                from datetime import datetime, timezone
                created = datetime.fromisoformat(
                    rows[0]["created_at"].replace("Z", "+00:00")
                )
                age_days = (
                    datetime.now(timezone.utc) - created
                ).total_seconds() / 86400
                if age_days <= max_age_days:
                    value = rows[0]["data"]
                    _MEMORY_CACHE[key] = {"ts": time.time(), "value": value}
                    return value
        except Exception as e:
            logger.warning("Cache: Supabase get failed for %s: %s", key, e)

    # 3. Local file fallback
    value = _local_get(key, max_age_days)
    if value is not None:
        _MEMORY_CACHE[key] = {"ts": time.time(), "value": value}
    return value


def cache_set(key: str, value: Any) -> None:
    """Stores a value in cache (memory + Supabase/local)."""
    _MEMORY_CACHE[key] = {"ts": time.time(), "value": value}

    client = _get_client()
    if client:
        try:
            client.table("score_cache").upsert(
                {"cache_key": key, "data": value}
            ).execute()
            return
        except Exception as e:
            logger.warning("Cache: Supabase set failed for %s: %s", key, e)

    _local_set(key, value)


def cache_stats() -> dict:
    """Quick visibility into cache size — useful for debugging cost savings."""
    client = _get_client()
    if client:
        try:
            res = client.table("score_cache").select(
                "cache_key", count="exact"
            ).execute()
            return {"backend": "supabase", "entries": res.count or 0}
        except Exception:
            pass
    store = _load_local()
    return {"backend": "local_file", "entries": len(store)}
