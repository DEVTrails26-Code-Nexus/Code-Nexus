"""
Premium Calculation Engine for Nexurance AI
P = B × Z × W × T formula with XGBoost enhancement (optional)
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Zone risk multipliers based on historical flood/AQI data for Bengaluru
ZONE_RISK_SCORES = {
    "hsr_layout": 1.3,
    "koramangala": 1.2,
    "whitefield": 0.8,
    "electronic_city": 0.9,
    "jp_nagar": 1.1,
    "indiranagar": 1.0,
    "marathahalli": 1.15,
    "btm_layout": 1.25,
    "jayanagar": 0.95,
    "malleshwaram": 0.85,
    "default": 1.0,
}

# Coverage amounts per plan tier
COVERAGE_AMOUNTS = {
    "starter": 500,
    "shield": 1200,
    "max": 2500,
}


def calculate_premium(
    zone: str,
    worker_history: Dict[str, Any],
    weather_forecast: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate personalized weekly premium using P = B × Z × W × T formula.
    
    B = 20 (base rate in Rs.)
    Z = Zone Risk Multiplier (0.7 to 1.5)
    W = Weather Forecast Factor (1.0 to 1.8)
    T = Trust Discount (0.85 to 1.0)
    """
    B = 20.0
    
    # Zone Risk Multiplier
    zone_key = zone.lower().replace(" ", "_")
    Z = ZONE_RISK_SCORES.get(zone_key, ZONE_RISK_SCORES["default"])
    
    # Weather Forecast Factor
    if weather_forecast is None:
        weather_forecast = {}
    rain_probability = weather_forecast.get("rain_probability_7day", 0.3)
    W = 1.0 + (rain_probability * 0.8)  # scales 1.0 to 1.8
    W = max(1.0, min(1.8, W))
    
    # Trust Discount — reward clean history
    clean_weeks = worker_history.get("consecutive_clean_weeks", 0)
    T = max(0.85, 1.0 - (clean_weeks * 0.015))  # up to 15% discount
    
    # Calculate for each tier
    base_premium = B * Z * W * T
    starter = round(max(15, min(25, base_premium * 0.75)))
    shield = round(max(26, min(40, base_premium)))
    max_plan = round(max(41, min(60, base_premium * 1.35)))
    
    # Determine recommended plan
    recommended = "shield"
    if worker_history.get("avg_hourly_earnings", 111) < 80:
        recommended = "starter"
    elif worker_history.get("total_claims", 0) > 5:
        recommended = "max"
    
    return {
        "starter": starter,
        "shield": shield,
        "max": max_plan,
        "zone_risk": round(Z, 2),
        "weather_factor": round(W, 2),
        "trust_discount": round(T, 2),
        "recommended": recommended,
        "base_premium": round(base_premium, 2),
    }


def get_zone_risk(zone: str) -> float:
    """Get risk multiplier for a zone."""
    zone_key = zone.lower().replace(" ", "_")
    return ZONE_RISK_SCORES.get(zone_key, ZONE_RISK_SCORES["default"])


def get_all_zone_risks() -> Dict[str, float]:
    """Get all zone risk scores for admin dashboard."""
    return {k: v for k, v in ZONE_RISK_SCORES.items() if k != "default"}
