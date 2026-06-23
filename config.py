from __future__ import annotations

from typing import Dict, List

SUPPORTED_CITIES: List[str] = [
    "ahmedabad",
    "surat",
    "vadodara",
    "baroda",
    "rajkot",
    "gandhinagar",
    "anand",
    "mehsana",
    "bharuch",
    "bhavnagar",
    "jamnagar",
    "junagadh",
    "gujarat",
    "gj",
]

WEIGHTS: Dict[str, float] = {
    "demand": 0.20,
    "footfall": 0.20,
    "competition": 0.20,
    "accessibility": 0.15,
    "catchment": 0.10,
    "spending_power": 0.15,
}

FOOTFALL_ANCHORS: Dict[str, List[str]] = {
    "restaurant": [
        "supermarket", "hospital", "school",
        "bus_station", "bank", "subway_station",
    ],
    "pharmacy": [
        "hospital", "doctor", "clinic",
        "residential", "bus_station", "bank",
    ],
    "supermarket": [
        "residential_area", "bus_station", "school",
        "bank", "pharmacy",
    ],
    "bank": [
        "supermarket", "office", "hospital",
        "bus_station", "school",
    ],
    "school": [
        "residential_area", "bus_station", "park",
        "library", "supermarket",
    ],
    "clothing": [
        "shopping_mall", "supermarket", "bus_station",
        "bank", "restaurant",
    ],
    "beauty": [
        "shopping_mall", "supermarket", "gym",
        "restaurant", "bus_station",
    ],
}

BRAND_KEYWORDS: Dict[str, str] = {
    "restaurant":  "fast food burger pizza QSR cafe restaurant",
    "pharmacy":    "pharmacy chemist medical store drugstore",
    "supermarket": "supermarket grocery kirana departmental store",
    "bank":        "bank ATM financial services",
    "school":      "school coaching institute tuition academy",
    "clothing":    "clothing fashion apparel garments boutique",
    "beauty":      "beauty salon parlour cosmetics skincare spa",
}

VERDICT_THRESHOLDS: Dict[str, float] = {
    "strong": 65.0,
    "moderate": 45.0,
}

# ---------- Competition queries per brand type ----------
COMPETITION_QUERIES: Dict[str, List[Dict]] = {
    "restaurant": [
        {"type": "restaurant",  "keyword": None},
        {"type": "cafe",        "keyword": None},
        {"type": "bakery",      "keyword": None},
        {"type": None,          "keyword": "juice shop lassi ice cream"},
        {"type": None,          "keyword": "vadapav chaat frankie puff snacks stall"},
    ],
    "pharmacy": [
        {"type": "pharmacy",    "keyword": None},
        {"type": None,          "keyword": "medical store chemist drugstore"},
        {"type": None,          "keyword": "apollo medplus wellness forever"},
    ],
    "supermarket": [
        {"type": "supermarket", "keyword": None},
        {"type": "grocery_or_supermarket", "keyword": None},
        {"type": None,          "keyword": "dmart reliance big bazaar"},
        {"type": None,          "keyword": "kirana general store provisions"},
    ],
    "bank": [
        {"type": "bank",        "keyword": None},
        {"type": "atm",         "keyword": None},
    ],
    "school": [
        {"type": "school",      "keyword": None},
        {"type": "university",  "keyword": None},
        {"type": None,          "keyword": "coaching tuition academy classes"},
    ],
    "clothing": [
        {"type": None,          "keyword": "clothing fashion apparel garments"},
        {"type": None,          "keyword": "zudio trends westside manyavar max pantaloon"},
        {"type": None,          "keyword": "boutique textile fabric showroom"},
        {"type": None,          "keyword": "shoes footwear nike puma woodland"},
        {"type": None,          "keyword": "accessories belt watch lenskart titan"},
    ],
    "beauty": [
        {"type": "beauty_salon", "keyword": None},
        {"type": "spa",          "keyword": None},
        {"type": None,           "keyword": "parlour salon beauty unisex"},
        {"type": None,           "keyword": "lakme nykaa cosmetics skincare"},
        {"type": None,           "keyword": "nail art tattoo piercing grooming"},
    ],
}

# ---------- Daytime demand signals ----------
DAYTIME_DEMAND_SIGNALS: List[Dict] = [
    {"type": "university",        "keyword": None,                              "weight": 3.0},
    {"type": "school",            "keyword": None,                              "weight": 1.5},
    {"type": None,                "keyword": "college institute polytechnic",   "weight": 2.5},
    {"type": None,                "keyword": "coaching tuition classes academy","weight": 1.5},
    {"type": "office",            "keyword": None,                              "weight": 1.5},
    {"type": None,                "keyword": "office complex business park IT park", "weight": 2.0},
    {"type": "bus_station",       "keyword": None,                              "weight": 2.0},
    {"type": "transit_station",   "keyword": None,                              "weight": 2.0},
    {"type": None,                "keyword": "BRTS AMTS bus stop",              "weight": 1.5},
    {"type": "hospital",          "keyword": None,                              "weight": 1.5},
    {"type": "park",              "keyword": None,                              "weight": 1.0},
    {"type": None,                "keyword": "market bazaar shopping complex",  "weight": 1.5},
    {"type": "tourist_attraction","keyword": None,                              "weight": 1.0},
    {"type": None,                "keyword": "temple mandir masjid church",     "weight": 0.8},
]

# ---------- Demand signals customized per brand type ----------
# Overrides DAYTIME_DEMAND_SIGNALS for specific types
BRAND_DEMAND_SIGNALS: Dict[str, List[Dict]] = {
    "pharmacy": [
        # Residential is primary — sick people live near pharmacies
        {"type": "hospital",     "keyword": None,                          "weight": 3.0},
        {"type": None,           "keyword": "clinic nursing home doctor",  "weight": 2.5},
        {"type": None,           "keyword": "pathology lab diagnostic",    "weight": 2.0},
        {"type": "university",   "keyword": None,                          "weight": 1.0},
        {"type": "school",       "keyword": None,                          "weight": 0.8},
        {"type": "bus_station",  "keyword": None,                          "weight": 1.0},
    ],
    "supermarket": [
        # Residential + transit is primary
        {"type": "bus_station",  "keyword": None,                          "weight": 2.0},
        {"type": "transit_station", "keyword": None,                       "weight": 2.0},
        {"type": "school",       "keyword": None,                          "weight": 1.0},
        {"type": "office",       "keyword": None,                          "weight": 1.5},
        {"type": None,           "keyword": "residential apartments housing", "weight": 1.5},
        {"type": "park",         "keyword": None,                          "weight": 0.8},
    ],
    "clothing": [
        # Mall + high street + young population signals
        {"type": "shopping_mall","keyword": None,                          "weight": 3.0},
        {"type": "university",   "keyword": None,                          "weight": 2.5},
        {"type": None,           "keyword": "college institute",           "weight": 2.0},
        {"type": "bus_station",  "keyword": None,                          "weight": 1.5},
        {"type": None,           "keyword": "multiplex cinema theatre",    "weight": 1.5},
        {"type": "restaurant",   "keyword": None,                          "weight": 1.0},
        {"type": None,           "keyword": "market high street commercial", "weight": 2.0},
    ],
    "beauty": [
        # Residential women + mall + young population
        {"type": "shopping_mall","keyword": None,                          "weight": 2.5},
        {"type": "university",   "keyword": None,                          "weight": 2.0},
        {"type": None,           "keyword": "college institute",           "weight": 1.5},
        {"type": "gym",          "keyword": None,                          "weight": 1.5},
        {"type": None,           "keyword": "residential apartments housing", "weight": 2.0},
        {"type": "bus_station",  "keyword": None,                          "weight": 1.0},
        {"type": None,           "keyword": "office complex working women", "weight": 1.5},
    ],
}