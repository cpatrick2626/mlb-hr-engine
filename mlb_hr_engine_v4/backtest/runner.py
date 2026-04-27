"""
Backtest runner — scores model predictions against actual historical outcomes.

For each historical date we:
  1. Pull actual box score results (hit_hr = True/False per starting batter)
  2. Run the v3 model to get model_prob for each batter
  3. Store (model_prob, hit_hr) pairs for calibration analysis

Note on look-ahead bias:
  The model uses *current* season stats, not stats as of the historical date.
  In early-season (April), most batters use prior-year stats anyway (PA < 30),
  so bias is minimal. Flag any result with season_pa > 100 as potentially biased.
"""

import sys
import time
from pathlib import Path
from typing import Optional

# Allow imports from parent directory (v3 root)
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients import mlb_stats, statcast as statcast_client
from data.park_factors import get_park
from engine import probability as prob


# Simple in-process cache to avoid re-fetching the same player twice
_season_cache: dict[int, dict] = {}
_recent_cache: dict[int, dict] = {}
_pitcher_cache: dict[int, dict] = {}


def score_date(
    date_str: str,
    results: list[dict],
    batter_data: dict,
    pitcher_data: dict,
) -> list[dict]:
    """
    Given actual game results for a date, add model_prob to each row.
    Returns enriched list with: player_id, player_name, team, opponent,
    lineup_spot, hit_hr, model_prob, season_pa, has_statcast.
    """
    scored = []
    for r in results:
        try:
            row = _score_player(r, batter_data, pitcher_data)
            if row:
                scored.append(row)
        except Exception:
            continue
    return scored


def _score_player(r: dict, batter_data: dict, pitcher_data: dict) -> Optional[dict]:
    pid = r["player_id"]

    # Fetch (and cache) season + recent stats
    if pid not in _season_cache:
        _season_cache[pid] = mlb_stats.get_player_season_stats(pid)
        time.sleep(0.1)
    if pid not in _recent_cache:
        _recent_cache[pid] = mlb_stats.get_player_recent_stats(pid)

    season_stats = _season_cache[pid]
    recent_stats = _recent_cache[pid]
    season_pa = int(season_stats.get("plateAppearances", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))

    if season_pa == 0 and recent_pa == 0:
        return None

    # Base HR rate + Statcast adjustment — mirror pipeline.py exactly
    sc_stats   = dict(batter_data.get(pid) or {})
    sc_pa      = sc_stats.get("pa", 0)
    sc_source  = sc_stats.get("statcast_source", "current" if sc_stats else "none")

    power_mult = statcast_client.batter_power_multiplier(pid, batter_data)
    raw_rate   = prob.base_hr_rate(season_stats, recent_stats, statcast_mult=power_mult)
    hr_rate    = prob.statcast_blended_rate(
        raw_rate, power_mult, season_pa,
        statcast_pa=sc_pa, statcast_source=sc_source,
    )

    # K% suppressor + early-season sparse-data discount
    k_fac      = prob.batter_k_suppressor(season_stats)
    early_supp = prob.early_season_suppressor(season_pa, sc_source)
    hr_rate    = hr_rate * k_fac * early_supp

    # Park factor
    home_team  = r.get("home_team", "")
    pk_factor  = get_park(home_team).get("hr_factor", 1.0)

    # Pitcher factor — full three-component model (HR/FB + Statcast contact + K/GB)
    pitcher_id = r.get("pitcher_id")
    if pitcher_id:
        if pitcher_id not in _pitcher_cache:
            _pitcher_cache[pitcher_id] = mlb_stats.get_pitcher_season_stats(pitcher_id)
            time.sleep(0.05)
        pit_stats  = _pitcher_cache[pitcher_id]
        sc_pit_fac = statcast_client.pitcher_contact_suppressor(pitcher_id, pitcher_data)
        k_gb_fac   = prob.pitcher_k_gb_suppressor(pit_stats)
        pit_factor = prob.pitcher_combined_factor(
            prob.pitcher_hr_factor(pit_stats), sc_pit_fac, k_gb_fac
        )
    else:
        pit_factor = 1.0

    exp_pa     = prob.expected_pa(r.get("lineup_spot"))
    model_prob = prob.game_hr_probability(
        hr_rate, exp_pa, pk_factor=pk_factor, pitcher_fac=pit_factor,
    )

    return {
        **r,
        "model_prob":  round(model_prob, 4),
        "hr_rate":     round(hr_rate, 5),
        "season_pa":   season_pa,
        "sc_source":   sc_source,
        "has_statcast": pid in batter_data,
    }


def clear_cache() -> None:
    """Call between date batches if memory is a concern."""
    _season_cache.clear()
    _recent_cache.clear()
    _pitcher_cache.clear()
