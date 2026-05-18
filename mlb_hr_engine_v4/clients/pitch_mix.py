"""
Pitch-mix analytics — pitcher hand splits, head-to-head record, and
batter performance broken down by pitch type.

Sources (free, no API key):
  - Baseball Savant statcast_search (pitcher): hand splits vs L/R batters
    AND per-pitch stats (speed, K%, HR rate) in a single query.
  - MLB Stats API vsPlayerTotal: career head-to-head pitcher vs batter
  - Baseball Savant statcast_search (batter): batter PA-ending events
    aggregated by pitch type (BA / SLG / K% / HR rate)
"""

import csv
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import config
from clients.pull_air import parse_pct_display, resolve_pull_air_pct

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://baseballsavant.mlb.com/",
})

MLB_API = "https://statsapi.mlb.com/api/v1"
SAVANT  = "https://baseballsavant.mlb.com"

# Bump this whenever the context schema changes — forces Streamlit session-state cache to refresh.
HVY_CACHE_VERSION = "11"

# {pitcher_id: {"hand_splits": {...}, "pitch_stats": {...}, "data_year": int}}
_PITCHER_SAVANT_CACHE: dict[int, dict] = {}
_H2H_CACHE:            dict[tuple, dict] = {}
_BATTER_PT_CACHE:      dict[tuple, dict] = {}  # keyed (batter_id, pitcher_hand)

# Minimum PA-ending events to consider a season's data usable
_MIN_PITCHER_PA = 20


def clear_caches() -> None:
    """Clear all module-level caches. Call this when the user forces a data refresh
    so stale empty-result entries (e.g. from a failed initial load) are evicted."""
    _PITCHER_SAVANT_CACHE.clear()
    _H2H_CACHE.clear()
    _BATTER_PT_CACHE.clear()


def _acc_pitch_row(totals: dict, pt: str, ev: str, row: dict) -> None:
    """Accumulate one PA-ending Savant row into a pitch_totals dict in-place."""
    p = totals.setdefault(pt, {
        "pa": 0, "hr": 0, "k": 0, "h": 0, "tb": 0.0, "ab": 0,
        "speed_sum": 0.0, "speed_n": 0, "hard_hit": 0, "contact": 0,
    })
    p["pa"] += 1
    try:
        spd = float(row.get("release_speed") or 0)
        if spd > 0:
            p["speed_sum"] += spd; p["speed_n"] += 1
    except (ValueError, TypeError):
        pass
    if "strikeout" in ev:
        p["k"] += 1; p["ab"] += 1
    elif ev == "home_run":
        p["hr"] += 1; p["h"] += 1; p["tb"] += 4; p["ab"] += 1
        _acc_ls(p, row)
    elif ev == "double":
        p["h"] += 1; p["tb"] += 2; p["ab"] += 1; _acc_ls(p, row)
    elif ev == "triple":
        p["h"] += 1; p["tb"] += 3; p["ab"] += 1; _acc_ls(p, row)
    elif ev == "single":
        p["h"] += 1; p["tb"] += 1; p["ab"] += 1; _acc_ls(p, row)
    elif ev not in ("walk", "hit_by_pitch", "catcher_interf"):
        p["ab"] += 1; _acc_ls(p, row)


def _acc_ls(p: dict, row: dict) -> None:
    try:
        ls = float(row.get("launch_speed") or 0)
        if ls > 0:
            p["contact"] += 1
            if ls >= 95:
                p["hard_hit"] += 1
    except (ValueError, TypeError):
        pass


def _finalize_pitch_stats(totals: dict, total_pa_denom: int) -> dict:
    """Convert raw pitch accumulator totals into a pitch_stats dict."""
    out = {}
    denom = total_pa_denom or 1
    for pt, p in totals.items():
        _ab       = p.get("ab", 0)
        # Require ≥3 AB to show BA/SLG — prevents 0.000 from pure-walk or tiny samples
        _pitch_ba  = round(p["h"]  / _ab, 3) if _ab >= 3 else None
        _pitch_slg = round(p["tb"] / _ab, 3) if _ab >= 3 else None
        _pitch_iso = round(max(0.0, _pitch_slg - _pitch_ba), 3) if _pitch_ba is not None else None
        _disp_hh  = round(p["hard_hit"] / p["contact"], 3) if p.get("contact", 0) >= 5 else None
        # Require ≥10 PA to show HR rate — prevents extreme small-sample HR%
        _hr_rate  = round(p["hr"] / p["pa"], 3) if p["pa"] >= 10 else None
        out[pt] = {
            "pa":        p["pa"],
            "pitch_pct": round(p["pa"] / denom, 4),
            "hr":        p["hr"],
            "k":         p["k"],
            "k_pct":     round(p["k"]  / p["pa"], 3) if p["pa"] else 0.0,
            "hr_rate":   _hr_rate,
            "avg_speed": round(p["speed_sum"] / p["speed_n"], 1) if p["speed_n"] else None,
            "display_hh": _disp_hh,
            # BA/SLG/ISO allowed vs this pitch type — used in arsenal display table
            "pitch_ba":  _pitch_ba,
            "pitch_slg": _pitch_slg,
            "pitch_iso": _pitch_iso,
        }
    return out

# Human-readable pitch type labels
PITCH_LABELS: dict[str, str] = {
    "FF": "4-Seam FB", "FA": "4-Seam FB", "SI": "Sinker",    "FC": "Cutter",
    "SL": "Slider",    "SV": "Sweeper",   "KC": "K-Curve",
    "CU": "Curveball", "CH": "Changeup",  "FS": "Splitter",
    "ST": "Sweeper",   "KN": "Knuckleball", "EP": "Eephus",
    "SC": "Screwball", "FO": "Forkball",  "CS": "Slow Curve",
}

_FASTBALL_TYPES = frozenset({"FF", "FA", "SI", "FC"})
_BREAKING_TYPES = frozenset({"SL", "CU", "KC", "SV", "ST", "CS"})

# Pitch type alias → canonical code used for batter-vs-pitcher joins.
# Savant has changed codes over seasons (e.g. SV→ST for Sweeper in 2023);
# without canonicalization the join silently misses historical batter data.
_PITCH_CANONICAL: dict[str, str] = {
    "FA": "FF",  # older 4-seam code → current FF
    "SV": "ST",  # pre-2023 Sweeper → post-2023 ST (same pitch, Savant renamed)
}
# Reverse map for fallback lookup (canonical → all aliases that map to it)
_PITCH_ALIASES: dict[str, list[str]] = {}
for _alias, _canon in _PITCH_CANONICAL.items():
    _PITCH_ALIASES.setdefault(_canon, []).append(_alias)


def _canonical_pt(pt: str) -> str:
    """Return canonical pitch type code, resolving known Savant naming changes."""
    return _PITCH_CANONICAL.get(pt, pt)


def _pitch_keys(pt: str) -> list[str]:
    """Canonical lookup order for pitch joins across Savant/leaderboard aliases."""
    raw = (pt or "").strip().upper()
    if not raw:
        return []
    canon = _canonical_pt(raw)
    keys: list[str] = []
    for key in (canon, raw, *_PITCH_ALIASES.get(canon, [])):
        if key and key not in keys:
            keys.append(key)
    return keys


def _lookup_pitch(mapping: dict | None, pt: str) -> dict:
    """Return the first matching pitch row across canonical and alias codes."""
    if not mapping:
        return {}
    for key in _pitch_keys(pt):
        row = mapping.get(key)
        if row:
            return row
    return {}


def _first_not_none(*vals):
    """Return the first non-None value, preserving legitimate 0/0.0 metrics."""
    for v in vals:
        if v is not None:
            return v
    return None

# League-average baselines for modifier signals — canonical values from config.py.
# Update config.py (not here) at each mid-season refresh.
_LG_HR_PA    = config.LEAGUE_AVG_HR_PA                         # HR per PA
_LG_SLG      = 0.410                                           # slugging pct (MLB 2026)
_LG_OPS      = 0.720                                           # OPS (MLB 2026)
_LG_K_PA     = 0.230                                           # strikeout rate
_LG_BARREL   = config.LEAGUE_AVG_BARREL_RATE * 100.0           # barrel% (0-100 scale)
_LG_SS       = config.LEAGUE_AVG_SWEET_SPOT  * 100.0           # sweet-spot% (0-100 scale)
_LG_PULL     = config.LEAGUE_AVG_PULL_PCT    * 100.0           # pull% (0-100 scale)
_LG_FB       = config.LEAGUE_AVG_FB_PCT      * 100.0           # fly-ball% (0-100 scale)
_LG_LD       = config.LEAGUE_AVG_LD_PCT      * 100.0           # line-drive% (0-100 scale)
_LG_EV       = config.LEAGUE_AVG_EXIT_VELO                     # exit velocity mph
_LG_PULL_AIR = _LG_PULL * (_LG_FB + _LG_LD) / 100.0           # pull-air% composite

_PA_EVENTS = frozenset({
    "home_run", "strikeout", "strikeout_double_play",
    "single", "double", "triple",
    "field_out", "force_out", "grounded_into_double_play",
    "double_play", "sac_fly", "field_error", "fielders_choice",
    "walk", "hit_by_pitch", "catcher_interf",
})
_HF_AB = (
    "home_run|strikeout|strikeout_double_play|single|double|triple|"
    "field_out|force_out|grounded_into_double_play|double_play|"
    "sac_fly|field_error|fielders_choice|"
)


def pitch_label(pt: str) -> str:
    return PITCH_LABELS.get(pt, pt)


def pitch_color(pt: str) -> str:
    if pt in _FASTBALL_TYPES:
        return "#f87171"
    if pt in _BREAKING_TYPES:
        return "#60a5fa"
    return "#4ade80"


def _build_pitch_rows(pitcher_arsenal: list[dict]) -> list[dict]:
    """
    Build display-ready pitch rows from pitcher arsenal for UI rendering.

    Converts 0-1 fraction fields to 0-100 percent scale so app.py can
    format them directly with :.0f without additional scaling.

    Fields per row:
      pitch_type    str   — Savant code (e.g. "FF")
      pitch_usage   float — usage share 0-100 (e.g. 42.0 for 42%)
      whiff_pct     float|None — whiff rate 0-100 (e.g. 24.5 for 24.5%)
      hard_hit_pct  float|None — hard-hit rate 0-100
      rv_per100     float|None — run value per 100 pitches (raw, can be negative)
      avg_speed     float|None — average velocity mph
    """
    rows = []
    for entry in pitcher_arsenal:
        pct = entry.get("pitch_pct") or 0.0
        if pct <= 0:
            continue
        whiff = entry.get("display_whiff")
        hh    = entry.get("display_hh")
        rows.append({
            "pitch_type":   entry.get("pitch_type", ""),
            "pitch_usage":  round(pct * 100.0, 1),
            "whiff_pct":    round(whiff * 100.0, 1) if whiff is not None else None,
            "hard_hit_pct": round(hh   * 100.0, 1) if hh    is not None else None,
            "rv_per100":    entry.get("display_rv100"),
            "avg_speed":    entry.get("avg_speed"),
        })
    return rows


def _build_batter_rows(pitcher_arsenal: list[dict], batter_vs: dict) -> list[dict]:
    """Build canonical batter-vs-pitch rows ordered by arsenal first, then remainder."""
    ordered_pts: list[str] = []
    for entry in sorted(pitcher_arsenal, key=lambda x: x.get("pitch_pct", 0), reverse=True):
        pt = _canonical_pt(entry.get("pitch_type", ""))
        if pt and pt not in ordered_pts:
            ordered_pts.append(pt)
    for pt, _stats in sorted(batter_vs.items(), key=lambda x: x[1].get("pa", 0), reverse=True):
        canon = _canonical_pt(pt)
        if canon and canon not in ordered_pts:
            ordered_pts.append(canon)

    rows = []
    for pt in ordered_pts:
        stats = _lookup_pitch(batter_vs, pt)
        ba = stats.get("ba")
        slg = stats.get("slg")
        rows.append({
            "pitch_type": pt,
            "pa": stats.get("pa"),
            "hr": stats.get("hr"),
            "hr_rate": stats.get("hr_rate"),
            "ba": ba,
            "slg": slg,
            "iso": round(max(0.0, slg - ba), 3) if ba is not None and slg is not None else None,
            "k_pct": stats.get("k_pct"),
        })
    return rows


def _build_canonical_pitch_mix(
    pitcher_arsenal: list[dict],
    batter_vs: dict,
    hand_splits: dict,
    h2h: dict,
    data_year: int,
) -> dict:
    """One canonical Pitch Mix object shared by all Main and JIG player cards."""
    pitch_rows = _build_pitch_rows(pitcher_arsenal)
    batter_rows = _build_batter_rows(pitcher_arsenal, batter_vs)
    return {
        "arsenal": pitcher_arsenal,
        "pitch_rows": pitch_rows,
        "batter_vs": batter_vs,
        "batter_rows": batter_rows,
        "hand_splits": hand_splits,
        "h2h": h2h,
        "data_year": data_year,
    }


# ── Pitcher data (single Savant query) ────────────────────────────────────────

def _fetch_pitcher_savant(pitcher_id: int) -> dict:
    """
    One Savant statcast_search query for a pitcher's PA-ending events.
    Populates both hand splits (vs L/R) and per-pitch stats.
    Falls back to the prior season when the current season has < _MIN_PITCHER_PA rows
    (handles IL stints, early-season returns, openers with few starts).
    Returns 'data_year' so the UI can label prior-year data.

    Data integrity:
      - hfGT=R| restricts to regular-season games only (prevents Spring Training /
        postseason contamination — primary source of inflated HR counts).
      - (game_pk, at_bat_number) deduplication guards against suspended/replayed
        games that can appear as duplicate rows in Savant exports.
      - game_year validation skips any row whose year does not match the queried
        season (defensive layer for Savant pagination edge cases).
    """
    if pitcher_id in _PITCHER_SAVANT_CACHE:
        return _PITCHER_SAVANT_CACHE[pitcher_id]

    empty = {"hand_splits": {"R": {}, "L": {}}, "pitch_stats": {}, "data_year": config.CURRENT_SEASON}
    if not pitcher_id:
        return empty

    result = empty
    _got_data = False  # True only when Savant returned usable rows
    for season in (config.CURRENT_SEASON, config.CURRENT_SEASON - 1):
        try:
            resp = _SESSION.get(
                f"{SAVANT}/statcast_search/csv",
                params={
                    "all":               "true",
                    "player_type":       "pitcher",
                    "pitchers_lookup[]": pitcher_id,
                    "season":            season,
                    "type":              "details",
                    "hfAB":              _HF_AB,
                    # Restrict to regular season: excludes Spring Training (S/E) and
                    # postseason (F/D/L/W) which Savant includes without this filter.
                    "hfGT":              "R|",
                },
                timeout=20,
            )
            resp.raise_for_status()

            hand_totals:          dict[str, dict] = {}
            pitch_totals:         dict[str, dict] = {}           # overall (all batters)
            pitch_totals_by_stand: dict[str, dict] = {"R": {}, "L": {}}  # vs RHB / vs LHB
            total_rows = 0
            seen_pa: set = set()  # (game_pk, at_bat_number) — dedup guard

            for row in csv.DictReader(io.StringIO(resp.text.lstrip("﻿"))):
                pt    = (row.get("pitch_type") or "").strip().upper()
                ev    = (row.get("events") or "").strip().lower()
                stand = (row.get("stand") or "").strip().upper()
                if not ev or not pt:
                    continue

                # game_year validation: skip rows contaminated from the wrong season.
                # Savant may name this column "game_year" or "year"; fall back to game_date year.
                raw_year = (row.get("game_year") or row.get("year")
                            or (row.get("game_date") or "")[:4])
                try:
                    row_season = int(raw_year) if raw_year else season
                except (ValueError, TypeError):
                    row_season = season
                # Only skip rows with an explicit wrong-year value; empty game_year is not skipped.
                if raw_year and row_season != season:
                    continue

                # Deduplication: each plate appearance must be counted only once.
                # Suspended games resumed on a later date can produce duplicate rows.
                pa_key = (row.get("game_pk", ""), row.get("at_bat_number", ""))
                if pa_key[0] and pa_key[1]:
                    if pa_key in seen_pa:
                        continue
                    seen_pa.add(pa_key)

                total_rows += 1

                if stand in ("L", "R"):
                    h = hand_totals.setdefault(stand, {
                        "pa": 0, "hr": 0, "h": 0, "tb": 0.0, "ab": 0,
                    })
                    h["pa"] += 1
                    if "strikeout" in ev:
                        h["ab"] += 1
                    elif ev == "home_run":
                        h["hr"] += 1; h["h"] += 1; h["tb"] += 4; h["ab"] += 1
                    elif ev == "double":
                        h["h"] += 1; h["tb"] += 2; h["ab"] += 1
                    elif ev == "triple":
                        h["h"] += 1; h["tb"] += 3; h["ab"] += 1
                    elif ev == "single":
                        h["h"] += 1; h["tb"] += 1; h["ab"] += 1
                    elif ev not in ("walk", "hit_by_pitch", "catcher_interf"):
                        h["ab"] += 1
                    # Per-stand pitch stats — use canonical code so keys are era-agnostic
                    _acc_pitch_row(pitch_totals_by_stand[stand], _canonical_pt(pt), ev, row)

                # Overall pitch stats — canonicalize (SV→ST, FA→FF) for consistent keys
                _acc_pitch_row(pitch_totals, _canonical_pt(pt), ev, row)

            # Skip this season if too sparse; try prior year
            if total_rows < _MIN_PITCHER_PA:
                print(f"[pitch_mix] pitcher {pitcher_id} season={season}: only {total_rows} rows — trying prior year")
                continue

            total_pa = sum(h["pa"] for h in hand_totals.values()) or 1
            total_hr = sum(h.get("hr", 0) for h in hand_totals.values())
            print(f"[pitch_mix] pitcher {pitcher_id} season={season}: {total_rows} PA-ending rows, "
                  f"{total_hr} HR ({len(seen_pa)} deduped)")
            hand_splits: dict[str, dict] = {"R": {}, "L": {}}
            for hand, h in hand_totals.items():
                ab  = h["ab"] or 1
                slg = round(h["tb"] / ab, 3)
                avg = round(h["h"]  / ab, 3)
                iso = round(max(0.0, slg - avg), 3)
                hand_splits[hand] = {"pa": h["pa"], "hr": h["hr"], "ba": avg, "slg": slg, "iso": iso}

            pitch_stats     = _finalize_pitch_stats(pitch_totals, total_pa)
            r_pa            = hand_totals.get("R", {}).get("pa", 0)
            l_pa            = hand_totals.get("L", {}).get("pa", 0)
            pitch_stats_vs_r = _finalize_pitch_stats(pitch_totals_by_stand["R"], r_pa)
            pitch_stats_vs_l = _finalize_pitch_stats(pitch_totals_by_stand["L"], l_pa)

            result = {
                "hand_splits":     hand_splits,
                "pitch_stats":     pitch_stats,
                "pitch_stats_vs_r": pitch_stats_vs_r,
                "pitch_stats_vs_l": pitch_stats_vs_l,
                "data_year":       season,
            }
            _got_data = True
            break  # good season found — stop iterating

        except Exception as e:
            print(f"[pitch_mix] pitcher savant fetch failed (pid={pitcher_id}, season={season}): {e}")

    # Only cache successful fetches — exceptions leave _got_data=False so we retry next call
    if _got_data:
        _PITCHER_SAVANT_CACHE[pitcher_id] = result
    return result


def get_pitcher_hand_splits(pitcher_id: int) -> dict:
    """
    Pitcher's stats split by batter handedness (current season, or prior if sparse).
    → {"R": {pa, hr, slg, iso}, "L": {...}}
    """
    return _fetch_pitcher_savant(pitcher_id).get("hand_splits", {"R": {}, "L": {}})


def get_pitcher_pitch_stats(pitcher_id: int, batter_side: str = "") -> dict:
    """
    Pitcher's per-pitch-type stats split by batter handedness when batter_side is given.
    batter_side: "R" → stats vs RHB, "L" → stats vs LHB, "" → overall.
    → {"FF": {pa, pitch_pct, hr, k, k_pct, hr_rate, avg_speed, display_hh}, ...}
    """
    savant = _fetch_pitcher_savant(pitcher_id)
    if batter_side == "R":
        return savant.get("pitch_stats_vs_r") or savant.get("pitch_stats", {})
    if batter_side == "L":
        return savant.get("pitch_stats_vs_l") or savant.get("pitch_stats", {})
    return savant.get("pitch_stats", {})


def get_pitcher_data_year(pitcher_id: int) -> int:
    """Returns the season year the pitcher's Savant data comes from."""
    return _fetch_pitcher_savant(pitcher_id).get("data_year", config.CURRENT_SEASON)


# ── Career H2H (lifetime, all years) ─────────────────────────────────────────

def get_h2h(pitcher_id: int, batter_id: int) -> dict:
    """
    Career head-to-head: pitcher vs batter, all seasons.
    → {pa, hr, bb, k, avg, slg, ops}
    Uses MLB Stats API vsPlayerTotal (no season filter = career totals).
    """
    key = (pitcher_id, batter_id)
    if key in _H2H_CACHE:
        return _H2H_CACHE[key]

    result: dict = {}
    if not pitcher_id or not batter_id:
        return result
    try:
        resp = _SESSION.get(f"{MLB_API}/people/{pitcher_id}/stats", params={
            "stats": "vsPlayerTotal", "opposingPlayerId": batter_id,
            "group": "pitching",
        }, timeout=8)
        resp.raise_for_status()
        for stat_group in resp.json().get("stats", []):
            splits = stat_group.get("splits", [])
            if splits:
                s = splits[0].get("stat", {})
                # vsPlayerTotal uses battersFaced; vsPlayer uses plateAppearances
                pa = int(s.get("plateAppearances") or s.get("battersFaced") or 0)
                result = {
                    "pa":  pa,
                    "hr":  int(s.get("homeRuns", 0)),
                    "bb":  int(s.get("baseOnBalls", 0)),
                    "k":   int(s.get("strikeOuts", 0)),
                    "avg": s.get("avg", ".000"),
                    "slg": s.get("sluggingPercentage") or s.get("slg") or ".000",
                    "ops": s.get("ops", ".000"),
                }
                break
    except Exception as e:
        print(f"[pitch_mix] h2h failed (pit={pitcher_id}, bat={batter_id}): {e}")

    _H2H_CACHE[key] = result
    return result


# ── Batter vs pitch types ─────────────────────────────────────────────────────

def _fetch_all_batter_pitch_splits(batter_id: int) -> None:
    """
    Fetch Savant data for a batter ONCE and populate _BATTER_PT_CACHE for
    all three split keys: (batter_id, ""), (batter_id, "R"), (batter_id, "L").
    This guarantees hand-split accuracy without multiple HTTP calls.

    Data integrity (mirrors pitcher fetch):
      - hfGT=R| restricts to regular-season games only (prevents Spring Training /
        postseason contamination).
      - (game_pk, at_bat_number) deduplication guards against suspended/replayed
        games that can produce duplicate rows.
      - game_year validation skips rows from the wrong season.
      - Pitch types are normalized to canonical codes before accumulation so that
        the batter-vs-pitch lookup joins correctly with pitcher arsenal codes.
    """
    totals_all: dict[str, dict] = {}
    totals_by_hand: dict[str, dict[str, dict]] = {"R": {}, "L": {}}
    season = config.CURRENT_SEASON

    def _acc(totals: dict, pt: str, ev: str) -> None:
        t = totals.setdefault(pt, {"pa": 0, "hr": 0, "h": 0, "k": 0, "tb": 0.0, "ab": 0})
        t["pa"] += 1
        if "strikeout" in ev:
            t["k"] += 1;  t["ab"] += 1
        elif ev == "home_run":
            t["hr"] += 1; t["h"] += 1; t["tb"] += 4; t["ab"] += 1
        elif ev == "double":
            t["h"] += 1;  t["tb"] += 2; t["ab"] += 1
        elif ev == "triple":
            t["h"] += 1;  t["tb"] += 3; t["ab"] += 1
        elif ev == "single":
            t["h"] += 1;  t["tb"] += 1; t["ab"] += 1
        elif ev not in ("walk", "hit_by_pitch", "catcher_interf"):
            t["ab"] += 1

    def _finalize(totals: dict) -> dict:
        out = {}
        for pt, t in totals.items():
            _ab = t["ab"]
            _pa = t["pa"]
            # Require ≥3 AB for BA/SLG — prevents fake 0.000 from pure-walk or tiny samples
            _ba  = round(t["h"]  / _ab, 3) if _ab >= 3 else None
            _slg = round(t["tb"] / _ab, 3) if _ab >= 3 else None
            # Require ≥10 PA for HR rate — prevents extreme small-sample values (e.g. 1 HR / 1 PA)
            _hr_rate = round(t["hr"] / _pa, 3) if _pa >= 10 else None
            out[pt] = {
                "pa":      _pa,
                "hr":      t["hr"],
                "k":       t["k"],
                "ba":      _ba,
                "slg":     _slg,
                "k_pct":   round(t["k"] / _pa, 3) if _pa else 0.0,
                "hr_rate": _hr_rate,
            }
        return out

    total_rows = 0
    seen_pa: set = set()

    try:
        resp = _SESSION.get(
            f"{SAVANT}/statcast_search/csv",
            params={
                "all":              "true",
                "player_type":      "batter",
                "batters_lookup[]": batter_id,
                "season":           season,
                "type":             "details",
                "hfAB":             _HF_AB,
                # Restrict to regular season — identical to pitcher fetch guard
                "hfGT":             "R|",
            },
            timeout=15,
        )
        resp.raise_for_status()

        for row in csv.DictReader(io.StringIO(resp.text.lstrip("﻿"))):
            raw_pt = (row.get("pitch_type") or "").strip().upper()
            ev     = (row.get("events") or "").strip().lower()
            if not raw_pt or not ev:
                continue

            # year validation — skip stale rows; check "year" as Savant column alias
            raw_year = (row.get("game_year") or row.get("year")
                        or (row.get("game_date") or "")[:4])
            try:
                row_season = int(raw_year) if raw_year else season
            except (ValueError, TypeError):
                row_season = season
            # Only skip when year is explicitly wrong; missing year field is not a reason to skip.
            if raw_year and row_season != season:
                continue

            # Deduplication: each plate appearance counted once
            pa_key = (row.get("game_pk", ""), row.get("at_bat_number", ""))
            if pa_key[0] and pa_key[1]:
                if pa_key in seen_pa:
                    continue
                seen_pa.add(pa_key)

            total_rows += 1
            # Normalize pitch type to canonical code before accumulating
            # so batter-vs-pitch lookup joins against pitcher arsenal correctly.
            pt = _canonical_pt(raw_pt)
            p_hand = (row.get("p_throws") or "").strip().upper()

            _acc(totals_all, pt, ev)
            if p_hand in ("R", "L"):
                _acc(totals_by_hand[p_hand], pt, ev)

    except Exception as e:
        print(f"[pitch_mix] batter_vs_pitches fetch failed (bid={batter_id}): {e}")

    if total_rows == 0:
        print(f"[pitch_mix] WARNING: batter Savant returned 0 PA-ending rows (bid={batter_id}, season={season})")

    _BATTER_PT_CACHE[(batter_id, "")]  = _finalize(totals_all)
    _BATTER_PT_CACHE[(batter_id, "R")] = _finalize(totals_by_hand["R"])
    _BATTER_PT_CACHE[(batter_id, "L")] = _finalize(totals_by_hand["L"])


def get_batter_vs_pitches(batter_id: int, pitcher_hand: str = "") -> dict:
    """
    Batter's season results aggregated by pitch type (PA-ending events only).
    pitcher_hand: "R" → vs RHP only, "L" → vs LHP only, "" → overall.
    One Savant fetch populates all three splits so calls are always O(1) after first.
    → {"FF": {pa, hr, k, ba, slg, k_pct, hr_rate}, "SL": {...}, ...}
    """
    _hand = pitcher_hand.upper() if pitcher_hand else ""
    _key  = (batter_id, _hand)
    if _key not in _BATTER_PT_CACHE:
        _fetch_all_batter_pitch_splits(batter_id)
    return _BATTER_PT_CACHE.get(_key, {})


# ── Context assembly ───────────────────────────────────────────────────────────

def load_hvy_context(player: dict, arsenal_data: dict | None = None,
                     disp_stats: dict | None = None) -> dict:
    """
    Assemble pitch-mix context for one player.
    arsenal_data: {pitcher_id: [pitch_dict, ...]} from clients/arsenal.py (usage % only).
    disp_stats: {(pitcher_id, pitch_type): {whiff_pct, hard_hit_pct, rv_per100}} display-only.
    Per-pitch speed/K%/HR-rate come from get_pitcher_pitch_stats() via Savant.
    """
    pitcher_id  = player.get("pitcher_id")
    batter_id   = player.get("player_id")
    batter_side = player.get("batter_side", "")

    # Merge arsenal usage% with live per-pitch stats + display-only leaderboard stats
    pitcher_hand    = player.get("pitcher_hand", "")
    # Switch hitters bat opposite the pitcher's hand — derive effective batting side
    if batter_side == "S":
        effective_batter_side = "R" if pitcher_hand == "L" else "L"
    else:
        effective_batter_side = batter_side
    pitcher_arsenal = _build_pitcher_arsenal_canonical(pitcher_id, arsenal_data, disp_stats, effective_batter_side)
    hand_splits     = get_pitcher_hand_splits(pitcher_id) if pitcher_id else {"R": {}, "L": {}}
    h2h             = get_h2h(pitcher_id, batter_id) if pitcher_id and batter_id else {}
    batter_vs       = get_batter_vs_pitches(batter_id, pitcher_hand) if batter_id else {}
    data_year       = get_pitcher_data_year(pitcher_id) if pitcher_id else config.CURRENT_SEASON
    pitch_mix       = _build_canonical_pitch_mix(pitcher_arsenal, batter_vs, hand_splits, h2h, data_year)

    modifier = _compute_modifier(player, pitcher_arsenal, hand_splits, h2h, batter_vs)

    # Data quality diagnostics
    if not pitcher_arsenal:
        print(f"[pitch_mix] INFO: no pitcher arsenal for pid={pitcher_id} "
              f"(player={player.get('player_name', '?')}) — pitch rows empty")
    elif data_year != config.CURRENT_SEASON:
        print(f"[pitch_mix] INFO: pitcher {pitcher_id} using prior-year ({data_year}) data "
              f"(player={player.get('player_name', '?')})")

    if not batter_vs and batter_id:
        print(f"[pitch_mix] INFO: no batter-vs-pitch data for bid={batter_id} "
              f"(player={player.get('player_name', '?')}) — Signal 2 neutral")

    return {
        "pitch_mix":       pitch_mix,
        "pitcher_arsenal": pitcher_arsenal,
        "hand_splits":     hand_splits,
        "h2h":             h2h,
        "batter_vs":       batter_vs,
        "hvy_modifier":    modifier,
        "data_year":       data_year,
        "pitch_rows":      pitch_mix["pitch_rows"],
        "batter_rows":     pitch_mix["batter_rows"],
    }


def load_hvy_contexts_batch(players: list[dict], arsenal_data: dict | None = None) -> dict:
    """
    Load HVY context for multiple players concurrently.
    Returns {player_id: context_dict}.
    """
    from clients.arsenal import get_pitch_display_stats
    import config as _cfg
    disp_stats = get_pitch_display_stats(_cfg.CURRENT_SEASON)

    contexts: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(load_hvy_context, p, arsenal_data, disp_stats): p.get("player_id")
            for p in players
            if p.get("player_id")
        }
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                contexts[pid] = fut.result()
            except Exception as e:
                print(f"[pitch_mix] batch context failed (pid={pid}): {e}")
                contexts[pid] = {}
    return contexts


def _build_pitcher_arsenal(pitcher_id: int | None, arsenal_data: dict | None,
                           disp_stats: dict | None = None,
                           batter_side: str = "") -> list[dict]:
    """
    Build a unified pitcher arsenal list merging:
      - Usage% from arsenal_data leaderboard (overall), overridden by per-stand
        pitch_pct from Savant raw data when batter_side is "R" or "L"
      - Per-pitch speed / K% / HR-rate / display_hh from get_pitcher_pitch_stats()
        filtered to vs-RHB or vs-LHB when batter_side is provided
      - Display-only whiff%/HH%/RV100 from disp_stats (no hand-split available)

    Formula fields (whiff_pct, hard_hit_pct, rv_per100) remain None.
    """
    if not pitcher_id:
        return []

    from_leaderboard: list[dict] = (arsenal_data or {}).get(pitcher_id) or []
    # Per-stand stats (vs the specific batter handedness) — falls back to overall if sparse
    pitch_stats = get_pitcher_pitch_stats(pitcher_id, batter_side)
    _disp = disp_stats or {}

    def _merge_display(entry: dict, pt: str, live: dict) -> dict:
        ds = _disp.get((pitcher_id, pt), {})
        # Fallback chain for display metrics (NOT used by formula):
        #   1. disp_stats (pitch-arsenal-stats leaderboard, separate fetch)
        #   2. entry (from arsenal_data — same endpoint, already parsed with whiff/HH/RV)
        # This ensures whiff%/HH%/RV/100 are populated even when disp_stats is empty
        # (e.g., when the leaderboard fetch returns different column names by year).
        return {
            **entry,
            # Override leaderboard pitch_pct with per-stand value when available
            "pitch_pct":     live.get("pitch_pct") or entry.get("pitch_pct", 0),
            "avg_speed":     live.get("avg_speed") or entry.get("avg_speed"),
            "k_pct":         live.get("k_pct"),
            "hr_rate":       live.get("hr_rate"),
            "pa":            live.get("pa", 0),
            # Per-pitch BA/SLG/ISO allowed by the pitcher — display only, not used by formula
            "pitch_ba":      live.get("pitch_ba"),
            "pitch_slg":     live.get("pitch_slg"),
            "pitch_iso":     live.get("pitch_iso"),
            # Display-only — NOT used by formula
            "display_whiff": _first_not_none(ds.get("whiff_pct"), entry.get("whiff_pct")),
            "display_hh":    _first_not_none(
                live.get("display_hh"),
                ds.get("hard_hit_pct"),
                entry.get("hard_hit_pct"),
            ),
            "display_rv100": ds.get("rv_per100")   if ds.get("rv_per100") is not None else entry.get("rv_per100"),
        }

    def _ps_lookup(pt: str) -> dict:
        """Resolve pitch stats with canonical/alias fallback so leaderboard codes match
        Savant raw codes across era changes (FA↔FF, SV↔ST)."""
        live = pitch_stats.get(pt) or {}
        if not live:
            ct = _canonical_pt(pt)
            live = pitch_stats.get(ct) or {}
        if not live:
            for _alias in _PITCH_ALIASES.get(_canonical_pt(pt), []):
                live = pitch_stats.get(_alias) or {}
                if live:
                    break
        return live

    if from_leaderboard:
        merged = [_merge_display(e, e.get("pitch_type", ""), _ps_lookup(e.get("pitch_type", "")))
                  for e in from_leaderboard]
        merged = _normalize_pitch_pct(merged, pitcher_id)
        return merged

    # No leaderboard entry — build from live Savant data
    if not pitch_stats:
        print(f"[pitch_mix] WARNING: no arsenal data for pitcher {pitcher_id} — HVY modifier uses reduced signal")
        return []
    arsenal = []
    for pt, ps in sorted(pitch_stats.items(), key=lambda x: x[1]["pitch_pct"], reverse=True):
        ds = _disp.get((pitcher_id, pt), {})
        arsenal.append({
            "pitch_type":    pt,
            "pitch_pct":     ps["pitch_pct"],
            "rv_per100":     None,       # formula field — keep None
            "pa":            ps["pa"],
            "avg_speed":     ps.get("avg_speed"),
            "whiff_pct":     None,       # formula field — keep None
            "hard_hit_pct":  None,       # formula field — keep None
            "k_pct":         ps.get("k_pct"),
            "hr_rate":       ps.get("hr_rate"),
            "pitch_ba":      ps.get("pitch_ba"),
            "pitch_slg":     ps.get("pitch_slg"),
            "pitch_iso":     ps.get("pitch_iso"),
            "display_whiff": ds.get("whiff_pct"),
            "display_hh":    _first_not_none(ps.get("display_hh"), ds.get("hard_hit_pct")),
            "display_rv100": ds.get("rv_per100"),
        })
    arsenal = _normalize_pitch_pct(arsenal, pitcher_id)
    return arsenal


def _normalize_pitch_pct(arsenal: list[dict], pitcher_id: int) -> list[dict]:
    """Validate and normalize pitch_pct so entries sum to ~1.0.

    Flags incomplete arsenals (sum < 0.80 suggests missing pitch types).
    Normalizes if sum deviates > 5% from 1.0 to keep percentages accurate.
    Removes entries with zero or negative usage.
    """
    arsenal = [e for e in arsenal if (e.get("pitch_pct") or 0.0) > 0]
    if not arsenal:
        return arsenal
    total = sum(e.get("pitch_pct", 0.0) for e in arsenal)
    if total < 0.80:
        print(f"[pitch_mix] WARNING: arsenal for pitcher {pitcher_id} sums to {total:.2f} "
              f"(< 0.80) — incomplete leaderboard data, some pitch types may be missing")
    if total > 0 and abs(total - 1.0) > 0.05:
        for e in arsenal:
            e["pitch_pct"] = round(e["pitch_pct"] / total, 4)
    return arsenal


def _build_pitcher_arsenal_canonical(
    pitcher_id: int | None,
    arsenal_data: dict | None,
    disp_stats: dict | None = None,
    batter_side: str = "",
) -> list[dict]:
    """Canonical pitch-mix merge used by all Main and JIG cards."""
    if not pitcher_id:
        return []

    from_leaderboard: list[dict] = (arsenal_data or {}).get(pitcher_id) or []
    split_pitch_stats = get_pitcher_pitch_stats(pitcher_id, batter_side)
    overall_pitch_stats = get_pitcher_pitch_stats(pitcher_id, "")
    _disp = disp_stats or {}

    def _disp_lookup(pt: str) -> dict:
        for key in _pitch_keys(pt):
            ds = _disp.get((pitcher_id, key), {})
            if ds:
                return ds
        return {}

    def _merge_display(entry: dict, pt: str, split_live: dict, overall_live: dict) -> dict:
        ds = _disp_lookup(pt)
        return {
            **entry,
            "pitch_type": _canonical_pt(pt),
            "pitch_pct": _first_not_none(
                split_live.get("pitch_pct"),
                overall_live.get("pitch_pct"),
                entry.get("pitch_pct"),
                0.0,
            ),
            "avg_speed": _first_not_none(
                split_live.get("avg_speed"),
                overall_live.get("avg_speed"),
                entry.get("avg_speed"),
            ),
            "k_pct": _first_not_none(split_live.get("k_pct"), overall_live.get("k_pct")),
            "hr_rate": _first_not_none(split_live.get("hr_rate"), overall_live.get("hr_rate")),
            "pa": _first_not_none(split_live.get("pa"), overall_live.get("pa"), entry.get("pa"), 0),
            "pitch_ba": _first_not_none(split_live.get("pitch_ba"), overall_live.get("pitch_ba")),
            "pitch_slg": _first_not_none(split_live.get("pitch_slg"), overall_live.get("pitch_slg")),
            "pitch_iso": _first_not_none(split_live.get("pitch_iso"), overall_live.get("pitch_iso")),
            "display_whiff": _first_not_none(ds.get("whiff_pct"), entry.get("whiff_pct")),
            "display_hh": _first_not_none(
                split_live.get("display_hh"),
                overall_live.get("display_hh"),
                ds.get("hard_hit_pct"),
                entry.get("hard_hit_pct"),
            ),
            "display_rv100": _first_not_none(ds.get("rv_per100"), entry.get("rv_per100")),
        }

    leaderboard_by_pitch: dict[str, dict] = {}
    for entry in from_leaderboard:
        pt = _canonical_pt(entry.get("pitch_type", ""))
        if not pt:
            continue
        current = leaderboard_by_pitch.get(pt, {})
        leaderboard_by_pitch[pt] = {
            **current,
            **entry,
            "pitch_type": pt,
            "pitch_pct": _first_not_none(entry.get("pitch_pct"), current.get("pitch_pct"), 0.0),
            "pa": _first_not_none(entry.get("pa"), current.get("pa"), 0),
            "avg_speed": _first_not_none(entry.get("avg_speed"), current.get("avg_speed")),
            "whiff_pct": _first_not_none(entry.get("whiff_pct"), current.get("whiff_pct")),
            "hard_hit_pct": _first_not_none(entry.get("hard_hit_pct"), current.get("hard_hit_pct")),
            "rv_per100": _first_not_none(entry.get("rv_per100"), current.get("rv_per100")),
        }

    if not leaderboard_by_pitch and not overall_pitch_stats:
        print(f"[pitch_mix] WARNING: no arsenal data for pitcher {pitcher_id} â€” HVY modifier uses reduced signal")
        return []

    all_pts = {
        *leaderboard_by_pitch.keys(),
        *[_canonical_pt(pt) for pt in split_pitch_stats.keys()],
        *[_canonical_pt(pt) for pt in overall_pitch_stats.keys()],
    }
    arsenal = []
    for pt in all_pts:
        entry = _lookup_pitch(leaderboard_by_pitch, pt)
        split_live = _lookup_pitch(split_pitch_stats, pt)
        overall_live = _lookup_pitch(overall_pitch_stats, pt)
        arsenal.append(_merge_display(entry, pt, split_live, overall_live))

    arsenal.sort(
        key=lambda x: (
            -(_first_not_none(x.get("pitch_pct"), 0.0)),
            -(_first_not_none(x.get("pa"), 0)),
            x.get("pitch_type", ""),
        )
    )
    return _normalize_pitch_pct(arsenal, pitcher_id)


# ── Modifier computation ───────────────────────────────────────────────────────

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _compute_modifier(
    player: dict,
    pitcher_arsenal: list,
    hand_splits: dict,
    h2h: dict,
    batter_vs: dict,
) -> float:
    """
    Pure matchup-quality HVY modifier [0.70, 1.40] — five reliability-scaled signals.

    Signal weights (additive):
      1. Pitcher HR rate vs batter handedness  ±0.10  reliability=PA/50
      2. Weighted arsenal matchup              ±0.10  reliability=batter-PA/15 per pitch
      3. Batter contact shape block            ±0.06  barrel/sweet-spot/pull-air/fb/EV
      4. Pitch arsenal block                   ±0.06  weighted pitcher K% and HR rate
      5. Career H2H OPS                        ±0.06  reliability=PA/20, min 3 PA

    Note: environment multiplier (park × weather) was removed. The core model
    already applies park_factor and weather_factor to model_prob, so including
    them here would double-count their effect in the HVY display signal.
    """
    batter_side = player.get("batter_side", "R")
    pit_hand    = player.get("pitcher_hand", "")

    # ── Signal 1: Pitcher HR rate vs batter handedness ────────────────────────
    # Switch hitters bat opposite the pitcher's hand, so derive effective side accordingly.
    if batter_side == "S":
        hand_key = "R" if pit_hand == "L" else "L"
    else:
        hand_key = "L" if batter_side == "L" else "R"
    split    = hand_splits.get(hand_key, {})
    sig1 = 0.0
    hand_pa = split.get("pa", 0)
    if hand_pa >= 3:
        reliability = min(1.0, hand_pa / 50.0)
        rate     = split.get("hr", 0) / hand_pa
        rate_dev = (rate - _LG_HR_PA) / _LG_HR_PA
        sig1 = _clamp(rate_dev * reliability * 0.10, -0.10, 0.10)

    # ── Signal 2: Weighted arsenal matchup (batter SLG vs each pitch type) ────
    sig2 = 0.0
    if pitcher_arsenal and batter_vs:
        total_w    = 0.0
        weighted_d = 0.0
        for entry in pitcher_arsenal:
            pct = entry.get("pitch_pct", 0.0)
            if pct <= 0:
                continue
            raw_pt = entry.get("pitch_type", "")
            # Canonical lookup: resolve pitch type aliases (e.g. SV→ST, FA→FF)
            # so batter-vs-pitch data joins correctly regardless of Savant era
            canon_pt = _canonical_pt(raw_pt)
            bpt = batter_vs.get(canon_pt) or batter_vs.get(raw_pt) or {}
            # Fallback: check reverse aliases (pitcher throws ST, batter data has SV)
            if not bpt:
                for alias in _PITCH_ALIASES.get(canon_pt, []):
                    bpt = batter_vs.get(alias, {})
                    if bpt:
                        break
            b_pa = bpt.get("pa", 0)
            if b_pa < 3:
                continue
            reliability = min(1.0, b_pa / 15.0)
            bslg  = bpt.get("slg") or _LG_SLG  # None when < 3 AB → fall back to league avg
            delta = (bslg - _LG_SLG) / _LG_SLG
            weighted_d += pct * delta * reliability
            total_w    += pct * reliability
        if total_w > 0:
            sig2 = _clamp((weighted_d / total_w) * 0.25, -0.10, 0.10)

    # ── Signal 3: Batter contact shape block ─────────────────────────────────
    pull_air = resolve_pull_air_pct(player)
    # Pipeline Statcast fields are display strings ("35.0%", "91.2"); parse before arithmetic.
    fb  = parse_pct_display(player.get("fb_pct"), _LG_FB)
    brl = parse_pct_display(player.get("barrel_pct"), _LG_BARREL)
    ss  = parse_pct_display(player.get("sweet_spot_pct"), _LG_SS)
    ev  = parse_pct_display(player.get("exit_velo"), _LG_EV)

    contact_score = (
        ((brl  - _LG_BARREL)                  / _LG_BARREL)          * 0.30 +
        ((ss   - _LG_SS)                       / _LG_SS)              * 0.20 +
        ((pull_air - _LG_PULL_AIR)             / max(_LG_PULL_AIR, 1)) * 0.20 +
        ((fb   - _LG_FB)                       / _LG_FB)              * 0.15 +
        ((ev   - _LG_EV)                       / 5.0)                 * 0.15
    )
    sig3 = _clamp(contact_score * 0.08, -0.06, 0.06)

    # ── Signal 4: Pitch arsenal block (weighted pitcher K% and HR rate) ───────
    sig4 = 0.0
    if pitcher_arsenal:
        total_pct = 0.0
        w_k = 0.0
        w_hr = 0.0
        for entry in pitcher_arsenal:
            pct = entry.get("pitch_pct", 0.0)
            if pct <= 0:
                continue
            pa  = entry.get("pa", 0)
            reliability = min(1.0, pa / 30.0)
            raw_k  = _first_not_none(entry.get("k_pct"), _LG_K_PA)
            raw_hr = _first_not_none(entry.get("hr_rate"), _LG_HR_PA)
            eff_k  = raw_k  * reliability + _LG_K_PA  * (1.0 - reliability)
            eff_hr = raw_hr * reliability + _LG_HR_PA * (1.0 - reliability)
            w_k  += pct * eff_k
            w_hr += pct * eff_hr
            total_pct += pct
        if total_pct > 0:
            avg_k  = w_k  / total_pct
            avg_hr = w_hr / total_pct
            # Above-avg HR rate helps batter; above-avg K rate hurts batter
            arsenal_score = ((avg_hr - _LG_HR_PA) / _LG_HR_PA) * 0.5 \
                          - ((avg_k  - _LG_K_PA)  / _LG_K_PA)  * 0.5
            sig4 = _clamp(arsenal_score * 0.12, -0.06, 0.06)

    # ── Signal 5: Career H2H OPS (reduced vs old formula, reliability-scaled) ─
    sig5 = 0.0
    h2h_pa = h2h.get("pa", 0)
    if h2h_pa >= 3:
        try:
            ops = float(str(h2h.get("ops", "0")).replace(",", "") or 0)
        except (ValueError, TypeError):
            ops = 0.0
        if ops > 0:
            reliability = min(1.0, h2h_pa / 20.0)
            ops_dev = (ops - _LG_OPS) / _LG_OPS
            sig5 = _clamp(ops_dev * reliability * 0.06, -0.06, 0.06)

    # ── Combine: pure matchup additive signals ───────────────────────────────
    # Park and weather are intentionally excluded — the core model (model_prob)
    # already incorporates park_factor and weather_factor. Adding them here
    # would double-count their effect when the HVY modifier informs pick decisions.
    modifier = _clamp(1.0 + sig1 + sig2 + sig3 + sig4 + sig5, 0.70, 1.40)
    return round(modifier, 3)
