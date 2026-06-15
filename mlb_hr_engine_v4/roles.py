"""
Role Layer — PRIME and EXPLOSIVE ticket role flags.

Read-only classification derived from existing leaderboard_rows fields.
No market data. No writes to model_prob, score, tier, or sort keys.
Non-exclusive: a player may hold both flags simultaneously.
"""
from __future__ import annotations
from typing import Any

import config


def _parse_pct(val: Any) -> float | None:
    """Parse string '44.8%' or float 44.8 → float. Returns None if unparseable."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        v = val.strip().rstrip("%")
        if not v or v in ("--", "-", "N/A"):
            return None
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _parse_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def classify_role(row: dict, tier: str = "") -> dict[str, bool]:
    """
    Derive PRIME and EXPLOSIVE role flags from a single leaderboard row.

    Args:
        row:  leaderboard player dict (pipeline output).
        tier: pre-computed FS tier string (APEX/ELITE/…). Pass from render context
              because pipeline rows do not carry a "tier" key — it is derived from
              model_prob at display time. Falls back to row.get("tier") if omitted.

    Returns {"prime": bool, "explosive": bool}.
    Never fabricates missing fields — a null required field = flag not awarded.
    """
    barrel  = _parse_pct(row.get("barrel_pct"))
    xslg    = _parse_float(row.get("xslg"))
    hh      = _parse_pct(row.get("hard_hit"))
    ev      = _parse_float(row.get("exit_velo"))
    if not tier:
        tier = row.get("tier") or ""
    max_ev  = _parse_float(row.get("max_ev"))
    blast   = _parse_float(row.get("blast"))
    pull_air = _parse_float(row.get("pull_air_pct"))

    # PRIME — all four Statcast fields must be present and above threshold,
    # and tier must be APEX or ELITE.
    prime = (
        barrel  is not None and barrel  >= config.ROLE_PRIME_BARREL_PCT
        and xslg    is not None and xslg    >= config.ROLE_PRIME_XSLG
        and hh      is not None and hh      >= config.ROLE_PRIME_HH_PCT
        and ev      is not None and ev      >= config.ROLE_PRIME_EV
        and tier in config.ROLE_PRIME_TIERS
    )

    # EXPLOSIVE — reliable core gate: max_ev + barrel% both required.
    # Swing trait gate: at least one of (blast% OR pull-air%) must pass its threshold.
    # Null blast = skip blast sub-criterion only; null pull_air = skip pull-air only.
    # Both null = no explosive trait present = EXPLOSIVE not awarded.
    explosive = False
    if (
        max_ev  is not None and max_ev  >= config.ROLE_EXPLOSIVE_MAX_EV
        and barrel is not None and barrel >= config.ROLE_EXPLOSIVE_BARREL_PCT
    ):
        blast_pass    = blast    is not None and blast    >= config.ROLE_EXPLOSIVE_BLAST_PCT
        pull_air_pass = pull_air is not None and pull_air >= config.ROLE_EXPLOSIVE_PULL_AIR_PCT
        explosive = blast_pass or pull_air_pass

    return {"prime": prime, "explosive": explosive}
