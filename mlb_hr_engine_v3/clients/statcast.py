"""
Baseball Savant (Statcast) client — no API key required.

Pulls aggregate leaderboard data for:
  - Batters: barrel%, exit velocity, hard-hit%, xSLG
  - Pitchers: barrel% against, exit velo against, hard-hit% against

Data is cached in memory for the session (one fetch per run).

Key insight: Statcast metrics (barrel%, exit velo) stabilize in ~50 PA,
far faster than HR/PA (~300 PA). This makes them especially valuable
in early-season models where HR sample sizes are tiny.
"""

import io
import csv
import requests
from functools import lru_cache
from typing import Optional

import config

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; MLB-HR-Engine/2.0)",
    "Accept": "text/csv,application/json,*/*",
})

# League averages (2026 MLB season, statcast leaderboard) used for normalization
LEAGUE_AVG_BARREL_RATE = 0.052    # barrel per PA (5.2%)
LEAGUE_AVG_EXIT_VELO   = 88.9     # mph avg_hit_speed
LEAGUE_AVG_HARD_HIT    = 0.394    # EV > 95 mph per BIP

# Conversion: ~57% of barrels result in HRs
BARREL_TO_HR_RATE = 0.57


def get_batter_statcast(year: int = None) -> dict[int, dict]:
    """
    Fetch batter Statcast leaderboard. Returns dict keyed by MLBAM player_id.
    Falls back to prior year if current year has insufficient data.
    """
    year = year or config.CURRENT_SEASON
    data = _fetch_leaderboard("batter", year)

    # If current season is sparse (< 100 rows), blend with prior year
    if len(data) < 100:
        prior = _fetch_leaderboard("batter", year - 1)
        # Fill in gaps from prior year for players not yet in current year
        for pid, stats in prior.items():
            if pid not in data:
                stats["season"] = year - 1
                data[pid] = stats

    return data


def get_pitcher_statcast(year: int = None) -> dict[int, dict]:
    """Fetch pitcher Statcast leaderboard (quality of contact allowed)."""
    year = year or config.CURRENT_SEASON
    data = _fetch_leaderboard("pitcher", year)
    if len(data) < 50:
        prior = _fetch_leaderboard("pitcher", year - 1)
        for pid, stats in prior.items():
            if pid not in data:
                stats["season"] = year - 1
                data[pid] = stats
    return data


def batter_power_multiplier(player_id: int, batter_data: dict[int, dict]) -> float:
    """
    Return a power multiplier based on barrel% vs league average.
    >1.0 = above-average power (underpriced by raw HR/PA)
    <1.0 = below-average power (overpriced by raw HR/PA)

    Capped at [0.60, 1.60] to prevent extreme values.
    """
    stats = batter_data.get(player_id)
    if not stats:
        return 1.0

    barrel_rate = stats.get("barrel_rate", LEAGUE_AVG_BARREL_RATE)
    ev = stats.get("exit_velocity_avg", LEAGUE_AVG_EXIT_VELO)
    hard_hit = stats.get("hard_hit_pct", LEAGUE_AVG_HARD_HIT)

    # Barrel-based component (strongest predictor)
    barrel_mult = barrel_rate / LEAGUE_AVG_BARREL_RATE

    # Exit velocity component (small secondary boost)
    ev_mult = 1.0 + (ev - LEAGUE_AVG_EXIT_VELO) / 100.0

    # Weighted composite
    composite = barrel_mult * 0.70 + ev_mult * 0.30

    return round(max(0.60, min(1.60, composite)), 3)


def pitcher_contact_suppressor(pitcher_id: int, pitcher_data: dict[int, dict]) -> float:
    """
    Return a contact-quality factor for the pitcher (how hard contact they allow).
    <1.0 = suppresses hard contact (good pitcher)
    >1.0 = allows hard contact (homer-prone pitcher)
    """
    stats = pitcher_data.get(pitcher_id)
    if not stats:
        return 1.0

    barrel_against = stats.get("barrel_rate", LEAGUE_AVG_BARREL_RATE)
    ev_against = stats.get("exit_velocity_avg", LEAGUE_AVG_EXIT_VELO)

    barrel_mult = barrel_against / LEAGUE_AVG_BARREL_RATE
    ev_mult = 1.0 + (ev_against - LEAGUE_AVG_EXIT_VELO) / 100.0

    composite = barrel_mult * 0.65 + ev_mult * 0.35
    return round(max(0.60, min(1.60, composite)), 3)


def statcast_summary(player_id: int, batter_data: dict[int, dict]) -> dict:
    """Return display-ready Statcast summary for a player."""
    stats = batter_data.get(player_id, {})
    brl = stats.get("barrel_rate", 0)
    ev = stats.get("exit_velocity_avg", 0)
    return {
        "barrel_pct": f"{brl*100:.1f}%" if brl else "",
        "exit_velo":  f"{ev:.1f}" if ev else "",
        "hard_hit":   f"{stats.get('hard_hit_pct', 0)*100:.1f}%",
        "season":     stats.get("season", config.CURRENT_SEASON),
    }


# ── Internal ──────────────────────────────────────────────────────────────────

@lru_cache(maxsize=8)
def _fetch_leaderboard(player_type: str, year: int) -> dict:
    """
    Cached fetch of Statcast exit-velocity/barrel leaderboard CSV.
    player_type: "batter" or "pitcher"
    Endpoint columns: brl_pa (barrel/PA%), avg_hit_speed (exit velo), ev95percent (hard hit%)
    """
    url = (
        "https://baseballsavant.mlb.com/leaderboard/statcast"
        f"?type={player_type}&year={year}&position=&team=&min=10&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=20)
        if resp.status_code != 200:
            return {}
        return _parse_leaderboard_csv(resp.text)
    except Exception as e:
        print(f"[statcast] Fetch failed ({player_type} {year}): {e}")
        return {}


def _parse_leaderboard_csv(raw: str) -> dict[int, dict]:
    """Parse Baseball Savant statcast leaderboard CSV keyed by MLBAM player_id."""
    result: dict[int, dict] = {}
    # Strip BOM if present
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))

    for row in reader:
        try:
            pid = int(row.get("player_id", 0))
            if not pid:
                continue

            bip = int(row.get("attempts", 0) or 0)
            # brl_pa is barrel per PA as a percentage — convert to rate
            barrel_rate_pa = float(row.get("brl_pa", 0) or 0) / 100.0
            barrel_bip_rate = float(row.get("brl_percent", 0) or 0) / 100.0
            # ev95percent: % of batted balls with EV > 95 mph (hard-hit proxy)
            hard_hit = float(row.get("ev95percent", 0) or 0) / 100.0
            ev = float(row.get("avg_hit_speed", 0) or 0)

            result[pid] = {
                "pa": bip,
                "barrel_rate": barrel_rate_pa,
                "barrel_bip_rate": barrel_bip_rate,
                "hard_hit_pct": hard_hit,
                "exit_velocity_avg": ev,
                "season": config.CURRENT_SEASON,
            }
        except (ValueError, KeyError):
            continue

    return result
