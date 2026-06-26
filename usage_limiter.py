"""
usage_limiter.py
─────────────────
Hard server-side enforcement of free-usage limits. This exists
BEFORE billing is wired up (Phase 1) specifically to stop unlimited
free abuse — without this, anyone can refresh the page forever and
each click costs you real Google API money with zero revenue.

This is intentionally simple and config-driven so Phase 1 (billing)
can later just plug a "is_premium" check in front of these limits
instead of rewriting this module.

Current default limits (placeholder — tune freely, see FREE_LIMITS
below). These map to your stated plan: "5 free scores first time,
then 1/day free if not subscribed."

Storage mirrors persistence.py's pattern: Supabase primary,
local-file fallback for dev / when Supabase isn't configured.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import date, datetime, timezone
from typing import Tuple

logger = logging.getLogger(__name__)

# ── Configurable limits (placeholder values — adjust to your plan) ──
FREE_LIMITS = {
    "lifetime_free_scores": 5,   # total free scores ever, per user
    "daily_free_scores": 1,      # after lifetime is used up, 1/day
}

_LOCAL_PATH = os.path.join(tempfile.gettempdir(), "siteiq_usage.json")


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
        logger.warning("Usage limiter: Supabase unavailable: %s", e)
        return None


# ── Local fallback ───────────────────────────────────────────────────
def _load_local() -> dict:
    try:
        if os.path.exists(_LOCAL_PATH):
            with open(_LOCAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Usage limiter: local load failed: %s", e)
    return {}


def _save_local(data: dict) -> None:
    try:
        with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning("Usage limiter: local save failed: %s", e)


def _local_get_record(user_id: str) -> dict:
    store = _load_local()
    return store.get(user_id, {"lifetime_count": 0, "daily_count": 0, "daily_date": ""})


def _local_increment(user_id: str, today: str) -> dict:
    store = _load_local()
    rec = store.get(user_id, {"lifetime_count": 0, "daily_count": 0, "daily_date": ""})
    if rec.get("daily_date") != today:
        rec["daily_count"] = 0
        rec["daily_date"] = today
    rec["lifetime_count"] += 1
    rec["daily_count"] += 1
    store[user_id] = rec
    _save_local(store)
    return rec


# ── Public API ───────────────────────────────────────────────────────
def get_usage(user_id: str) -> dict:
    """Returns current usage counts for a user without incrementing."""
    today = date.today().isoformat()
    client = _get_client()
    if client:
        try:
            res = (
                client.table("usage_counters")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows:
                rec = rows[0]
                daily_count = rec["daily_count"] if rec.get("daily_date") == today else 0
                return {
                    "lifetime_count": rec.get("lifetime_count", 0),
                    "daily_count": daily_count,
                }
            return {"lifetime_count": 0, "daily_count": 0}
        except Exception as e:
            logger.warning("Usage limiter: Supabase read failed: %s", e)

    rec = _local_get_record(user_id)
    daily_count = rec["daily_count"] if rec.get("daily_date") == today else 0
    return {"lifetime_count": rec.get("lifetime_count", 0), "daily_count": daily_count}


def can_score(user_id: str, is_premium: bool = False) -> Tuple[bool, str, dict]:
    """
    Checks whether this user is allowed to run another score right now.
    Does NOT increment — call record_score() only after a successful score.

    Returns (allowed, reason, usage_dict)
    """
    if is_premium:
        return True, "premium", get_usage(user_id)

    usage = get_usage(user_id)

    if usage["lifetime_count"] < FREE_LIMITS["lifetime_free_scores"]:
        remaining = FREE_LIMITS["lifetime_free_scores"] - usage["lifetime_count"]
        return True, f"{remaining} free score(s) remaining (first-time allowance)", usage

    if usage["daily_count"] < FREE_LIMITS["daily_free_scores"]:
        return True, "daily free score available", usage

    return (
        False,
        "Free limit reached for today. Upgrade to Premium for unlimited "
        "scoring and full detailed reports, or come back tomorrow.",
        usage,
    )


def record_score(user_id: str) -> None:
    """Call this AFTER a successful score to increment usage counters."""
    today = date.today().isoformat()

    client = _get_client()
    if client:
        try:
            res = (
                client.table("usage_counters")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows:
                rec = rows[0]
                daily_count = rec["daily_count"] + 1 if rec.get("daily_date") == today else 1
                client.table("usage_counters").update(
                    {
                        "lifetime_count": rec.get("lifetime_count", 0) + 1,
                        "daily_count": daily_count,
                        "daily_date": today,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).eq("user_id", user_id).execute()
            else:
                client.table("usage_counters").insert(
                    {
                        "user_id": user_id,
                        "lifetime_count": 1,
                        "daily_count": 1,
                        "daily_date": today,
                    }
                ).execute()
            return
        except Exception as e:
            logger.warning("Usage limiter: Supabase write failed: %s", e)

    _local_increment(user_id, today)
