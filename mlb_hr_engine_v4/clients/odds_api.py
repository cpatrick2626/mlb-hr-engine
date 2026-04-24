"""
The Odds API client — batter_home_runs player props.
Free tier: 500 requests/month. https://the-odds-api.com

MANUAL ODDS FALLBACK
If the API is unreachable (e.g. corporate network), you can enter odds manually:
  1. Run the engine once — it saves codex_hr_engine_v4/manual_odds.csv with today's top players.
  2. Open that CSV and fill in the 'american_odds' column from any sportsbook.
  3. Re-run — the engine loads the CSV automatically.

CSV format:  player_name, american_odds, bookmaker
Example row: Aaron Judge, +285, DraftKings
"""

import csv
import os
import requests
from pathlib import Path
from typing import Optional

import config

BASE = "https://api.the-odds-api.com/v4"
MANUAL_ODDS_PATH = Path(__file__).parent.parent / "manual_odds.csv"
_SESSION = requests.Session()


# ──────────────────────────────────────────────────────────────────────────────
# Public interface
# ──────────────────────────────────────────────────────────────────────────────

def get_hr_odds_all_games() -> tuple[list[dict], str, dict]:
    """
    Try the API first; fall back to manual_odds.csv if blocked.
    Returns (props_list, source_label, quota_dict).
    quota_dict keys: 'used', 'remaining' (ints, or None if unavailable).
    """
    if config.ODDS_API_KEY:
        props, quota = _try_api()
        if props:
            return props, "The Odds API", quota

    # Fall back to manual CSV
    manual = load_manual_odds()
    if manual:
        return manual, "manual_odds.csv", {"used": None, "remaining": None}

    return [], "none", {"used": None, "remaining": None}


def load_manual_odds() -> list[dict]:
    """Load odds from manual_odds.csv if it exists and has filled-in data."""
    if not MANUAL_ODDS_PATH.exists():
        return []

    props: list[dict] = []
    with open(MANUAL_ODDS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get("american_odds", "").strip()
            if not raw or raw in ("?", "", "0"):
                continue  # Skip unfilled rows
            try:
                price = int(raw.replace("+", ""))
                props.append({
                    "player_name": row.get("player_name", "").strip(),
                    "price": price,
                    "bookmaker": row.get("bookmaker", "manual").strip(),
                    "description": "Over 0.5",
                    "game_id": "manual",
                    "home_team": "",
                    "away_team": "",
                })
            except ValueError:
                continue

    return props


def write_shopping_list(top_players: list[dict]) -> None:
    """
    Write a prefilled manual_odds.csv with today's top model picks.
    The user fills in american_odds from their preferred sportsbook.
    """
    rows = []
    for p in top_players:
        rows.append({
            "player_name": p.get("player_name", ""),
            "team": p.get("team", ""),
            "opponent": p.get("opponent", ""),
            "pitcher": p.get("pitcher_name", "TBD"),
            "model_prob_pct": f"{p.get('model_prob', 0)*100:.1f}%",
            "american_odds": "?",  # User fills this in
            "bookmaker": "",       # User fills this in
        })

    with open(MANUAL_ODDS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ──────────────────────────────────────────────────────────────────────────────
# API internals
# ──────────────────────────────────────────────────────────────────────────────

_last_quota: dict = {"used": None, "remaining": None}


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
    try:
        resp = _SESSION.get(
            f"{BASE}/sports/baseball_mlb/events",
            params={"apiKey": config.ODDS_API_KEY, "dateFormat": "iso"},
            timeout=12,
        )
        _parse_quota(resp)
        if resp.status_code != 200:
            return []
        return resp.json()
    except Exception:
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
        for bookmaker in data.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") != "batter_home_runs":
                    continue
                for outcome in market.get("outcomes", []):
                    # Only the Over 0.5 line = "will hit at least 1 HR today"
                    if outcome.get("point") != 0.5:
                        continue
                    # Odds API: description = player name, name = "Over"/"Under"
                    player_name = outcome.get("description", "")
                    if not player_name:
                        continue
                    props.append({
                        "player_name": player_name,
                        "description": f"Over {outcome.get('point', 0.5)} HR",
                        "price": int(outcome.get("price", 99999)),
                        "bookmaker": bookmaker.get("key", ""),
                        "game_id": event_id,
                    })
        return props
    except Exception:
        return []


def _normalize(name: str) -> str:
    return name.lower().strip()

