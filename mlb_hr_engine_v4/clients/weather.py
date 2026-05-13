"""
Open-Meteo weather client — free, no API key.
Fetches temperature and wind at game time for stadium location.
"""

import math
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
    cache_key = f"{lat:.3f},{lon:.3f},{game_hour_local}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    try:
        resp = _SESSION.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,windspeed_10m,winddirection_10m,relativehumidity_2m",
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
        temps  = hourly.get("temperature_2m", [])
        winds  = hourly.get("windspeed_10m", [])
        dirs   = hourly.get("winddirection_10m", [])
        humids = hourly.get("relativehumidity_2m", [])

        t_idx = min(game_hour_local, len(temps)  - 1) if temps  else 0
        w_idx = min(game_hour_local, len(winds)  - 1) if winds  else 0
        d_idx = min(game_hour_local, len(dirs)   - 1) if dirs   else 0
        h_idx = min(game_hour_local, len(humids) - 1) if humids else 0

        result = {
            "temp_f":      round(temps[t_idx],  1) if temps  else 70.0,
            "wind_mph":    round(winds[w_idx],  1) if winds  else 0.0,
            "wind_deg":    round(dirs[d_idx],   0) if dirs   else 0.0,
            "humidity_pct": int(humids[h_idx])     if humids else 55,
        }
    except Exception as e:
        print(f"[weather] fetch/parse failed ({lat},{lon}): {e} — using neutral defaults")
        result = {"temp_f": 70.0, "wind_mph": 0.0, "wind_deg": 0.0, "humidity_pct": 55}

    _CACHE[cache_key] = result
    return result


def wind_factor(wind_mph: float, wind_deg: float, is_dome: bool = False, cf_bearing: float = 0.0) -> float:
    """
    Stage 5 (expert pipeline): continuous wind adjustment (~3% per mph blowing out to CF).
    wind_deg: meteorological convention — direction wind is BLOWING FROM (0=N, 90=E, ...).
    cf_bearing: compass direction FROM home plate TO center field (park-specific).
    Tailwind (boost) when wind blows FROM the opposite of cf_bearing;
    headwind (suppress) when wind blows FROM cf_bearing direction.
    """
    if is_dome or wind_mph < 2:
        return 1.0
    # A tailwind toward CF occurs when wind comes from (cf_bearing + 180°).
    opposing     = (cf_bearing + 180) % 360
    angle_diff   = abs(((wind_deg - opposing) + 180) % 360 - 180)
    wind_to_cf   = wind_mph * math.cos(math.radians(angle_diff))
    adj          = wind_to_cf * 0.003
    return max(0.82, min(1.18, 1.0 + adj))


DOME_TEAMS = {"TB", "MIA", "TOR", "MIL", "HOU", "ARI", "TEX", "SEA"}


def temp_factor(temp_f: float) -> float:
    """
    Stage 5 (expert pipeline): continuous temperature adjustment.
    Formula: ~2% per 10°F from baseline 72°F (denser/thinner air affects carry).
    """
    adj = 0.002 * (temp_f - 72.0)
    return max(0.82, min(1.08, 1.0 + adj))


def humidity_factor(humidity_pct: float, is_dome: bool = False) -> float:
    """
    Adjusts HR carry based on relative humidity.
    Denser humid air reduces ball flight; dry air increases carry.
    Baseline 50% RH → 1.0. Effect: ±0.5% per 10 RH points from baseline.
    Caps at [0.96, 1.04] — smaller than temp since humidity effect is secondary.
    Domes have controlled humidity — always return 1.0.
    """
    if is_dome:
        return 1.0
    adj = -0.0005 * (humidity_pct - 50.0)
    return round(max(0.96, min(1.04, 1.0 + adj)), 4)
