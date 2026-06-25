from __future__ import annotations
from typing import Dict, Tuple


# Rent benchmarks for Gujarat retail market
# Based on market knowledge — Rs. per sq ft per month
# Ranges: (min, typical, max) in Rs. per month for standard unit sizes
# Restaurant: ~300-500 sqft | Pharmacy: ~200-300 sqft
# Supermarket: ~2000-5000 sqft | Bank: ~500-1000 sqft
# School: ~2000-5000 sqft | Clothing: ~500-1000 sqft
# Beauty: ~200-400 sqft | Healthcare: ~300-600 sqft
# Fitness: ~2000-4000 sqft | Education: ~500-2000 sqft
# Hardware: ~1000-3000 sqft | Cinema: ~10000-30000 sqft
# Automotive: ~2000-5000 sqft

# Structure: area_type -> brand_type -> (min, typical, max) in Rs./month
RENT_BENCHMARKS: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    "mall": {
        "restaurant":  (80000,  150000, 300000),
        "pharmacy":    (60000,  100000, 200000),
        "supermarket": (300000, 600000, 1200000),
        "bank":        (100000, 200000, 400000),
        "school":      (200000, 400000, 800000),
        "clothing":    (100000, 200000, 500000),
        "beauty":      (60000,  120000, 250000),
        "healthcare":  (80000,  150000, 300000),
        "fitness":     (200000, 400000, 800000),
        "education":   (100000, 200000, 400000),
        "hardware":    (150000, 300000, 600000),
        "cinema":      (800000, 1500000, 3000000),
        "automotive":  (200000, 400000, 800000),
    },
    "high_street": {
        "restaurant":  (50000,  90000,  180000),
        "pharmacy":    (40000,  70000,  140000),
        "supermarket": (150000, 300000, 600000),
        "bank":        (80000,  150000, 300000),
        "school":      (100000, 200000, 400000),
        "clothing":    (60000,  120000, 250000),
        "beauty":      (40000,  75000,  150000),
        "healthcare":  (50000,  100000, 200000),
        "fitness":     (100000, 200000, 400000),
        "education":   (60000,  120000, 250000),
        "hardware":    (80000,  160000, 320000),
        "cinema":      (500000, 1000000, 2000000),
        "automotive":  (100000, 200000, 400000),
    },
    "residential": {
        "restaurant":  (25000,  50000,  100000),
        "pharmacy":    (20000,  40000,  80000),
        "supermarket": (60000,  120000, 250000),
        "bank":        (40000,  80000,  160000),
        "school":      (60000,  120000, 250000),
        "clothing":    (30000,  60000,  120000),
        "beauty":      (20000,  40000,  80000),
        "healthcare":  (25000,  50000,  100000),
        "fitness":     (50000,  100000, 200000),
        "education":   (30000,  60000,  120000),
        "hardware":    (40000,  80000,  160000),
        "cinema":      (200000, 400000, 800000),
        "automotive":  (50000,  100000, 200000),
    },
    "highway": {
        "restaurant":  (40000,  80000,  160000),
        "pharmacy":    (30000,  60000,  120000),
        "supermarket": (100000, 200000, 400000),
        "bank":        (50000,  100000, 200000),
        "school":      (80000,  160000, 320000),
        "clothing":    (40000,  80000,  160000),
        "beauty":      (25000,  50000,  100000),
        "healthcare":  (40000,  80000,  160000),
        "fitness":     (80000,  160000, 320000),
        "education":   (50000,  100000, 200000),
        "hardware":    (80000,  160000, 320000),
        "cinema":      (400000, 800000, 1600000),
        "automotive":  (80000,  160000, 320000),
    },
    "commercial": {
        "restaurant":  (40000,  80000,  160000),
        "pharmacy":    (35000,  65000,  130000),
        "supermarket": (120000, 250000, 500000),
        "bank":        (70000,  140000, 280000),
        "school":      (80000,  160000, 320000),
        "clothing":    (50000,  100000, 200000),
        "beauty":      (35000,  70000,  140000),
        "healthcare":  (45000,  90000,  180000),
        "fitness":     (80000,  160000, 320000),
        "education":   (50000,  100000, 200000),
        "hardware":    (70000,  140000, 280000),
        "cinema":      (400000, 800000, 1600000),
        "automotive":  (80000,  160000, 320000),
    },
    "suburban": {
        "restaurant":  (20000,  40000,  80000),
        "pharmacy":    (15000,  30000,  60000),
        "supermarket": (50000,  100000, 200000),
        "bank":        (30000,  60000,  120000),
        "school":      (50000,  100000, 200000),
        "clothing":    (25000,  50000,  100000),
        "beauty":      (15000,  30000,  60000),
        "healthcare":  (20000,  40000,  80000),
        "fitness":     (40000,  80000,  160000),
        "education":   (25000,  50000,  100000),
        "hardware":    (35000,  70000,  140000),
        "cinema":      (150000, 300000, 600000),
        "automotive":  (40000,  80000,  160000),
    },
    "industrial": {
        "restaurant":  (15000,  30000,  60000),
        "pharmacy":    (12000,  25000,  50000),
        "supermarket": (40000,  80000,  160000),
        "bank":        (25000,  50000,  100000),
        "school":      (40000,  80000,  160000),
        "clothing":    (20000,  40000,  80000),
        "beauty":      (12000,  25000,  50000),
        "healthcare":  (18000,  35000,  70000),
        "fitness":     (35000,  70000,  140000),
        "education":   (20000,  40000,  80000),
        "hardware":    (30000,  60000,  120000),
        "cinema":      (100000, 200000, 400000),
        "automotive":  (35000,  70000,  140000),
    },
}

# City multipliers — Ahmedabad = base 1.0
CITY_MULTIPLIERS: Dict[str, float] = {
    "ahmedabad": 1.0,
    "surat":     0.85,
    "vadodara":  0.75,
    "baroda":    0.75,
    "rajkot":    0.70,
    "gandhinagar": 0.80,
    "anand":     0.65,
    "mehsana":   0.60,
    "bharuch":   0.65,
    "bhavnagar": 0.60,
    "jamnagar":  0.60,
    "junagadh":  0.55,
    "nadiad":    0.60,
    "morbi":     0.55,
    "palanpur":  0.50,
    "gandhidham":0.65,
    "bhuj":      0.55,
}


def _detect_area_type(scores: Dict[str, float]) -> str:
    """
    Detect area type from scoring signals.
    Uses catchment, footfall, spending power to classify.
    """
    catchment     = scores.get("catchment", 50)
    footfall      = scores.get("footfall", 50)
    spending      = scores.get("spending_power", 50)
    accessibility = scores.get("accessibility", 50)

    if catchment >= 80 and footfall >= 80:
        return "mall"
    elif catchment >= 65 and accessibility >= 75:
        return "high_street"
    elif spending >= 55 and catchment >= 55:
        return "commercial"
    elif accessibility >= 80 and catchment < 50:
        return "highway"
    elif catchment >= 50 and footfall >= 50:
        return "residential"
    elif catchment >= 35:
        return "suburban"
    else:
        return "industrial"


def _detect_city(address: str) -> str:
    """Detect city from address string."""
    addr_lower = address.lower()
    for city in CITY_MULTIPLIERS:
        if city in addr_lower:
            return city
    return "ahmedabad"  # default


def get_rent_benchmark(
    address: str,
    brand_type: str,
    scores: Dict[str, float],
) -> Dict:
    """
    Returns rent benchmark for a given address + brand type.
    Detects area type from scores, applies city multiplier.
    """
    area_type  = _detect_area_type(scores)
    city       = _detect_city(address)
    multiplier = CITY_MULTIPLIERS.get(city, 0.70)

    area_rents = RENT_BENCHMARKS.get(
        area_type, RENT_BENCHMARKS["residential"]
    )
    base = area_rents.get(
        brand_type, area_rents.get("restaurant", (30000, 60000, 120000))
    )

    rent_min     = round(base[0] * multiplier / 1000) * 1000
    rent_typical = round(base[1] * multiplier / 1000) * 1000
    rent_max     = round(base[2] * multiplier / 1000) * 1000

    return {
        "area_type":    area_type,
        "city":         city,
        "multiplier":   multiplier,
        "rent_min":     rent_min,
        "rent_typical": rent_typical,
        "rent_max":     rent_max,
        "brand_type":   brand_type,
    }