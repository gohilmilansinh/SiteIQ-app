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
        "supermarket",
        "hospital",
        "school",
        "bus_station",
        "bank",
        "subway_station",
    ],
    "pharmacy": [
        "hospital",
        "doctor",
        "clinic",
        "residential",
        "bus_station",
        "bank",
    ],
    "supermarket": [
        "residential_area",
        "bus_station",
        "school",
        "bank",
        "pharmacy",
    ],
    "bank": [
        "supermarket",
        "office",
        "hospital",
        "bus_station",
        "school",
    ],
    "school": [
        "residential_area",
        "bus_station",
        "park",
        "library",
        "supermarket",
    ],
}

BRAND_KEYWORDS: Dict[str, str] = {
    "restaurant": "fast food burger pizza QSR cafe restaurant",
    "pharmacy": "pharmacy chemist medical store drugstore",
    "supermarket": "supermarket grocery kirana departmental store",
    "bank": "bank ATM financial services",
    "school": "school coaching institute tuition academy",
}

# All Place types + keywords to query per brand type for competition
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
    ],
    "supermarket": [
        {"type": "supermarket", "keyword": None},
        {"type": "grocery_or_supermarket", "keyword": None},
        {"type": None,          "keyword": "dmart reliance big bazaar kirana"},
    ],
    "bank": [
        {"type": "bank",        "keyword": None},
        {"type": "atm",         "keyword": None},
    ],
    "school": [
        {"type": "school",      "keyword": None},
        {"type": None,          "keyword": "coaching tuition academy classes"},
    ],
}

VERDICT_THRESHOLDS: Dict[str, float] = {
    "strong": 65.0,
    "moderate": 45.0,
}

# Daytime demand signals — place types + weights
# Higher weight = stronger demand generator
DAYTIME_DEMAND_SIGNALS: List[Dict] = [
    # Education — students generate massive consistent daytime footfall
    {"type": "university",       "keyword": None,                        "weight": 3.0},
    {"type": "school",           "keyword": None,                        "weight": 1.5},
    {"type": None,               "keyword": "college institute polytechnic", "weight": 2.5},
    {"type": None,               "keyword": "coaching tuition classes academy", "weight": 1.5},

    # Office / commercial — working population
    {"type": "office",           "keyword": None,                        "weight": 1.5},
    {"type": None,               "keyword": "office complex business park IT park", "weight": 2.0},

    # Transit — people passing through
    {"type": "bus_station",      "keyword": None,                        "weight": 2.0},
    {"type": "transit_station",  "keyword": None,                        "weight": 2.0},
    {"type": None,               "keyword": "BRTS AMTS bus stop",        "weight": 1.5},

    # Attractions — people come here intentionally
    {"type": "hospital",         "keyword": None,                        "weight": 1.5},
    {"type": "park",             "keyword": None,                        "weight": 1.0},
    {"type": None,               "keyword": "market bazaar shopping complex", "weight": 1.5},
    {"type": "tourist_attraction","keyword": None,                       "weight": 1.0},
    {"type": None,               "keyword": "temple mandir masjid church", "weight": 0.8},
]
