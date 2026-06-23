from __future__ import annotations
from typing import Dict, List

# Known brands per type with threat level
# threat: "high" = major national/international chain
#         "medium" = strong regional chain  
#         "low" = local chain
KNOWN_BRANDS: Dict[str, List[Dict]] = {
    "restaurant": [
        {"name": "McDonald's",   "threat": "high"},
        {"name": "Domino's",     "threat": "high"},
        {"name": "KFC",          "threat": "high"},
        {"name": "Pizza Hut",    "threat": "high"},
        {"name": "Burger King",  "threat": "high"},
        {"name": "Subway",       "threat": "high"},
        {"name": "Wow Momo",     "threat": "medium"},
        {"name": "Barbeque Nation", "threat": "medium"},
        {"name": "Haldiram",     "threat": "medium"},
        {"name": "Cafe Coffee Day", "threat": "medium"},
        {"name": "Starbucks",    "threat": "high"},
        {"name": "Chaayos",      "threat": "medium"},
        {"name": "Biryani By Kilo", "threat": "medium"},
        {"name": "Faasos",       "threat": "medium"},
        {"name": "Behrouz",      "threat": "medium"},
        {"name": "Box8",         "threat": "low"},
        {"name": "Jumboking",    "threat": "low"},
        {"name": "Goli Vada Pav","threat": "low"},
    ],
    "pharmacy": [
        {"name": "Apollo Pharmacy", "threat": "high"},
        {"name": "MedPlus",         "threat": "high"},
        {"name": "Wellness Forever","threat": "high"},
        {"name": "Netmeds",         "threat": "medium"},
        {"name": "1mg",             "threat": "medium"},
        {"name": "Guardian Pharmacy","threat": "medium"},
        {"name": "Frank Ross",      "threat": "low"},
    ],
    "supermarket": [
        {"name": "DMart",           "threat": "high"},
        {"name": "D-Mart",          "threat": "high"},
        {"name": "Reliance Smart",  "threat": "high"},
        {"name": "Reliance Fresh",  "threat": "high"},
        {"name": "Big Bazaar",      "threat": "high"},
        {"name": "Star Bazaar",     "threat": "high"},
        {"name": "Vishal Mega Mart","threat": "medium"},
        {"name": "More Supermarket","threat": "medium"},
        {"name": "Spencer's",       "threat": "medium"},
        {"name": "V-Mart",          "threat": "medium"},
        {"name": "Lots Wholesale",  "threat": "medium"},
    ],
    "bank": [
        {"name": "SBI",             "threat": "high"},
        {"name": "HDFC Bank",       "threat": "high"},
        {"name": "ICICI Bank",      "threat": "high"},
        {"name": "Axis Bank",       "threat": "high"},
        {"name": "Kotak Mahindra",  "threat": "high"},
        {"name": "Bank of Baroda",  "threat": "high"},
        {"name": "Punjab National", "threat": "high"},
        {"name": "Yes Bank",        "threat": "medium"},
        {"name": "IndusInd Bank",   "threat": "medium"},
        {"name": "Federal Bank",    "threat": "medium"},
        {"name": "Union Bank",      "threat": "medium"},
        {"name": "Canara Bank",     "threat": "medium"},
    ],
    "school": [
        {"name": "Podar",           "threat": "high"},
        {"name": "Eurokids",        "threat": "high"},
        {"name": "Kidzee",          "threat": "high"},
        {"name": "VIBGYOR",         "threat": "high"},
        {"name": "Ryan International","threat": "high"},
        {"name": "Bachpan",         "threat": "medium"},
        {"name": "Smartkids",       "threat": "medium"},
        {"name": "Little Millennium","threat": "medium"},
    ],
    "clothing": [
        {"name": "Zudio",           "threat": "high"},
        {"name": "Westside",        "threat": "high"},
        {"name": "Pantaloons",      "threat": "high"},
        {"name": "Max Fashion",     "threat": "high"},
        {"name": "Manyavar",        "threat": "high"},
        {"name": "Trends",          "threat": "high"},
        {"name": "H&M",             "threat": "high"},
        {"name": "Zara",            "threat": "high"},
        {"name": "FBB",             "threat": "medium"},
        {"name": "V-Mart",          "threat": "medium"},
        {"name": "Lenskart",        "threat": "medium"},
        {"name": "Titan",           "threat": "medium"},
        {"name": "Woodland",        "threat": "medium"},
        {"name": "Nike",            "threat": "high"},
        {"name": "Puma",            "threat": "high"},
        {"name": "Adidas",          "threat": "high"},
        {"name": "Bata",            "threat": "medium"},
        {"name": "Relaxo",          "threat": "low"},
    ],
    "beauty": [
        {"name": "Lakme",           "threat": "high"},
        {"name": "Nykaa",           "threat": "high"},
        {"name": "VLCC",            "threat": "high"},
        {"name": "Naturals",        "threat": "high"},
        {"name": "Jawed Habib",     "threat": "high"},
        {"name": "Enrich",          "threat": "high"},
        {"name": "YLG",             "threat": "medium"},
        {"name": "Green Trends",    "threat": "medium"},
        {"name": "Toni & Guy",      "threat": "medium"},
        {"name": "Looks Salon",     "threat": "medium"},
        {"name": "Bodycraft",       "threat": "medium"},
    ],
    "healthcare": [
        {"name": "Apollo",          "threat": "high"},
        {"name": "Fortis",          "threat": "high"},
        {"name": "Medanta",         "threat": "high"},
        {"name": "Max Hospital",    "threat": "high"},
        {"name": "Manipal",         "threat": "high"},
        {"name": "Sterling Hospital","threat": "high"},
        {"name": "HCG",             "threat": "high"},
        {"name": "Care Hospital",   "threat": "medium"},
        {"name": "Thyrocare",       "threat": "medium"},
        {"name": "Dr Lal PathLabs","threat": "medium"},
        {"name": "SRL Diagnostics", "threat": "medium"},
        {"name": "Patanjali",       "threat": "medium"},
    ],
    "fitness": [
        {"name": "Cult.fit",        "threat": "high"},
        {"name": "Gold's Gym",      "threat": "high"},
        {"name": "Anytime Fitness", "threat": "high"},
        {"name": "Snap Fitness",    "threat": "medium"},
        {"name": "Talwalkars",      "threat": "high"},
        {"name": "Fitness First",   "threat": "medium"},
        {"name": "CrossFit",        "threat": "medium"},
        {"name": "Sarva Yoga",      "threat": "medium"},
        {"name": "Cure.fit",        "threat": "medium"},
    ],
    "education": [
        {"name": "BYJU'S",          "threat": "high"},
        {"name": "Vedantu",         "threat": "high"},
        {"name": "Aakash",          "threat": "high"},
        {"name": "FIITJEE",         "threat": "high"},
        {"name": "Allen",           "threat": "high"},
        {"name": "Resonance",       "threat": "high"},
        {"name": "Unacademy",       "threat": "medium"},
        {"name": "Aptech",          "threat": "medium"},
        {"name": "NIIT",            "threat": "medium"},
        {"name": "Amul",            "threat": "low"},
    ],
    "hardware": [
        {"name": "Mr DIY",          "threat": "high"},
        {"name": "Asian Paints",    "threat": "high"},
        {"name": "Berger Paints",   "threat": "high"},
        {"name": "Godrej Interio",  "threat": "high"},
        {"name": "IKEA",            "threat": "high"},
        {"name": "Home Centre",     "threat": "high"},
        {"name": "Nilkamal",        "threat": "medium"},
        {"name": "Pepperfry",       "threat": "medium"},
        {"name": "Havells",         "threat": "medium"},
        {"name": "Anchor",          "threat": "low"},
        {"name": "Philips",         "threat": "medium"},
    ],
    "cinema": [
        {"name": "PVR",             "threat": "high"},
        {"name": "INOX",            "threat": "high"},
        {"name": "Cinepolis",       "threat": "high"},
        {"name": "Carnival",        "threat": "medium"},
        {"name": "Miraj",           "threat": "medium"},
        {"name": "SPI Cinemas",     "threat": "medium"},
        {"name": "Mukta A2",        "threat": "low"},
    ],
    "automotive": [
        {"name": "Maruti Suzuki",   "threat": "high"},
        {"name": "Hyundai",         "threat": "high"},
        {"name": "Tata Motors",     "threat": "high"},
        {"name": "Honda",           "threat": "high"},
        {"name": "Toyota",          "threat": "high"},
        {"name": "Mahindra",        "threat": "high"},
        {"name": "Hero MotoCorp",   "threat": "high"},
        {"name": "Bajaj",           "threat": "high"},
        {"name": "TVS",             "threat": "high"},
        {"name": "Royal Enfield",   "threat": "high"},
        {"name": "Ather",           "threat": "medium"},
        {"name": "Ola Electric",    "threat": "medium"},
        {"name": "CEAT",            "threat": "medium"},
        {"name": "MRF",             "threat": "medium"},
        {"name": "Apollo Tyres",    "threat": "medium"},
        {"name": "3M",              "threat": "medium"},
        {"name": "Bosch",           "threat": "medium"},
    ],
}


def _name_matches(place_name: str, brand_name: str) -> bool:
    """
    Fuzzy match — checks if brand name words appear in place name.
    Handles variations like DMart/D-Mart/D Mart,
    Domino's/Dominos, McDonald's/McDonalds etc.
    """
    # Normalize both — remove punctuation, lowercase
    import re
    def normalize(s):
        return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()

    place_norm = normalize(place_name)
    brand_norm = normalize(brand_name)

    # Direct substring match after normalization
    if brand_norm in place_norm:
        return True

    # Word-level match — all significant words of brand must appear
    brand_words = [w for w in brand_norm.split() if len(w) > 2]
    if brand_words and all(w in place_norm for w in brand_words):
        return True

    return False


def detect_known_brands(
    competitor_details: list,
    brand_type: str,
) -> list:
    """
    Scans competitor list and flags known brands.
    Returns list of detected known brands with threat level.
    """
    known = KNOWN_BRANDS.get(brand_type, [])
    detected = []
    seen_brands = set()

    for comp in competitor_details:
        place_name = comp.get("name", "")
        for brand in known:
            if (brand["name"] not in seen_brands and
                    _name_matches(place_name, brand["name"])):
                seen_brands.add(brand["name"])
                detected.append({
                    "brand":      brand["name"],
                    "threat":     brand["threat"],
                    "distance_m": comp.get("distance_m", 0),
                    "strength":   comp.get("strength", 0),
                    "reviews":    comp.get("reviews", 0),
                    "rating":     comp.get("rating", 0),
                })

    # Sort by threat level then distance
    threat_order = {"high": 0, "medium": 1, "low": 2}
    detected.sort(key=lambda x: (
        threat_order.get(x["threat"], 3),
        x["distance_m"]
    ))
    return detected