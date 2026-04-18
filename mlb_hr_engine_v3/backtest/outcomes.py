"""
Fetch actual game outcomes (HR yes/no per batter) from MLB Stats API box scores.
Used by the backtest runner to compare model predictions vs reality.
"""

import time
from datetime import date, timedelta
from typing import Optional

import requests

MLB_API = "https://statsapi.mlb.com/api/v1"
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "MLB-HR-Engine/3.0"})


def get_date_range(start_date: str, end_date: str) -> list[str]:
    """Return list of ISO date strings between start and end (inclusive)."""
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    dates = []
    cur = s
    while cur <= e:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return dates


def get_game_results(date_str: str) -> list[dict]:
    """
    For a completed date, return one row per starting batter:
      {player_id, player_name, team, opponent, home_team,
       pitcher_id, pitcher_name, lineup_spot, hit_hr}

    Skips games with no box score (postponed, not yet played, etc).
    """
    games = _get_schedule_final(date_str)
    if not games:
        return []

    results = []
    for game in games:
        try:
            box = _get_boxscore(game["game_pk"])
            rows = _parse_boxscore(game, box)
            results.extend(rows)
            time.sleep(0.15)  # be polite to the API
        except Exception:
            continue
    return results


# ── Internal ──────────────────────────────────────────────────────────────────

def _get(path: str, params: dict = None) -> dict:
    resp = _SESSION.get(f"{MLB_API}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get_schedule_final(date_str: str) -> list[dict]:
    """Games that were completed on this date."""
    data = _get("/schedule", {
        "sportId": 1,
        "date": date_str,
        "hydrate": "probablePitcher,team,lineups",
    })
    games = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            status = g.get("status", {}).get("abstractGameState", "")
            if status != "Final":
                continue
            home = g.get("teams", {}).get("home", {})
            away = g.get("teams", {}).get("away", {})
            games.append({
                "game_pk":    g.get("gamePk"),
                "home_team":  home.get("team", {}).get("abbreviation", ""),
                "away_team":  away.get("team", {}).get("abbreviation", ""),
                "lineups":    g.get("lineups", {}),
            })
    return games


def _get_boxscore(game_pk: int) -> dict:
    return _get(f"/game/{game_pk}/boxscore")


def _parse_boxscore(game: dict, box: dict) -> list[dict]:
    """Extract starting batter rows with actual HR outcome."""
    rows = []
    home = game["home_team"]
    away = game["away_team"]

    for side, team, opp in [("home", home, away), ("away", away, home)]:
        team_data = box.get("teams", {}).get(side, {})
        players   = team_data.get("players", {})
        batters   = team_data.get("batters", [])

        # Resolve pitcher for the other side (they face the other team's pitcher)
        opp_side     = "away" if side == "home" else "home"
        opp_pitchers = box.get("teams", {}).get(opp_side, {}).get("pitchers", [])
        starter_pid  = opp_pitchers[0] if opp_pitchers else None
        starter_info = box.get("teams", {}).get(opp_side, {}).get(
            "players", {}).get(f"ID{starter_pid}", {}) if starter_pid else {}
        pitcher_name = starter_info.get("person", {}).get("fullName", "TBD")

        for pid in batters:
            pdata = players.get(f"ID{pid}", {})
            order_str = pdata.get("battingOrder", "")
            if not order_str:
                continue
            try:
                order = int(order_str)
            except ValueError:
                continue
            # Only starting batters (100, 200, ..., 900) — bench guys are 101, 201, etc.
            if order % 100 != 0:
                continue
            lineup_spot = order // 100

            stats   = pdata.get("stats", {}).get("batting", {})
            hit_hr  = int(stats.get("homeRuns", 0)) > 0
            name    = pdata.get("person", {}).get("fullName", "")

            rows.append({
                "player_id":    pid,
                "player_name":  name,
                "team":         team,
                "opponent":     opp,
                "home_team":    home,
                "pitcher_id":   starter_pid,
                "pitcher_name": pitcher_name,
                "lineup_spot":  lineup_spot,
                "hit_hr":       hit_hr,
            })

    return rows
