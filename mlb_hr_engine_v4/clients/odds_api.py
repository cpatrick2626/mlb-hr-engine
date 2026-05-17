"""
The Odds API client — batter_home_runs player props.
Free tier: 500 requests/month. https://the-odds-api.com

API quota notes:
- Each _try_api() call costs 1 + N requests (1 events + 1 per game).
- Results are cached to disk for CACHE_TTL_MINUTES to avoid repeated charges.
- Events are filtered to today's window only to minimize N.
"""

import json
import os
import requests
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import config

BASE = "https://api.the-odds-api.com/v4"
_CACHE_PATH = Path(__file__).parent.parent / "data" / "odds_cache.json"
CACHE_TTL_MINUTES = 45
_SESSION = requests.Session()


# ──────────────────────────────────────────────────────────────────────────────
# Public interface
# ──────────────────────────────────────────────────────────────────────────────

def get_hr_odds_all_games() -> tuple[list[dict], str, dict]:
    """
    Fetch HR props from The Odds API.
    Returns (props_list, source_label, quota_dict).
    quota_dict keys: 'used', 'remaining' (ints, or None if unavailable).
    """
    global _last_error
    _last_error = ""

    if not config.ODDS_API_KEY:
        _last_error = "No API key — paste your key in the sidebar."
        return [], "none", {"used": None, "remaining": None}

    cached = _load_cache()
    if cached is not None:
        props, quota = cached
        return props, "The Odds API (cached)", quota

    props, quota = _try_api()
    if props:
        _save_cache(props, quota)
        return props, "The Odds API", quota

    # Fresh fetch returned nothing (quota exhausted, network error, etc.).
    # Serve the expired cache as a last resort so the pipeline still has odds data.
    stale = _load_cache_stale()
    if stale:
        stale_props, stale_quota = stale
        print(f"[odds_api] WARNING: live fetch failed — serving {len(stale_props)} stale cached props")
        return stale_props, "The Odds API (stale cache)", stale_quota

    return [], "none", {"used": None, "remaining": None}


# ──────────────────────────────────────────────────────────────────────────────
# API internals
# ──────────────────────────────────────────────────────────────────────────────

_last_quota: dict = {"used": None, "remaining": None}
_last_error: str  = ""


def get_last_error() -> str:
    return _last_error


# ──────────────────────────────────────────────────────────────────────────────
# Disk cache
# ──────────────────────────────────────────────────────────────────────────────

def _load_cache() -> tuple[list[dict], dict] | None:
    try:
        if not _CACHE_PATH.exists():
            return None
        with open(_CACHE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        age_minutes = (time.time() - data["timestamp"]) / 60
        if age_minutes > CACHE_TTL_MINUTES:
            return None
        return data["props"], data["quota"]
    except Exception:
        return None


def _load_cache_stale() -> tuple[list[dict], dict] | None:
    """Load cache regardless of age — used as last-resort fallback when live fetch fails."""
    try:
        if not _CACHE_PATH.exists():
            return None
        with open(_CACHE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        props = data.get("props")
        if not props:
            return None
        return props, data.get("quota", {"used": None, "remaining": None})
    except Exception:
        return None


def _save_cache(props: list[dict], quota: dict) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "props": props, "quota": quota}, f)
    except Exception as e:
        print(f"[odds_api] cache write failed: {e}")


def _parse_quota(resp) -> None:
    try:
        used = resp.headers.get("x-requests-used")
        remaining = resp.headers.get("x-requests-remaining")
        if used is not None:
            _last_quota["used"] = int(used)
        if remaining is not None:
            _last_quota["remaining"] = int(remaining)
    except (ValueError, AttributeError):
        pass


def _try_api() -> tuple[list[dict], dict]:
    events = _get_events()
    if not events:
        return [], dict(_last_quota)
    all_props: list[dict] = []
    for event in events:
        props = _get_event_props(event["id"])
        for p in props:
            p["home_team"] = event.get("home_team", "")
            p["away_team"] = event.get("away_team", "")
        all_props.extend(props)
    return all_props, dict(_last_quota)


def _get_events() -> list[dict]:
    global _last_error
    now_utc = datetime.now(timezone.utc)
    # Anchor window on ET midnight (UTC-4) so games are never missed after 8 PM ET
    now_et = now_utc - timedelta(hours=4)
    et_midnight_utc = now_et.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=4)
    today_start = et_midnight_utc + timedelta(hours=9)   # ~5 AM ET
    today_end   = today_start + timedelta(hours=23)       # ~4 AM next-day ET — covers all late west-coast games
    try:
        resp = _SESSION.get(
            f"{BASE}/sports/baseball_mlb/events",
            params={
                "apiKey": config.ODDS_API_KEY,
                "dateFormat": "iso",
                "commenceTimeFrom": today_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commenceTimeTo":   today_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=12,
        )
        _parse_quota(resp)
        if resp.status_code != 200:
            _KNOWN = {
                401: "Invalid API key (401). Check your ODDS_API_KEY.",
                422: "API key missing or malformed (422). Check your ODDS_API_KEY.",
                429: "Monthly quota exhausted (429). Free tier: 500 req/month. Upgrade at the-odds-api.com.",
            }
            msg = _KNOWN.get(resp.status_code, f"API error {resp.status_code}")
            try:
                api_msg = resp.json().get("message", "")
                if api_msg:
                    msg += f" — {api_msg}"
            except Exception:
                pass
            _last_error = msg
            return []
        return resp.json()
    except Exception as e:
        _last_error = f"Network error reaching The Odds API: {e}"
        return []


def _get_event_props(event_id: str) -> list[dict]:
    try:
        resp = _SESSION.get(
            f"{BASE}/sports/baseball_mlb/events/{event_id}/odds",
            params={
                "apiKey": config.ODDS_API_KEY,
                "regions": "us",
                "markets": "batter_home_runs",
                "oddsFormat": "american",
            },
            timeout=12,
        )
        _parse_quota(resp)
        if resp.status_code != 200:
            return []
        data = resp.json()
        props: list[dict] = []
        # Track Under prices per (bookmaker, player) so we can compute overround
        # when both sides are available — used by engine/vig.py for empirical measurement.
        under_prices: dict[tuple[str, str], int] = {}

        for bookmaker in data.get("bookmakers", []):
            bk_key = bookmaker.get("key", "")
            for market in bookmaker.get("markets", []):
                if market.get("key") != "batter_home_runs":
                    continue
                for outcome in market.get("outcomes", []):
                    if outcome.get("point") != 0.5:
                        continue
                    player_name = outcome.get("description", "")
                    if not player_name:
                        continue
                    price = outcome.get("price")
                    if not price:
                        continue
                    try:
                        price = int(price)
                    except (ValueError, TypeError):
                        continue
                    # Reject impossible American odds (must be ≥+100 or ≤-100)
                    if -100 < price < 100:
                        continue
                    side = outcome.get("name", "Over")   # "Over" or "Under"
                    if side == "Under":
                        # Store Under price keyed by (bookmaker, player) for overround calc
                        under_prices[(bk_key, player_name)] = price
                    else:
                        props.append({
                            "player_name": player_name,
                            "description": f"Over {outcome.get('point', 0.5)} HR",
                            "price": price,
                            "bookmaker": bk_key,
                            "game_id": event_id,
                        })

        # Annotate Over props with measured overround when Under price is available.
        # overround = implied(over) + implied(under) - 1; true vig = overround / 2 ≈ one-sided margin.
        for prop in props:
            key = (prop["bookmaker"], prop["player_name"])
            under_p = under_prices.get(key)
            if under_p is not None:
                over_imp   = 100.0 / (prop["price"] + 100.0) if prop["price"] > 0 else abs(prop["price"]) / (abs(prop["price"]) + 100.0)
                under_imp  = 100.0 / (under_p + 100.0) if under_p > 0 else abs(under_p) / (abs(under_p) + 100.0)
                overround  = round(over_imp + under_imp - 1.0, 4)
                prop["measured_overround"] = overround  # empirical two-sided vig for this book/player
        return props
    except Exception as e:
        print(f"[odds_api] props fetch failed for event {event_id}: {e}")
        return []
