"""
Open-Meteo weather client — free, no API key.
Fetches temperature and wind at game time for stadium location.
"""

import requests
from datetime import datetime

_SESSION = requests.Session()
_CACHE: dict[str, dict] = {}


def get_game_weather(lat: float, lon: float, game_hour_local: int = 19) -> dict:
    """
    Return weather conditions for a stadium location.
    game_hour_local: local hour of game start (0-23). Default 19 = 7 PM local time,
    which covers the majority of MLB evening starts. Open-Meteo is requested with
    timezone=auto so the hourly array is already in local time — index 19 = 7 PM local.

    Returns: temp_f, wind_mph, wind_deg (or defaults if unavailable).
    """
    cache_key = f"{lat:.3f},{lon:.3f}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    try:
        resp = _SESSION.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,windspeed_10m,winddirection_10m",
                "temperature_unit": "fahrenheit",
                "windspeed_unit": "mph",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("windspeed_10m", [])
        dirs = hourly.get("winddirection_10m", [])

        idx = min(game_hour_local, len(temps) - 1) if temps else 0

        result = {
            "temp_f": round(temps[idx], 1) if temps else 70.0,
            "wind_mph": round(winds[idx], 1) if winds else 0.0,
            "wind_deg": round(dirs[idx], 0) if dirs else 0.0,
        }
    except Exception:
        result = {"temp_f": 70.0, "wind_mph": 0.0, "wind_deg": 0.0}

    _CACHE[cache_key] = result
    return result


def wind_factor(wind_mph: float, wind_deg: float, is_dome: bool = False) -> float:
    """
    Stage 5 (expert pipeline): continuous wind adjustment.
    Formula: wind_adj = wind_to_CF_mph * 0.003  (~3% per mph blowing out)
    wind_to_CF_mph = component of wind blowing toward CF (angle-weighted).
    Most parks' CF orientation is roughly east-facing (~90°).
    """
    import math
    if is_dome or wind_mph < 2:
        return 1.0
    cf_bearing   = 90.0   # typical park CF direction
    angle_diff   = abs(((wind_deg - cf_bearing) + 180) % 360 - 180)
    wind_to_cf   = wind_mph * math.cos(math.radians(angle_diff))
    adj          = wind_to_cf * 0.003
    return max(0.82, min(1.18, 1.0 + adj))


DOME_TEAMS = {"TB", "MIA", "TOR", "MIL", "HOU", "ARI", "TEX"}


def temp_factor(temp_f: float) -> float:
    """
    Stage 5 (expert pipeline): continuous temperature adjustment.
    Formula: ~2% per 10°F from baseline 72°F (denser/thinner air affects carry).
    """
    adj = 0.002 * (temp_f - 72.0)
    return max(0.82, min(1.08, 1.0 + adj))
