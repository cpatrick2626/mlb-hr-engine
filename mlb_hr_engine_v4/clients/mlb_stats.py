"""
MLB Stats API client â€" free, no API key required.
Docs: https://statsapi.mlb.com/docs/
"""

import sys
import time
import requests
from datetime import date, timedelta
from typing import Optional

import config

MLB_API = "https://statsapi.mlb.com/api/v1"
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Codex-HR-Engine/1.0"})

# Session-level cache for game logs â€" avoids duplicate API calls when
# get_player_recent_stats() and get_player_short_form() are both called.
_GAME_LOG_CACHE: dict[int, list] = {}

# Pitcher game log cache — shared by get_pitcher_recent_stats() and
# get_pitcher_days_rest(), which previously made identical requests independently.
_PITCHER_GAME_LOG_CACHE: dict[int, list] = {}

# Bulk stats caches - populated by bulk fetch operations
_BULK_SEASON_STATS_CACHE: dict[int, dict] = {}
_BULK_RECENT_STATS_CACHE: dict[int, dict] = {}
_BULK_PITCHER_STATS_CACHE: dict[int, dict] = {}

# Success-only individual caches — only store non-empty results so transient
# API failures don't permanently block retries for the rest of the session.
_player_season_cache:  dict[int, dict] = {}
_pitcher_season_cache: dict[int, dict] = {}
_platoon_splits_cache: dict[int, dict] = {}
_player_info_cache:    dict[int, dict] = {}


def _pitcher_game_log_splits(pitcher_id: int) -> list:
    if pitcher_id not in _PITCHER_GAME_LOG_CACHE:
        try:
            data = _get(f"/people/{pitcher_id}/stats", {
                "stats": "gameLog", "group": "pitching",
                "season": config.CURRENT_SEASON,
                "limit": 162,
            })
            splits = data.get("stats", [{}])[0].get("splits", [])
            _PITCHER_GAME_LOG_CACHE[pitcher_id] = sorted(
                splits, key=lambda s: s.get("date", ""), reverse=True
            )
        except Exception as e:
            # Don't cache: a transient failure shouldn't permanently suppress this pitcher
            print(f"[mlb_stats] pitcher game log failed (id={pitcher_id}): {e}")
            return []
    return _PITCHER_GAME_LOG_CACHE[pitcher_id]


def _game_log_splits(player_id: int) -> list:
    if player_id not in _GAME_LOG_CACHE:
        try:
            data = _get(f"/people/{player_id}/stats", {
                "stats": "gameLog", "group": "hitting",
                "season": config.CURRENT_SEASON,
                "limit": 162,   # full season; without this MLB API silently caps results
            })
            splits = data.get("stats", [{}])[0].get("splits", [])
            # Normalize to newest-first regardless of API sort order
            _GAME_LOG_CACHE[player_id] = sorted(
                splits, key=lambda s: s.get("date", ""), reverse=True
            )
        except Exception as e:
            # Don't cache: a transient failure shouldn't permanently suppress this batter
            print(f"[mlb_stats] batter game log failed (id={player_id}): {e}")
            return []
    return _GAME_LOG_CACHE[player_id]


def parse_ip(innings_raw) -> float:
    """Parse MLB Stats API inningsPitched ('6.2' means 6⅔ IP) to a float."""
    try:
        if isinstance(innings_raw, (int, float)):
            return float(innings_raw)
        parts = str(innings_raw).split(".")
        return int(parts[0]) + int(parts[1]) / 3.0 if len(parts) > 1 else float(innings_raw)
    except Exception:
        return 0.0


def _get(path: str, params: dict = None) -> dict:
    url = f"{MLB_API}{path}"
    for attempt in range(3):
        try:
            resp = _SESSION.get(url, params=params, timeout=15)
            if resp.status_code in (404, 403):
                return {}  # permanent client error — don't retry
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)  # 1s, then 2s


def get_today_pitcher_map(target_date: Optional[str] = None) -> dict[str, dict]:
    """
    Return {batting_team_abbr: {"id": pitcher_id, "name": pitcher_name}} for today.
    Each batting team is mapped to the opposing pitcher they face.
    Used to detect probable-pitcher changes after the model first loaded.
    """
    games = get_today_schedule(target_date)
    pitcher_map: dict[str, dict] = {}
    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        hp = game.get("home_pitcher", {})   # home pitcher → away batters face him
        ap = game.get("away_pitcher", {})   # away pitcher → home batters face him
        if ap and home:
            pitcher_map[home] = {"id": ap.get("id"), "name": ap.get("name", "TBD")}
        if hp and away:
            pitcher_map[away] = {"id": hp.get("id"), "name": hp.get("name", "TBD")}
    return pitcher_map


def get_confirmed_lineup_player_ids(target_date: Optional[str] = None) -> set[int]:
    """Return set of player IDs currently confirmed in any posted lineup for target_date.
    Used for late-scratch detection: if a slip player's ID is absent, they may be scratched.
    """
    games = get_today_schedule(target_date)
    ids: set[int] = set()
    for game in games:
        for lineup in [game.get("home_lineup", []), game.get("away_lineup", [])]:
            for batter in lineup:
                if batter.get("id"):
                    ids.add(batter["id"])
    return ids


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
                "game_time_utc": g.get("gameDate", ""),  # ISO datetime UTC e.g. "2026-04-26T22:05:00Z"
                "home_team": home_abbr,
                "away_team": away_abbr,
                "home_team_id": home.get("team", {}).get("id"),
                "away_team_id": away.get("team", {}).get("id"),
                "home_pitcher": _parse_pitcher(home_pitcher),
                "away_pitcher": _parse_pitcher(away_pitcher),
                "home_lineup": home_lineup,
                "away_lineup": away_lineup,
                "venue_team": home_abbr,
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
    if player_id in _player_season_cache:
        return _player_season_cache[player_id]

    # Check bulk cache first
    if player_id in _BULK_SEASON_STATS_CACHE:
        stats = _BULK_SEASON_STATS_CACHE[player_id]
        pa = int(stats.get("plateAppearances", 0))
        if pa < 30:
            prior = _get_prior_season_stats(player_id)
            if prior:
                _player_season_cache[player_id] = prior
                return prior
        _player_season_cache[player_id] = stats
        return stats

    # Fall back to individual fetch
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
                _player_season_cache[player_id] = prior
                return prior
        if stats:
            _player_season_cache[player_id] = stats
        return stats
    except Exception as e:
        print(f"[mlb_stats] batter season stats failed (id={player_id}): {e}")
        result = _get_prior_season_stats(player_id)
        if result:
            _player_season_cache[player_id] = result
        return result


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
    except Exception as e:
        print(f"[mlb_stats] batter prior-season stats failed (id={player_id}): {e}")
        return {}


def get_player_recent_stats(player_id: int) -> dict:
    """Aggregate hitting stats over last RECENT_GAMES games (newest-first, game-count window)."""
    # Check bulk cache first
    if player_id in _BULK_RECENT_STATS_CACHE:
        return _BULK_RECENT_STATS_CACHE[player_id]

    # Fall back to individual fetch
    splits = _game_log_splits(player_id)  # already sorted newest-first
    recent = splits[:config.RECENT_GAMES]
    totals = {"homeRuns": 0, "plateAppearances": 0, "atBats": 0,
              "sluggingPercentage": 0, "avg": 0, "games": 0}
    total_ab = 0
    total_hits = 0
    total_tb = 0
    for split in recent:
        st = split.get("stat", {})
        totals["homeRuns"]         += int(st.get("homeRuns", 0))
        totals["plateAppearances"] += int(st.get("plateAppearances", 0))
        ab = int(st.get("atBats", 0))
        totals["atBats"]           += ab
        totals["games"]            += 1
        total_ab   += ab
        total_hits += int(st.get("hits", 0))
        total_tb   += int(st.get("totalBases", 0))
    if total_ab > 0:
        totals["avg"]              = total_hits / total_ab
        totals["sluggingPercentage"] = total_tb / total_ab
    return totals


def get_pitcher_season_stats(pitcher_id: int) -> dict:
    """
    Pitching stats — current season with prior-year fallback.
    Includes airOuts for HR/FB calculation (v2 enhancement).
    """
    if pitcher_id in _pitcher_season_cache:
        return _pitcher_season_cache[pitcher_id]

    def _cache(result: dict) -> dict:
        if result:
            _pitcher_season_cache[pitcher_id] = result
        return result

    # Check bulk cache first
    if pitcher_id in _BULK_PITCHER_STATS_CACHE:
        stats = _BULK_PITCHER_STATS_CACHE[pitcher_id]
        if parse_ip(stats.get("inningsPitched", "0.0")) < 5:
            return _cache(_get_prior_pitcher_stats(pitcher_id) or stats)
        return _cache(stats)

    # Fall back to individual fetch
    try:
        data = _get(f"/people/{pitcher_id}/stats", {
            "stats": "season",
            "group": "pitching",
            "season": config.CURRENT_SEASON,
        })
        splits = _first_splits(data)
        stats = splits.get("stat", {}) if splits else {}
        if parse_ip(stats.get("inningsPitched", "0.0")) < 5:
            return _cache(_get_prior_pitcher_stats(pitcher_id) or stats)
        return _cache(stats)
    except Exception as e:
        print(f"[mlb_stats] pitcher season stats failed (id={pitcher_id}): {e}")
        return _cache(_get_prior_pitcher_stats(pitcher_id))


def _get_prior_pitcher_stats(pitcher_id: int) -> dict:
    try:
        data = _get(f"/people/{pitcher_id}/stats", {
            "stats": "season",
            "group": "pitching",
            "season": config.CURRENT_SEASON - 1,
        })
        splits = _first_splits(data)
        return splits.get("stat", {}) if splits else {}
    except Exception as e:
        print(f"[mlb_stats] pitcher prior-season stats failed (id={pitcher_id}): {e}")
        return {}


def get_player_short_form(player_id: int, days: int = 14) -> dict:
    """
    Aggregate hitting stats over last SHORT_FORM_GAMES games.
    Game-count window is more consistent than calendar days for streak detection.
    The `days` param is kept for backward compatibility but not used.
    """
    splits = _game_log_splits(player_id)  # already sorted newest-first
    recent = splits[:config.SHORT_FORM_GAMES]
    totals = {"homeRuns": 0, "plateAppearances": 0, "atBats": 0, "games": 0}
    for split in recent:
        st = split.get("stat", {})
        totals["homeRuns"]         += int(st.get("homeRuns", 0))
        totals["plateAppearances"] += int(st.get("plateAppearances", 0))
        totals["atBats"]           += int(st.get("atBats", 0))
        totals["games"]            += 1
    return totals


def get_player_platoon_splits(player_id: int) -> dict:
    """
    L/R platoon HR splits for a batter.
    Returns: {"vl": hr_rate, "vr": hr_rate, "vl_pa": int, "vr_pa": int}
    Uses MLB Stats API statSplits endpoint.
    """
    if player_id in _platoon_splits_cache:
        return _platoon_splits_cache[player_id]
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
            st   = split.get("stat", {})
            pa   = int(st.get("plateAppearances", 0))
            hr   = int(st.get("homeRuns", 0))
            if pa > 0:
                result[code]           = hr / pa
                result[f"{code}_pa"]   = pa
        if result:
            _platoon_splits_cache[player_id] = result
        return result
    except Exception as e:
        print(f"[mlb_stats] platoon splits failed (id={player_id}): {e}")
        return {}


def get_pitcher_recent_stats(pitcher_id: int, days: int = 30) -> dict:
    """
    Aggregate pitching stats over last PITCHER_RECENT_GAMES starts.
    Game-count window is more consistent than calendar days.
    The `days` param is kept for backward compatibility but not used.
    """
    splits = _pitcher_game_log_splits(pitcher_id)
    recent = splits[:config.PITCHER_RECENT_GAMES]
    totals: dict = {"homeRuns": 0, "inningsPitched": 0.0, "battersFaced": 0,
                    "strikeOuts": 0, "groundOuts": 0, "airOuts": 0, "baseOnBalls": 0}
    for split in recent:
        st = split.get("stat", {})
        totals["homeRuns"]     += int(st.get("homeRuns", 0))
        totals["battersFaced"] += int(st.get("battersFaced", 0))
        totals["strikeOuts"]   += int(st.get("strikeOuts", 0))
        totals["groundOuts"]   += int(st.get("groundOuts", 0))
        totals["airOuts"]      += int(st.get("airOuts", 0))
        totals["baseOnBalls"]  += int(st.get("baseOnBalls", 0))
        totals["inningsPitched"] += parse_ip(st.get("inningsPitched", "0.0"))
    return totals


# ── Backtest as-of functions ───────────────────────────────────────────────────
# These eliminate look-ahead bias by using only game log entries before date_str.
# The game logs are already cached (fetched for streak/recent factors), so no
# extra API calls are needed.

def get_player_stats_as_of(player_id: int, date_str: str) -> tuple[dict, dict]:
    """
    Return (season_stats, recent_stats) using only games with date < date_str.
    Falls back to prior-year stats if accumulated PA < 30 (early season).
    """
    splits = _game_log_splits(player_id)
    prior  = [s for s in splits if s.get("date", "") < date_str]

    season = _acc_hitting(prior)
    if int(season.get("plateAppearances", 0)) < 30:
        prior_yr = _get_prior_season_stats(player_id)
        if prior_yr:
            return prior_yr, {}

    recent = _acc_hitting(prior[:config.RECENT_GAMES])
    return season, recent


def get_pitcher_stats_as_of(pitcher_id: int, date_str: str) -> dict:
    """Accumulated pitcher stats using only starts with date < date_str."""
    splits = _pitcher_game_log_splits(pitcher_id)
    prior  = [s for s in splits if s.get("date", "") < date_str]
    return _acc_pitching(prior)


def get_player_short_form_as_of(player_id: int, date_str: str) -> dict:
    """Streak stats from last SHORT_FORM_GAMES games before date_str."""
    splits = _game_log_splits(player_id)
    prior  = [s for s in splits if s.get("date", "") < date_str]
    recent = prior[:config.SHORT_FORM_GAMES]
    totals = {"homeRuns": 0, "plateAppearances": 0, "atBats": 0, "games": 0}
    for split in recent:
        st = split.get("stat", {})
        totals["homeRuns"]          += int(st.get("homeRuns", 0))
        totals["plateAppearances"]  += int(st.get("plateAppearances", 0))
        totals["atBats"]            += int(st.get("atBats", 0))
        totals["games"]             += 1
    return totals


def _acc_hitting(splits: list) -> dict:
    """Accumulate per-game hitting splits into a season-stats-shaped dict."""
    keys = ("plateAppearances", "atBats", "hits", "homeRuns",
            "doubles", "triples", "strikeOuts", "baseOnBalls")
    totals: dict = {k: 0 for k in keys}
    for s in splits:
        st = s.get("stat", {})
        for k in keys:
            totals[k] += int(st.get(k, 0))

    ab = totals["atBats"]
    hr = totals["homeRuns"]
    db = totals["doubles"]
    tr = totals["triples"]
    hi = totals["hits"]
    bb = totals["baseOnBalls"]
    pa = totals["plateAppearances"]

    if ab > 0:
        tb = hi + db + 2*tr + 3*hr  # hi counts all hits once; +1/+2/+3 extra bases for 2B/3B/HR
        totals["avg"]                = round(hi / ab, 3)
        totals["sluggingPercentage"] = round(tb / ab, 3)
    else:
        totals["avg"]                = 0.0
        totals["sluggingPercentage"] = 0.0
    if pa > 0:
        totals["onBasePercentage"] = round((hi + bb) / pa, 3)
    else:
        totals["onBasePercentage"] = 0.0
    return totals


def get_pitcher_recent_stats_as_of(pitcher_id: int, date_str: str) -> dict:
    """Recent pitcher stats from last PITCHER_RECENT_GAMES starts before date_str."""
    splits = _pitcher_game_log_splits(pitcher_id)
    prior  = [s for s in splits if s.get("date", "") < date_str]
    recent = prior[:config.PITCHER_RECENT_GAMES]
    return _acc_pitching(recent)


def _acc_pitching(splits: list) -> dict:
    """Accumulate per-start pitching splits into a pitcher-stats-shaped dict."""
    totals: dict = {"homeRuns": 0, "inningsPitched": 0.0, "battersFaced": 0,
                    "strikeOuts": 0, "groundOuts": 0, "airOuts": 0, "baseOnBalls": 0}
    for s in splits:
        st = s.get("stat", {})
        totals["homeRuns"]     += int(st.get("homeRuns", 0))
        totals["battersFaced"] += int(st.get("battersFaced", 0))
        totals["strikeOuts"]   += int(st.get("strikeOuts", 0))
        totals["groundOuts"]   += int(st.get("groundOuts", 0))
        totals["airOuts"]      += int(st.get("airOuts", 0))
        totals["baseOnBalls"]  += int(st.get("baseOnBalls", 0))
        totals["inningsPitched"] += parse_ip(st.get("inningsPitched", "0.0"))
    # Keep inningsPitched as a float so pitcher_recent_factor can use < comparisons directly.
    # pitcher_hr_factor also accepts float (handled via isinstance check in probability.py).
    return totals


def get_pitcher_days_rest(pitcher_id: int) -> int:
    """Days since pitcher's last start. Returns 5 (standard rotation) if unknown."""
    splits = _pitcher_game_log_splits(pitcher_id)
    if not splits:
        return 5
    last_date_str = splits[0].get("date", "")
    if not last_date_str:
        return 5
    try:
        last_date = date.fromisoformat(last_date_str)
        today = date.fromisoformat(config.TARGET_DATE) if config.TARGET_DATE else date.today()
        return max(0, (today - last_date).days)
    except Exception:
        return 5


def get_player_info(player_id: int) -> dict:
    '''Minimal bio: bats, position, full name.'''
    if player_id in _player_info_cache:
        return _player_info_cache[player_id]
    try:
        data = _get(f"/people/{player_id}", {"hydrate": "currentTeam"})
        people = data.get("people", [])
        result = people[0] if people else {}
        if result:
            _player_info_cache[player_id] = result
        return result
    except Exception as e:
        print(f"[mlb_stats] player info failed (id={player_id}): {e}")
        return {}


def get_team_active_roster(team_id: int) -> list[dict]:
    """
    Fetch active roster batters as a lineup fallback when lineups aren't posted yet.
    Returns non-pitchers only; lineup_spot=None so DEFAULT_PA is used.
    """
    try:
        data = _get(f"/teams/{team_id}/roster", {"rosterType": "active"})
        roster = []
        for entry in data.get("roster", []):
            if entry.get("position", {}).get("type") == "Pitcher":
                continue
            person = entry.get("person", {})
            pid  = person.get("id")
            name = person.get("fullName", "")
            if pid and name:
                roster.append({"id": pid, "name": name, "lineup_spot": None})
        return roster
    except Exception:
        return []


def _first_splits(data: dict) -> Optional[dict]:
    stats_list = data.get("stats", [])
    if not stats_list:
        return None
    splits = stats_list[0].get("splits", [])
    return splits[0] if splits else None


# ── Bulk fetch functions for optimization ────────────────────────────────────

def bulk_fetch_player_stats(player_ids: set[int]) -> None:
    """
    Pre-fetch and cache stats for multiple players in bulk.
    Dramatically reduces API calls by using hydrated requests.

    Args:
        player_ids: Set of player IDs to fetch stats for
    """
    if not player_ids:
        return

    # Clear previous bulk caches
    _BULK_SEASON_STATS_CACHE.clear()
    _BULK_RECENT_STATS_CACHE.clear()

    # Convert to list and batch process (MLB API has URL length limits)
    player_list = list(player_ids)
    batch_size = 50  # Process 50 players at a time to avoid URL limits

    for i in range(0, len(player_list), batch_size):
        batch = player_list[i:i + batch_size]
        _fetch_batch_stats(batch)


def _fetch_batch_stats(player_ids: list[int]) -> None:
    """Fetch stats for a batch of players using hydrated requests."""

    # Build comma-separated list of player IDs
    player_ids_str = ",".join(str(pid) for pid in player_ids)

    try:
        # Fetch season and game log stats in a single hydrated request
        data = _get(f"/people", {
            "personIds": player_ids_str,
            "hydrate": f"stats(group=[hitting],type=[season,gameLog],season={config.CURRENT_SEASON}),currentTeam"
        })

        people = data.get("people", [])

        for person in people:
            player_id = person.get("id")
            if not player_id:
                continue

            stats_list = person.get("stats", [])

            # Extract season stats
            season_stats = {}
            game_logs = []

            for stat_group in stats_list:
                stat_type = stat_group.get("type", {}).get("displayName", "")

                if stat_type == "season":
                    splits = stat_group.get("splits", [])
                    if splits:
                        season_stats = splits[0].get("stat", {})

                elif stat_type == "gameLog":
                    game_logs = stat_group.get("splits", [])
                    # Sort game logs by date (newest first)
                    game_logs = sorted(game_logs, key=lambda s: s.get("date", ""), reverse=True)

            # Cache season stats
            _BULK_SEASON_STATS_CACHE[player_id] = season_stats

            if game_logs:
                _GAME_LOG_CACHE[player_id] = game_logs
                recent_stats = _calculate_recent_from_logs(game_logs)
                _BULK_RECENT_STATS_CACHE[player_id] = recent_stats
            else:
                _BULK_RECENT_STATS_CACHE[player_id] = {}

    except Exception as e:
        # Fall back to individual fetching if bulk fails
        print(f"[mlb_stats] Bulk fetch failed for batch, falling back: {e}")


def _calculate_recent_from_logs(game_logs: list) -> dict:
    """Aggregate stats from the last RECENT_GAMES games (game-count window, not calendar days)."""
    recent_logs = [log.get("stat", {}) for log in game_logs[:config.RECENT_GAMES]]

    if not recent_logs:
        return {}

    # Aggregate stats
    totals = {
        "plateAppearances": 0,
        "atBats": 0,
        "hits": 0,
        "homeRuns": 0,
        "doubles": 0,
        "triples": 0,
        "baseOnBalls": 0,  # MLB API field name (not "walks")
        "strikeOuts": 0,
        "rbi": 0,
        "runs": 0,
    }

    for stat in recent_logs:
        for key in totals:
            totals[key] += int(stat.get(key, 0))

    # Calculate percentages
    if totals["atBats"] > 0:
        hi, db, tr, hr = totals["hits"], totals["doubles"], totals["triples"], totals["homeRuns"]
        totals["avg"]                = round(hi / totals["atBats"], 3)
        totals["sluggingPercentage"] = round((hi + db + 2*tr + 3*hr) / totals["atBats"], 3)
    else:
        totals["avg"] = 0.0
        totals["sluggingPercentage"] = 0.0

    if totals["plateAppearances"] > 0:
        totals["onBasePercentage"] = round(
            (totals["hits"] + totals["baseOnBalls"]) / totals["plateAppearances"], 3
        )
        totals["ops"] = totals["onBasePercentage"] + totals["sluggingPercentage"]
    else:
        totals["onBasePercentage"] = 0.0
        totals["ops"] = 0.0

    return totals


def bulk_fetch_pitcher_stats(pitcher_ids: set[int]) -> None:
    """
    Pre-fetch and cache stats for multiple pitchers in bulk.

    Args:
        pitcher_ids: Set of pitcher IDs to fetch stats for
    """
    if not pitcher_ids:
        return

    _BULK_PITCHER_STATS_CACHE.clear()

    pitcher_list = list(pitcher_ids)
    batch_size = 50

    for i in range(0, len(pitcher_list), batch_size):
        batch = pitcher_list[i:i + batch_size]
        _fetch_batch_pitcher_stats(batch)


def _fetch_batch_pitcher_stats(pitcher_ids: list[int]) -> None:
    """Fetch stats for a batch of pitchers."""

    pitcher_ids_str = ",".join(str(pid) for pid in pitcher_ids)

    try:
        data = _get(f"/people", {
            "personIds": pitcher_ids_str,
            "hydrate": f"stats(group=[pitching],type=[season,gameLog],season={config.CURRENT_SEASON})"
        })

        people = data.get("people", [])

        for person in people:
            pitcher_id = person.get("id")
            if not pitcher_id:
                continue

            stats_list = person.get("stats", [])

            for stat_group in stats_list:
                stat_type = stat_group.get("type", {}).get("displayName", "")

                if stat_type == "season":
                    splits = stat_group.get("splits", [])
                    if splits:
                        _BULK_PITCHER_STATS_CACHE[pitcher_id] = splits[0].get("stat", {})

                elif stat_type == "gameLog":
                    game_logs = stat_group.get("splits", [])
                    game_logs = sorted(game_logs, key=lambda s: s.get("date", ""), reverse=True)
                    _PITCHER_GAME_LOG_CACHE[pitcher_id] = game_logs

    except Exception as e:
        print(f"[mlb_stats] Bulk pitcher fetch failed for batch: {e}")


def clear_all_caches() -> None:
    """Clear all in-process caches. Call this before a Force Refresh so
    the next load fetches fresh player stats, platoon splits, and game logs."""
    _GAME_LOG_CACHE.clear()
    _PITCHER_GAME_LOG_CACHE.clear()
    _BULK_SEASON_STATS_CACHE.clear()
    _BULK_RECENT_STATS_CACHE.clear()
    _BULK_PITCHER_STATS_CACHE.clear()
    _player_season_cache.clear()
    _pitcher_season_cache.clear()
    _platoon_splits_cache.clear()
    _player_info_cache.clear()
