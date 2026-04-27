"""
Backtest runner — scores model predictions against actual historical outcomes.

For each historical date we:
  1. Pull actual box score results (hit_hr = True/False per starting batter)
  2. Run the model to get model_prob for each batter
  3. Store (model_prob, hit_hr) pairs for calibration analysis

Look-ahead bias is eliminated by using get_player_stats_as_of / get_pitcher_stats_as_of,
which accumulate game log entries strictly before each game date. No extra API calls
are needed — game logs are already cached by the streak/recent factor fetches.
The only remaining look-ahead source is the Statcast leaderboard (barrel%, exit velo),
which is fetched once at backtest time and reflects the full current season.
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


# Per-date caches: keyed by (player_id, date_str) so each game date gets
# its own accumulated-stats snapshot without cross-date contamination.
_batter_cache:  dict[tuple, tuple[dict, dict]] = {}  # (pid, date) -> (season, recent)
_pitcher_cache: dict[tuple, dict]              = {}  # (pid, date) -> stats


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
            row = _score_player(r, date_str, batter_data, pitcher_data)
            if row:
                scored.append(row)
        except Exception:
            continue
    return scored


def _score_player(r: dict, date_str: str, batter_data: dict, pitcher_data: dict) -> Optional[dict]:
    pid        = r["player_id"]
    cache_key  = (pid, date_str)

    # Fetch stats accumulated up to (but not including) this game date
    if cache_key not in _batter_cache:
        _batter_cache[cache_key] = mlb_stats.get_player_stats_as_of(pid, date_str)
    season_stats, recent_stats = _batter_cache[cache_key]

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

    # Streak factor — games before date_str only
    short_form = mlb_stats.get_player_short_form_as_of(pid, date_str)
    streak_fac = prob.hot_streak_factor(short_form, season_stats)

    # K% suppressor + early-season sparse-data discount
    k_fac      = prob.batter_k_suppressor(season_stats)
    early_supp = prob.early_season_suppressor(season_pa, sc_source)

    # Batter handedness + platoon splits (lru_cached — current season, minor residual look-ahead)
    batter_info = mlb_stats.get_player_info(pid)
    batter_side = batter_info.get("batSide", {}).get("code", "")
    splits      = mlb_stats.get_player_platoon_splits(pid)

    # Park factor — fly-ball adjusted using Statcast fb_pct (mirrors pipeline.py)
    home_team  = r.get("home_team", "")
    pk_factor  = get_park(home_team).get("hr_factor", 1.0)
    pk_factor  = prob.fly_ball_adjusted_park_factor(pk_factor, sc_stats.get("fb_pct"))

    # Pitcher factor — full three-component model (HR/FB + Statcast contact + K/GB)
    pitcher_id   = r.get("pitcher_id")
    pitcher_hand = ""
    if pitcher_id:
        pit_key = (pitcher_id, date_str)
        if pit_key not in _pitcher_cache:
            _pitcher_cache[pit_key] = mlb_stats.get_pitcher_stats_as_of(pitcher_id, date_str)
        pit_stats      = _pitcher_cache[pit_key]
        sc_pit_fac     = statcast_client.pitcher_contact_suppressor(pitcher_id, pitcher_data)
        k_gb_fac       = prob.pitcher_k_gb_suppressor(pit_stats)
        pit_factor     = prob.pitcher_combined_factor(
            prob.pitcher_hr_factor(pit_stats), sc_pit_fac, k_gb_fac
        )
        # Recent form — starts before date_str only
        recent_pit_stats = mlb_stats.get_pitcher_recent_stats_as_of(pitcher_id, date_str)
        recent_pit_fac   = prob.pitcher_recent_factor(recent_pit_stats)
        pit_factor       = max(0.55, min(1.60, pit_factor * recent_pit_fac))
        # Pitcher handedness for platoon (lru_cached)
        pitcher_info = mlb_stats.get_player_info(pitcher_id)
        pitcher_hand = pitcher_info.get("pitchHand", {}).get("code", "")
    else:
        sc_pit_fac = 1.0
        pit_factor = 1.0

    # Platoon factor
    plat_factor = prob.platoon_factor(splits, pitcher_hand, batter_side, season_pa)

    # Batter-pitcher interaction: elite power hitter vs hittable pitcher synergy
    batter_excess  = max(0.0, power_mult - 1.0)
    pitcher_excess = max(0.0, sc_pit_fac - 1.0)
    interaction    = batter_excess * pitcher_excess * 0.35

    hr_rate    = hr_rate * streak_fac * k_fac * early_supp * (1.0 + interaction)

    exp_pa     = prob.expected_pa(r.get("lineup_spot"))
    model_prob = prob.game_hr_probability(
        hr_rate, exp_pa, pk_factor=pk_factor, pitcher_fac=pit_factor,
        plat_factor=plat_factor,
    )

    return {
        **r,
        "model_prob":   round(model_prob, 4),
        "hr_rate":      round(hr_rate, 5),
        "season_pa":    season_pa,
        "sc_source":    sc_source,
        "has_statcast": pid in batter_data,
    }


def clear_cache() -> None:
    """Call between date batches if memory is a concern."""
    _batter_cache.clear()
    _pitcher_cache.clear()
