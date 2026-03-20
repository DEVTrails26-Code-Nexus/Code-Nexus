"""
Trigger Service for Nexurance AI
Checks external disruption triggers: Weather (OpenWeatherMap), AQI, IMD flood alerts.
Falls back to mock data in demo mode.
"""
import os
import asyncio
import logging
import time
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "demo_key")
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "demo_key")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# In-memory trigger overrides for demo simulation
_trigger_overrides: Dict[str, Dict[str, Any]] = {}

# Zone coordinates (Bengaluru areas)
ZONE_COORDINATES = {
    "koramangala": (12.9352, 77.6245),
    "hsr_layout": (12.9116, 77.6389),
    "whitefield": (12.9698, 77.7500),
    "electronic_city": (12.8390, 77.6771),
    "jp_nagar": (12.9063, 77.5857),
    "indiranagar": (12.9784, 77.6408),
    "marathahalli": (12.9591, 77.6974),
    "btm_layout": (12.9166, 77.6101),
    "jayanagar": (12.9299, 77.5838),
    "malleshwaram": (12.9969, 77.5700),
}


def get_zone_coordinates(zone: str) -> Tuple[float, float]:
    """Get lat/lng for a zone. Defaults to Koramangala."""
    zone_key = zone.lower().replace(" ", "_")
    return ZONE_COORDINATES.get(zone_key, (12.9352, 77.6245))


def set_trigger_override(zone: str, override_data: Dict[str, Any]):
    """Set a trigger override for demo simulation."""
    zone_key = zone.lower().replace(" ", "_")
    _trigger_overrides[zone_key] = {
        **override_data,
        "timestamp": time.time(),
        "expires": time.time() + override_data.get("duration_seconds", 3600),
    }
    logger.info(f"🌧️ Trigger override set for zone '{zone}': {override_data}")


def clear_trigger_override(zone: str):
    """Clear trigger override for a zone."""
    zone_key = zone.lower().replace(" ", "_")
    _trigger_overrides.pop(zone_key, None)


def get_active_overrides() -> Dict[str, Dict]:
    """Get all active trigger overrides."""
    now = time.time()
    active = {}
    for zone, data in list(_trigger_overrides.items()):
        if data.get("expires", 0) > now:
            active[zone] = data
        else:
            del _trigger_overrides[zone]
    return active


async def check_disruption(zone: str, lat: float = None, lng: float = None) -> Dict[str, Any]:
    """
    Check all Level 1 (environmental) and Level 2 (social/civic) triggers.
    """
    if lat is None or lng is None:
        lat, lng = get_zone_coordinates(zone)
    
    zone_key = zone.lower().replace(" ", "_")
    
    # Check for demo overrides first
    if zone_key in _trigger_overrides:
        override = _trigger_overrides[zone_key]
        if override.get("expires", 0) > time.time():
            logger.info(f"Using trigger override for zone '{zone}'")
            return _build_override_result(override)
    
    # Use real APIs if a valid OpenWeatherMap key is available (even in demo mode)
    has_real_key = OPENWEATHER_API_KEY and OPENWEATHER_API_KEY != "demo_key" and len(OPENWEATHER_API_KEY) > 10
    if has_real_key and HAS_HTTPX:
        logger.info(f"🌦️ Checking LIVE weather for zone '{zone}' ({lat}, {lng})")
        return await _check_real_apis(zone, lat, lng)
    
    # Fallback: return calm weather (no disruption)
    return _get_demo_weather(zone)


def _build_override_result(override: Dict) -> Dict[str, Any]:
    """Build trigger result from an override."""
    rainfall = override.get("rainfall_mm_hr", 75)
    aqi = override.get("aqi", 0)
    flood = override.get("flood_alert", False)
    
    rain_alert = rainfall > 50
    aqi_alert = aqi > 400
    
    env_score = (
        min(1.0, rainfall / 100) * 0.40 +
        min(1.0, aqi / 500) * 0.30 +
        (1.0 if flood else 0.0) * 0.30
    )
    
    trigger_level = 0
    if rain_alert or aqi_alert or flood:
        trigger_level = 1
    
    return {
        "trigger_level": trigger_level,
        "rain_alert": rain_alert,
        "rainfall_mm_hr": rainfall,
        "rainfall_mm": rainfall * override.get("duration_hours", 2),
        "aqi_level": aqi,
        "aqi_alert": aqi_alert,
        "flood_alert": flood,
        "curfew_alert": False,
        "disruption_score": round(env_score, 3),
        "rain_confirmed": rain_alert,
        "weather_data": {
            "rainfall_mm_hr": rainfall,
            "total_mm": rainfall * override.get("duration_hours", 2),
            "description": "heavy intensity rain" if rain_alert else "moderate rain",
            "rain_confirmed": rain_alert,
        },
        "disruption_duration_hours": override.get("duration_hours", 2),
        "source": "simulation",
    }


def _get_demo_weather(zone: str) -> Dict[str, Any]:
    """Return calm demo weather (no disruption)."""
    return {
        "trigger_level": 0,
        "rain_alert": False,
        "rainfall_mm_hr": 2.5,
        "rainfall_mm": 5.0,
        "aqi_level": 85,
        "aqi_alert": False,
        "flood_alert": False,
        "curfew_alert": False,
        "disruption_score": 0.05,
        "rain_confirmed": False,
        "weather_data": {
            "rainfall_mm_hr": 2.5,
            "total_mm": 5.0,
            "description": "light rain",
            "rain_confirmed": False,
        },
        "disruption_duration_hours": 0,
        "source": "demo",
    }


async def _check_real_apis(zone: str, lat: float, lng: float) -> Dict[str, Any]:
    """Check real weather/AQI APIs."""
    try:
        results = await asyncio.gather(
            _check_rainfall_api(lat, lng),
            _check_aqi_api(lat, lng),
            _check_imd_alerts(lat, lng),
            return_exceptions=True,
        )
        
        # Check for errors in the API calls
        if isinstance(results[0], Exception) or isinstance(results[1], Exception):
            err = results[0] if isinstance(results[0], Exception) else results[1]
            logger.warning(f"Live API request failed ({err}), falling back to demo weather")
            return _get_demo_weather(zone)

        rain_data = results[0]
        aqi_data = results[1]
        imd_data = results[2] if not isinstance(results[2], Exception) else {}
        
        rain_alert = rain_data.get("rainfall_mm_hr", 0) > 50
        aqi_alert = aqi_data.get("aqi", 0) > 400
        flood_alert = imd_data.get("flood_warning", False)
        
        env_score = (
            min(1.0, rain_data.get("rainfall_mm_hr", 0) / 100) * 0.40 +
            min(1.0, aqi_data.get("aqi", 0) / 500) * 0.30 +
            (1.0 if flood_alert else 0.0) * 0.30
        )
        
        trigger_level = 0
        if rain_alert or aqi_alert or flood_alert:
            trigger_level = 1
        
        return {
            "trigger_level": trigger_level,
            "rain_alert": rain_alert,
            "rainfall_mm_hr": rain_data.get("rainfall_mm_hr", 0),
            "rainfall_mm": rain_data.get("total_mm", 0),
            "aqi_level": aqi_data.get("aqi", 0),
            "aqi_alert": aqi_alert,
            "flood_alert": flood_alert,
            "curfew_alert": False,
            "disruption_score": round(env_score, 3),
            "rain_confirmed": rain_alert,
            "weather_data": rain_data,
            "disruption_duration_hours": _estimate_disruption_duration(rain_data),
            "source": "live_api",
        }
    except Exception as e:
        logger.error(f"API check failed: {e}")
        return _get_demo_weather(zone)


async def _check_rainfall_api(lat: float, lng: float) -> Dict[str, Any]:
    """Check OpenWeatherMap for current rainfall."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat, "lon": lng,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()  # Raise on 401/403/500
        data = resp.json()
    
    rain = data.get("rain", {})
    weather_desc = data.get("weather", [{}])[0].get("description", "clear sky")
    temp = data.get("main", {}).get("temp", 0)
    humidity = data.get("main", {}).get("humidity", 0)
    logger.info(f"🌤️ OpenWeatherMap: {weather_desc}, {temp}°C, {humidity}% humidity, rain={rain}")
    
    return {
        "rainfall_mm_hr": rain.get("1h", 0),
        "total_mm": rain.get("3h", 0),
        "description": weather_desc,
        "rain_confirmed": rain.get("1h", 0) > 20,
        "temperature": temp,
        "humidity": humidity,
    }


async def _check_aqi_api(lat: float, lng: float) -> Dict[str, Any]:
    """Check AQI from OpenWeatherMap Air Pollution API."""
    try:
        url = "https://api.openweathermap.org/data/2.5/air_pollution"
        params = {
            "lat": lat, "lon": lng,
            "appid": OPENWEATHER_API_KEY,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        
        aqi_value = data.get("list", [{}])[0].get("main", {}).get("aqi", 1)
        # OpenWeatherMap AQI is 1-5 scale, convert to Indian AQI scale (0-500)
        aqi_mapping = {1: 50, 2: 100, 3: 200, 4: 300, 5: 450}
        return {"aqi": aqi_mapping.get(aqi_value, 100)}
    except Exception:
        return {"aqi": 85}  # Default safe AQI


async def _check_imd_alerts(lat: float, lng: float) -> Dict[str, Any]:
    """Check IMD/NDMA for flood warnings."""
    # In production: parse IMD RSS feed
    # For now: return no flood warning
    return {"flood_warning": False}


def _estimate_disruption_duration(rain_data: Dict) -> float:
    """Estimate how long the disruption will last based on rainfall data."""
    rainfall = rain_data.get("rainfall_mm_hr", 0)
    if rainfall > 100:
        return 3.0
    if rainfall > 50:
        return 2.0
    if rainfall > 20:
        return 1.0
    return 0.0


def get_zone_status(zone: str) -> Dict[str, Any]:
    """Get current status for a zone (synchronous, for quick lookups)."""
    zone_key = zone.lower().replace(" ", "_")
    
    # Check overrides
    if zone_key in _trigger_overrides:
        override = _trigger_overrides[zone_key]
        if override.get("expires", 0) > time.time():
            return _build_override_result(override)
    
    return _get_demo_weather(zone)


def get_weather_forecast(zone: str) -> Dict[str, Any]:
    """Get weather forecast factors for premium calculation."""
    zone_key = zone.lower().replace(" ", "_")
    
    # Demo forecasts with varying rain probabilities by zone
    forecasts = {
        "koramangala": {"rain_probability_7day": 0.45},
        "hsr_layout": {"rain_probability_7day": 0.55},
        "whitefield": {"rain_probability_7day": 0.25},
        "electronic_city": {"rain_probability_7day": 0.30},
        "jp_nagar": {"rain_probability_7day": 0.40},
        "indiranagar": {"rain_probability_7day": 0.35},
        "marathahalli": {"rain_probability_7day": 0.42},
        "btm_layout": {"rain_probability_7day": 0.50},
    }
    return forecasts.get(zone_key, {"rain_probability_7day": 0.30})
