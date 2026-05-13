"""
Baseball Savant pitch arsenal client — free, no API key.

Endpoint:
  https://baseballsavant.mlb.com/leaderboard/pitch-arsenals
  ?year={year}&min=1&type=pitcher&hand=&csv=true

Provides per-pitcher, per-pitch-type data:
  pitch_pct     — usage share (0–1 after normalization)
  rv_per100     — run value per 100 pitches (negative = pitcher-favourable)
  avg_speed     — average velocity in mph
  whiff_pct     — swing-and-miss rate (0–1)
  hard_hit_pct  — hard-hit rate allowed (0–1)
  pa            — batters faced on this pitch type this season

Two signals computed from this data:
  arsenal_matchup_factor  — overall pitcher quality vs league (HR vulnerability)
  pitcher_velo_decline_factor — YoY fastball velocity decline → increased HR risk
"""

import io
import csv
import requests
from typing import Optional

import config

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/csv,*/*;q=0.8",
    "Referer": "https://baseballsavant.mlb.com/",
})

# {year: {pitcher_id: [pitch_dict, ...]}}
_ARSENAL_CACHE: dict[int, dict[int, list]] = {}

# Pitch type codes Savant uses for fastball family
_FASTBALL_TYPES = frozenset({"FF", "SI", "FC"})


# ── Public API ─────────────────────────────────────────────────────────────────

def get_pitcher_arsenal(year: int = None) -> dict[int, list[dict]]:
    """
    Return full pitcher arsenal for the season.
    {pitcher_id: [{"pitch_type", "pitch_pct", "rv_per100", "pa",
                   "avg_speed", "whiff_pct", "hard_hit_pct"}, ...]}
    Returns {} on network or parse failure — all callers fall back to 1.0 factor.
    """
    year = year or config.CURRENT_SEASON
    if year in _ARSENAL_CACHE:
        return _ARSENAL_CACHE[year]

    url = (
        "https://baseballsavant.mlb.com/leaderboard/pitch-arsenals"
        f"?year={year}&min=1&type=pitcher&hand=&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=25)
        if resp.status_code != 200:
            print(f"[arsenal] HTTP {resp.status_code} for year={year}")
            return {}
        result = _parse_arsenal_csv(resp.text)
        _ARSENAL_CACHE[year] = result
        return result
    except Exception as exc:
        print(f"[arsenal] fetch failed (year={year}): {exc}")
        return {}


def arsenal_matchup_factor(
    pitcher_id: int,
    arsenal_data: dict[int, list[dict]],
    batter_side: str = "",  # reserved for future hand-split CSV support
) -> float:
    """
    Pitcher arsenal quality factor for HR vulnerability.
      > 1.0 → pitcher's arsenal is below average; more HRs expected
      < 1.0 → pitcher dominates; fewer HRs expected
      = 1.0 → league average or insufficient data

    Method: usage-weighted composite of run value per 100 pitches (75%) and
    whiff rate vs league average (25%). Both signals are stabilized toward
    neutral for small per-pitch samples.

    Stabilization half-lives:
      RV/100: 50 PA per pitch type (high variance; shrink aggressively)
      Whiff%: 30 PA per pitch type

    Caps: [0.82, 1.20] — arsenal is supplemental, not dominant.
    """
    pitches = arsenal_data.get(pitcher_id)
    if not pitches:
        return 1.0

    LEAGUE_AVG_WHIFF = config.ARSENAL_LEAGUE_AVG_WHIFF  # ~0.245
    RV_SCALE         = config.ARSENAL_RV_SCALE           # 40.0

    total_pct   = 0.0
    weighted_rv = 0.0
    weighted_wh = 0.0

    for p in pitches:
        pct  = p.get("pitch_pct") or 0.0
        rv   = p.get("rv_per100")
        pa   = p.get("pa") or 0
        whiff = p.get("whiff_pct")

        if pct <= 0:
            continue

        # Stabilize RV toward 0 (neutral) for small samples
        if rv is not None and pa > 0:
            rv_trust = pa / (pa + 50.0)
            rv = rv * rv_trust
        else:
            rv = 0.0

        # Stabilize whiff toward league average for small samples
        if whiff is not None and pa > 0:
            wh_trust = pa / (pa + 30.0)
            whiff = wh_trust * whiff + (1.0 - wh_trust) * LEAGUE_AVG_WHIFF
        else:
            whiff = LEAGUE_AVG_WHIFF

        weighted_rv += pct * rv
        weighted_wh += pct * whiff
        total_pct   += pct

    if total_pct <= 0:
        return 1.0

    avg_rv    = weighted_rv / total_pct
    avg_whiff = weighted_wh / total_pct

    # RV component: positive RV → pitcher is hittable → more HRs
    rv_component = 1.0 + (avg_rv / RV_SCALE)

    # Whiff component: above-league whiff → fewer balls in play → fewer HRs
    whiff_dev     = (avg_whiff - LEAGUE_AVG_WHIFF) / max(LEAGUE_AVG_WHIFF, 0.01)
    whiff_component = 1.0 - 0.12 * whiff_dev

    # 75% RV, 25% whiff — RV is more comprehensive
    combined = 0.75 * rv_component + 0.25 * whiff_component
    return round(_clamp(combined, 0.82, 1.20), 3)


def pitcher_velo_decline_factor(
    pitcher_id: int,
    arsenal_curr: dict[int, list[dict]],
    arsenal_prior: dict[int, list[dict]],
) -> float:
    """
    Year-over-year fastball velocity decline signal.

    Primary fastball = highest-usage pitch among FF, SI, FC with speed data.
    Minimum 50 PA in prior year for the comparison to be valid.

    If velocity declined > VELO_DECLINE_THRESHOLD_MPH:
      factor = 1.0 + VELO_DECLINE_RATE × (decline − threshold)
    Caps at 1.08 — velocity decline alone can't be a dominant signal.
    Returns 1.0 when either year's data is unavailable.
    One-sided: we only boost HR risk for declines (velocity gain is handled by
    other factors and is a positive indicator for the pitcher, not an HR risk).
    """
    curr_pitches  = arsenal_curr.get(pitcher_id)
    prior_pitches = arsenal_prior.get(pitcher_id)
    if not curr_pitches or not prior_pitches:
        return 1.0

    curr_fb  = _primary_fastball(curr_pitches)
    prior_fb = _primary_fastball(prior_pitches)
    if curr_fb is None or prior_fb is None:
        return 1.0
    if (prior_fb.get("pa") or 0) < 50:
        return 1.0  # prior sample too thin to trust delta

    curr_speed  = curr_fb.get("avg_speed")
    prior_speed = prior_fb.get("avg_speed")
    if curr_speed is None or prior_speed is None:
        return 1.0

    delta = prior_speed - curr_speed  # positive = current year is slower
    if delta < config.VELO_DECLINE_THRESHOLD_MPH:
        return 1.0

    factor = 1.0 + config.VELO_DECLINE_RATE * delta
    return round(min(1.08, factor), 3)


# ── Internals ──────────────────────────────────────────────────────────────────

def _primary_fastball(pitches: list[dict]) -> Optional[dict]:
    """Return highest-usage fastball pitch entry with valid speed + PA >= 20."""
    candidates = [
        p for p in pitches
        if p.get("pitch_type", "") in _FASTBALL_TYPES
        and p.get("avg_speed") is not None
        and (p.get("pa") or 0) >= 20
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.get("pitch_pct", 0))


def _parse_arsenal_csv(raw: str) -> dict[int, list[dict]]:
    """Parse Savant pitch arsenal CSV. Handles both 0–100 and 0–1 percentage columns."""
    result: dict[int, list] = {}
    reader = csv.DictReader(io.StringIO(raw.lstrip("﻿")))

    def _f(row, *keys) -> Optional[float]:
        for k in keys:
            v = row.get(k)
            if v not in (None, "", "null", "NA", "N/A", "--"):
                try:
                    return float(v)
                except ValueError:
                    pass
        return None

    for row in reader:
        try:
            pid = int(row.get("player_id") or 0)
            if not pid:
                continue

            pitch_type = (row.get("pitch_type") or row.get("n_pitchtype") or "").strip().upper()
            if not pitch_type:
                continue

            pitch_pct  = _f("pitch_percent", "usage_percent")
            rv_per100  = _f("run_value_per100", "rv_100", "rv100")
            pa         = _f("pa", "attempts")
            avg_speed  = _f("avg_speed", "velocity_avg", "avg_velocity")
            whiff_pct  = _f("whiff_percent", "whiff_pct")
            hard_hit   = _f("hard_hit_percent", "hard_hit_pct")

            if pitch_pct is None:
                continue

            # Normalise 0–100 → 0–1 for percentage columns
            if pitch_pct > 1.5:
                pitch_pct /= 100.0
            if whiff_pct is not None and whiff_pct > 1.5:
                whiff_pct /= 100.0
            if hard_hit is not None and hard_hit > 1.5:
                hard_hit /= 100.0

            entry = {
                "pitch_type":   pitch_type,
                "pitch_pct":    pitch_pct,
                "rv_per100":    rv_per100,
                "pa":           int(pa) if pa is not None else 0,
                "avg_speed":    avg_speed,
                "whiff_pct":    whiff_pct,
                "hard_hit_pct": hard_hit,
            }
            result.setdefault(pid, []).append(entry)
        except (ValueError, KeyError):
            continue

    return result


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
