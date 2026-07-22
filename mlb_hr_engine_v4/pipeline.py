"""
Shared data pipeline — used by both main.py (CLI) and app.py (Streamlit).

Call load_game_data() once per session. It fetches everything and returns
a single dict that both the CLI display and the Streamlit UI can consume.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta, datetime, timezone
from rapidfuzz import fuzz, process as fuzz_process
import logging
import math
import os
import unicodedata

import config
from config import (
    MATCHUP_QUALITY_ELITE_THRESHOLD,
    MATCHUP_QUALITY_STRONG_THRESHOLD,
    MATCHUP_QUALITY_AVG_THRESHOLD,
    PITCHER_VULNERABILITY_HR9_THRESHOLD,
)
from clients import mlb_stats, odds_api
from clients import weather as weather_client
from clients import statcast as statcast_client
from clients.pitch_mix import get_h2h
from data.park_factors import get_park
from engine import market as mkt, probability as prob, ev as ev_engine, sizing, filters
from engine import calibration as _cal
from output import ranker, parlay as parlay_engine
from output.parlay import build_profile_parlays
try:
    from tracking import adaptive_weights as _aw
except ImportError:
    _aw = None

# Frozen 2026-07-09 pending deliberate calibration replay — prevents
# auto-mutation of prob_scale (and min_ev_pct/recent_weight) during analysis.
# Flip to False to re-enable auto-learning once calibration is ready.
AUTO_LEARN_FROZEN = True

# Typical batting-slot cache — populated once per slate run by _fetch_typical_slots()
# before the parallel profile phase. Read-only during threading. {player_id: mode_slot}
_TYPICAL_SLOT_CACHE: dict[int, int] = {}

_LOG = logging.getLogger(__name__)
_WAREHOUSE_EXECUTOR = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="batter-stat-history",
)


def _warehouse_json_value(value):
    """Deeply normalize a value for JSONB without dropping payload fields."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _warehouse_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_warehouse_json_value(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    # NumPy/pandas scalars expose item(); normalize the underlying Python value.
    try:
        scalar = value.item()
    except (AttributeError, TypeError, ValueError):
        scalar = value
    if scalar is not value:
        return _warehouse_json_value(scalar)

    # Preserve otherwise unsupported values as text rather than deleting fields.
    return str(value)


def _write_batter_stat_history(
    slate_date: str,
    run_ts: str,
    players: tuple[dict, ...],
) -> None:
    """Background worker: batch-upsert one immutable unified slate snapshot."""
    try:
        rows = []
        for player in players:
            batter_id = player.get("player_id")
            game_pk = player.get("game_pk")
            if batter_id is None or game_pk is None:
                raise ValueError(
                    "warehouse capture requires player_id and game_pk for every batter"
                )
            rows.append({
                "slate_date": slate_date,
                "run_ts": run_ts,
                "batter_id": int(batter_id),
                "game_pk": int(game_pk),
                "raw_payload": _warehouse_json_value(player),
            })

        if not rows:
            return

        # A dedicated client keeps this background write isolated from the
        # board/cache persistence client used concurrently by API/cron callers.
        from supabase import create_client

        warehouse_client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
        warehouse_client.table("batter_stat_history").upsert(
            rows,
            on_conflict="slate_date,run_ts,batter_id,game_pk",
        ).execute()
        _LOG.info(
            "[warehouse] batter_stat_history captured %d rows for %s at %s",
            len(rows), slate_date, run_ts,
        )
    except Exception as exc:
        _LOG.warning(
            "[warehouse] batter_stat_history capture failed (non-fatal): %s",
            exc,
            exc_info=True,
        )


def _schedule_batter_stat_history_capture(slate_date: str, players: list[dict]) -> None:
    """Submit capture without waiting; board generation always continues."""
    run_ts = datetime.now(timezone.utc).isoformat()
    try:
        _WAREHOUSE_EXECUTOR.submit(
            _write_batter_stat_history,
            slate_date,
            run_ts,
            tuple(players),
        )
    except Exception as exc:
        _LOG.warning(
            "[warehouse] batter_stat_history scheduling failed (non-fatal): %s",
            exc,
            exc_info=True,
        )


# ── Core helpers (same logic as v3 main.py, extracted here) ──────────────────

def _fetch_typical_slots(
    player_ids: set,
    trailing_days: int = 7,
    reference_date: "date | None" = None,
) -> dict[int, int]:
    """
    For each player_id, compute their mode batting slot over the past trailing_days days.
    Calls the MLB schedule API directly (bypassing get_today_schedule's Final-game filter)
    so completed games' confirmed lineups are included.
    reference_date: ET-anchored date from the caller (avoids UTC off-by-one on Fly.io).
    Returns {player_id: mode_slot}. Used for MAIN projected PA — display-only.
    """
    from collections import Counter
    from datetime import date as _date, timedelta

    slots: dict[int, list[int]] = {}
    today = reference_date or _date.today()
    for i in range(1, trailing_days + 1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            data = mlb_stats._get("/schedule", {"sportId": 1, "date": d, "hydrate": "lineups,team"})
            for date_entry in data.get("dates", []):
                for game in date_entry.get("games", []):
                    lineups = game.get("lineups", {})
                    for side in ("homePlayers", "awayPlayers"):
                        for pos, batter in enumerate(lineups.get(side, []), 1):
                            pid = batter.get("id")
                            if pid and pid in player_ids:
                                slots.setdefault(pid, []).append(pos)
        except Exception as e:
            print(f"[pipeline] typical-slot fetch for {d} failed: {e}")

    return {pid: Counter(lst).most_common(1)[0][0] for pid, lst in slots.items()}


def _matchup_quality_tier(
    model_prob: float,
    barrel_pct: float,
    exit_velo: float | None,
    pitcher_hr9: float,
    park_factor: float,
) -> str:
    """
    Deterministic matchup quality tier for Full Slate display.
    Batter-threat axis only (two-axis model: pitcher vulnerability is the
    separate pitcher_vuln field — see _pitcher_vulnerability_tier).
    Uses MAIN factors only. No JIG/HVY logic.

    Inputs:
    - model_prob: calibrated game HR probability (0.0-1.0)
    - barrel_pct: Statcast barrel rate (0.0-1.0)
    - exit_velo: exit velocity (float, mph) or None — reserved, currently unused
    - pitcher_hr9: pitcher HR/9 ratio — reserved, currently unused
    - park_factor: park HR factor (0.7-1.3 typical) — reserved, currently unused

    Returns: one of {ELITE, STRONG, AVG, WEAK}

    Logic:
    - ELITE: model_prob >= 0.15 (top-tier threat)
    - STRONG: model_prob >= 0.10 (solid threat)
    - WEAK: model_prob < 0.05 OR barrel_pct < 0.04 (low power/low threat)
    - AVG: everything else (playable/neutral)
    """
    model_prob = float(model_prob or 0.0)
    barrel_pct = float(barrel_pct or 0.0)
    exit_velo = float(exit_velo or 0.0)
    pitcher_hr9 = float(pitcher_hr9 or 0.0)
    park_factor = float(park_factor or 1.0)

    # ELITE: top batter threat (15%+ HR probability from model)
    if model_prob >= MATCHUP_QUALITY_ELITE_THRESHOLD:
        return "ELITE"

    # STRONG: solid threat (10-15% HR probability)
    if model_prob >= MATCHUP_QUALITY_STRONG_THRESHOLD:
        return "STRONG"

    # WEAK: low power or very low HR probability
    if model_prob < MATCHUP_QUALITY_AVG_THRESHOLD or barrel_pct < 0.04:
        return "WEAK"

    # AVG: everything else
    return "AVG"


def _pitcher_vulnerability_tier(pitcher_hr9) -> str:
    """
    Pitcher-vulnerability axis (two-axis model, separate from matchup_quality).
    TARGET: pitcher_hr9 >= 2.2 (top ~5% most hittable — best HR matchup).
    NEUTRAL: otherwise; missing/null pitcher_hr9 is never TARGET.
    Display-only — never combined numerically with the batter-threat tier
    (pitcher_hr9 already feeds model_prob; combining would double-count).
    """
    if float(pitcher_hr9 or 0.0) >= PITCHER_VULNERABILITY_HR9_THRESHOLD:
        return "TARGET"
    return "NEUTRAL"


def _utc_to_local_hour(game_time_utc: str, tz_offset: int) -> int:
    """Parse game_time_utc ('2026-04-26T22:05:00Z') and return local game hour (0-23)."""
    try:
        utc_hour = int(game_time_utc[11:13])
        return (utc_hour + tz_offset) % 24
    except (IndexError, ValueError):
        return 19  # fallback to 7pm local


def _safe_float(val) -> "float | None":
    """Convert a Statcast value that may be '--', None, or a numeric string to float."""
    try:
        return float(val) if val and str(val) != '--' else None
    except (ValueError, TypeError):
        return None


def _recent_form_games_from_cache(player_id: int) -> list[dict]:
    """Format up to five cached batter game logs for display-only persistence."""
    cached_games = mlb_stats._GAME_LOG_CACHE.get(player_id, [])
    if not isinstance(cached_games, list):
        return []

    recent_games = []
    for split in cached_games[:5]:
        if not isinstance(split, dict):
            continue
        stat = split.get("stat") or {}
        if not isinstance(stat, dict):
            stat = {}
        ab = mlb_stats._safe_int(stat.get("atBats"))
        recent_games.append({
            "date": split.get("date"),
            "hr": mlb_stats._safe_int(stat.get("homeRuns")),
            "avg": round(mlb_stats._safe_int(stat.get("hits")) / ab, 3) if ab else None,
            "slg": round(mlb_stats._safe_int(stat.get("totalBases")) / ab, 3) if ab else None,
            "pa": mlb_stats._safe_int(stat.get("plateAppearances")),
        })
    return recent_games


def _build_player_profile(
    player_id, player_name, lineup_spot, team, opponent,
    home_team, pitcher, batter_data, pitcher_data,
    game_time_utc: str = "",
    bat_tracking_data: dict = None,
):
    season_stats    = mlb_stats.get_player_season_stats(player_id)
    recent_stats    = mlb_stats.get_player_recent_stats(player_id)
    short_form      = mlb_stats.get_player_short_form(player_id, days=14)
    season_pa = int(season_stats.get("plateAppearances", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    if season_pa == 0 and recent_pa == 0:
        print(f"[pipeline] zero-PA drop: {player_name} (id={player_id})")
        return None

    power_mult = statcast_client.batter_power_multiplier(player_id, batter_data)
    sc_stats   = dict(batter_data.get(player_id) or {})
    sc_pa      = sc_stats.get("pa", 0)
    # Default to "current" only when the player IS in batter_data (tier-1 rows have no key set);
    # players absent entirely get "none" so confidence_score awards no Statcast bonus.
    sc_source  = sc_stats.get("statcast_source", "current" if sc_stats else "none")
    sc_barrel  = float(sc_stats.get("barrel_rate") or 0.0)
    raw_rate   = prob.base_hr_rate(season_stats, recent_stats, statcast_mult=power_mult,
                                    recent_weight=_aw.get("recent_weight") if _aw is not None else None,
                                    barrel_rate=sc_barrel)
    hr_rate    = prob.statcast_blended_rate(
        raw_rate, power_mult, season_pa,
        statcast_pa=sc_pa, statcast_source=sc_source,
    )
    sc_summary = statcast_client.statcast_summary(player_id, batter_data)

    # Derived contact-quality fields used by profile-based parlay scoring
    # Compute SLG and OBP from available counting stats
    # MLB Stats API bulk group omits sluggingPercentage/onBasePercentage
    _ab  = int(season_stats.get("atBats", 0) or 0)
    _h   = int(season_stats.get("hits", 0) or 0)
    _2b  = int(season_stats.get("doubles", 0) or 0)
    _3b  = int(season_stats.get("triples", 0) or 0)
    _hr  = int(season_stats.get("homeRuns", 0) or 0)
    _bb  = int(season_stats.get("baseOnBalls", 0) or 0)
    _hbp = int(season_stats.get("hitByPitch", 0) or 0)
    _1b  = _h - _2b - _3b - _hr
    _tb  = _1b + (2 * _2b) + (3 * _3b) + (4 * _hr)
    actual_slg = round(_tb / _ab, 3) if _ab > 0 else 0.0
    # OBP approximation — SF not in bulk group, excluded
    actual_obp = round((_h + _bb + _hbp) / (_ab + _bb + _hbp), 3) \
               if (_ab + _bb + _hbp) > 0 else 0.0
    xba_float  = _safe_float(sc_stats.get("xba"))
    xslg_float = _safe_float(sc_stats.get("xslg"))

    xiso       = (round(xslg_float - xba_float, 3)
                  if (xslg_float is not None and xba_float is not None) else None)
    xslg_diff  = (round(xslg_float - actual_slg, 3)
                  if xslg_float is not None else None)

    streak_fac = prob.hot_streak_factor(short_form, season_stats)
    k_fac      = prob.batter_k_suppressor(season_stats)

    # Batter handedness needed for park factor — fetch before pk_factor computation
    batter_info = mlb_stats.get_player_info(player_id)
    batter_side = batter_info.get("batSide", {}).get("code", "")
    splits            = mlb_stats.get_player_platoon_splits(player_id)
    multiseason_splits = mlb_stats.get_player_multiseason_splits(player_id)

    exp_pa    = prob.expected_pa(lineup_spot)
    pk_factor = prob.park_factor(home_team, batter_side)
    pk_factor = prob.fly_ball_adjusted_park_factor(pk_factor, sc_stats.get("fb_pct"))

    pitcher_id   = pitcher.get("id")
    pitcher_name = pitcher.get("name", "TBD")
    pitcher_hand = ""
    pitcher_stats = {}
    recent_pitcher_stats = {}
    pitcher_days_rest = 5
    if pitcher_id:
        pitcher_stats        = mlb_stats.get_pitcher_season_stats(pitcher_id)
        recent_pitcher_stats = mlb_stats.get_pitcher_recent_stats(pitcher_id)
        pitcher_days_rest    = mlb_stats.get_pitcher_days_rest(pitcher_id)
        info = mlb_stats.get_player_info(pitcher_id)
        pitcher_hand = info.get("pitchHand", {}).get("code", "")

    hr_fb_fac      = prob.pitcher_hr_factor(pitcher_stats)
    sc_pit_fac     = statcast_client.pitcher_contact_suppressor(pitcher_id or 0, pitcher_data)
    k_gb_fac       = prob.pitcher_k_gb_suppressor(pitcher_stats)
    pit_factor     = prob.pitcher_combined_factor(hr_fb_fac, sc_pit_fac, k_gb_fac)
    recent_pit_fac = prob.pitcher_recent_factor(recent_pitcher_stats)
    pit_factor     = max(0.55, min(1.60, pit_factor * recent_pit_fac))
    fatigue_fac    = prob.pitcher_fatigue_factor(pitcher_days_rest)
    pit_factor     = max(0.55, min(1.60, pit_factor * fatigue_fac))

    # Non-linear pitcher factor attenuation.
    # Middle band [0.85, 1.15]: compress by PITCHER_FACTOR_SCALE (low signal, high noise).
    # Tails (<0.85 or >1.15): pass through unattenuated (genuine suppressor/vulnerability signal).
    # This preserves dangerous pitcher signal (HR/9 2.5+) while reducing noise in the middle.
    _pfs = getattr(config, "PITCHER_FACTOR_SCALE", 1.0)
    if _pfs < 1.0:
        deviation = pit_factor - 1.0
        if abs(deviation) <= 0.15:
            # Middle band: compress toward 1.0
            pit_factor = 1.0 + deviation * _pfs
        else:
            # Tail: preserve direction, compress only the middle portion
            middle = 0.15 * math.copysign(1.0, deviation)
            tail = deviation - middle
            pit_factor = 1.0 + middle * _pfs + tail
        pit_factor = max(0.55, min(1.60, pit_factor))

    # Pitcher HR/9 for confidence threshold flag
    pit_ip = mlb_stats.parse_ip(pitcher_stats.get("inningsPitched", "0.0"))
    pit_hrs  = int(pitcher_stats.get("homeRuns", 0))
    pitcher_hr9 = round((pit_hrs / pit_ip) * 9.0, 2) if pit_ip >= 5 else 0.0

    park_data  = get_park(home_team)
    is_dome    = home_team in weather_client.DOME_TEAMS
    cf_bearing = park_data.get("cf_bearing", 0.0)
    game_hour  = _utc_to_local_hour(game_time_utc, park_data.get("tz_offset", -5))
    weather    = weather_client.get_game_weather(park_data["lat"], park_data["lon"], game_hour)
    _pull_pct_raw = sc_stats.get("pull_pct")
    _pull_pct_float = float(_pull_pct_raw) if _pull_pct_raw is not None else None
    w_factor   = max(0.80, min(1.20,
        weather_client.temp_factor(weather["temp_f"])
        * weather_client.wind_factor(weather["wind_mph"], weather["wind_deg"], is_dome, cf_bearing,
                                     batter_side=batter_side, pull_pct=_pull_pct_float)
        * weather_client.humidity_factor(weather["humidity_pct"])
    ))

    plat_factor = prob.platoon_factor(splits, pitcher_hand, batter_side, season_pa)

    # H2H career multiplier
    h2h_data   = get_h2h(pitcher_id or 0, player_id)
    h2h_mult   = prob.h2h_factor(h2h_data)

    # Stage 6: batter × pitcher interaction term (non-additive matchup synergy).
    # Uses pit_factor (full combined signal) instead of sc_pit_fac alone — sc_pit_fac
    # is already embedded in pit_factor at 40% weight, so using it directly double-counted
    # the Statcast signal. Coefficient adaptive (default 0.20, tuned by auto-learn).
    batter_excess  = max(0.0, power_mult - 1.0)
    pitcher_excess = max(0.0, pit_factor - 1.0)
    _ic = _aw.get("interaction_coeff", 0.20) if _aw is not None else 0.20
    interaction    = batter_excess * pitcher_excess * _ic

    early_supp    = prob.early_season_suppressor(season_pa, sc_source)
    adjusted_rate = min(0.15, hr_rate * streak_fac * k_fac * early_supp * h2h_mult * (1.0 + interaction))
    model_prob = prob.game_hr_probability(
        adjusted_rate, exp_pa,
        pk_factor=pk_factor, pitcher_fac=pit_factor,
        w_factor=w_factor, plat_factor=plat_factor,
        power_mult=power_mult,
    )
    # When lineup hasn't been posted (spot is None), the player may not start.
    # 0.82 discount ≈ 82% probability of actually being in the lineup.
    if not lineup_spot:
        model_prob = round(model_prob * 0.82, 4)

    # Apply adaptive calibration scale (moves model_prob toward observed hit rate)
    model_prob = round(_aw.apply_prob_scale(model_prob), 4) if _aw is not None else model_prob
    # Apply post-model probability calibration (monotone → ranking preserved)
    # barrel_rate passed for elite tier Platt (ELITE_PLATT_ENABLED in config.py)
    model_prob = round(_cal.apply_calibration(model_prob, barrel_rate=sc_barrel), 4)

    # ── MAIN projected values (display-only; never fed into scoring/EV/filters) ──
    # Projection: same calc sequence without ×0.82 lineup penalty, using typical slot PA.
    # pitcher_id must be known (probable announced) or we emit null — no pitcher = no projection.
    # When lineup is already posted: projected == current (confirmed single value).
    _proj_model_prob: "float | None" = None
    _proj_pa_src: "str | None" = None
    if pitcher_id is not None:
        if lineup_spot:
            # Lineup confirmed: projection collapses to the real scored value
            _proj_model_prob = model_prob
            _proj_pa_src = "confirmed"
        else:
            _typ_slot = _TYPICAL_SLOT_CACHE.get(player_id)
            _proj_exp_pa = prob.expected_pa(_typ_slot) if _typ_slot else config.DEFAULT_PA
            _proj_pa_src = "typical-slot" if _typ_slot else "default"
            # Identical calc as real model_prob: game_hr_probability → prob_scale → calibration
            # adjusted_rate is already finalized above; omit ×0.82 (projection assumes player starts)
            _proj_raw = prob.game_hr_probability(
                adjusted_rate, _proj_exp_pa,
                pk_factor=pk_factor, pitcher_fac=pit_factor,
                w_factor=w_factor, plat_factor=plat_factor,
                power_mult=power_mult,
            )
            if _aw is not None:
                _proj_raw = round(_aw.apply_prob_scale(_proj_raw), 4)
            _proj_model_prob = round(_cal.apply_calibration(_proj_raw, barrel_rate=sc_barrel), 4)

    # Additional fields for Full Slate table display
    season_hits = int(season_stats.get("hits", 0))
    season_ab = int(season_stats.get("atBats", 0))
    season_avg = round(season_hits / season_ab, 3) if season_ab > 0 else 0.0

    xwoba_raw = _safe_float(sc_stats.get("xwoba"))

    season_k = int(season_stats.get("strikeOuts", 0))
    season_sf = int(season_stats.get("sacFlies", 0))
    season_hr = int(season_stats.get("homeRuns", 0))
    season_air_outs = int(season_stats.get("airOuts", 0) or 0)
    season_fly_balls = season_hr + season_air_outs
    hrfb = round(season_hr / season_fly_balls * 100, 1) if season_fly_balls > 0 else None
    season_babip = round(
        (season_hits - season_hr) / (season_ab - season_k - season_hr + season_sf), 3
    ) if (season_ab - season_k - season_hr + season_sf) > 0 else None

    pull_pct_val = _safe_float(sc_stats.get("pull_pct"))
    oppo_pct_val = _safe_float(sc_stats.get("oppo_pct"))
    if pull_pct_val is not None and oppo_pct_val is not None:
        center_pct_raw = 1.0 - pull_pct_val - oppo_pct_val
        center_pct = round(max(0.0, center_pct_raw) * 100, 1)
    else:
        center_pct = None

    # Real per-hand batter splits (display only — never feeds model_prob/scoring).
    # Faced hand: RHP -> vr split, LHP -> vl split. Emitted at any PA count;
    # the consumer applies the 30-PA reliability rule using the pa field.
    _ss = splits.get("split_stats") or {}
    _vs_l = _ss.get("vl") or {}
    _vs_r = _ss.get("vr") or {}
    if pitcher_hand.upper().startswith("L"):
        _faced, _faced_hand = _vs_l, "L"
    elif pitcher_hand.upper().startswith("R"):
        _faced, _faced_hand = _vs_r, "R"
    else:
        _faced, _faced_hand = {}, None

    matchup_quality = _matchup_quality_tier(
        model_prob=model_prob,
        barrel_pct=sc_barrel,
        exit_velo=_safe_float(sc_stats.get("exit_velocity_avg")),
        pitcher_hr9=pitcher_hr9,
        park_factor=pk_factor,
    )

    return {
        "player_id": player_id, "player_name": player_name,
        "team": team, "opponent": opponent, "home_team": home_team,
        "pitcher_name": pitcher_name, "pitcher_id": pitcher_id,
        "pitcher_confirmed": pitcher_id is not None,
        "lineup_spot": lineup_spot, "expected_pa": round(exp_pa, 1),
        "lineup_confirmed": lineup_spot is not None,
        # MAIN projected display fields (display-only; never read by scoring/EV/filters)
        "model_prob_projected": _proj_model_prob,
        "hrprob_projected": round(_proj_model_prob * 100, 1) if _proj_model_prob is not None else None,
        "projected_pa_source": _proj_pa_src,
        "season_pa": season_pa, "season_hr": int(season_stats.get("homeRuns", 0)),
        "hrfb": hrfb,
        "recent_pa": recent_pa, "hr_rate": round(hr_rate, 5),
        "raw_hr_rate": round(raw_rate, 5), "statcast_power_mult": power_mult,
        "has_statcast": (player_id in batter_data
                         and batter_data[player_id].get("statcast_source", "current") == "current"),
        "statcast_source": sc_source,
        "barrel_pct": sc_summary["barrel_pct"],
        "exit_velo": sc_summary["exit_velo"], "hard_hit": sc_summary["hard_hit"],
        "sweet_spot_pct": sc_summary["sweet_spot_pct"],
        "fb_pct": sc_summary["fb_pct"], "gb_pct": sc_summary["gb_pct"],
        "ld_pct": sc_summary["ld_pct"], "pull_pct": sc_summary["pull_pct"],
        "pull_air_pct": sc_summary.get("pull_air_pct"),
        "max_ev": sc_summary.get("max_ev"),
        "oppo_pct": sc_summary["oppo_pct"],
        "park_factor": round(pk_factor, 3), "pitcher_factor": round(pit_factor, 3),
        "pitcher_days_rest": pitcher_days_rest, "fatigue_factor": round(fatigue_fac, 3),
        "weather_factor": round(w_factor, 3), "platoon_factor": round(plat_factor, 3),
        "h2h_factor": round(h2h_mult, 4),
        "batter_side": batter_side,
        "pitcher_hand": pitcher_hand,
        # Real hand-specific batter splits (display only — not read by scoring)
        "vs_hand":       _faced_hand,
        "vs_hand_avg":   _faced.get("avg"),
        "vs_hand_slg":   _faced.get("slg"),
        "vs_hand_iso":   _faced.get("iso"),
        "vs_hand_hr":    _faced.get("hr"),
        "vs_hand_hr_pa": _faced.get("hr_pa"),
        "vs_hand_pa":    _faced.get("pa"),
        "vs_lhp_avg":    _vs_l.get("avg"),
        "vs_lhp_slg":    _vs_l.get("slg"),
        "vs_lhp_iso":    _vs_l.get("iso"),
        "vs_lhp_hr":     _vs_l.get("hr"),
        "vs_lhp_hr_pa":  _vs_l.get("hr_pa"),
        "vs_lhp_pa":     _vs_l.get("pa"),
        "vs_rhp_avg":    _vs_r.get("avg"),
        "vs_rhp_slg":    _vs_r.get("slg"),
        "vs_rhp_iso":    _vs_r.get("iso"),
        "vs_rhp_hr":     _vs_r.get("hr"),
        "vs_rhp_hr_pa":  _vs_r.get("hr_pa"),
        "vs_rhp_pa":     _vs_r.get("pa"),
        # Multi-season vs-hand splits (display only — never read by scoring)
        "multi_season_vs_hand": multiseason_splits,
        "model_prob": round(model_prob, 4), "weather": weather,
        "pitcher_hr9": pitcher_hr9,
        "short_form_pa": int(short_form.get("plateAppearances", 0)),
        "short_form_hr": int(short_form.get("homeRuns", 0)),
        # Display-only cache snapshot; never read by scoring, filters, or ranking.
        "recent_form_games": _recent_form_games_from_cache(player_id),
        "streak_factor": round(streak_fac, 3),
        "k_factor": round(k_fac, 3),
        "early_season_suppressor": round(early_supp, 3),
        "avg_launch_angle": sc_summary.get("avg_launch_angle"),
        "xslg": sc_summary.get("xslg"),
        "xba": xba_float,
        "xiso": xiso,
        "xslg_diff": xslg_diff,
        "actual_slg": round(actual_slg, 3),
        "actual_obp": round(actual_obp, 3),
        "batting_avg": season_avg,
        "babip": season_babip,
        "xwoba": xwoba_raw,
        "center_pct": center_pct,
        "matchup_quality": matchup_quality,
        "pitcher_vuln": _pitcher_vulnerability_tier(pitcher_hr9),
        "batter_bb_pct": round(_bb / season_pa, 3) if season_pa > 0 else None,
        "batter_k_pct":  round(season_k / season_pa, 3) if season_pa > 0 else None,
        # Bat-tracking summary is display-only; never read by scoring, filters, or ranking.
        **statcast_client.bat_tracking_summary(player_id, bat_tracking_data or {}),
        # Pitcher season stats (display only — not used in model)
        "pitcher_era":    _safe_float(pitcher_stats.get("era")),
        "pitcher_whip":   _safe_float(pitcher_stats.get("whip")),
        "pitcher_k_pct":  (round(int(pitcher_stats.get("strikeOuts", 0)) /
                                  int(pitcher_stats.get("battersFaced", 0)) * 100, 1)
                           if int(pitcher_stats.get("battersFaced") or 0) > 0 else None),
        "pitcher_bb_pct": (round(int(pitcher_stats.get("baseOnBalls", 0)) /
                                  int(pitcher_stats.get("battersFaced", 0)) * 100, 1)
                           if int(pitcher_stats.get("battersFaced") or 0) > 0 else None),
        # Pitcher statcast allowed (display only)
        "pitcher_barrel_allowed": _safe_float((pitcher_data.get(pitcher_id) or {}).get("barrel_rate")),
        "pitcher_hh_allowed":     _safe_float((pitcher_data.get(pitcher_id) or {}).get("hard_hit_pct")),
        "pitcher_fb_allowed":     _safe_float((pitcher_data.get(pitcher_id) or {}).get("fb_pct")),
        "pitcher_gb_allowed":     _safe_float((pitcher_data.get(pitcher_id) or {}).get("gb_pct")),
    }


def _ascii_fold(name: str) -> str:
    """Strip accents for robust fuzzy matching (e.g. 'José' → 'Jose')."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")

_NAME_MATCH_CACHE: dict[str, str | None] = {}


def _build_odds_lookup(all_props):
    """Pre-build a lookup structure for O(1) odds matching."""
    if not all_props:
        return {}, []

    # Group props by player name; store both original and ascii-folded key
    odds_by_player = {}
    for prop in all_props:
        name = prop["player_name"]
        key  = _ascii_fold(name)
        if key not in odds_by_player:
            odds_by_player[key] = []
        odds_by_player[key].append(prop)

    unique_names = list(odds_by_player.keys())
    return odds_by_player, unique_names


def _select_own_event_props(player, matches):
    """Doubleheader disambiguation: a name-matched props pool spanning multiple
    Odds API events means a DH sibling's lines merged into one pool. Keep only
    the props for the event whose teams match this player's matchup; among DH
    twin events (same matchup twice) pick the one whose commence_time is nearest
    the player's game start — same rule as _attach_fd_links. Returns None when
    the pool can't be cleanly narrowed (unmappable teams, missing commence_time)
    so the caller falls back to the pooled match instead of dropping odds."""
    home = player.get("home_team")
    away = player.get("team") if player.get("team") != home else player.get("opponent")
    by_event: dict[str, list[dict]] = {}
    for p in matches:
        by_event.setdefault(p.get("game_id"), []).append(p)
    candidates = []
    for props in by_event.values():
        rep = props[0]
        e_home = odds_api.TEAM_NAME_TO_ABBR.get(rep.get("home_team", ""))
        e_away = odds_api.TEAM_NAME_TO_ABBR.get(rep.get("away_team", ""))
        if e_home == home and e_away == away:
            candidates.append(props)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    def _dist(props):
        try:
            a = datetime.fromisoformat((player.get("game_time_utc") or "").replace("Z", "+00:00"))
            b = datetime.fromisoformat((props[0].get("commence_time") or "").replace("Z", "+00:00"))
            return abs((a - b).total_seconds())
        except Exception:
            return float("inf")
    best = min(candidates, key=_dist)
    if _dist(best) == float("inf"):
        return None
    return best


def _match_odds(player, odds_lookup, unique_names):
    """Match odds using pre-built lookup structure (O(1) after fuzzy match)."""
    if not odds_lookup:
        return player

    # Fold accents before matching so 'José' == 'Jose' at the fuzzy layer
    folded_name = _ascii_fold(player["player_name"])
    if folded_name not in _NAME_MATCH_CACHE:
        # 85 threshold: catches middle-initial differences ("Michael A. Taylor" ↔ "Michael Taylor")
        # while still preventing false matches between distinct names.
        m = fuzz_process.extractOne(
            folded_name, unique_names,
            scorer=fuzz.token_sort_ratio, score_cutoff=85,
        )
        _NAME_MATCH_CACHE[folded_name] = m[0] if m else None
    matched_name = _NAME_MATCH_CACHE[folded_name]
    if not matched_name:
        return player

    matches = odds_lookup.get(matched_name, [])
    if not matches:
        return player

    # DH guard: only fires when the name-matched pool spans >1 Odds API event.
    # Single-event pools (the non-DH case) take the unchanged path below.
    if len({p.get("game_id") for p in matches}) > 1:
        own = _select_own_event_props(player, matches)
        if own:
            matches = own

    prices  = [p["price"] for p in matches]
    summary = mkt.market_summary(prices)
    best    = max(matches, key=lambda x: x["price"])
    fd_matches = [p for p in matches if p.get("bookmaker") == "fanduel"]
    fd_odds = max(fd_matches, key=lambda x: x["price"])["price"] if fd_matches else None
    # Deduplicate per book: keep best price per bookmaker for the comparison table
    book_best: dict[str, int] = {}
    for prop in matches:
        bk = prop.get("bookmaker", "")
        if bk and (bk not in book_best or prop["price"] > book_best[bk]):
            book_best[bk] = prop["price"]

    # Dynamic per-book vig: more accurate than global VIG_FACTOR when book identity is known
    fixed_nvp = round(summary.get("no_vig_prob_consensus", 0), 4)
    vig_by_book: dict[str, float] = {}
    if config.DYNAMIC_VIG_ENABLED and book_best:
        dyn_summary = mkt.market_summary_dynamic(book_best)
        market_nvp  = round(dyn_summary.get("no_vig_prob_dynamic", fixed_nvp), 4)
        vig_by_book = dyn_summary.get("vig_by_book", {})
    else:
        market_nvp  = fixed_nvp

    player.update({
        "best_american":           best["price"], "best_bookmaker": best.get("bookmaker", ""),
        "all_prices":              prices, "n_books": summary.get("n_books", 1),
        "prices_by_book":          book_best,   # {bookmaker: american_odds} for comparison table
        # market_no_vig_prob is the primary EV/edge baseline (dynamic when DYNAMIC_VIG_ENABLED)
        "market_no_vig_prob":      market_nvp,
        "market_no_vig_prob_fixed": fixed_nvp,  # always fixed-vig value for comparison display
        "vig_by_book":             vig_by_book,  # {book: vig_fraction} used
        "market_implied_avg":      round(summary.get("implied_prob_avg", 0), 4),
        "fanduel_american":        fd_odds,
    })
    return player


def _build_fd_link_map() -> dict[tuple[str, str], list[dict]]:
    """Map (away_abbr, home_abbr) → FanDuel deep-link entries from the odds fetch.
    Display/handoff only — never read by scoring. Unmapped team names are skipped
    so unmatched games simply keep null links."""
    fd_map: dict[tuple[str, str], list[dict]] = {}
    try:
        for entry in odds_api.get_fd_links():
            home = odds_api.TEAM_NAME_TO_ABBR.get(entry.get("home_team", ""))
            away = odds_api.TEAM_NAME_TO_ABBR.get(entry.get("away_team", ""))
            if not home or not away:
                continue
            fd_map.setdefault((away, home), []).append(entry)
    except Exception as e:
        print(f"[pipeline] fd link map skipped: {e}")
    return fd_map


def _attach_fd_links(player, fd_link_map):
    """Attach fd_event_link / fd_event_sid / fd_bet_link to a player row.
    Pure display passthrough for the FanDuel handoff — not read by scoring.
    Absent links stay None; the frontend falls back to name search."""
    player.setdefault("fd_event_link", None)
    player.setdefault("fd_event_sid", None)
    player.setdefault("fd_bet_link", None)
    if not fd_link_map:
        return
    home = player.get("home_team")
    away = player.get("team") if player.get("team") != home else player.get("opponent")
    entries = fd_link_map.get((away, home))
    if not entries:
        return
    entry = entries[0]
    if len(entries) > 1:
        # Doubleheader: same matchup twice today — pick the event whose
        # commence_time is closest to this player's game start.
        def _dist(e):
            try:
                a = datetime.fromisoformat((player.get("game_time_utc") or "").replace("Z", "+00:00"))
                b = datetime.fromisoformat((e.get("commence_time") or "").replace("Z", "+00:00"))
                return abs((a - b).total_seconds())
            except Exception:
                return float("inf")
        entry = min(entries, key=_dist)
    player["fd_event_link"] = entry.get("event_link")
    player["fd_event_sid"]  = entry.get("event_sid")
    # Opportunistic outcome-level bet link (FD rarely posts these — absence is normal)
    bet_links = entry.get("bet_links") or {}
    if bet_links:
        folded = _ascii_fold(player.get("player_name", ""))
        for nm, link in bet_links.items():
            if _ascii_fold(nm) == folded:
                player["fd_bet_link"] = link
                break


def _enrich_with_ev(player):
    if not player.get("best_american"):
        return player
    dec_odds = mkt.american_to_decimal(player["best_american"])
    model_p  = player["model_prob"]
    market_p = player.get("market_no_vig_prob", 0)

    # edge_pct uses the full model signal (odds-independent)
    player["edge_pct"] = ev_engine.edge_pct(model_p, market_p)

    # EV% is capped so long-shot odds (+2000, +3000) can't amplify a small
    # probability gap into absurd triple-digit EV values.
    # Cap: model cannot claim more than 1.4x the market's true probability.
    # At 1.4x the math produces max ~45% EV regardless of odds length.
    ev_model_p = min(model_p, market_p * 1.4) if market_p > 0 else model_p
    player["ev_pct"] = ev_engine.expected_value_pct(ev_model_p, dec_odds)

    barrel_pct_str = str(player.get("barrel_pct", "")).replace("%", "").strip()
    try:
        barrel_raw = (
            float(barrel_pct_str) / 100.0
            if barrel_pct_str and barrel_pct_str not in ("--", "0", "0.0")
            else config.LEAGUE_AVG_BARREL_RATE
        )
    except (ValueError, TypeError):
        barrel_raw = config.LEAGUE_AVG_BARREL_RATE

    try:
        pitcher_hr9 = float(player.get("pitcher_hr9", 0) or 0)
    except (ValueError, TypeError):
        pitcher_hr9 = 0.0

    player["confidence"] = prob.confidence_score(
        player.get("season_pa", 0),
        model_p, market_p,
        statcast_source=player.get("statcast_source", "none"),
        barrel_rate=barrel_raw,
        pitcher_hr9=pitcher_hr9,
        lineup_confirmed=bool(player.get("lineup_spot")),
        n_books=player.get("n_books", 1),
        platoon_factor=float(player.get("platoon_factor", 1.0) or 1.0),
    )
    player["bet_dollars"] = sizing.bet_dollars(model_p, player["best_american"])
    return player


def serializable(players: list) -> list:
    """Strip non-JSON-serializable fields (weather dict, sets, bytes) for JSON dumps."""
    return [
        {k: v for k, v in p.items() if k != "weather" and not isinstance(v, (set, bytes))}
        for p in players
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def load_game_data(
    target_date: str = None,
    progress_cb=None,       # optional callable(str) for status messages
) -> dict:
    """
    Full pipeline: schedule → Statcast → per-player profiles → odds → EV → filters → rank.
    Returns a dict consumed by both main.py and app.py.
    """
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    _ET = timezone(timedelta(hours=-4))  # EDT (Apr–Oct)
    game_date = target_date or (config.TARGET_DATE or datetime.now(_ET).strftime("%Y-%m-%d"))

    # Clear stale name-match cache so expired None entries from a previous run
    # (e.g., a run where props were empty or quota-exhausted) don't block matching.
    _NAME_MATCH_CACHE.clear()

    # Run adaptive learning if new settled picks are available since last run
    if AUTO_LEARN_FROZEN:
        print("[pipeline] auto_apply_safe skipped: AUTO_LEARN_FROZEN=True")
    else:
        try:
            from tracking import auto_learn as _al
            result = _al.auto_apply_safe()
            if result.get("applied"):
                if _aw is not None:
                    _aw.invalidate_cache()
                _cb(f"Adaptive weights updated: {', '.join(result['applied'])}")
        except Exception as _e:
            print(f"[pipeline] auto_apply_safe skipped: {_e}")

    # Fetch schedule and odds in parallel for improved performance
    _cb("Fetching schedule and odds concurrently...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both fetch tasks concurrently
        future_schedule = executor.submit(mlb_stats.get_today_schedule, game_date)
        future_odds = executor.submit(odds_api.get_hr_odds_all_games)

        # Collect schedule result
        try:
            games = future_schedule.result()
        except Exception as e:
            print(f"[pipeline] schedule fetch failed: {e}")
            games = []

    # Validate game dates — reject stale cached games from wrong date
    valid_games = []
    for g in games:
        g_date = g.get("game_date") or (g.get("game_time_utc", "")[:10] if g.get("game_time_utc") else "")
        if g_date and g_date != game_date:
            print(f"[pipeline] WARNING: skipping game {g.get('game_pk')} dated {g_date} (expected {game_date})")
            continue
        valid_games.append(g)
    games = valid_games

    # Collect odds result with error handling
    try:
        all_props, odds_source, odds_quota = future_odds.result()
    except Exception:
        all_props, odds_source, odds_quota = [], "none", {"used": None, "remaining": None}

    # Collect all player and pitcher IDs from lineups first (for Statcast filtering)
    _cb("Collecting lineup players...")
    batter_ids = set()
    pitcher_ids = set()

    # Pre-scan games to collect all player IDs; cache rosters to avoid double API calls
    _roster_cache: dict[int, list] = {}
    for game in games:
        # Add starting pitchers
        if game.get("home_pitcher", {}).get("id"):
            pitcher_ids.add(game["home_pitcher"]["id"])
        if game.get("away_pitcher", {}).get("id"):
            pitcher_ids.add(game["away_pitcher"]["id"])

        # Add batters from lineups
        for lineup, tid in [
            (game.get("home_lineup", []), game.get("home_team_id")),
            (game.get("away_lineup", []), game.get("away_team_id")),
        ]:
            if lineup:
                for batter in lineup:
                    if batter.get("id"):
                        batter_ids.add(batter["id"])
            elif tid:
                if tid not in _roster_cache:
                    _roster_cache[tid] = mlb_stats.get_team_active_roster(tid)
                for player in _roster_cache[tid]:
                    if player.get("id"):
                        batter_ids.add(player["id"])

    # Fetch Statcast and MLB stats in parallel
    _cb(f"Loading data for {len(batter_ids)} batters, {len(pitcher_ids)} pitchers...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(statcast_client.get_batter_statcast, player_ids=batter_ids): "batter_statcast",
            executor.submit(statcast_client.get_pitcher_statcast, player_ids=pitcher_ids): "pitcher_statcast",
            executor.submit(mlb_stats.bulk_fetch_player_stats, batter_ids): "mlb_player_stats",
            executor.submit(mlb_stats.bulk_fetch_pitcher_stats, pitcher_ids): "mlb_pitcher_stats",
            executor.submit(statcast_client.get_bat_tracking): "bat_tracking",
        }

        results = {}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"Error fetching {key}: {e}")
                results[key] = {} if key in ("batter_statcast", "pitcher_statcast") else None

    # Batted-ball data is already merged into batter_data/pitcher_data by get_*_statcast()
    batter_data      = results.get("batter_statcast", {})
    pitcher_data     = results.get("pitcher_statcast", {})
    bat_tracking_data = results.get("bat_tracking", {})

    if not batter_data:
        print("[pipeline] WARNING: Statcast batter data is empty — all power multipliers default to 1.0")
        _cb("⚠️ Statcast unavailable — running without power adjustment (MLB stats only)")
    if not pitcher_data:
        print("[pipeline] WARNING: Statcast pitcher data is empty — pitcher contact suppressor defaults to 1.0")

    # Collect tasks first so roster fallbacks run before the parallel phase.
    tasks: list[tuple] = []
    for game in games:
        home, away = game["home_team"], game["away_team"]
        game_time_utc = game.get("game_time_utc", "")
        for lineup, team, opp, team_id, opp_pitcher in [
            (game["home_lineup"], home, away, game.get("home_team_id"), game.get("away_pitcher", {})),
            (game["away_lineup"], away, home, game.get("away_team_id"), game.get("home_pitcher", {})),
        ]:
            if not lineup:
                if team_id:
                    if team_id not in _roster_cache:
                        _roster_cache[team_id] = mlb_stats.get_team_active_roster(team_id)
                    lineup = _roster_cache[team_id]
                if not lineup:
                    print(f"[pipeline] WARNING: no lineup and empty roster fallback for {team} (team_id={team_id}) — skipping")
                    continue
            for batter in lineup:
                pid  = batter.get("id")
                name = batter.get("name", "Unknown")
                if not pid:
                    continue
                tasks.append((pid, name, batter.get("lineup_spot"), team, opp, home, opp_pitcher,
                              game_time_utc, game.get("game_pk"), game.get("status", "Scheduled")))

    # Typical-slot fetch for MAIN projected values (display-only)
    # Runs after tasks are collected so we know which player_ids to look up.
    # Populated before the profile thread pool so reads are safe across threads.
    global _TYPICAL_SLOT_CACHE
    _TYPICAL_SLOT_CACHE.clear()
    _cb("Fetching typical batting slots for MAIN projection...")
    try:
        _task_pids = {t[0] for t in tasks}
        _TYPICAL_SLOT_CACHE.update(_fetch_typical_slots(
            _task_pids,
            reference_date=datetime.now(_ET).date(),
        ))
        print(f"[pipeline] typical-slot cache: {len(_TYPICAL_SLOT_CACHE)}/{len(_task_pids)} players resolved")
    except Exception as _ts_err:
        print(f"[pipeline] typical-slot fetch failed (projection disabled): {_ts_err}")

    # Pre-warm weather cache: fetch each unique (lat, lon, hour) combo in parallel
    # before the 16-thread profile pool starts, so threads never race on the same park.
    _unique_wx = {
        (get_park(home_team)["lat"], get_park(home_team)["lon"],
         _utc_to_local_hour(game_time_utc, get_park(home_team).get("tz_offset", -5)))
        for _, _, _, _, _, home_team, _, game_time_utc, _, _ in tasks
    }
    if _unique_wx:
        with ThreadPoolExecutor(max_workers=min(len(_unique_wx), 8)) as _wx_exec:
            list(_wx_exec.map(lambda t: weather_client.get_game_weather(*t), _unique_wx))

    _cb(f"Building profiles for {len(tasks)} players...")

    _drop_no_profile = [0]  # mutable counter: profiles that returned None (zero-PA or other)

    def _profile(args: tuple):
        pid, name, spot, team, opp, home_team, opp_pitcher, game_time_utc, game_pk, game_status = args
        try:
            profile = _build_player_profile(
                pid, name, spot, team, opp, home_team, opp_pitcher,
                batter_data, pitcher_data,
                game_time_utc=game_time_utc,
                bat_tracking_data=bat_tracking_data,
            )
            if profile is None:
                _drop_no_profile[0] += 1
            if profile:
                profile["game_time_utc"] = game_time_utc
                profile["game_pk"]       = game_pk
                profile["game_status"]   = game_status
            return profile
        except Exception as e:
            print(f"[pipeline] profile error for {name} ({pid}): {e}")
            return None

    all_players = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        for p in executor.map(_profile, tasks):
            if p:
                all_players.append(p)

    _cb("Computing EV...")
    # Pre-build odds lookup structure once (O(n))
    odds_lookup, unique_names = _build_odds_lookup(all_props)
    print(f"[pipeline] odds props: {len(all_props)} lines | {len(unique_names)} unique players")

    # FanDuel deep links keyed by team matchup (display/handoff only)
    fd_link_map = _build_fd_link_map()

    # Now match each player using the pre-built structure (O(1) per player)
    for p in all_players:
        _match_odds(p, odds_lookup, unique_names)
        _enrich_with_ev(p)
        _attach_fd_links(p, fd_link_map)

    n_with_odds = sum(1 for p in all_players if p.get("best_american"))
    print(f"[pipeline] {n_with_odds}/{len(all_players)} players matched to odds")

    qualified    = []
    team_players: dict[str, list[dict]] = {}
    sc_counts    = {"current": 0, "blended": 0, "prior": 0, "none": 0}
    pit_ids: set = set()
    _fail_reason_counts: dict[str, int] = {}
    for p in all_players:
        passed, reasons = filters.apply_filters(p)
        p["filter_reasons"] = reasons
        p["soft_flags"]     = filters.soft_flags(p)
        if passed:
            qualified.append(p)
        else:
            for r in reasons:
                # Bucket by the first word of the reason for concise summary
                bucket = r.split("(")[0].split("≥")[0].split(">")[0].strip()
                _fail_reason_counts[bucket] = _fail_reason_counts.get(bucket, 0) + 1
        if p.get("best_american"):
            team_players.setdefault(p["team"], []).append(p)
        src = p.get("statcast_source") or ""
        sc_counts[src if src in sc_counts else "none"] += 1
        if p.get("pitcher_id"):
            pit_ids.add(p["pitcher_id"])

    for team in team_players:
        team_players[team].sort(key=lambda x: x.get("model_prob", 0), reverse=True)

    if _fail_reason_counts:
        sorted_fails = sorted(_fail_reason_counts.items(), key=lambda x: x[1], reverse=True)
        print(f"[pipeline] filter failure summary: {dict(sorted_fails)}")
    print(f"[pipeline] {len(qualified)} qualified of {len(all_players)} total")

    _game_batter_counts: dict = {}
    for _p in all_players:
        _gk = str(_p.get("game_pk", "unknown"))
        _game_batter_counts[_gk] = _game_batter_counts.get(_gk, 0) + 1
    _low_games = {k: v for k, v in _game_batter_counts.items() if v < 7}
    print(
        f"[pipeline] SLATE_STATS | games={len(games)} attempted={len(tasks)} "
        f"emitted={len(all_players)} odds_lines={len(all_props)} "
        f"matched={n_with_odds} qualified={len(qualified)} "
        f"dropped_zero_pa={_drop_no_profile[0]} "
        f"dropped_exception={len(tasks) - len(all_players) - _drop_no_profile[0]} "
        f"game_batter_counts={_game_batter_counts}"
        + (f" LOW_COUNT={_low_games}" if _low_games else "")
    )

    ranked      = ranker.rank_picks(qualified)
    all_by_model = ranker.rank_all_by_model(all_players)

    # Stamp tier + score on every player so strategies_ui can sort by confidence
    # Keyed on (player_name, game_pk) so doubleheader siblings resolve to
    # their own game's ranked entry instead of colliding on name alone.
    _ranked_map = {(p.get("player_name"), p.get("game_pk")): p for p in ranked}
    _ranked_by_name = {p.get("player_name"): p for p in ranked}
    for p in all_players:
        _key = (p.get("player_name"), p.get("game_pk"))
        _rp = _ranked_map.get(_key)
        if _rp is None and p.get("game_pk") is None:
            # Missing game_pk: degrade to name-only match rather than drop the tier
            _rp = _ranked_by_name.get(p.get("player_name"))
        if _rp is not None:
            # Qualified picks already have tier/score from rank_picks
            p["confidence_tier"] = _rp.get("confidence_tier", "C")
            p["score"]           = _rp.get("score", 0)
        else:
            if "confidence" not in p:
                p["confidence_tier"] = "NE"
            else:
                edge = p.get("edge_pct", 0)
                conf = p.get("confidence", 0)
                p["confidence_tier"] = ranker.confidence_tier(conf, edge)
            p["score"]           = ranker.composite_score(p.get("model_prob", 0))

    ranker.rank_within_tiers(all_players)

    # Auto parlay combos (legacy leg-count view + new profile-based view)
    auto_parlays    = parlay_engine.build_auto_parlays(ranked)
    profile_parlays = build_profile_parlays(all_players)

    # Warehouse Phase 1: capture the complete unified pre-split batter payload.
    # Submission is asynchronous and never gates the live board return path.
    _schedule_batter_stat_history_capture(game_date, all_players)

    return {
        "date":         game_date,
        "games":        games,
        "all_players":  all_players,
        "all_by_model": all_by_model,
        "qualified":    qualified,  # Add for main.py compatibility
        "ranked":       ranked,
        "odds_source":   odds_source,
        "odds_quota":    odds_quota,
        "batter_data":  batter_data,  # Add for main.py compatibility
        "batter_count":  len(batter_data),
        "team_players":  team_players,
        "auto_parlays":    auto_parlays,
        "profile_parlays": profile_parlays,
        "n_with_odds":  n_with_odds,
        "fail_reasons": _fail_reason_counts,
        "_capture_stats": {
            "games_scheduled": len(games),
            "players_attempted": len(tasks),
            "odds_lines_fetched": len(all_props),
            "players_matched_to_odds": n_with_odds,
            "qualified_count": len(qualified),
        },
        "stats": {
            "games":     len(games),
            "players":   len(all_players),
            "qualified": len(qualified),
            "filtered":  len(all_players) - len(qualified),
            "n_with_odds": n_with_odds,
            "sc_current":  sc_counts["current"],
            "sc_blended":  sc_counts["blended"],
            "sc_prior":    sc_counts["prior"],
            "sc_none":     sc_counts["none"],
            "pit_sc_count": len(pitcher_data),
            "pit_total":   len(pit_ids),
        },
    }
