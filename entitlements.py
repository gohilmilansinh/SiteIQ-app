"""
entitlements.py
─────────────────
Single source of truth for "is this user premium right now?"

Every other module (usage_limiter, score_panel gating, app.py) should
call is_premium() from HERE rather than re-implementing the check —
that way when billing logic changes (e.g. you move to real Razorpay
Subscriptions in Phase 2), you update it in exactly one place.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Tiny in-process cache so we don't hit Supabase on every single
# Streamlit rerun (which happens A LOT). 30s is short enough that
# a freshly-activated subscription shows up almost immediately.
_CACHE: dict[str, dict] = {}
_CACHE_TTL = 30


def _get_supabase():
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "") or __import__("os").environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or __import__("os").environ.get("SUPABASE_KEY", "")
    except Exception:
        import os
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning("Entitlements: Supabase unavailable: %s", e)
        return None


def get_subscription(user_id: str, use_cache: bool = True) -> Optional[dict]:
    """Returns the raw subscription row for a user, or None if no row exists."""
    if use_cache:
        cached = _CACHE.get(user_id)
        if cached and (time.time() - cached["ts"] < _CACHE_TTL):
            return cached["value"]

    client = _get_supabase()
    if not client:
        return None

    try:
        res = (
            client.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        value = res.data[0] if res.data else None
        _CACHE[user_id] = {"ts": time.time(), "value": value}
        return value
    except Exception as e:
        logger.warning("Entitlements: failed to read subscription for %s: %s", user_id, e)
        return None


def is_premium(user_id: str) -> bool:
    """
    Returns True only if the user has an active subscription that
    hasn't expired yet. This is the function everything else should call.
    """
    sub = get_subscription(user_id)
    if not sub:
        return False
    if sub.get("status") != "active" or sub.get("plan") != "premium":
        return False

    period_end = sub.get("current_period_end")
    if not period_end:
        return False

    try:
        end_dt = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) < end_dt
    except Exception:
        return False


def days_remaining(user_id: str) -> int:
    """Returns days left on current premium period, 0 if not premium/expired."""
    sub = get_subscription(user_id)
    if not sub or not sub.get("current_period_end"):
        return 0
    try:
        end_dt = datetime.fromisoformat(sub["current_period_end"].replace("Z", "+00:00"))
        delta = end_dt - datetime.now(timezone.utc)
        return max(0, delta.days)
    except Exception:
        return 0


def invalidate_cache(user_id: str) -> None:
    """Call this right after activating/changing a subscription so the
    next is_premium() check reflects it immediately instead of waiting
    out the cache TTL."""
    _CACHE.pop(user_id, None)
