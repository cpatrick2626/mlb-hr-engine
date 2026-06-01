"""
Shared Pull AIR% resolution for HVY (display-scale 0–100).

Canonical value comes from pipeline `pull_air_pct` (Statcast-derived).
Fallback matches `app._pf` parsing of `pull_pct` / `fb_pct` / `ld_pct`.
"""

from __future__ import annotations

import math
from typing import Any, Mapping


def parse_pct_display(val: Any, default: float = 0.0) -> float:
    """Match `app._pf`: strip '%', treat None/'--'/empty as default."""
    if val is None:
        return default
    try:
        v = str(val).replace("%", "").strip()
        return float(v) if v and v != "--" else default
    except ValueError:
        return default


def _canonical_pull_air_pct(val: Any) -> float | None:
    """Return float if val coerces to a finite float (excludes bool)."""
    if val is None or isinstance(val, bool):
        return None
    try:
        x = float(val)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def resolve_pull_air_pct(player: Mapping[str, Any]) -> float:
    """
    Prefer finite `pull_air_pct` from the pipeline; else legacy `_pf`×formula.

    Legacy: pull_air = parse_pct_display(pull_pct) * (parse_pct_display(fb_pct)
              + parse_pct_display(ld_pct)) / 100.0
    """
    if not isinstance(player, Mapping):
        return 0.0
    c = _canonical_pull_air_pct(player.get("pull_air_pct"))
    if c is not None:
        return float(c)
    pull = parse_pct_display(player.get("pull_pct"), 0.0)
    fb = parse_pct_display(player.get("fb_pct"), 0.0)
    ld = parse_pct_display(player.get("ld_pct"), 0.0)
    return pull * (fb + ld) / 100.0
