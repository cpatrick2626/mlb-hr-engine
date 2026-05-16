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
# {year: {(pitcher_id, pitch_type): {whiff_pct, hard_hit_pct, rv_per100}}}
_PITCH_STATS_CACHE: dict[int, dict] = {}

# Pitch type codes Savant uses for fastball family
_FASTBALL_TYPES = frozenset({"FF", "SI", "FC"})


def clear_caches() -> None:
    """Evict stale cache entries so the next fetch hits the network."""
    _ARSENAL_CACHE.clear()
    _PITCH_STATS_CACHE.clear()


def get_pitch_display_stats(year: int = None) -> dict:
    """
    Fetch per-pitcher, per-pitch-type display stats from Savant pitch-arsenal-stats leaderboard.
    Returns {(pitcher_id, pitch_type): {"whiff_pct": float, "hard_hit_pct": float, "rv_per100": float}}
    Returns {} on any failure — callers fall back to '—' display.
    These stats are DISPLAY ONLY and must not be used in formula calculations.
    """
    year = year or config.CURRENT_SEASON
    if year in _PITCH_STATS_CACHE:
        return _PITCH_STATS_CACHE[year]

    url = (
        "https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats"
        f"?year={year}&type=pitcher&min=1&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=20)
        if resp.status_code != 200:
            return {}
        result = _parse_pitch_stats_csv(resp.text)
        _PITCH_STATS_CACHE[year] = result
        return result
    except Exception as exc:
        print(f"[arsenal] pitch-stats fetch failed (year={year}): {exc}")
        return {}


def _parse_pitch_stats_csv(raw: str) -> dict:
    """Parse pitch-arsenal-stats CSV → {(pitcher_id, pitch_type): {whiff_pct, hard_hit_pct, rv_per100}}."""
    result: dict = {}
    # Savant uses several column naming conventions across years — try all variants
    _WHIFF_COLS  = ("whiff_pct", "whiff_percent", "whiff")
    _HH_COLS     = ("hard_hit_pct", "hard_hit_percent", "hard_hit_pct2")
    _RV_COLS     = ("run_value_per100", "rv_per100", "run_value_per_100", "rv100")
    _PIT_COLS    = ("pitcher", "player_id", "pitcher_id")
    _PT_COLS     = ("pitch_type", "pitch_type_code")

    def _try(row, keys):
        for k in keys:
            v = row.get(k, "")
            if v not in ("", None):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    pass
        return None

    reader = csv.DictReader(io.StringIO(raw.lstrip("﻿")))
    for row in reader:
        try:
            pid = None
            for col in _PIT_COLS:
                try:
                    pid = int(row.get(col) or 0)
                    if pid:
                        break
                except (ValueError, TypeError):
                    pass
            if not pid:
                continue
            pt = (row.get("pitch_type") or row.get("pitch_type_code") or "").strip().upper()
            if not pt:
                continue
            whiff = _try(row, _WHIFF_COLS)
            hh    = _try(row, _HH_COLS)
            rv    = _try(row, _RV_COLS)
            # Savant sometimes uses 0-100 scale for pct fields — normalize to 0-1
            if whiff is not None and whiff > 1.5:
                whiff = whiff / 100.0
            if hh is not None and hh > 1.5:
                hh = hh / 100.0
            result[(pid, pt)] = {"whiff_pct": whiff, "hard_hit_pct": hh, "rv_per100": rv}
        except Exception:
            continue
    return result


# ── Public API ─────────────────────────────────────────────────────────────────

def get_pitcher_arsenal(year: int = None) -> dict[int, list[dict]]:
    """
    Return full pitcher arsenal for the season.
    {pitcher_id: [{"pitch_type", "pitch_pct", "rv_per100", "pa",
                   "avg_speed", "whiff_pct", "hard_hit_pct"}, ...]}
    Returns {} on network or parse failure — all callers fall back to 1.0 factor.

    Primary source: pitch-arsenal-stats endpoint (per-pitch RV/100, usage, whiff).
    Fallback: pitch-arsenals wide-format CSV (usage-only; note: empty as of 2026).
    """
    year = year or config.CURRENT_SEASON
    if year in _ARSENAL_CACHE:
        return _ARSENAL_CACHE[year]

    # Primary: pitch-arsenal-stats has rv_per100, pitch_usage, whiff%, pa, hard_hit%
    result = _fetch_arsenal_from_stats(year)
    if result:
        _ARSENAL_CACHE[year] = result
        return result

    # Fallback: wide-format CSV (pitch percentages only; no RV/100 or whiff)
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


def _fetch_arsenal_from_stats(year: int) -> dict[int, list[dict]]:
    """
    Fetch pitcher arsenal from pitch-arsenal-stats endpoint (per-pitch-type rows).
    Returns {pitcher_id: [pitch_dict, ...]} or {} on failure.
    Column mapping:
      player_id -> pitcher_id
      pitch_usage -> pitch_pct (0-100 scale, converted to 0-1)
      run_value_per_100 -> rv_per100
      pa -> pa (int)
      whiff_percent -> whiff_pct (0-100 scale, converted to 0-1)
      hard_hit_percent -> hard_hit_pct (0-100 scale, converted to 0-1)
      avg_speed: not available on this endpoint — set to None
    """
    url = (
        "https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats"
        f"?year={year}&type=pitcher&min=1&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=25)
        if resp.status_code != 200:
            print(f"[arsenal] stats HTTP {resp.status_code} for year={year}")
            return {}
        raw = resp.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(raw))
        result: dict[int, list] = {}
        for row in reader:
            try:
                pid_raw = row.get("player_id") or row.get("pitcher") or ""
                pid = int(pid_raw) if pid_raw.strip() else 0
                if not pid:
                    continue
                pt = (row.get("pitch_type") or "").strip().upper()
                if not pt:
                    continue

                def _f(key):
                    v = (row.get(key) or "").strip()
                    try:
                        return float(v) if v else None
                    except ValueError:
                        return None

                usage    = _f("pitch_usage")
                rv       = _f("run_value_per_100")
                pa_raw   = _f("pa")
                whiff    = _f("whiff_percent")
                hard_hit = _f("hard_hit_percent")

                if usage is None or usage <= 0:
                    continue
                # Savant returns 0-100 scale for percentages
                pct = usage / 100.0 if usage > 1.5 else usage
                if whiff is not None and whiff > 1.5:
                    whiff = whiff / 100.0
                if hard_hit is not None and hard_hit > 1.5:
                    hard_hit = hard_hit / 100.0

                pitch = {
                    "pitch_type":   pt,
                    "pitch_pct":    round(pct, 4),
                    "rv_per100":    rv,
                    "pa":           int(pa_raw) if pa_raw is not None else 0,
                    "avg_speed":    None,  # not provided by this endpoint
                    "whiff_pct":    whiff,
                    "hard_hit_pct": hard_hit,
                }
                if pid not in result:
                    result[pid] = []
                result[pid].append(pitch)
            except Exception:
                continue

        # Sort each pitcher's pitches by usage descending
        for pid in result:
            result[pid].sort(key=lambda p: p["pitch_pct"], reverse=True)

        if result:
            print(f"[arsenal] stats endpoint: {len(result)} pitchers loaded for year={year}")
        return result
    except Exception as exc:
        print(f"[arsenal] stats fetch failed (year={year}): {exc}")
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
    """
    Parse Savant pitch arsenal WIDE-format CSV.

    Actual columns (2026): 'pitcher' (player_id), then per-pitch usage columns:
      ff_pitcher, si_pitcher, fc_pitcher, sl_pitcher, ch_pitcher,
      cu_pitcher, fs_pitcher, kn_pitcher, st_pitcher, sv_pitcher
    Values are usage percentages (0–100 scale).
    """
    result: dict[int, list] = {}

    # Map CSV column suffix → pitch type code
    _PT_COLS: dict[str, str] = {
        "ff_pitcher": "FF", "si_pitcher": "SI", "fc_pitcher": "FC",
        "sl_pitcher": "SL", "ch_pitcher": "CH", "cu_pitcher": "CU",
        "fs_pitcher": "FS", "kn_pitcher": "KN", "st_pitcher": "ST",
        "sv_pitcher": "SV", "kc_pitcher": "KC",
    }

    reader = csv.DictReader(io.StringIO(raw.lstrip("﻿")))
    for row in reader:
        try:
            pid = int(row.get("pitcher") or 0)
            if not pid:
                continue

            pitches = []
            for col, pt in _PT_COLS.items():
                raw_val = (row.get(col) or "").strip()
                if not raw_val:
                    continue
                try:
                    pct = float(raw_val)
                except ValueError:
                    continue
                if pct <= 0:
                    continue
                if pct > 1.5:
                    pct /= 100.0
                pitches.append({
                    "pitch_type":   pt,
                    "pitch_pct":    round(pct, 4),
                    "rv_per100":    None,
                    "pa":           0,
                    "avg_speed":    None,
                    "whiff_pct":    None,
                    "hard_hit_pct": None,
                })

            if pitches:
                # Sort descending by usage so primary pitch is first
                pitches.sort(key=lambda p: p["pitch_pct"], reverse=True)
                result[pid] = pitches
        except (ValueError, KeyError):
            continue

    return result


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
