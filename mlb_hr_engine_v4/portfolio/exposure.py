"""
portfolio/exposure.py — Portfolio exposure concentration analysis (Session 27).

Tracks and scores exposure concentration across multiple dimensions:
  team, barrel tier, odds range, park factor tier, weather tier, pitcher, sportsbook.

Uses HHI (Herfindahl-Hirschman Index) to quantify concentration:
  HHI = Σ (share_i)^2
  HHI = 1.0 = fully concentrated (one bucket)
  HHI = 1/N = perfectly diversified
  HHI > 0.25 = high concentration (antitrust threshold analogy)
  HHI > 0.18 = moderate concentration

Exposure alerts fire when:
  - Single team > TEAM_SHARE_ALERT (25%) of portfolio
  - Same-game (team+date) > SAME_GAME_CAP (40%) of portfolio
  - Barrel <6% > BARREL_LOW_ALERT (50%) of portfolio
  - Any odds tier > ODDS_TIER_CAP (50%) of portfolio
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional


# ── Thresholds ────────────────────────────────────────────────────────────────
TEAM_SHARE_ALERT   = 0.20   # single team >20% of daily portfolio = high exposure
SAME_GAME_CAP      = 0.35   # single game >35% = extreme same-game concentration
BARREL_LOW_ALERT   = 0.60   # >60% of picks in barrel <6% = poor quality concentration
ODDS_TIER_CAP      = 0.55   # >55% of picks in same odds tier = range concentration
HHI_HIGH           = 0.25   # HHI above this = high concentration warning
HHI_MODERATE       = 0.15   # HHI above this = moderate concentration note


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(str(v).strip()) if v is not None and str(v).strip() != "" else default
    except (ValueError, TypeError):
        return default


def _barrel_tier(r: dict) -> str:
    b = _safe_float(r.get("barrel_pct"))
    if b < 4:   return "barrel <4%"
    if b < 6:   return "barrel 4-6%"
    if b < 8:   return "barrel 6-8%"
    if b < 10:  return "barrel 8-10%"
    if b < 12:  return "barrel 10-12%"
    return "barrel 12%+"


def _odds_tier(r: dict) -> str:
    o = int(_safe_float(r.get("american_odds") or r.get("best_odds"), 100))
    if o < 300:  return "+100-299"
    if o < 500:  return "+300-499"
    if o < 700:  return "+500-699"
    if o < 1000: return "+700-999"
    return "+1000+"


def _park_tier(r: dict) -> str:
    pf = _safe_float(r.get("park_factor"), 1.0)
    if pf < 0.90: return "park penalty (<0.90)"
    if pf < 0.97: return "slight penalty (0.90-0.97)"
    if pf < 1.03: return "neutral (0.97-1.03)"
    if pf < 1.10: return "slight boost (1.03-1.10)"
    return "strong boost (1.10+)"


def _weather_tier(r: dict) -> str:
    wf = _safe_float(r.get("weather_factor"), 1.0)
    if wf < 0.92: return "weather penalty (<0.92)"
    if wf < 0.98: return "slight penalty (0.92-0.98)"
    if wf < 1.02: return "neutral (0.98-1.02)"
    return "weather boost (1.02+)"


def _ev_tier(r: dict) -> str:
    ev = _safe_float(r.get("ev_pct"))
    if ev < 3:   return "EV 0-3%"
    if ev < 5:   return "EV 3-5%"
    if ev < 8:   return "EV 5-8%"
    if ev < 12:  return "EV 8-12%"
    return "EV 12%+"


def _archetype(r: dict) -> str:
    """Classify pick by barrel quality + odds range."""
    barrel = _safe_float(r.get("barrel_pct"))
    odds   = int(_safe_float(r.get("american_odds") or r.get("best_odds"), 100))
    if barrel >= 10:   bcat = "elite"
    elif barrel >= 6:  bcat = "mid"
    else:              bcat = "low"
    if odds < 300:     ocat = "favorite"
    elif odds < 600:   ocat = "mid-odds"
    else:              ocat = "longshot"
    return f"{bcat}/{ocat}"


# ── HHI calculation ───────────────────────────────────────────────────────────

def _hhi(counts: dict) -> float:
    """Compute Herfindahl-Hirschman Index from a frequency dict."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return round(sum((v / total) ** 2 for v in counts.values()), 4)


# ── Exposure profile builder ──────────────────────────────────────────────────

def build_exposure_profile(rows: list[dict]) -> dict:
    """
    Build a full exposure profile for a set of picks.

    Args:
        rows: pick_tracker rows (any schema version)

    Returns:
        Nested dict with exposure distributions and HHI for each dimension.
    """
    if not rows:
        return {"n": 0, "dimensions": {}}

    n = len(rows)

    dimensions: dict[str, dict] = {}

    def _build_dim(label: str, key_fn) -> None:
        counts: dict[str, int] = defaultdict(int)
        for r in rows:
            counts[key_fn(r)] += 1
        hhi = _hhi(counts)
        max_share = max(v / n for v in counts.values()) if counts else 0.0
        ideal_hhi = 1.0 / len(counts) if counts else 1.0
        dimensions[label] = {
            "distribution": dict(sorted(counts.items(), key=lambda x: -x[1])),
            "hhi":          hhi,
            "ideal_hhi":    round(ideal_hhi, 4),
            "max_share":    round(max_share, 4),
            "n_buckets":    len(counts),
        }

    _build_dim("team",         lambda r: (r.get("team") or "UNK").upper().strip())
    _build_dim("barrel_tier",  _barrel_tier)
    _build_dim("odds_tier",    _odds_tier)
    _build_dim("park_tier",    _park_tier)
    _build_dim("weather_tier", _weather_tier)
    _build_dim("ev_tier",      _ev_tier)
    _build_dim("archetype",    _archetype)

    # Date-team clustering (same-game exposure)
    by_date_team: dict[tuple, int] = defaultdict(int)
    for r in rows:
        key = (r.get("date", ""), (r.get("team") or "UNK").upper().strip())
        by_date_team[key] += 1
    max_game_share = max(v / n for v in by_date_team.values()) if by_date_team else 0.0
    game_hhi = _hhi(by_date_team)

    # Pitcher (if available)
    pitcher_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        p = (r.get("pitcher") or "").strip()
        if p:
            pitcher_counts[p] += 1
    if pitcher_counts:
        _build_dim("pitcher", lambda r: (r.get("pitcher") or "unknown").strip())

    # Sportsbook (if available)
    book_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        b = (r.get("sportsbook") or "").strip()
        book_counts[b if b else "unknown"] += 1
    if any(k != "unknown" for k in book_counts):
        _build_dim("sportsbook", lambda r: (r.get("sportsbook") or "unknown").strip())

    return {
        "n":               n,
        "dimensions":      dimensions,
        "max_game_share":  round(max_game_share, 4),
        "game_hhi":        round(game_hhi, 4),
        "n_games":         len(by_date_team),
    }


def exposure_alerts(profile: dict) -> list[dict]:
    """
    Generate exposure alerts from a profile.

    Returns:
        List of {level, dimension, message} dicts sorted by severity.
    """
    alerts = []
    n = profile.get("n", 0)
    if n == 0:
        return alerts

    dims = profile.get("dimensions", {})

    # Same-game concentration
    max_game = profile.get("max_game_share", 0.0)
    if max_game > SAME_GAME_CAP:
        alerts.append({
            "level":     "HIGH",
            "dimension": "same_game",
            "message":   f"Single game has {max_game*100:.1f}% of portfolio ({max_game*n:.0f}/{n} picks). "
                         f"Cap same-team picks to reduce correlated exposure.",
        })
    elif max_game > TEAM_SHARE_ALERT:
        alerts.append({
            "level":     "MODERATE",
            "dimension": "same_game",
            "message":   f"Single game has {max_game*100:.1f}% of portfolio. "
                         f"Consider capping at {SAME_GAME_CAP*100:.0f}%.",
        })

    # Team HHI
    team_dim = dims.get("team", {})
    team_hhi = team_dim.get("hhi", 0.0)
    if team_hhi > HHI_HIGH:
        alerts.append({
            "level":     "HIGH",
            "dimension": "team",
            "message":   f"Team HHI={team_hhi:.3f} (threshold: {HHI_HIGH}). "
                         f"Portfolio is highly concentrated in few teams. "
                         f"Diversify across more teams or cap picks per team.",
        })
    elif team_hhi > HHI_MODERATE:
        alerts.append({
            "level":     "MODERATE",
            "dimension": "team",
            "message":   f"Team HHI={team_hhi:.3f} — moderate concentration. "
                         f"Ideal HHI={team_dim.get('ideal_hhi',0):.3f} ({team_dim.get('n_buckets',0)} teams).",
        })

    # Barrel quality concentration
    barrel_dim = dims.get("barrel_tier", {})
    if barrel_dim:
        barrel_dist = barrel_dim.get("distribution", {})
        low_barrel = barrel_dist.get("barrel <4%", 0) + barrel_dist.get("barrel 4-6%", 0)
        low_pct = low_barrel / n
        if low_pct > BARREL_LOW_ALERT:
            alerts.append({
                "level":     "HIGH",
                "dimension": "barrel_quality",
                "message":   f"{low_pct*100:.1f}% of picks have barrel <6% — below the edge breakeven threshold. "
                             f"Session 24 synthetic ROI for barrel<6%: −2.7% to −100%. "
                             f"Consider applying a barrel≥6% floor (or ≥8% for higher quality).",
            })
        elif low_pct > 0.40:
            alerts.append({
                "level":     "MODERATE",
                "dimension": "barrel_quality",
                "message":   f"{low_pct*100:.1f}% of picks have barrel <6%. "
                             f"Portfolio quality would improve with a barrel floor filter.",
            })

    # Odds concentration
    odds_dim = dims.get("odds_tier", {})
    if odds_dim and odds_dim.get("max_share", 0) > ODDS_TIER_CAP:
        top_bucket = max(odds_dim.get("distribution", {}).items(), key=lambda x: x[1], default=("unknown", 0))
        alerts.append({
            "level":     "MODERATE",
            "dimension": "odds_range",
            "message":   f"{top_bucket[0]} contains {odds_dim['max_share']*100:.1f}% of picks. "
                         f"Consider spreading exposure across odds ranges.",
        })

    # EV quality
    ev_dim = dims.get("ev_tier", {})
    if ev_dim:
        ev_dist = ev_dim.get("distribution", {})
        low_ev = ev_dist.get("EV 0-3%", 0)
        if low_ev / n > 0.30:
            alerts.append({
                "level":     "MODERATE",
                "dimension": "ev_quality",
                "message":   f"{low_ev/n*100:.1f}% of picks have EV<3%. "
                             f"Consider raising MIN_EV_PCT to 4% for higher-quality picks.",
            })

    return sorted(alerts, key=lambda x: {"HIGH": 0, "MODERATE": 1, "LOW": 2}.get(x["level"], 3))


def exposure_summary_text(profile: dict) -> list[str]:
    """Format profile as readable text lines."""
    lines = []
    n = profile.get("n", 0)
    dims = profile.get("dimensions", {})

    lines.append(f"  Portfolio size: {n} picks across {profile.get('n_games', 0)} team-games")

    for dim_name in ["team", "barrel_tier", "odds_tier", "ev_tier", "park_tier", "weather_tier"]:
        dim = dims.get(dim_name)
        if not dim:
            continue
        hhi     = dim["hhi"]
        ideal   = dim["ideal_hhi"]
        n_b     = dim["n_buckets"]
        max_s   = dim["max_share"]
        lines.append(f"\n  {dim_name.upper().replace('_',' ')}:")
        lines.append(f"    Buckets: {n_b}  HHI: {hhi:.3f}  (ideal: {ideal:.3f})  max share: {max_s*100:.1f}%")
        dist = dim["distribution"]
        for bucket, cnt in list(dist.items())[:5]:   # top 5
            pct = cnt / n * 100
            bar = "█" * int(pct / 2)
            lines.append(f"    {bucket:<25} {cnt:>4} ({pct:>5.1f}%)  {bar}")

    return lines


def fragility_score(profile: dict) -> float:
    """
    Composite fragility score [0-100]. Higher = more fragile.

    Components:
      - Game concentration (40%)
      - Barrel quality (35%)
      - EV quality (25%)
    """
    n = profile.get("n", 0)
    if n == 0:
        return 0.0

    dims = profile.get("dimensions", {})

    # Game concentration component (0-40)
    max_game = profile.get("max_game_share", 0.0)
    game_score = min(40.0, max_game / SAME_GAME_CAP * 40.0)

    # Barrel quality component (0-35)
    barrel_dist = dims.get("barrel_tier", {}).get("distribution", {})
    low_barrel_pct = (barrel_dist.get("barrel <4%", 0) + barrel_dist.get("barrel 4-6%", 0)) / n if n else 0
    barrel_score = min(35.0, low_barrel_pct / BARREL_LOW_ALERT * 35.0)

    # EV quality component (0-25)
    ev_dist = dims.get("ev_tier", {}).get("distribution", {})
    low_ev_pct = ev_dist.get("EV 0-3%", 0) / n if n else 0
    ev_score = min(25.0, low_ev_pct / 0.30 * 25.0)

    total = game_score + barrel_score + ev_score
    return round(total, 1)
