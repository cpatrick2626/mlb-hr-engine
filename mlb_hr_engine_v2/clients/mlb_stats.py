"""
MLB Stats API client â€” free, no API key required.
Docs: https://statsapi.mlb.com/docs/
"""

import sys
import requests
from datetime import date, timedelta
from typing import Optional

import config

MLB_API = "https://statsapi.mlb.com/api/v1"
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Codex-HR-Engine/1.0"})


def _get(path: str, params: dict = None) -> dict:
    url = f"{MLB_API}{path}"
    resp = _SESSION.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_today_schedule(target_date: Optional[str] = None) -> list[dict]:
    """
    Return parsed list of today's games with venue, lineups, and probable pitchers.
    Each game dict has: game_pk, home_team, away_team, venue_team,
    home_lineup, away_lineup, home_pitcher, away_pitcher, status.
    """
    game_date = target_date or (config.TARGET_DATE or date.today().strftime("%Y-%m-%d"))
    data = _get("/schedule", {
        "sportId": 1,
        "date": game_date,
        "hydrate": "lineups,probablePitcher(note),team,venue",
        "language": "en",
    })

    games: list[dict] = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            status = g.get("status", {}).get("abstractGameState", "")
            if status == "Final":
                continue  # skip completed games

            home = g.get("teams", {}).get("home", {})
            away = g.get("teams", {}).get("away", {})
            home_abbr = home.get("team", {}).get("abbreviation", "")
            away_abbr = away.get("team", {}).get("abbreviation", "")

            # Probable pitchers
            home_pitcher = home.get("probablePitcher", {})
            away_pitcher = away.get("probablePitcher", {})

            # Lineups (may be empty if not yet posted)
            lineups = g.get("lineups", {})
            home_lineup = _parse_lineup(lineups.get("homePlayers", []))
            away_lineup = _parse_lineup(lineups.get("awayPlayers", []))

            games.append({
                "game_pk": g.get("gamePk"),
                "game_date": game_date,
                "home_team": home_abbr,
                "away_team": away_abbr,
                "home_pitcher": _parse_pitcher(home_pitcher),
                "away_pitcher": _parse_pitcher(away_pitcher),
                "home_lineup": home_lineup,
                "away_lineup": away_lineup,
                "venue_team": home_abbr,  # home team = their park
                "status": status,
            })

    return games


def _parse_lineup(players: list) -> list[dict]:
    result = []
    for i, p in enumerate(players, 1):
        result.append({
            "id": p.get("id"),
            "name": p.get("fullName", ""),
            "lineup_spot": i,
        })
    return result


def _parse_pitcher(pitcher: dict) -> dict:
    if not pitcher:
        return {}
    return {
        "id": pitcher.get("id"),
        "name": pitcher.get("fullName", "TBD"),
    }


def get_player_season_stats(player_id: int) -> dict:
    """
    Hitting stats for the current season.
    Falls back to prior season if current season has < 30 PA (early season noise).
    """
    try:
        data = _get(f"/people/{player_id}/stats", {
            "stats": "season",
            "group": "hitting",
            "season": config.CURRENT_SEASON,
        })
        splits = _first_splits(data)
        stats = splits.get("stat", {}) if splits else {}

        # Early season: supplement with prior year if PA is thin
        pa = int(stats.get("plateAppearances", 0))
        if pa < 30:
            prior = _get_prior_season_stats(player_id)
            if prior:
                return prior  # Use prior season as base rate
        return stats
    except Exception:
        return _get_prior_season_stats(player_id)


def _get_prior_season_stats(player_id: int) -> dict:
    """Fetch prior season hitting stats as fallback."""
    try:
        data = _get(f"/people/{player_id}/stats", {
            "stats": "season",
            "group": "hitting",
            "season": config.CURRENT_SEASON - 1,
        })
        splits = _first_splits(data)
        return splits.get("stat", {}) if splits else {}
    except Exception:
        return {}


def get_player_recent_stats(player_id: int) -> dict:
    """
    Aggregate hitting stats over the last RECENT_DAYS from game log.
    Returns dict with homeRuns, plateAppearances, games.
    """
    try:
        data = _get(f"/people/{player_id}/stats", {
            "stats": "gameLog",
            "group": "hitting",
            "season": config.CURRENT_SEASON,
        })
        splits = data.get("stats", [{}])[0].get("splits", [])
    except Exception:
        return {}

    cutoff = date.today() - timedelta(days=config.RECENT_DAYS)
    totals = {"homeRuns": 0, "plateAppearances": 0, "atBats": 0, "games": 0}

    for split in splits:
        raw_date = split.get("date", "2000-01-01")
        try:
            game_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if game_date < cutoff:
            continue
        st = split.get("stat", {})
        totals["homeRuns"] += int(st.get("homeRuns", 0))
        totals["plateAppearances"] += int(st.get("plateAppearances", 0))
        totals["atBats"] += int(st.get("atBats", 0))
        totals["games"] += 1

    return totals


def get_pitcher_season_stats(pitcher_id: int) -> dict:
    """
    Pitching stats â€” current season with prior-year fallback.
    Includes airOuts for HR/FB calculation (v2 enhancement).
    """
    try:
        data = _get(f"/people/{pitcher_id}/stats", {
            "stats": "season",
            "group": "pitching",
            "season": config.CURRENT_SEASON,
        })
        splits = _first_splits(data)
        stats = splits.get("stat", {}) if splits else {}
        # If pitcher has < 5 IP this season, fall back to prior year
        ip_str = stats.get("inningsPitched", "0.0")
        try:
            parts = str(ip_str).split(".")
            ip = int(parts[0]) + int(parts[1]) / 3.0 if len(parts) > 1 else float(ip_str)
        except Exception:
            ip = 0.0
        if ip < 5:
            return _get_prior_pitcher_stats(pitcher_id) or stats
        return stats
    except Exception:
        return _get_prior_pitcher_stats(pitcher_id)


def _get_prior_pitcher_stats(pitcher_id: int) -> dict:
    try:
        data = _get(f"/people/{pitcher_id}/stats", {
            "stats": "season",
            "group": "pitching",
            "season": config.CURRENT_SEASON - 1,
        })
        splits = _first_splits(data)
        return splits.get("stat", {}) if splits else {}
    except Exception:
        return {}


def get_player_platoon_splits(player_id: int) -> dict:
    """
    L/R platoon HR splits for a batter.
    Returns: {"vs_LHP": hr_rate, "vs_RHP": hr_rate}
    Uses MLB Stats API statSplits endpoint.
    """
    try:
        data = _get(f"/people/{player_id}/stats", {
            "stats": "statSplits",
            "group": "hitting",
            "season": config.CURRENT_SEASON,
            "sitCodes": "vl,vr",
        })
        splits_raw = data.get("stats", [{}])[0].get("splits", [])
        result = {}
        for split in splits_raw:
            code = split.get("split", {}).get("code", "")
            st = split.get("stat", {})
            pa = int(st.get("plateAppearances", 0))
            hr = int(st.get("homeRuns", 0))
            if pa > 0:
                result[code] = hr / pa
        return result  # keys: "vl" = vs LHP, "vr" = vs RHP
    except Exception:
        return {}


def get_player_info(player_id: int) -> dict:
    """Minimal bio â€” bats, position, full name."""
    try:
        data = _get(f"/people/{player_id}", {"hydrate": "currentTeam"})
        people = data.get("people", [])
        return people[0] if people else {}
    except Exception:
        return {}


def _first_splits(data: dict) -> Optional[dict]:
    stats_list = data.get("stats", [])
    if not stats_list:
        return None
    splits = stats_list[0].get("splits", [])
    return splits[0] if splits else None

