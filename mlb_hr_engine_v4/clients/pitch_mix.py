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

# {pitcher_id: {"hand_splits": {...}, "pitch_stats": {...}, "data_year": int}}
_PITCHER_SAVANT_CACHE: dict[int, dict] = {}
_H2H_CACHE:            dict[tuple, dict] = {}
_BATTER_PT_CACHE:      dict[int, dict] = {}

# Minimum PA-ending events to consider a season's data usable
_MIN_PITCHER_PA = 20

# Human-readable pitch type labels
PITCH_LABELS: dict[str, str] = {
    "FF": "4-Seam FB", "SI": "Sinker",    "FC": "Cutter",
    "SL": "Slider",    "SV": "Sweeper",   "KC": "K-Curve",
    "CU": "Curveball", "CH": "Changeup",  "FS": "Splitter",
    "ST": "Sweeper",   "KN": "Knuckleball",
}

_FASTBALL_TYPES = frozenset({"FF", "SI", "FC"})
_BREAKING_TYPES = frozenset({"SL", "CU", "KC", "SV", "ST"})

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


# ── Pitcher data (single Savant query) ────────────────────────────────────────

def _fetch_pitcher_savant(pitcher_id: int) -> dict:
    """
    One Savant statcast_search query for a pitcher's PA-ending events.
    Populates both hand splits (vs L/R) and per-pitch stats.
    Falls back to the prior season when the current season has < _MIN_PITCHER_PA rows
    (handles IL stints, early-season returns, openers with few starts).
    Returns 'data_year' so the UI can label prior-year data.
    """
    if pitcher_id in _PITCHER_SAVANT_CACHE:
        return _PITCHER_SAVANT_CACHE[pitcher_id]

    empty = {"hand_splits": {"R": {}, "L": {}}, "pitch_stats": {}, "data_year": config.CURRENT_SEASON}
    if not pitcher_id:
        return empty

    result = empty
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
                },
                timeout=20,
            )
            resp.raise_for_status()

            hand_totals:  dict[str, dict] = {}
            pitch_totals: dict[str, dict] = {}
            total_rows = 0

            for row in csv.DictReader(io.StringIO(resp.text.lstrip("﻿"))):
                pt    = (row.get("pitch_type") or "").strip().upper()
                ev    = (row.get("events") or "").strip().lower()
                stand = (row.get("stand") or "").strip().upper()
                if not ev or not pt:
                    continue
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

                p = pitch_totals.setdefault(pt, {
                    "pa": 0, "hr": 0, "k": 0, "h": 0, "tb": 0.0, "ab": 0,
                    "speed_sum": 0.0, "speed_n": 0,
                })
                p["pa"] += 1
                try:
                    spd = float(row.get("release_speed") or 0)
                    if spd > 0:
                        p["speed_sum"] += spd
                        p["speed_n"]   += 1
                except (ValueError, TypeError):
                    pass
                if "strikeout" in ev:
                    p["k"] += 1; p["ab"] += 1
                elif ev == "home_run":
                    p["hr"] += 1; p["h"] += 1; p["tb"] += 4; p["ab"] += 1
                elif ev == "double":
                    p["h"] += 1; p["tb"] += 2; p["ab"] += 1
                elif ev == "triple":
                    p["h"] += 1; p["tb"] += 3; p["ab"] += 1
                elif ev == "single":
                    p["h"] += 1; p["tb"] += 1; p["ab"] += 1
                elif ev not in ("walk", "hit_by_pitch", "catcher_interf"):
                    p["ab"] += 1

            # Skip this season if too sparse; try prior year
            if total_rows < _MIN_PITCHER_PA:
                continue

            total_pa = sum(h["pa"] for h in hand_totals.values()) or 1
            hand_splits: dict[str, dict] = {"R": {}, "L": {}}
            for hand, h in hand_totals.items():
                ab  = h["ab"] or 1
                slg = round(h["tb"] / ab, 3)
                avg = round(h["h"]  / ab, 3)
                iso = round(max(0.0, slg - avg), 3)
                hand_splits[hand] = {"pa": h["pa"], "hr": h["hr"], "slg": slg, "iso": iso}

            pitch_stats: dict[str, dict] = {}
            for pt, p in pitch_totals.items():
                pitch_stats[pt] = {
                    "pa":        p["pa"],
                    "pitch_pct": round(p["pa"] / total_pa, 4),
                    "hr":        p["hr"],
                    "k":         p["k"],
                    "k_pct":     round(p["k"]  / p["pa"], 3) if p["pa"] else 0.0,
                    "hr_rate":   round(p["hr"] / p["pa"], 3) if p["pa"] else 0.0,
                    "avg_speed": round(p["speed_sum"] / p["speed_n"], 1)
                                 if p["speed_n"] else None,
                }

            result = {"hand_splits": hand_splits, "pitch_stats": pitch_stats, "data_year": season}
            break  # good season found — stop iterating

        except Exception as e:
            print(f"[pitch_mix] pitcher savant fetch failed (pid={pitcher_id}, season={season}): {e}")

    _PITCHER_SAVANT_CACHE[pitcher_id] = result
    return result


def get_pitcher_hand_splits(pitcher_id: int) -> dict:
    """
    Pitcher's stats split by batter handedness (current season, or prior if sparse).
    → {"R": {pa, hr, slg, iso}, "L": {...}}
    """
    return _fetch_pitcher_savant(pitcher_id).get("hand_splits", {"R": {}, "L": {}})


def get_pitcher_pitch_stats(pitcher_id: int) -> dict:
    """
    Pitcher's per-pitch-type stats (current season, or prior if sparse).
    → {"FF": {pa, pitch_pct, hr, k, k_pct, hr_rate, avg_speed}, ...}
    """
    return _fetch_pitcher_savant(pitcher_id).get("pitch_stats", {})


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

def get_batter_vs_pitches(batter_id: int) -> dict:
    """
    Batter's season results aggregated by pitch type (PA-ending events only).
    → {"FF": {pa, hr, k, ba, slg, k_pct, hr_rate}, "SL": {...}, ...}
    """
    if batter_id in _BATTER_PT_CACHE:
        return _BATTER_PT_CACHE[batter_id]

    result: dict[str, dict] = {}
    try:
        resp = _SESSION.get(
            f"{SAVANT}/statcast_search/csv",
            params={
                "all":              "true",
                "player_type":      "batter",
                "batters_lookup[]": batter_id,
                "season":           config.CURRENT_SEASON,
                "type":             "details",
                "hfAB":             _HF_AB,
            },
            timeout=15,
        )
        resp.raise_for_status()

        totals: dict[str, dict] = {}
        for row in csv.DictReader(io.StringIO(resp.text.lstrip("﻿"))):
            pt = (row.get("pitch_type") or "").strip().upper()
            ev = (row.get("events") or "").strip().lower()
            if not pt or not ev:
                continue
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

        for pt, t in totals.items():
            ab = t["ab"] or 1
            result[pt] = {
                "pa":      t["pa"],
                "hr":      t["hr"],
                "k":       t["k"],
                "ba":      round(t["h"] / ab, 3),
                "slg":     round(t["tb"] / ab, 3),
                "k_pct":   round(t["k"] / t["pa"], 3) if t["pa"] else 0.0,
                "hr_rate": round(t["hr"] / t["pa"], 3) if t["pa"] else 0.0,
            }
    except Exception as e:
        print(f"[pitch_mix] batter_vs_pitches failed (bid={batter_id}): {e}")

    _BATTER_PT_CACHE[batter_id] = result
    return result


# ── Context assembly ───────────────────────────────────────────────────────────

def load_hvy_context(player: dict, arsenal_data: dict | None = None) -> dict:
    """
    Assemble pitch-mix context for one player.
    arsenal_data: {pitcher_id: [pitch_dict, ...]} from clients/arsenal.py (usage % only).
    Per-pitch speed/K%/HR-rate come from get_pitcher_pitch_stats() via Savant.
    """
    pitcher_id  = player.get("pitcher_id")
    batter_id   = player.get("player_id")
    batter_side = player.get("batter_side", "")

    # Merge arsenal usage% with live per-pitch stats from Savant
    pitcher_arsenal = _build_pitcher_arsenal(pitcher_id, arsenal_data)
    hand_splits     = get_pitcher_hand_splits(pitcher_id) if pitcher_id else {"R": {}, "L": {}}
    h2h             = get_h2h(pitcher_id, batter_id) if pitcher_id and batter_id else {}
    batter_vs       = get_batter_vs_pitches(batter_id) if batter_id else {}
    data_year       = get_pitcher_data_year(pitcher_id) if pitcher_id else config.CURRENT_SEASON

    modifier = _compute_modifier(batter_side, pitcher_arsenal, hand_splits, h2h, batter_vs)

    return {
        "pitcher_arsenal": pitcher_arsenal,
        "hand_splits":     hand_splits,
        "h2h":             h2h,
        "batter_vs":       batter_vs,
        "hvy_modifier":    modifier,
        "data_year":       data_year,
    }


def load_hvy_contexts_batch(players: list[dict], arsenal_data: dict | None = None) -> dict:
    """
    Load HVY context for multiple players concurrently.
    Returns {player_id: context_dict}.
    """
    contexts: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(load_hvy_context, p, arsenal_data): p.get("player_id")
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


def _build_pitcher_arsenal(pitcher_id: int | None, arsenal_data: dict | None) -> list[dict]:
    """
    Build a unified pitcher arsenal list merging:
      - Usage percentages from arsenal_data (Savant season leaderboard CSV)
      - Per-pitch speed / K% / HR-rate from get_pitcher_pitch_stats() (Savant statcast_search)

    Falls back to pitch_stats alone when arsenal_data has no entry for this pitcher.
    """
    if not pitcher_id:
        return []

    from_leaderboard: list[dict] = (arsenal_data or {}).get(pitcher_id) or []
    pitch_stats = get_pitcher_pitch_stats(pitcher_id)

    if from_leaderboard:
        # Enrich leaderboard entries with live per-pitch stats
        merged = []
        for entry in from_leaderboard:
            pt   = entry.get("pitch_type", "")
            live = pitch_stats.get(pt, {})
            merged.append({
                **entry,
                "avg_speed":   live.get("avg_speed") or entry.get("avg_speed"),
                "k_pct":       live.get("k_pct"),
                "hr_rate":     live.get("hr_rate"),
                "pa":          live.get("pa", 0),
            })
        return merged

    # No leaderboard entry — build from live Savant data
    if not pitch_stats:
        return []
    arsenal = []
    for pt, ps in sorted(pitch_stats.items(), key=lambda x: x[1]["pitch_pct"], reverse=True):
        arsenal.append({
            "pitch_type":   pt,
            "pitch_pct":    ps["pitch_pct"],
            "rv_per100":    None,
            "pa":           ps["pa"],
            "avg_speed":    ps.get("avg_speed"),
            "whiff_pct":    None,
            "hard_hit_pct": None,
            "k_pct":        ps.get("k_pct"),
            "hr_rate":      ps.get("hr_rate"),
        })
    return arsenal


# ── Modifier computation ───────────────────────────────────────────────────────

def _compute_modifier(
    batter_side: str,
    pitcher_arsenal: list,
    hand_splits: dict,
    h2h: dict,
    batter_vs: dict,
) -> float:
    """
    Composite HVY modifier on top of JIG Way base score [0.70, 1.40].

    Three independent signals, each contributing ±5-12%:
      1. Pitcher's HR rate vs this batter's handedness
      2. Batter's SLG vs pitcher's primary pitch type
      3. Career head-to-head history (≥5 PA required for signal)
    """
    modifier = 1.0

    # ── 1. Pitcher HR rate vs batter handedness ────────────────────────────────
    hand_key = "L" if batter_side == "L" else "R"
    split    = hand_splits.get(hand_key, {})
    if split.get("pa", 0) >= 20:
        rate  = split["hr"] / split["pa"]
        ratio = rate / 0.028  # league avg HR/PA
        if ratio > 1.30:
            modifier *= 1.12
        elif ratio > 1.10:
            modifier *= 1.06
        elif ratio < 0.70:
            modifier *= 0.90
        elif ratio < 0.90:
            modifier *= 0.95

    # ── 2. Batter vs pitcher's primary pitch type ──────────────────────────────
    if pitcher_arsenal and batter_vs:
        top = max(pitcher_arsenal, key=lambda p: p.get("pitch_pct", 0), default=None)
        if top:
            bpt = batter_vs.get(top.get("pitch_type", ""), {})
            if bpt.get("pa", 0) >= 8:
                ratio = bpt.get("slg", 0.0) / 0.410  # league avg SLG
                if ratio > 1.25:
                    modifier *= 1.10
                elif ratio > 1.10:
                    modifier *= 1.05
                elif ratio < 0.75:
                    modifier *= 0.92
                elif ratio < 0.90:
                    modifier *= 0.96

    # ── 3. Career head-to-head history ────────────────────────────────────────
    if h2h.get("pa", 0) >= 5:
        try:
            ops = float(str(h2h.get("ops", ".000")).replace(",", "") or 0)
        except (ValueError, TypeError):
            ops = 0.0
        if ops > 0.900:
            modifier *= 1.10
        elif ops > 0.770:
            modifier *= 1.04
        elif ops < 0.550:
            modifier *= 0.90
        elif ops < 0.650:
            modifier *= 0.95

    return round(max(0.70, min(1.40, modifier)), 3)
