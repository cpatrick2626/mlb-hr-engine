"""Display-only batter damage profile by canonical pitch type.

This module is intentionally isolated from ``clients.pitch_mix`` scoring state.
It reuses only the public pitch-type canonicalizer. Its PA-ending and all-pitch
fetches plus its cache are reachable from ``/api/batter-detail`` only and never
participate in slate assembly, sorting, or scoring.
"""

from __future__ import annotations

import copy
import csv
import io
import logging
import math
from datetime import datetime, timezone

import requests

import config
from clients.pitch_mix import canonical_pitch_type
from clients.session_utils import configure_session


log = logging.getLogger("uvicorn.error")

SAVANT = "https://baseballsavant.mlb.com"
SOURCE = "Baseball Savant statcast_search/csv (batter PA-ending + all pitches)"

# Display gates only. These constants do not feed MAIN or JIG scoring.
MIN_XWOBA_SAMPLES = 10
MIN_BARREL_CONTACTS = 5
MIN_WHIFF_SWINGS = 15

# Ratified Phase B4 tactical display contracts. Retune display behavior here;
# none of these constants is imported by or reachable from scoring code.
PILL_EXPLOIT_XWOBA = 0.380
PILL_HUNT_XWOBA = 0.340
TOP_USAGE_PCT = 20.0
DAMAGE_XWOBA_FLOOR = 0.200
DAMAGE_XWOBA_CEILING = 0.500

_SWING_DESCRIPTIONS = frozenset({
    "hit_into_play", "foul", "foul_tip", "swinging_strike",
    "swinging_strike_blocked", "missed_bunt", "foul_bunt",
    "bunt_foul_tip",
})
_WHIFF_DESCRIPTIONS = frozenset({
    "swinging_strike", "swinging_strike_blocked", "missed_bunt",
})

# Mirrors the existing PA-ending query without importing or mutating its
# scoring-coupled accumulator/cache.
_PA_ENDING_HF_AB = (
    "home_run|strikeout|strikeout_double_play|single|double|triple|"
    "field_out|force_out|grounded_into_double_play|double_play|"
    "sac_fly|field_error|fielders_choice|"
)

_SESSION = configure_session(requests.Session())
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://baseballsavant.mlb.com/",
})

# Keyed by (batter_id, pitcher_hand, season). This cache is display-only and is
# deliberately separate from clients.pitch_mix._BATTER_PT_CACHE.
_BATTER_PITCH_PROFILE_DISPLAY_CACHE: dict[tuple[int, str, int], dict] = {}

_PITCH_ORDER = {
    code: index
    for index, code in enumerate(("FF", "SI", "FC", "SL", "ST", "CH", "FS", "CU", "KC"))
}


def _float_or_none(value) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def _empty_profile(*, pitcher_hand: str, reason: str,
                   columns_present: dict[str, bool] | None = None) -> dict:
    return {
        "rows": [],
        "_meta": {
            "source": SOURCE,
            "freshness": "Gap",
            "availability": {
                "xwoba": "Gap", "barrel_pct": "Gap", "whiff_pct": "Gap",
            },
            "pitcher_hand": pitcher_hand or "ALL",
            "season": config.CURRENT_SEASON,
            "fetched_at": None,
            "cache": "miss",
            "columns_present": columns_present or {
                "estimated_woba_using_speedangle": False,
                "launch_speed_angle": False,
                "description": False,
                "pitch_type": False,
                "p_throws": False,
            },
            "sample_policy": {
                "xwoba_min_observations": MIN_XWOBA_SAMPLES,
                "barrel_pct_min_contacts": MIN_BARREL_CONTACTS,
                "whiff_pct_min_swings": MIN_WHIFF_SWINGS,
            },
            "tactical_contract": {
                "exploit_xwoba_min": PILL_EXPLOIT_XWOBA,
                "hunt_xwoba_min": PILL_HUNT_XWOBA,
                "top_usage_min_pct": TOP_USAGE_PCT,
                "damage_metric": "xwOBA-based damage",
                "damage_xwoba_range": [DAMAGE_XWOBA_FLOOR, DAMAGE_XWOBA_CEILING],
            },
            "units": {
                "xwoba": "rate", "barrel_pct": "percent",
                "whiff_pct": "percent", "damage": "0-100 xwOBA-based",
            },
            "reason": reason,
            "display_only": True,
        },
    }


def _damage_from_xwoba(xwoba: float | None) -> float | None:
    if xwoba is None:
        return None
    scaled = (
        (xwoba - DAMAGE_XWOBA_FLOOR)
        / (DAMAGE_XWOBA_CEILING - DAMAGE_XWOBA_FLOOR)
        * 100.0
    )
    return round(max(0.0, min(100.0, scaled)), 1)


def _pill_from_xwoba(xwoba: float | None) -> tuple[str, bool]:
    if xwoba is None:
        return "NEUTRAL", True
    if xwoba >= PILL_EXPLOIT_XWOBA:
        return "EXPLOIT", False
    if xwoba >= PILL_HUNT_XWOBA:
        return "HUNT", False
    return "NEUTRAL", False


def _finalize(
    pa_totals: dict[str, dict],
    whiff_totals: dict[str, dict],
    *,
    pa_freshness: str,
    whiff_freshness: str,
) -> list[dict]:
    rows = []
    for pitch_type in set(pa_totals) | set(whiff_totals):
        sample = pa_totals.get(pitch_type, {
            "pa_ending_events": 0, "xwoba_sum": 0.0, "xwoba_n": 0,
            "contacts": 0, "barrels": 0,
        })
        whiff_sample = whiff_totals.get(pitch_type, {"swings": 0, "whiffs": 0})
        xwoba_n = sample["xwoba_n"]
        contacts = sample["contacts"]
        swings = whiff_sample["swings"]
        xwoba = (
            round(sample["xwoba_sum"] / xwoba_n, 3)
            if xwoba_n >= MIN_XWOBA_SAMPLES else None
        )
        barrel_pct = (
            round(sample["barrels"] / contacts * 100.0, 1)
            if contacts >= MIN_BARREL_CONTACTS else None
        )
        whiff_pct = (
            round(whiff_sample["whiffs"] / swings * 100.0, 1)
            if swings >= MIN_WHIFF_SWINGS else None
        )
        pill, pill_thin_sample = _pill_from_xwoba(xwoba)
        damage = _damage_from_xwoba(xwoba)
        rows.append({
            "pitch_type": pitch_type,
            "xwoba": xwoba,
            "barrel_pct": barrel_pct,
            "whiff_pct": whiff_pct,
            "pill": pill,
            "pill_thin_sample": pill_thin_sample,
            "damage": damage,
            "sample": {
                "pa_ending_events": sample["pa_ending_events"],
                "xwoba_observations": xwoba_n,
                "contacts": contacts,
                "barrels": sample["barrels"],
                "swings": swings,
                "whiffs": whiff_sample["whiffs"],
            },
            "availability": {
                "xwoba": pa_freshness if xwoba is not None else "Gap",
                "barrel_pct": pa_freshness if barrel_pct is not None else "Gap",
                "whiff_pct": whiff_freshness if whiff_pct is not None else "Gap",
                "pill": pa_freshness if not pill_thin_sample else "Gap",
                "damage": pa_freshness if damage is not None else "Gap",
            },
        })
    rows.sort(key=lambda row: (_PITCH_ORDER.get(row["pitch_type"], 99), row["pitch_type"]))
    return rows


def _fetch_pa_ending_profile(batter_id: int) -> tuple[dict[str, dict], dict[str, bool], str | None]:
    """Fetch B3 PA-ending xwOBA/barrel inputs without touching scoring state."""
    season = config.CURRENT_SEASON
    try:
        response = _SESSION.get(
            f"{SAVANT}/statcast_search/csv",
            params={
                "all": "true",
                "player_type": "batter",
                "batters_lookup[]": batter_id,
                "season": season,
                "type": "details",
                "hfAB": _PA_ENDING_HF_AB,
                "hfGT": "R|",
            },
            timeout=20,
            stream=True,
        )
        response.raise_for_status()
        csv_body = response.content
        response.close()
    except Exception as exc:
        log.warning("batter pitch-profile display fetch failed bid=%s: %s", batter_id, exc)
        return {}, {}, "pa_ending_fetch_failed"

    reader = csv.DictReader(io.StringIO(csv_body.decode("utf-8-sig")))
    fieldnames = set(reader.fieldnames or [])
    columns_present = {
        "estimated_woba_using_speedangle": "estimated_woba_using_speedangle" in fieldnames,
        "launch_speed_angle": "launch_speed_angle" in fieldnames,
    }
    totals_by_hand: dict[str, dict[str, dict]] = {"": {}, "R": {}, "L": {}}
    seen_pa: set[tuple[str, str]] = set()

    for row in reader:
        raw_pitch_type = (row.get("pitch_type") or "").strip().upper()
        event = (row.get("events") or "").strip().lower()
        if not raw_pitch_type or not event:
            continue

        raw_year = row.get("game_year") or row.get("year") or (row.get("game_date") or "")[:4]
        try:
            row_season = int(raw_year) if raw_year else season
        except (TypeError, ValueError):
            row_season = season
        if raw_year and row_season != season:
            continue

        pa_key = (row.get("game_pk", ""), row.get("at_bat_number", ""))
        if pa_key[0] and pa_key[1]:
            if pa_key in seen_pa:
                continue
            seen_pa.add(pa_key)

        pitch_type = canonical_pitch_type(raw_pitch_type)
        pitcher_hand = (row.get("p_throws") or "").strip().upper()
        hands = [""] + ([pitcher_hand] if pitcher_hand in {"R", "L"} else [])
        xwoba = _float_or_none(row.get("estimated_woba_using_speedangle"))
        launch_speed_angle = _float_or_none(row.get("launch_speed_angle"))

        for hand in hands:
            sample = totals_by_hand[hand].setdefault(pitch_type, {
                "pa_ending_events": 0,
                "xwoba_sum": 0.0,
                "xwoba_n": 0,
                "contacts": 0,
                "barrels": 0,
            })
            sample["pa_ending_events"] += 1
            if xwoba is not None:
                sample["xwoba_sum"] += xwoba
                sample["xwoba_n"] += 1
            if launch_speed_angle is not None:
                sample["contacts"] += 1
                if launch_speed_angle == 6.0:
                    sample["barrels"] += 1

    if not any(totals_by_hand.values()):
        return {}, columns_present, "pa_ending_empty_response"

    return totals_by_hand, columns_present, None


def _fetch_all_pitches_whiff_display(
    batter_id: int,
) -> tuple[dict[str, dict], dict[str, bool], str | None]:
    """Fetch every regular-season pitch seen and accumulate whiffs / swings."""
    season = config.CURRENT_SEASON
    try:
        response = _SESSION.get(
            f"{SAVANT}/statcast_search/csv",
            params={
                "all": "true",
                "player_type": "batter",
                "batters_lookup[]": batter_id,
                "season": season,
                "type": "details",
                "hfGT": "R|",
            },
            timeout=20,
            stream=True,
        )
        response.raise_for_status()
        csv_body = response.content
        response.close()
    except Exception as exc:
        log.warning("batter all-pitches whiff fetch failed bid=%s: %s", batter_id, exc)
        return {}, {}, "all_pitches_fetch_failed"

    reader = csv.DictReader(io.StringIO(csv_body.decode("utf-8-sig")))
    fieldnames = set(reader.fieldnames or [])
    columns_present = {
        "description": "description" in fieldnames,
        "pitch_type": "pitch_type" in fieldnames,
        "p_throws": "p_throws" in fieldnames,
    }
    if not all(columns_present.values()):
        return {}, columns_present, "all_pitches_columns_missing"

    totals_by_hand: dict[str, dict[str, dict]] = {"": {}, "R": {}, "L": {}}
    seen_pitches: set[tuple[str, str, str]] = set()
    for row in reader:
        raw_pitch_type = (row.get("pitch_type") or "").strip().upper()
        description = (row.get("description") or "").strip().lower()
        if not raw_pitch_type or description not in _SWING_DESCRIPTIONS:
            continue

        raw_year = row.get("game_year") or row.get("year") or (row.get("game_date") or "")[:4]
        try:
            row_season = int(raw_year) if raw_year else season
        except (TypeError, ValueError):
            row_season = season
        if raw_year and row_season != season:
            continue

        pitch_key = (
            row.get("game_pk", ""), row.get("at_bat_number", ""),
            row.get("pitch_number", ""),
        )
        if all(pitch_key):
            if pitch_key in seen_pitches:
                continue
            seen_pitches.add(pitch_key)

        pitch_type = canonical_pitch_type(raw_pitch_type)
        pitcher_hand = (row.get("p_throws") or "").strip().upper()
        hands = [""] + ([pitcher_hand] if pitcher_hand in {"R", "L"} else [])
        for hand in hands:
            sample = totals_by_hand[hand].setdefault(
                pitch_type, {"swings": 0, "whiffs": 0},
            )
            sample["swings"] += 1
            if description in _WHIFF_DESCRIPTIONS:
                sample["whiffs"] += 1

    if not any(totals_by_hand.values()):
        return {}, columns_present, "all_pitches_empty_response"
    return totals_by_hand, columns_present, None


def _fetch_batter_pitch_profile_display(batter_id: int) -> dict[str, dict]:
    """Fetch isolated PA-ending/all-pitch inputs and build hand-split profiles."""
    season = config.CURRENT_SEASON
    pa_by_hand, pa_columns, pa_reason = _fetch_pa_ending_profile(batter_id)
    whiff_by_hand, whiff_columns, whiff_reason = _fetch_all_pitches_whiff_display(batter_id)
    if not pa_by_hand and not whiff_by_hand:
        return {}

    fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    profiles = {}
    for hand in ("", "R", "L"):
        pa_totals = pa_by_hand.get(hand, {})
        whiff_totals = whiff_by_hand.get(hand, {})
        rows = _finalize(
            pa_totals,
            whiff_totals,
            pa_freshness="Live" if pa_totals else "Gap",
            whiff_freshness="Live" if whiff_totals else "Gap",
        )
        xwoba_available = any(row["xwoba"] is not None for row in rows)
        barrel_available = any(row["barrel_pct"] is not None for row in rows)
        whiff_available = any(row["whiff_pct"] is not None for row in rows)
        profile_freshness = (
            "Live" if xwoba_available or barrel_available or whiff_available else "Gap"
        )
        profiles[hand] = {
            "rows": rows,
            "_meta": {
                "source": SOURCE,
                "freshness": profile_freshness,
                "availability": {
                    "xwoba": "Live" if xwoba_available else "Gap",
                    "barrel_pct": "Live" if barrel_available else "Gap",
                    "whiff_pct": "Live" if whiff_available else "Gap",
                },
                "pitcher_hand": hand or "ALL",
                "season": season,
                "fetched_at": fetched_at,
                "cache": "miss",
                "columns_present": {**pa_columns, **whiff_columns},
                "sample_policy": {
                    "xwoba_min_observations": MIN_XWOBA_SAMPLES,
                    "barrel_pct_min_contacts": MIN_BARREL_CONTACTS,
                    "whiff_pct_min_swings": MIN_WHIFF_SWINGS,
                },
                "tactical_contract": {
                    "exploit_xwoba_min": PILL_EXPLOIT_XWOBA,
                    "hunt_xwoba_min": PILL_HUNT_XWOBA,
                    "top_usage_min_pct": TOP_USAGE_PCT,
                    "damage_metric": "xwOBA-based damage",
                    "damage_xwoba_range": [DAMAGE_XWOBA_FLOOR, DAMAGE_XWOBA_CEILING],
                },
                "units": {
                    "xwoba": "rate", "barrel_pct": "percent",
                    "whiff_pct": "percent", "damage": "0-100 xwOBA-based",
                },
                "reason": (
                    "no_rows_for_pitcher_hand" if not rows
                    else pa_reason or whiff_reason
                ),
                "display_only": True,
            },
        }
    return profiles


def pitch_mix_verdict_display(rows: list[dict], pitcher_arsenal: list[dict] | None) -> dict:
    """Apply the ratified display-only verdict contract to profile + usage rows."""
    if not pitcher_arsenal:
        return {
            "label": None, "exploit_pitches": [], "availability": "Gap",
            "freshness": "Gap",
            "source": "/api/pitcher-detail arsenal display snapshot",
            "reason": "pitcher_usage_unavailable", "display_only": True,
        }

    usage_by_pitch: dict[str, float] = {}
    for arsenal_row in pitcher_arsenal:
        pitch_type = canonical_pitch_type(
            arsenal_row.get("pitch_type") or arsenal_row.get("code") or "",
        )
        if not pitch_type:
            continue
        raw_usage = arsenal_row.get("usage")
        if raw_usage is None:
            raw_usage = arsenal_row.get("pitch_pct")
        try:
            usage = float(raw_usage)
        except (TypeError, ValueError):
            continue
        if 0 < usage <= 1.0:
            usage *= 100.0
        if usage > 0:
            usage_by_pitch[pitch_type] = max(usage_by_pitch.get(pitch_type, 0.0), usage)
    if not usage_by_pitch:
        return {
            "label": None, "exploit_pitches": [], "availability": "Gap",
            "freshness": "Gap",
            "source": "/api/pitcher-detail arsenal display snapshot",
            "reason": "pitcher_usage_unavailable", "display_only": True,
        }

    profile_by_pitch = {row.get("pitch_type"): row for row in rows}
    joined = []
    for pitch_type, usage in usage_by_pitch.items():
        profile = profile_by_pitch.get(pitch_type, {})
        joined.append({
            "pitch_type": pitch_type,
            "usage": round(usage, 1),
            "xwoba": profile.get("xwoba"),
            "pill": profile.get("pill"),
        })
    main = [row for row in joined if row["usage"] >= TOP_USAGE_PCT]
    main_complete = bool(main) and all(row["xwoba"] is not None for row in main)
    exploit_pitches = [row for row in joined if row["pill"] == "EXPLOIT"]

    if any(row["pill"] == "EXPLOIT" for row in main):
        label, reason = "DEPLOY", "top_usage_exploit"
    elif main and not main_complete:
        label, reason = None, "main_arsenal_xwoba_unavailable"
    elif (
        exploit_pitches
        or any(row["pill"] == "HUNT" for row in main)
        or any(row["pill"] in {"EXPLOIT", "HUNT"} for row in joined)
    ):
        label, reason = "WATCHLIST", "lower_usage_or_mixed_edge"
    elif main and all(row["xwoba"] < PILL_HUNT_XWOBA for row in main):
        label, reason = "SCRATCH", "main_arsenal_below_hunt_threshold"
    elif not main and all(row["xwoba"] is not None for row in joined):
        label, reason = "HOLD", "neutral_no_top_usage_offering"
    else:
        label, reason = None, "insufficient_xwoba_evidence"

    return {
        "label": label,
        "exploit_pitches": exploit_pitches,
        "availability": "Live" if label is not None else "Gap",
        "freshness": "Live" if label is not None else "Gap",
        "source": "/api/pitcher-detail arsenal display snapshot + pitch_profile xwOBA",
        "reason": reason,
        "top_usage_min_pct": TOP_USAGE_PCT,
        "display_only": True,
    }


def get_batter_pitch_profile_display(batter_id: int, pitcher_hand: str = "") -> dict:
    """Return the display profile for one batter and opposing pitcher hand."""
    hand = (pitcher_hand or "").strip().upper()
    if hand not in {"R", "L"}:
        hand = ""
    key = (int(batter_id), hand, config.CURRENT_SEASON)
    cached = _BATTER_PITCH_PROFILE_DISPLAY_CACHE.get(key)
    if cached is not None:
        result = copy.deepcopy(cached)
        result["_meta"]["cache"] = "hit"
        return result

    profiles = _fetch_batter_pitch_profile_display(int(batter_id))
    if not profiles:
        return _empty_profile(pitcher_hand=hand, reason="fetch_failed_or_empty_response")

    for split_hand, profile in profiles.items():
        split_key = (int(batter_id), split_hand, config.CURRENT_SEASON)
        _BATTER_PITCH_PROFILE_DISPLAY_CACHE[split_key] = copy.deepcopy(profile)

    result = copy.deepcopy(_BATTER_PITCH_PROFILE_DISPLAY_CACHE.get(key))
    if result is None:
        return _empty_profile(
            pitcher_hand=hand,
            reason="no_rows_for_pitcher_hand",
            columns_present=profiles[""].get("_meta", {}).get("columns_present"),
        )
    return result
