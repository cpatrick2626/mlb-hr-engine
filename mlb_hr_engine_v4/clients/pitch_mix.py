"""
Pitch-mix analytics — pitcher hand splits, head-to-head record, and
batter performance broken down by pitch type.

Sources (free, no API key):
  - MLB Stats API statSplits: pitcher HR/SLG/ISO allowed vs RHB and LHB
  - MLB Stats API vsPlayer:   head-to-head pitcher vs batter this season
  - Baseball Savant statcast_search: batter PA-ending events aggregated
    by pitch type (BA / SLG / K% / HR rate)
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

_HAND_SPLIT_CACHE: dict[int, dict]        = {}
_H2H_CACHE:        dict[tuple, dict]      = {}
_BATTER_PT_CACHE:  dict[int, dict]        = {}

# Human-readable pitch type labels
PITCH_LABELS: dict[str, str] = {
    "FF": "4-Seam FB", "SI": "Sinker",    "FC": "Cutter",
    "SL": "Slider",    "SV": "Sweeper",   "KC": "K-Curve",
    "CU": "Curveball", "CH": "Changeup",  "FS": "Splitter",
    "ST": "Sweeper",   "KN": "Knuckleball",
}

_FASTBALL_TYPES = frozenset({"FF", "SI", "FC"})
_BREAKING_TYPES = frozenset({"SL", "CU", "KC", "SV", "ST"})


def pitch_label(pt: str) -> str:
    return PITCH_LABELS.get(pt, pt)


def pitch_color(pt: str) -> str:
    if pt in _FASTBALL_TYPES:
        return "#f87171"
    if pt in _BREAKING_TYPES:
        return "#60a5fa"
    return "#4ade80"


# ── Public data fetchers ───────────────────────────────────────────────────────

def get_pitcher_hand_splits(pitcher_id: int) -> dict:
    """
    Pitcher's 2026 stats split by batter handedness.
    → {"R": {pa, hr, slg, iso}, "L": {...}}
    """
    if pitcher_id in _HAND_SPLIT_CACHE:
        return _HAND_SPLIT_CACHE[pitcher_id]

    result: dict[str, dict] = {"R": {}, "L": {}}
    try:
        resp = _SESSION.get(f"{MLB_API}/people/{pitcher_id}/stats", params={
            "stats": "statSplits", "group": "pitching",
            "season": config.CURRENT_SEASON,
        }, timeout=8)
        resp.raise_for_status()
        for stat_group in resp.json().get("stats", []):
            for split in stat_group.get("splits", []):
                code = split.get("split", {}).get("code", "").lower()
                hand = "R" if code in ("vr", "v-r") else "L" if code in ("vl", "v-l") else None
                if not hand:
                    continue
                s   = split.get("stat", {})
                pa  = int(s.get("plateAppearances", 0))
                hr  = int(s.get("homeRuns", 0))
                try:
                    slg = float(s.get("sluggingPercentage", 0) or 0)
                    avg = float(s.get("avg", 0) or 0)
                    iso = round(max(0.0, slg - avg), 3)
                except (ValueError, TypeError):
                    slg = iso = 0.0
                result[hand] = {"pa": pa, "hr": hr, "slg": slg, "iso": iso}
    except Exception as e:
        print(f"[pitch_mix] hand_splits failed (pid={pitcher_id}): {e}")

    _HAND_SPLIT_CACHE[pitcher_id] = result
    return result


def get_h2h(pitcher_id: int, batter_id: int) -> dict:
    """
    Head-to-head: pitcher vs batter, 2026.
    → {pa, hr, bb, k, avg, slg, ops}
    """
    key = (pitcher_id, batter_id)
    if key in _H2H_CACHE:
        return _H2H_CACHE[key]

    result: dict = {}
    if not pitcher_id or not batter_id:
        return result
    try:
        resp = _SESSION.get(f"{MLB_API}/people/{pitcher_id}/stats", params={
            "stats": "vsPlayer", "opposingPlayerId": batter_id,
            "group": "pitching", "season": config.CURRENT_SEASON,
        }, timeout=8)
        resp.raise_for_status()
        for stat_group in resp.json().get("stats", []):
            splits = stat_group.get("splits", [])
            if splits:
                s = splits[0].get("stat", {})
                result = {
                    "pa":  int(s.get("plateAppearances", 0)),
                    "hr":  int(s.get("homeRuns", 0)),
                    "bb":  int(s.get("baseOnBalls", 0)),
                    "k":   int(s.get("strikeOuts", 0)),
                    "avg": s.get("avg", ".000"),
                    "slg": s.get("sluggingPercentage", ".000"),
                    "ops": s.get("ops", ".000"),
                }
                break
    except Exception as e:
        print(f"[pitch_mix] h2h failed (pit={pitcher_id}, bat={batter_id}): {e}")

    _H2H_CACHE[key] = result
    return result


def get_batter_vs_pitches(batter_id: int) -> dict:
    """
    Batter's 2026 results aggregated by pitch type (PA-ending events only).
    → {"FF": {pa, hr, k, ba, slg, k_pct, hr_rate}, "SL": {...}, ...}

    Uses Savant statcast_search filtered to PA-ending events to keep dataset
    to ~300-600 rows per batter (vs ~2000+ rows for all pitches).
    """
    if batter_id in _BATTER_PT_CACHE:
        return _BATTER_PT_CACHE[batter_id]

    result: dict[str, dict] = {}
    _PA_EVENTS = {
        "home_run", "strikeout", "strikeout_double_play",
        "single", "double", "triple",
        "field_out", "force_out", "grounded_into_double_play",
        "double_play", "sac_fly", "field_error", "fielders_choice",
        "walk", "hit_by_pitch", "catcher_interf",
    }
    try:
        resp = _SESSION.get(
            f"{SAVANT}/statcast_search/csv",
            params={
                "all":              "true",
                "player_type":      "batter",
                "batters_lookup[]": batter_id,
                "season":           config.CURRENT_SEASON,
                "type":             "details",
                "hfAB":             "|".join([
                    "home_run", "strikeout", "strikeout_double_play",
                    "single", "double", "triple", "field_out", "force_out",
                    "grounded_into_double_play", "double_play",
                    "sac_fly", "field_error", "fielders_choice",
                ]),
            },
            timeout=15,
        )
        resp.raise_for_status()

        totals: dict[str, dict] = {}
        for row in csv.DictReader(io.StringIO(resp.text)):
            pt = (row.get("pitch_type") or "").strip().upper()
            ev = (row.get("events") or "").strip()
            if not pt or not ev or pt == "PITCH_TYPE":
                continue
            t = totals.setdefault(pt, {"pa": 0, "hr": 0, "h": 0, "k": 0, "tb": 0.0, "ab": 0})
            t["pa"] += 1
            ev_lower = ev.lower()
            if "strikeout" in ev_lower:
                t["k"] += 1;  t["ab"] += 1
            elif ev_lower == "home_run":
                t["hr"] += 1; t["h"] += 1; t["tb"] += 4; t["ab"] += 1
            elif ev_lower == "double":
                t["h"] += 1;  t["tb"] += 2; t["ab"] += 1
            elif ev_lower == "triple":
                t["h"] += 1;  t["tb"] += 3; t["ab"] += 1
            elif ev_lower == "single":
                t["h"] += 1;  t["tb"] += 1; t["ab"] += 1
            elif ev_lower not in ("walk", "hit_by_pitch", "catcher_interf"):
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
    arsenal_data: {pitcher_id: [pitch_dict, ...]} from clients/arsenal.py.
    """
    pitcher_id  = player.get("pitcher_id")
    batter_id   = player.get("player_id")
    batter_side = player.get("batter_side", "")

    pitcher_arsenal = []
    if arsenal_data and pitcher_id:
        pitcher_arsenal = arsenal_data.get(pitcher_id) or []

    hand_splits = get_pitcher_hand_splits(pitcher_id) if pitcher_id else {}
    h2h         = get_h2h(pitcher_id, batter_id) if pitcher_id and batter_id else {}
    batter_vs   = get_batter_vs_pitches(batter_id) if batter_id else {}

    modifier = _compute_modifier(batter_side, pitcher_arsenal, hand_splits, h2h, batter_vs)

    return {
        "pitcher_arsenal": pitcher_arsenal,
        "hand_splits":     hand_splits,
        "h2h":             h2h,
        "batter_vs":       batter_vs,
        "hvy_modifier":    modifier,
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
      3. Head-to-head history (≥5 PA required for signal)
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

    # ── 3. Head-to-head history ────────────────────────────────────────────────
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
