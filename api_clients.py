"""
api_clients.py
────────────────
Isolates ALL external API calls (Google Places, Geocoding, OSMnx)
from the scoring math in scorer.py.

Why this split matters for a paying product:
Before this refactor, every score_*() function in scorer.py mixed
"call Google" with "compute the score" with "silently swallow any
exception and return a guessed fallback number." A client paying for
a report has no way to know whether a 72/100 demand score came from
real data or from a guessed fallback because the API call failed.

Every function here returns a Result object with an explicit
`.ok` flag and `.error` message. Callers in scorer.py check `.ok`
and record it — this is what powers the "⚠️ some signals used
fallback data" badge now shown in score_panel.py.

Nothing about the actual scoring math lives here — this file only
talks to external services and normalizes their responses/failures.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ApiResult:
    """Wraps any external API call's outcome explicitly."""
    ok: bool
    data: Any = None
    error: Optional[str] = None
    source: str = ""  # e.g. "google_places", "google_geocode", "osmnx"


# ── Google Maps client (singleton) ──────────────────────────────────
def _get_gmaps_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GOOGLE_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    except Exception:
        return os.environ.get("GOOGLE_API_KEY", "")


_gmaps_client = None


def get_gmaps_client():
    global _gmaps_client
    if _gmaps_client is not None:
        return _gmaps_client
    key = _get_gmaps_key()
    if not key:
        logger.warning("api_clients: GOOGLE_API_KEY not set — Places/Geocoding disabled.")
        return None
    try:
        import googlemaps
        _gmaps_client = googlemaps.Client(key=key)
        return _gmaps_client
    except Exception as e:
        logger.error("api_clients: failed to init Google Maps client: %s", e)
        return None


def is_gmaps_available() -> bool:
    return get_gmaps_client() is not None


# ── Geocoding ────────────────────────────────────────────────────────
def geocode_address(address: str) -> ApiResult:
    client = get_gmaps_client()
    if client is None:
        return ApiResult(ok=False, error="Google Maps client not configured.", source="google_geocode")

    try:
        result = client.geocode(address + ", Gujarat, India")
        if not result:
            return ApiResult(ok=False, error="No geocoding results returned.", source="google_geocode")

        found_gujarat = False
        components = result[0].get("address_components", [])
        for comp in components:
            types = comp.get("types", [])
            name = comp.get("long_name", "").lower()
            if "administrative_area_level_1" in types:
                if "gujarat" in name:
                    found_gujarat = True
                else:
                    return ApiResult(ok=False, error="Address resolved outside Gujarat.", source="google_geocode")

        formatted = result[0].get("formatted_address", "").lower()
        if not found_gujarat and "gujarat" not in formatted:
            return ApiResult(ok=False, error="Could not confirm address is in Gujarat.", source="google_geocode")

        loc = result[0]["geometry"]["location"]
        return ApiResult(ok=True, data={"lat": loc["lat"], "lng": loc["lng"]}, source="google_geocode")

    except Exception as exc:
        logger.warning("api_clients: geocode failed for %r: %s", address, exc)
        return ApiResult(ok=False, error=f"Geocoding API error: {exc}", source="google_geocode")


# ── Places Nearby Search ────────────────────────────────────────────
def places_nearby(
    lat: float,
    lng: float,
    radius: int,
    place_type: Optional[str] = None,
    keyword: Optional[str] = None,
) -> ApiResult:
    """
    Wraps gmaps.places_nearby with explicit error capture.
    Returns ApiResult.data = list of place dicts on success.
    """
    client = get_gmaps_client()
    if client is None:
        return ApiResult(ok=False, data=[], error="Google Maps client not configured.", source="google_places")

    try:
        kwargs: Dict[str, Any] = dict(location=(lat, lng), radius=radius)
        if place_type:
            kwargs["type"] = place_type
        if keyword:
            kwargs["keyword"] = keyword

        result = client.places_nearby(**kwargs)
        places = result.get("results", [])
        return ApiResult(ok=True, data=places, source="google_places")

    except Exception as exc:
        logger.warning(
            "api_clients: places_nearby failed (type=%s, keyword=%s): %s",
            place_type, keyword, exc,
        )
        return ApiResult(ok=False, data=[], error=f"Places API error: {exc}", source="google_places")


def places_nearby_multi(
    lat: float,
    lng: float,
    radius: int,
    queries: List[Dict[str, Optional[str]]],
) -> ApiResult:
    """
    Runs multiple places_nearby queries, deduplicates by place_id.
    Tracks partial failures — if SOME queries fail but others succeed,
    ok=True but error notes how many failed (caller decides if that's
    enough to flag as "fallback used").
    """
    seen_ids: set = set()
    all_places: List[Dict[str, Any]] = []
    failures = 0

    for q in queries:
        res = places_nearby(lat, lng, radius, q.get("type"), q.get("keyword"))
        if not res.ok:
            failures += 1
            continue
        for place in res.data:
            pid = place.get("place_id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_places.append(place)

    if failures == len(queries) and queries:
        return ApiResult(
            ok=False, data=[],
            error=f"All {len(queries)} place queries failed.",
            source="google_places",
        )

    error_msg = f"{failures}/{len(queries)} sub-queries failed." if failures else None
    return ApiResult(ok=True, data=all_places, error=error_msg, source="google_places")


# ── OSMnx road network ───────────────────────────────────────────────
def get_road_network(lat: float, lng: float, dist: int = 300) -> ApiResult:
    try:
        import osmnx as ox
        G = ox.graph_from_point((lat, lng), dist=dist, network_type="drive")
        intersections = len([n for n, d in G.degree() if d > 2])
        total_nodes = len(G.nodes)
        return ApiResult(
            ok=True,
            data={"intersections": intersections, "total_nodes": total_nodes},
            source="osmnx",
        )
    except Exception as exc:
        logger.warning("api_clients: OSMnx road network fetch failed: %s", exc)
        return ApiResult(ok=False, data=None, error=f"OSM road network error: {exc}", source="osmnx")


def get_osm_buildings(lat: float, lng: float, dist: int = 1000) -> ApiResult:
    try:
        import osmnx as ox
        tags = {"building": ["residential", "apartments", "house"]}
        b = ox.features_from_point((lat, lng), tags=tags, dist=dist)
        return ApiResult(ok=True, data={"count": len(b)}, source="osmnx")
    except Exception as exc:
        logger.warning("api_clients: OSM buildings fetch failed: %s", exc)
        return ApiResult(ok=False, data={"count": 0}, error=f"OSM buildings error: {exc}", source="osmnx")
