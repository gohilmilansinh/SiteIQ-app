from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from config import (
    FOOTFALL_ANCHORS,
    SUPPORTED_CITIES,
    VERDICT_THRESHOLDS,
    WEIGHTS,
)
from census_data import score_population
from cache_layer import cache_get, cache_set, grid_key, address_key
import api_clients

logger = logging.getLogger(__name__)

# ── Cache TTLs (days) ───────────────────────────────────────────────
TTL_GEOCODE       = 365
TTL_DEMAND        = 60
TTL_FOOTFALL      = 60
TTL_COMPETITION   = 30
TTL_ACCESSIBILITY = 180
TTL_CATCHMENT     = 60
TTL_SPENDING      = 90


def validate_address(address: str) -> Tuple[bool, str]:
    address_lower = address.strip().lower()
    if len(address_lower) < 6:
        return False, (
            "Address too short. Please provide a specific area "
            "and city name — e.g. 'Bopal, Ahmedabad, Gujarat'."
        )

    if not any(city in address_lower for city in SUPPORTED_CITIES):
        return False, (
            "This address does not appear to be in Gujarat. "
            "SiteScore currently covers Ahmedabad, Surat, Vadodara, "
            "and Rajkot only. Please include your city name."
        )

    return True, "Valid"


# ════════════════════════════════════════════════════════════
# CACHED WRAPPERS — each returns (score, data, used_fallback: bool)
# ════════════════════════════════════════════════════════════

def cached_geocode(address: str) -> Tuple[Any, Any, bool]:
    key = address_key(address)
    hit = cache_get(key, max_age_days=TTL_GEOCODE)
    if hit is not None:
        return hit.get("lat"), hit.get("lng"), hit.get("used_fallback", False)

    res = api_clients.geocode_address(address)
    if not res.ok:
        logger.warning("Geocoding failed for %r: %s", address, res.error)
        return None, None, True

    lat, lng = res.data["lat"], res.data["lng"]
    cache_set(key, {"lat": lat, "lng": lng, "used_fallback": False})
    return lat, lng, False


def cached_demand(
    lat: float, lng: float, brand_type: str = "restaurant"
) -> Tuple[float, Dict[str, Any], bool]:
    key = f"{grid_key(lat, lng)}:demand:{brand_type}"
    hit = cache_get(key, max_age_days=TTL_DEMAND)
    if hit is not None:
        return hit["score"], hit["data"], hit.get("used_fallback", False)

    score, data, fallback = score_demand(lat, lng, brand_type)
    cache_set(key, {"score": score, "data": data, "used_fallback": fallback})
    return score, data, fallback


def cached_footfall(
    lat: float, lng: float, brand_type: str = "restaurant"
) -> Tuple[float, Dict[str, int], bool]:
    key = f"{grid_key(lat, lng)}:footfall:{brand_type}"
    hit = cache_get(key, max_age_days=TTL_FOOTFALL)
    if hit is not None:
        return hit["score"], hit["data"], hit.get("used_fallback", False)

    score, data, fallback = score_footfall(lat, lng, brand_type)
    cache_set(key, {"score": score, "data": data, "used_fallback": fallback})
    return score, data, fallback


def cached_competition(
    lat: float, lng: float, brand_type: str = "restaurant"
) -> Tuple[float, List[Dict[str, Any]], bool]:
    key = f"{grid_key(lat, lng)}:competition:{brand_type}"
    hit = cache_get(key, max_age_days=TTL_COMPETITION)
    if hit is not None:
        return hit["score"], hit["data"], hit.get("used_fallback", False)

    score, data, fallback = score_competition(lat, lng, brand_type)
    cache_set(key, {"score": score, "data": data, "used_fallback": fallback})
    return score, data, fallback


def cached_accessibility(lat: float, lng: float) -> Tuple[float, Dict[str, int], bool]:
    key = f"{grid_key(lat, lng)}:accessibility"
    hit = cache_get(key, max_age_days=TTL_ACCESSIBILITY)
    if hit is not None:
        return hit["score"], hit["data"], hit.get("used_fallback", False)

    score, data, fallback = score_accessibility(lat, lng)
    cache_set(key, {"score": score, "data": data, "used_fallback": fallback})
    return score, data, fallback


def cached_catchment(lat: float, lng: float) -> Tuple[float, int, bool]:
    key = f"{grid_key(lat, lng)}:catchment"
    hit = cache_get(key, max_age_days=TTL_CATCHMENT)
    if hit is not None:
        return hit["score"], hit["data"], hit.get("used_fallback", False)

    score, data, fallback = score_catchment(lat, lng)
    cache_set(key, {"score": score, "data": data, "used_fallback": fallback})
    return score, data, fallback


def cached_spending(lat: float, lng: float) -> Tuple[float, Dict[str, Any], bool]:
    key = f"{grid_key(lat, lng)}:spending"
    hit = cache_get(key, max_age_days=TTL_SPENDING)
    if hit is not None:
        return hit["score"], hit["data"], hit.get("used_fallback", False)

    score, data, fallback = score_spending_power(lat, lng)
    cache_set(key, {"score": score, "data": data, "used_fallback": fallback})
    return score, data, fallback


# ════════════════════════════════════════════════════════════
# SCORING FUNCTIONS — pure(ish) logic, calling api_clients for data.
# Each returns (score, data, used_fallback: bool) — used_fallback=True
# means the API failed/was unavailable and a guessed default was used
# instead of real data. This is what powers the data_quality badge.
# ════════════════════════════════════════════════════════════

def score_demand(
    lat: float, lng: float, brand_type: str = "restaurant"
) -> Tuple[float, Dict[str, Any], bool]:
    used_fallback = False

    # ── Residential score (40%) — Census 2011 ward data ──────
    pop_score, pop_data = score_population(lat, lng)

    if pop_data["estimated_population"] == 0:
        building_res = api_clients.get_osm_buildings(lat, lng, dist=1000)
        if building_res.ok:
            count = building_res.data["count"]
            pop_score = round(min(count / 200 * 100, 100), 1)
            pop_data = {"method": "osm_buildings", "count": count,
                        "population": 0, "households": 0}
        else:
            used_fallback = True
            pop_score = 30.0
            pop_data = {"method": "fallback", "population": 0, "households": 0}
    else:
        pop_data["method"] = "census_2011"

    # ── Daytime signals score (60%) ───────────────────────────
    daytime_score = 0.0
    daytime_found: Dict[str, int] = {}

    if api_clients.is_gmaps_available():
        from config import DAYTIME_DEMAND_SIGNALS, BRAND_DEMAND_SIGNALS
        signals = BRAND_DEMAND_SIGNALS.get(brand_type, DAYTIME_DEMAND_SIGNALS)
        seen_ids: set = set()
        total_weighted = 0.0
        signal_failures = 0

        for signal in signals:
            res = api_clients.places_nearby(
                lat, lng, radius=1000,
                place_type=signal.get("type"), keyword=signal.get("keyword"),
            )
            if not res.ok:
                signal_failures += 1
                continue

            new_places = [p for p in res.data if p.get("place_id") not in seen_ids]
            for p in new_places:
                seen_ids.add(p.get("place_id"))

            if new_places:
                label = signal.get("type") or signal.get("keyword", "")[:20]
                count = len(new_places)
                daytime_found[label] = count
                contribution = min(count, 5) * signal["weight"]
                total_weighted += contribution

        if signals and signal_failures == len(signals):
            used_fallback = True

        daytime_score = round(min(total_weighted / 50 * 100, 100), 1)
    else:
        used_fallback = True
        daytime_score = pop_score  # fall back to residential only

    combined = round(pop_score * 0.40 + daytime_score * 0.60, 1)

    return combined, {
        "method":         pop_data.get("method", "census_2011"),
        "population":     pop_data.get("estimated_population", pop_data.get("population", 0)),
        "households":     pop_data.get("estimated_households", pop_data.get("households", 0)),
        "wards":          pop_data.get("contributing_wards", pop_data.get("wards", [])),
        "residential_score": pop_score,
        "daytime_score":     daytime_score,
        "daytime_signals":   daytime_found,
    }, used_fallback


def score_footfall(
    lat: float, lng: float, brand_type: str = "restaurant"
) -> Tuple[float, Dict[str, int], bool]:
    if not api_clients.is_gmaps_available():
        return 50.0, {}, True

    anchors = FOOTFALL_ANCHORS.get(brand_type, FOOTFALL_ANCHORS["restaurant"])
    total = 0
    found: Dict[str, int] = {}
    failures = 0

    for anchor in anchors:
        res = api_clients.places_nearby(lat, lng, radius=500, place_type=anchor)
        if not res.ok:
            failures += 1
            continue
        count = len(res.data)
        if count > 0:
            found[anchor] = count
        total += count

    used_fallback = bool(anchors) and failures == len(anchors)
    return round(min(total / 10 * 100, 100), 1), found, used_fallback


def score_competition(
    lat: float, lng: float, brand_type: str = "restaurant"
) -> Tuple[float, List[Dict[str, Any]], bool]:
    if not api_clients.is_gmaps_available():
        return 50.0, [], True

    import math
    from config import COMPETITION_QUERIES

    queries = COMPETITION_QUERIES.get(brand_type, COMPETITION_QUERIES["restaurant"])
    result = api_clients.places_nearby_multi(lat, lng, radius=500, queries=queries)

    if not result.ok:
        return 50.0, [], True

    all_places = result.data
    used_fallback = result.error is not None  # partial failures noted but not fatal

    if not all_places:
        return 100.0, [], used_fallback

    weighted_pressure = 0.0
    competitor_details: List[Dict[str, Any]] = []

    for place in all_places:
        review_count = place.get("user_ratings_total", 0)
        rating       = place.get("rating", 3.0)
        name         = place.get("name", "Unknown")

        review_weight = (
            min(math.log10(review_count) / 3.0, 1.0)
            if review_count > 0 else 0.05
        )
        rating_weight  = rating / 5.0
        brand_strength = review_weight * 0.7 + rating_weight * 0.3

        location  = place.get("geometry", {}).get("location", {})
        place_lat = location.get("lat", lat)
        place_lng = location.get("lng", lng)

        R    = 6371000
        dlat = math.radians(place_lat - lat)
        dlng = math.radians(place_lng - lng)
        a    = (math.sin(dlat / 2) ** 2 +
                math.cos(math.radians(lat)) *
                math.cos(math.radians(place_lat)) *
                math.sin(dlng / 2) ** 2)
        distance_m = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if distance_m <= 100:
            distance_weight = 1.0
        elif distance_m <= 250:
            distance_weight = 0.7
        elif distance_m <= 400:
            distance_weight = 0.4
        else:
            distance_weight = 0.2

        pressure = brand_strength * distance_weight
        weighted_pressure += pressure

        competitor_details.append({
            "name":            name,
            "reviews":         review_count,
            "rating":          rating,
            "distance_m":      round(distance_m),
            "brand_strength":  round(brand_strength, 2),
            "distance_weight": distance_weight,
            "strength":        round(pressure, 2),
        })

    competitor_details.sort(key=lambda x: x["strength"], reverse=True)
    score = max(100.0 - (weighted_pressure / 10 * 100), 0.0)
    return round(score, 1), competitor_details, used_fallback


def score_accessibility(lat: float, lng: float) -> Tuple[float, Dict[str, int], bool]:
    res = api_clients.get_road_network(lat, lng, dist=300)
    if not res.ok:
        return 40.0, {"intersections": 0, "total_nodes": 0}, True

    intersections = res.data["intersections"]
    total_nodes = res.data["total_nodes"]
    return round(min(intersections / 15 * 100, 100), 1), {
        "intersections": intersections,
        "total_nodes": total_nodes,
    }, False


def score_catchment(lat: float, lng: float) -> Tuple[float, int, bool]:
    if not api_clients.is_gmaps_available():
        return 30.0, 0, True

    res = api_clients.places_nearby(lat, lng, radius=1000, keyword="cafe restaurant shop")
    if not res.ok:
        return 30.0, 0, True

    count = len(res.data)
    return round(min(count / 20 * 100, 100), 1), count, False


def score_spending_power(lat: float, lng: float) -> Tuple[float, Dict[str, Any], bool]:
    if not api_clients.is_gmaps_available():
        return 50.0, {"avg_price_level": None, "sample_size": 0}, True

    res = api_clients.places_nearby(lat, lng, radius=1000, keyword="restaurant cafe shop hotel")
    if not res.ok:
        return 50.0, {"avg_price_level": None, "sample_size": 0}, True

    places = res.data
    if not places:
        return 50.0, {"avg_price_level": None, "sample_size": 0}, False

    price_levels = [p["price_level"] for p in places if "price_level" in p]
    if not price_levels:
        # Not a failure — just no price data published for these places.
        return 50.0, {"avg_price_level": None, "sample_size": 0}, False

    avg = sum(price_levels) / len(price_levels)
    score = round(min(avg / 4 * 100, 100), 1)

    return score, {
        "avg_price_level": round(avg, 2),
        "sample_size": len(price_levels),
        "distribution": {
            "budget (0-1)": sum(1 for p in price_levels if p <= 1),
            "moderate (2)": sum(1 for p in price_levels if p == 2),
            "premium (3-4)": sum(1 for p in price_levels if p >= 3),
        },
    }, False


# ════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════

def score_site(address: str, brand_type: str = "restaurant") -> Dict[str, Any]:
    is_valid, message = validate_address(address)
    if not is_valid:
        return {"error": message}

    lat, lng, geo_fallback = cached_geocode(address)
    if not lat:
        return {
            "error": (
                "Could not find this address in Gujarat. "
                "Try adding area name and city — "
                "e.g. 'Bopal, Ahmedabad, Gujarat'."
            )
        }

    demand_score, demand_data, demand_fb           = cached_demand(lat, lng, brand_type)
    footfall_score, footfall_found, footfall_fb     = cached_footfall(lat, lng, brand_type)
    competition_score, competitor_details, comp_fb  = cached_competition(lat, lng, brand_type)
    access_score, access_data, access_fb            = cached_accessibility(lat, lng)
    catchment_score, catchment_count, catchment_fb  = cached_catchment(lat, lng)
    spending_score, spending_data, spending_fb       = cached_spending(lat, lng)

    scores = {
        "demand": demand_score,
        "footfall": footfall_score,
        "competition": competition_score,
        "accessibility": access_score,
        "catchment": catchment_score,
        "spending_power": spending_score,
    }

    total = sum(scores[k] * WEIGHTS[k] for k in scores)
    verdict = (
        "Strong" if total >= VERDICT_THRESHOLDS["strong"]
        else "Moderate" if total >= VERDICT_THRESHOLDS["moderate"]
        else "Weak"
    )

    # ── Aggregate data quality — surfaced to the user in score_panel.py
    fallback_map = {
        "demand": demand_fb,
        "footfall": footfall_fb,
        "competition": comp_fb,
        "accessibility": access_fb,
        "catchment": catchment_fb,
        "spending_power": spending_fb,
    }
    failed_signals = [k for k, v in fallback_map.items() if v]
    if failed_signals:
        logger.warning(
            "score_site: %s used fallback data for signals: %s",
            address, failed_signals,
        )

    return {
        "address": address,
        "lat": lat,
        "lng": lng,
        "brand_type": brand_type,
        "scores": scores,
        "total_score": round(total, 1),
        "verdict": verdict,
        "competitor_details": competitor_details,
        "data_quality": {
            "had_fallback": len(failed_signals) > 0,
            "failed_signals": failed_signals,
        },
        "raw": {
            "demand_buildings":        demand_data.get("count", 0),
            "demand_population":       demand_data.get("population", 0),
            "demand_households":       demand_data.get("households", 0),
            "demand_method":           demand_data.get("method", "unknown"),
            "demand_wards":            demand_data.get("wards", []),
            "demand_residential_score": demand_data.get("residential_score", 0),
            "demand_daytime_score":    demand_data.get("daytime_score", 0),
            "demand_daytime_signals":  demand_data.get("daytime_signals", {}),
            "footfall_anchors": footfall_found,
            "intersections": access_data["intersections"],
            "road_nodes": access_data["total_nodes"],
            "catchment_places": catchment_count,
            "competitor_count": len(competitor_details),
            "spending_data": spending_data,
        },
    }
