from __future__ import annotations
from typing import Dict, Any

# Revenue benchmarks by brand type (monthly, Gujarat market)
# Based on industry averages — will be replaced with client data
REVENUE_BENCHMARKS = {
    "restaurant": {
        "base_monthly":   250000,   # Rs. 2.5L/month baseline
        "per_score_point": 4500,    # Rs. 4500 per score point above 50
        "setup_cost":     1500000,  # Rs. 15L average setup
    },
    "pharmacy": {
        "base_monthly":   180000,
        "per_score_point": 3200,
        "setup_cost":     800000,
    },
    "supermarket": {
        "base_monthly":   400000,
        "per_score_point": 6000,
        "setup_cost":     3000000,
    },
    "bank": {
        "base_monthly":   300000,
        "per_score_point": 4000,
        "setup_cost":     2000000,
    },
    "school": {
        "base_monthly":   200000,
        "per_score_point": 3000,
        "setup_cost":     2500000,
    },
}

# Rent as % of revenue thresholds
RENT_THRESHOLDS = {
    "excellent": 0.10,   # rent < 10% of revenue = excellent
    "good":      0.15,   # rent < 15% = good
    "moderate":  0.20,   # rent < 20% = acceptable
    "high":      0.30,   # rent < 30% = risky
    # above 30% = not viable
}


def estimate_monthly_revenue(
    total_score: float,
    brand_type: str = "restaurant"
) -> float:
    """
    Estimates monthly revenue potential based on site score.
    Uses industry benchmarks — replaced with client data later.
    """
    bench = REVENUE_BENCHMARKS.get(
        brand_type, REVENUE_BENCHMARKS["restaurant"])

    # Revenue scales with score above 50 baseline
    score_above_base = max(0, total_score - 50)
    estimated = (bench["base_monthly"] +
                 score_above_base * bench["per_score_point"])

    # Cap at 3x base for very high scores
    return min(estimated, bench["base_monthly"] * 3)


def calculate_roi(
    total_score:   float,
    monthly_rent:  float,
    brand_type:    str = "restaurant",
    setup_cost:    float | None = None,
) -> Dict[str, Any]:
    """
    Returns full ROI analysis for a site given rent input.
    """
    bench = REVENUE_BENCHMARKS.get(
        brand_type, REVENUE_BENCHMARKS["restaurant"])

    est_revenue  = estimate_monthly_revenue(total_score, brand_type)
    actual_setup = setup_cost or bench["setup_cost"]

    # Core metrics
    rent_pct     = monthly_rent / est_revenue if est_revenue > 0 else 1
    monthly_profit = est_revenue - monthly_rent
    annual_profit  = monthly_profit * 12
    payback_months = (actual_setup / monthly_profit
                      if monthly_profit > 0 else 999)

    # ROI score 0-100
    if rent_pct <= RENT_THRESHOLDS["excellent"]:
        roi_score  = 90 + (10 * (1 - rent_pct /
                                 RENT_THRESHOLDS["excellent"]))
        rent_label = "Excellent"
        rent_color = "#1D9E75"
    elif rent_pct <= RENT_THRESHOLDS["good"]:
        roi_score  = 70 + (20 * (RENT_THRESHOLDS["good"] - rent_pct) /
                           (RENT_THRESHOLDS["good"] -
                            RENT_THRESHOLDS["excellent"]))
        rent_label = "Good"
        rent_color = "#1D9E75"
    elif rent_pct <= RENT_THRESHOLDS["moderate"]:
        roi_score  = 50 + (20 * (RENT_THRESHOLDS["moderate"] - rent_pct) /
                           (RENT_THRESHOLDS["moderate"] -
                            RENT_THRESHOLDS["good"]))
        rent_label = "Acceptable"
        rent_color = "#BA7517"
    elif rent_pct <= RENT_THRESHOLDS["high"]:
        roi_score  = 20 + (30 * (RENT_THRESHOLDS["high"] - rent_pct) /
                           (RENT_THRESHOLDS["high"] -
                            RENT_THRESHOLDS["moderate"]))
        rent_label = "High Risk"
        rent_color = "#C0392B"
    else:
        roi_score  = max(0, 20 - (rent_pct - RENT_THRESHOLDS["high"]) * 100)
        rent_label = "Not Viable"
        rent_color = "#C0392B"

    roi_score = round(min(100, max(0, roi_score)), 1)

    # Combined score: 70% location + 30% ROI
    combined_score = round(total_score * 0.70 + roi_score * 0.30, 1)

    # Final verdict
    if combined_score >= 65 and rent_pct <= RENT_THRESHOLDS["moderate"]:
        verdict     = "Strong Investment"
        verdict_col = "#1D9E75"
        recommend   = "Proceed to lease negotiation"
    elif combined_score >= 50 or rent_pct <= RENT_THRESHOLDS["high"]:
        verdict     = "Conditional Investment"
        verdict_col = "#BA7517"
        recommend   = "Negotiate rent down before committing"
    else:
        verdict     = "Poor Investment"
        verdict_col = "#C0392B"
        recommend   = "Seek alternative site or lower rent"

    return {
        "est_monthly_revenue":  round(est_revenue),
        "monthly_rent":         round(monthly_rent),
        "monthly_profit":       round(monthly_profit),
        "annual_profit":        round(annual_profit),
        "rent_pct_of_revenue":  round(rent_pct * 100, 1),
        "payback_months":       round(payback_months, 1),
        "roi_score":            roi_score,
        "combined_score":       combined_score,
        "rent_label":           rent_label,
        "rent_color":           rent_color,
        "verdict":              verdict,
        "verdict_color":        verdict_col,
        "recommendation":       recommend,
        "setup_cost":           actual_setup,
        "brand_type":           brand_type,
        "location_score":       total_score,
    }