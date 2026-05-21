"""
Open-Meteo weather client - free, no API key.
Fetches temperature, wind, and humidity at game time for stadium location.
"""

from __future__ import annotations

import math
from time import monotonic

import config
import requests

from clients.session_utils import configure_session

_SESSION = configure_session(requests.Session())
_CACHE: dict[str, dict] = {}
_DEGRADED_CACHE: dict[str, dict] = {}
_WEATHER_RETRY_COOLDOWN_S = 15 * 60


def _neutral_weather(*, source: str = "neutral-fallback", trust: str = "degraded", degraded: bool = True) -> dict:
    """Return neutral weather defaults with explicit trust metadata."""
    return {
        "temp_f": 70.0,
        "wind_mph": 0.0,
        "wind_deg": 0.0,
        "humidity_pct": 55,
        "weather_source": source,
        "weather_trust": trust,
        "weather_degraded": degraded,
    }


def get_game_weather(lat: float, lon: float, game_hour_local: int = 19) -> dict:
    """
    Return weather conditions for a stadium location.
    game_hour_local: local hour of game start (0-23). Default 19 = 7 PM local time,
    which covers the majority of MLB evening starts. Open-Meteo is requested with
    timezone=auto so the hourly array is already in local time - index 19 = 7 PM local.

    Returns: temp_f, wind_mph, wind_deg (or defaults if unavailable).
    """
    safe_hour = max(0, min(int(game_hour_local), 23))
    cache_key = f"{lat:.3f},{lon:.3f},{safe_hour}"

    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    degraded = _DEGRADED_CACHE.get(cache_key)
    now = monotonic()
    if degraded is not None:
        if now < degraded["retry_after"]:
            return degraded["result"]
        _DEGRADED_CACHE.pop(cache_key, None)

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
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("windspeed_10m", [])
        dirs = hourly.get("winddirection_10m", [])
        humids = hourly.get("relativehumidity_2m", [])

        t_idx = min(safe_hour, len(temps) - 1) if temps else 0
        w_idx = min(safe_hour, len(winds) - 1) if winds else 0
        d_idx = min(safe_hour, len(dirs) - 1) if dirs else 0
        h_idx = min(safe_hour, len(humids) - 1) if humids else 0

        result = {
            "temp_f": round(temps[t_idx], 1) if temps else 70.0,
            "wind_mph": round(winds[w_idx], 1) if winds else 0.0,
            "wind_deg": round(dirs[d_idx], 0) if dirs else 0.0,
            "humidity_pct": int(humids[h_idx]) if humids else 55,
            "weather_source": "open-meteo",
            "weather_trust": "fresh",
            "weather_degraded": False,
        }
        _CACHE[cache_key] = result
        _DEGRADED_CACHE.pop(cache_key, None)
        return result
    except Exception:
        result = _neutral_weather(source="open-meteo")
        _DEGRADED_CACHE[cache_key] = {
            "retry_after": now + _WEATHER_RETRY_COOLDOWN_S,
            "result": result,
        }
        return result


def wind_factor(wind_mph: float, wind_deg: float, is_dome: bool = False, cf_bearing: float = 0.0) -> float:
    """
    Stage 5 (expert pipeline): continuous wind adjustment (~3% per mph blowing out to CF).
    wind_deg: meteorological convention - direction wind is BLOWING FROM (0=N, 90=E, ...).
    cf_bearing: compass direction FROM home plate TO center field (park-specific).
    Tailwind (boost) when wind blows FROM the opposite of cf_bearing;
    headwind (suppress) when wind blows FROM cf_bearing direction.
    """
    if is_dome or wind_mph < 2:
        return 1.0
    opposing = (cf_bearing + 180) % 360
    angle_diff = abs(((wind_deg - opposing) + 180) % 360 - 180)
    wind_to_cf = wind_mph * math.cos(math.radians(angle_diff))
    adj = wind_to_cf * 0.003
    return max(0.82, min(1.18, 1.0 + adj))


DOME_TEAMS = {"TB", "MIA", "TOR", "MIL", "HOU", "ARI", "TEX", "SEA"}


def humidity_factor(humidity_pct: float) -> float:
    """
    Stage 5 (expert pipeline): continuous humidity adjustment.
    Physics: humid air contains lighter water vapor molecules (MW=18) displacing
    heavier N2 (MW=28) and O2 (MW=32), making humid air LESS dense. Less dense
    air reduces aerodynamic drag, so balls carry slightly farther - a small HR boost.
    Effect: ~1.5% per 10pp RH from 55% baseline. Range: +/-4%.
    Dome teams already set wind=1.0; humidity still applies for air density effect
    (dome air is typically climate-controlled near the baseline ~55% RH).
    """
    adj = 0.0015 * (humidity_pct - config.LEAGUE_AVG_HUMIDITY)
    return max(0.96, min(1.04, 1.0 + adj))


def temp_factor(temp_f: float) -> float:
    """
    Stage 5 (expert pipeline): continuous temperature adjustment.
    Formula: ~2% per 10F from baseline 72F (denser/thinner air affects carry).
    """
    adj = 0.002 * (temp_f - 72.0)
    return max(0.82, min(1.08, 1.0 + adj))
