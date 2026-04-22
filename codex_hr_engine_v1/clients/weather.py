"""
Open-Meteo weather client — free, no API key.
Fetches temperature and wind at game time for stadium location.
"""

import requests
from datetime import datetime

_SESSION = requests.Session()
_CACHE: dict[str, dict] = {}


def get_game_weather(lat: float, lon: float, game_hour_utc: int = 18) -> dict:
    """
    Return weather conditions for a stadium location.
    game_hour_utc: approximate game start hour in UTC (default 6 PM ET ≈ 22 UTC, but we'll use local noon as fallback).

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

        # Pick the closest hour to game_hour_utc (simple: just grab midday index)
        idx = min(game_hour_utc, len(temps) - 1) if temps else 0

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
    Rough HR adjustment for wind speed and direction.
    Wind direction 0-360°: blowing FROM that compass bearing.
    Typical ballparks face various orientations — we approximate:
      - High wind out (wind_mph > 12 from "behind" batter) → boost
      - High wind in (into batter's face) → suppress
    Without park-specific orientation, we use a simplified model:
      - Direction 45-135° = generally "out to CF" for typical E-facing parks → boost
      - Direction 225-315° = "in from CF" → suppress
    """
    if is_dome:
        return 1.0

    factor = 1.0

    # Temperature already handled in probability.py; here just wind
    if wind_mph < 5:
        return 1.0

    # Approximate "out" direction (favorable) vs "in" (unfavorable)
    out_deg = 90   # east wind = blowing toward LF/CF in most parks
    angle_diff = abs(((wind_deg - out_deg) + 180) % 360 - 180)

    if angle_diff < 60:  # wind blowing "out"
        if wind_mph >= 15:
            factor = 1.15
        elif wind_mph >= 10:
            factor = 1.08
        else:
            factor = 1.04
    elif angle_diff > 120:  # wind blowing "in"
        if wind_mph >= 15:
            factor = 0.82
        elif wind_mph >= 10:
            factor = 0.90
        else:
            factor = 0.95

    return factor


DOME_TEAMS = {"TB", "MIA", "TOR", "MIL", "HOU", "ARI", "TEX"}


def temp_factor(temp_f: float) -> float:
    """Cold air is denser → suppresses carry; hot air is thinner → boosts."""
    if temp_f < 40:
        return 0.82
    if temp_f < 50:
        return 0.88
    if temp_f < 60:
        return 0.94
    if temp_f > 90:
        return 1.06
    if temp_f > 80:
        return 1.03
    return 1.0
