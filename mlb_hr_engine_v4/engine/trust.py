"""
engine/trust.py — Source trust-state taxonomy for MLB HR Engine (Room 07).

Governs what model signals are active, what outputs are displayed, and what
betting escalation is permitted under degraded data conditions.

── Source labels ──────────────────────────────────────────────────────────────
  SC   Statcast (Baseball Savant barrel/exit-velo/FB% data)
  BL   Baseline (MLB Stats API — schedule, lineups, player stats)
  PR   Props/Odds (The Odds API / manual_odds.csv fallback)
  --   Unavailable (no usable data from any source)

── Per-source trust levels ────────────────────────────────────────────────────
  LIVE        Fresh data from primary source, within TTL
  CACHED      Valid cache hit from current session or disk (within TTL)
  STALE       Expired cache served as emergency fallback (>TTL)
  FALLBACK    Secondary source active (e.g. manual_odds.csv for PR)
  DEGRADED    Partial data — critical fields missing
  UNAVAILABLE No data from any source (maps to "--" display label)

── Composite engine state ─────────────────────────────────────────────────────
  FULL        All SC + BL + PR are LIVE or CACHED
  DEGRADED    ≥1 source is STALE, FALLBACK, or DEGRADED
  RESTRICTED  Critical source UNAVAILABLE — suppress exploit escalation
  BLOCKED     BL unavailable — no lineup means no picks possible

── Penalty flags (derived from composite state) ──────────────────────────────
  statcast_active       False → power multiplier frozen at 1.0
  ev_display_active     False → hide EV% values in output
  escalation_active     False → block exploit escalation / deploy actions
  ranking_active        False → suppress all pick rankings
  lineup_filter_active  False → disable lineup-position (PA) filter

── Usage ──────────────────────────────────────────────────────────────────────
  from engine.trust import build_pr_trust, build_sc_trust, build_bl_trust
  from engine.trust import build_engine_trust, get_engine_trust, set_engine_trust

  sc = build_sc_trust(fetched_at_iso="2026-05-20T14:00:00+00:00")
  bl = build_bl_trust(fetched_at_iso="2026-05-20T15:30:00+00:00", lineup_available=True)
  pr = build_pr_trust(source_label="The Odds API (cached)", fetched_at_iso="2026-05-20T15:45:00+00:00")
  trust = build_engine_trust(sc, bl, pr)
  set_engine_trust(trust)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ── Freshness thresholds (minutes) ────────────────────────────────────────────

# Statcast: scraped from Baseball Savant; updates once daily before noon ET.
SC_LIVE_TTL_MIN         = 360    # 6h  — fresh for in-session use
SC_STALE_DISABLE_MIN    = 1440   # 24h — beyond this, disable SC factor entirely

# Baseline (MLB Stats API): lineups posted ~60–90min before first pitch.
BL_LIVE_TTL_MIN         = 90     # 90min — safe for pre-game lineup lock
BL_STALE_FILTER_MIN     = 180    # 3h  — disable lineup-position filter

# Props/Odds: disk cache TTL matches CACHE_TTL_MINUTES in odds_api.py.
PR_LIVE_TTL_MIN         = 45     # 45min — matches existing cache TTL
PR_STALE_HIDE_EV_MIN    = 120    # 2h  — hide EV% display beyond this
PR_STALE_DISABLE_ESC_MIN = 240   # 4h  — disable escalation beyond this


# ── Enums ─────────────────────────────────────────────────────────────────────

class SourceLevel(str, Enum):
    LIVE        = "LIVE"
    CACHED      = "CACHED"
    STALE       = "STALE"
    FALLBACK    = "FALLBACK"
    DEGRADED    = "DEGRADED"
    UNAVAILABLE = "--"


class EngineState(str, Enum):
    FULL        = "FULL"
    DEGRADED    = "DEGRADED"
    RESTRICTED  = "RESTRICTED"
    BLOCKED     = "BLOCKED"


# Severity ordering (higher = worse)
_LEVEL_SEVERITY: dict[SourceLevel, int] = {
    SourceLevel.LIVE:        0,
    SourceLevel.CACHED:      1,
    SourceLevel.STALE:       2,
    SourceLevel.FALLBACK:    2,
    SourceLevel.DEGRADED:    3,
    SourceLevel.UNAVAILABLE: 4,
}

_STATE_SEVERITY: dict[EngineState, int] = {
    EngineState.FULL:       0,
    EngineState.DEGRADED:   1,
    EngineState.RESTRICTED: 2,
    EngineState.BLOCKED:    3,
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class SourceTrust:
    """Trust state for one data source (SC, BL, or PR)."""
    source: str                          # "SC" | "BL" | "PR"
    level: SourceLevel
    age_minutes: Optional[float] = None  # minutes since data was fetched
    fetched_at: str = ""                 # ISO-8601 UTC timestamp of fetch
    message: str = ""                    # human-readable one-liner for UX
    degraded_fields: list[str] = field(default_factory=list)  # missing fields

    @property
    def severity(self) -> int:
        return _LEVEL_SEVERITY[self.level]

    @property
    def is_healthy(self) -> bool:
        return self.level in (SourceLevel.LIVE, SourceLevel.CACHED)

    @property
    def is_usable(self) -> bool:
        return self.level != SourceLevel.UNAVAILABLE

    @property
    def badge(self) -> str:
        return _LEVEL_BADGE[self.level]

    def to_dict(self) -> dict:
        return {
            "source":          self.source,
            "level":           self.level.value,
            "age_minutes":     round(self.age_minutes, 1) if self.age_minutes is not None else None,
            "fetched_at":      self.fetched_at,
            "message":         self.message,
            "degraded_fields": self.degraded_fields,
        }


@dataclass
class EngineTrust:
    """
    Composite engine-level trust state derived from SC + BL + PR.

    All penalty flags are computed by apply_penalties() and stored here
    so that pipeline.py and app.py both read from one authoritative object.
    """
    sc: SourceTrust
    bl: SourceTrust
    pr: SourceTrust
    state: EngineState
    computed_at: str = ""

    # Penalty flags — derived, do not set manually
    statcast_active:      bool = True   # False → power_mult = 1.0 (no SC boost/penalty)
    ev_display_active:    bool = True   # False → suppress EV% in all output
    escalation_active:    bool = True   # False → block exploit escalation / bet deploy
    ranking_active:       bool = True   # False → suppress all pick rankings and output
    lineup_filter_active: bool = True   # False → disable lineup-position PA filter

    @property
    def severity(self) -> int:
        return _STATE_SEVERITY[self.state]

    @property
    def is_full(self) -> bool:
        return self.state == EngineState.FULL

    @property
    def is_blocked(self) -> bool:
        return self.state == EngineState.BLOCKED

    @property
    def badge(self) -> str:
        return _STATE_BADGE[self.state]

    @property
    def active_suppressions(self) -> list[str]:
        """Return list of suppressed capabilities for UX warning display."""
        out = []
        if not self.statcast_active:
            out.append("Statcast factor disabled (SC stale/unavailable)")
        if not self.ev_display_active:
            out.append("EV% hidden (odds too stale)")
        if not self.escalation_active:
            out.append("Escalation blocked (odds unavailable)")
        if not self.ranking_active:
            out.append("Rankings blocked (no lineup data)")
        if not self.lineup_filter_active:
            out.append("Lineup-position filter disabled (lineup degraded)")
        return out

    def to_dict(self) -> dict:
        return {
            "state":                self.state.value,
            "computed_at":          self.computed_at,
            "sc":                   self.sc.to_dict(),
            "bl":                   self.bl.to_dict(),
            "pr":                   self.pr.to_dict(),
            "statcast_active":      self.statcast_active,
            "ev_display_active":    self.ev_display_active,
            "escalation_active":    self.escalation_active,
            "ranking_active":       self.ranking_active,
            "lineup_filter_active": self.lineup_filter_active,
            "active_suppressions":  self.active_suppressions,
        }


# ── Display constants ─────────────────────────────────────────────────────────

_LEVEL_BADGE: dict[SourceLevel, str] = {
    SourceLevel.LIVE:        "LIVE",
    SourceLevel.CACHED:      "CACHED",
    SourceLevel.STALE:       "STALE",
    SourceLevel.FALLBACK:    "FALLBACK",
    SourceLevel.DEGRADED:    "DEGRADED",
    SourceLevel.UNAVAILABLE: "--",
}

_STATE_BADGE: dict[EngineState, str] = {
    EngineState.FULL:       "FULL",
    EngineState.DEGRADED:   "DEGRADED",
    EngineState.RESTRICTED: "RESTRICTED",
    EngineState.BLOCKED:    "BLOCKED",
}

# Severity → CSS-friendly color label (consumed by UX layer, not applied here)
LEVEL_COLOR: dict[SourceLevel, str] = {
    SourceLevel.LIVE:        "green",
    SourceLevel.CACHED:      "yellow",
    SourceLevel.STALE:       "orange",
    SourceLevel.FALLBACK:    "blue",
    SourceLevel.DEGRADED:    "red",
    SourceLevel.UNAVAILABLE: "gray",
}

STATE_COLOR: dict[EngineState, str] = {
    EngineState.FULL:       "green",
    EngineState.DEGRADED:   "yellow",
    EngineState.RESTRICTED: "orange",
    EngineState.BLOCKED:    "red",
}


# ── Factory helpers ───────────────────────────────────────────────────────────

def _age_minutes(fetched_at_iso: Optional[str]) -> Optional[float]:
    """Compute minutes since fetched_at_iso (UTC ISO string). Returns None if unparseable."""
    if not fetched_at_iso:
        return None
    try:
        if fetched_at_iso.endswith("Z"):
            fetched_at_iso = fetched_at_iso[:-1] + "+00:00"
        ts = datetime.fromisoformat(fetched_at_iso)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
    except Exception:
        return None


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ── Source trust factories ────────────────────────────────────────────────────

def build_sc_trust(
    fetched_at_iso: Optional[str] = None,
    *,
    missing_fields: Optional[list[str]] = None,
    fetch_failed: bool = False,
) -> SourceTrust:
    """
    Build Statcast (SC) trust state from fetch metadata.

    Args:
        fetched_at_iso:  ISO UTC timestamp of the Statcast fetch.
        missing_fields:  List of fields that are absent (e.g. ["barrel_rate"]).
        fetch_failed:    True when the entire fetch returned no data.
    """
    missing = missing_fields or []

    if fetch_failed or fetched_at_iso is None:
        return SourceTrust(
            source="SC",
            level=SourceLevel.UNAVAILABLE,
            age_minutes=None,
            fetched_at="",
            message="Statcast unavailable — power multiplier disabled",
        )

    age = _age_minutes(fetched_at_iso)

    if missing:
        return SourceTrust(
            source="SC",
            level=SourceLevel.DEGRADED,
            age_minutes=age,
            fetched_at=fetched_at_iso,
            message=f"Statcast partial — missing: {', '.join(missing)}",
            degraded_fields=missing,
        )

    if age is not None and age > SC_STALE_DISABLE_MIN:
        return SourceTrust(
            source="SC",
            level=SourceLevel.UNAVAILABLE,
            age_minutes=age,
            fetched_at=fetched_at_iso,
            message=f"Statcast too old ({age/60:.1f}h) — power multiplier disabled",
        )

    if age is not None and age > SC_LIVE_TTL_MIN:
        return SourceTrust(
            source="SC",
            level=SourceLevel.STALE,
            age_minutes=age,
            fetched_at=fetched_at_iso,
            message=f"Statcast stale ({age/60:.1f}h) — using cached signal",
        )

    level = SourceLevel.LIVE if (age is not None and age < 5) else SourceLevel.CACHED
    return SourceTrust(
        source="SC",
        level=level,
        age_minutes=age,
        fetched_at=fetched_at_iso,
        message="Statcast fresh",
    )


def build_bl_trust(
    fetched_at_iso: Optional[str] = None,
    *,
    lineup_available: bool = True,
    fetch_failed: bool = False,
) -> SourceTrust:
    """
    Build Baseline/MLB-Stats (BL) trust state.

    Args:
        fetched_at_iso:    ISO UTC timestamp of the MLB Stats API fetch.
        lineup_available:  False when today's lineup was not returned.
        fetch_failed:      True when the entire API call failed.
    """
    if fetch_failed or fetched_at_iso is None:
        return SourceTrust(
            source="BL",
            level=SourceLevel.UNAVAILABLE,
            age_minutes=None,
            fetched_at="",
            message="MLB Stats API unavailable — no picks possible",
        )

    age = _age_minutes(fetched_at_iso)

    if not lineup_available:
        return SourceTrust(
            source="BL",
            level=SourceLevel.DEGRADED,
            age_minutes=age,
            fetched_at=fetched_at_iso,
            message="Lineup not yet posted — lineup-position filter disabled",
            degraded_fields=["lineup"],
        )

    if age is not None and age > BL_STALE_FILTER_MIN:
        return SourceTrust(
            source="BL",
            level=SourceLevel.STALE,
            age_minutes=age,
            fetched_at=fetched_at_iso,
            message=f"MLB Stats stale ({age/60:.1f}h) — lineup may have changed",
        )

    if age is not None and age > BL_LIVE_TTL_MIN:
        return SourceTrust(
            source="BL",
            level=SourceLevel.CACHED,
            age_minutes=age,
            fetched_at=fetched_at_iso,
            message="MLB Stats cached — check lineup lock",
        )

    return SourceTrust(
        source="BL",
        level=SourceLevel.LIVE,
        age_minutes=age,
        fetched_at=fetched_at_iso,
        message="MLB Stats fresh",
    )


def build_pr_trust(
    source_label: str = "",
    fetched_at_iso: Optional[str] = None,
) -> SourceTrust:
    """
    Build Props/Odds (PR) trust state from the source label returned by odds_api.py.

    source_label values from odds_api.get_hr_odds_all_games():
      "The Odds API"              → LIVE
      "The Odds API (cached)"     → CACHED
      "The Odds API (stale cache)"→ STALE
      "manual_odds.csv"           → FALLBACK
      "none" or ""                → UNAVAILABLE
    """
    age = _age_minutes(fetched_at_iso)
    label = source_label.lower().strip()

    if not label or label == "none":
        return SourceTrust(
            source="PR",
            level=SourceLevel.UNAVAILABLE,
            age_minutes=age,
            fetched_at=fetched_at_iso or "",
            message="No odds data — EV% and escalation disabled",
        )

    if "manual" in label or "csv" in label:
        return SourceTrust(
            source="PR",
            level=SourceLevel.FALLBACK,
            age_minutes=age,
            fetched_at=fetched_at_iso or "",
            message="Using manual_odds.csv fallback — EV approximate",
        )

    if "stale" in label:
        msg_age = f" ({age/60:.1f}h)" if age else ""
        hide_ev = age is not None and age > PR_STALE_HIDE_EV_MIN
        ev_note = " — EV% hidden" if hide_ev else ""
        return SourceTrust(
            source="PR",
            level=SourceLevel.STALE,
            age_minutes=age,
            fetched_at=fetched_at_iso or "",
            message=f"Odds stale{msg_age}{ev_note}",
        )

    if "cached" in label:
        return SourceTrust(
            source="PR",
            level=SourceLevel.CACHED,
            age_minutes=age,
            fetched_at=fetched_at_iso or "",
            message="Odds from cache (within TTL)",
        )

    # "The Odds API" bare — live fetch
    return SourceTrust(
        source="PR",
        level=SourceLevel.LIVE,
        age_minutes=age,
        fetched_at=fetched_at_iso or "",
        message="Odds live",
    )


# ── Composite engine trust ────────────────────────────────────────────────────

def _compute_engine_state(sc: SourceTrust, bl: SourceTrust, pr: SourceTrust) -> EngineState:
    """Derive composite state from worst-case source combination."""
    if bl.level == SourceLevel.UNAVAILABLE:
        return EngineState.BLOCKED

    if sc.level == SourceLevel.UNAVAILABLE or pr.level == SourceLevel.UNAVAILABLE:
        return EngineState.RESTRICTED

    unhealthy = {SourceLevel.STALE, SourceLevel.FALLBACK, SourceLevel.DEGRADED}
    if any(s.level in unhealthy for s in (sc, bl, pr)):
        return EngineState.DEGRADED

    return EngineState.FULL


def _apply_penalties(
    sc: SourceTrust,
    bl: SourceTrust,
    pr: SourceTrust,
    state: EngineState,
) -> dict[str, bool]:
    """Compute all penalty flags from source trust states."""

    # Statcast factor disabled when SC is stale or worse
    statcast_active = sc.level not in (SourceLevel.STALE, SourceLevel.UNAVAILABLE)

    # EV% display hidden when PR is unavailable OR stale beyond EV threshold
    pr_too_stale_for_ev = (
        pr.level == SourceLevel.STALE
        and pr.age_minutes is not None
        and pr.age_minutes > PR_STALE_HIDE_EV_MIN
    )
    ev_display_active = pr.level != SourceLevel.UNAVAILABLE and not pr_too_stale_for_ev

    # Escalation blocked when PR unavailable OR stale beyond escalation threshold
    pr_too_stale_for_esc = (
        pr.level == SourceLevel.STALE
        and pr.age_minutes is not None
        and pr.age_minutes > PR_STALE_DISABLE_ESC_MIN
    )
    escalation_active = (
        pr.level != SourceLevel.UNAVAILABLE
        and not pr_too_stale_for_esc
        and state not in (EngineState.BLOCKED, EngineState.RESTRICTED)
    )

    # Rankings blocked when BL unavailable (no lineup = no picks)
    ranking_active = bl.level != SourceLevel.UNAVAILABLE

    # Lineup-position filter disabled when BL is UNAVAILABLE or DEGRADED (lineup not posted)
    lineup_filter_active = bl.level not in (SourceLevel.UNAVAILABLE, SourceLevel.DEGRADED)

    return {
        "statcast_active":      statcast_active,
        "ev_display_active":    ev_display_active,
        "escalation_active":    escalation_active,
        "ranking_active":       ranking_active,
        "lineup_filter_active": lineup_filter_active,
    }


def build_engine_trust(sc: SourceTrust, bl: SourceTrust, pr: SourceTrust) -> EngineTrust:
    """Build composite EngineTrust with penalties applied. Call after all three source fetches."""
    state = _compute_engine_state(sc, bl, pr)
    flags = _apply_penalties(sc, bl, pr, state)
    return EngineTrust(
        sc=sc,
        bl=bl,
        pr=pr,
        state=state,
        computed_at=_now_utc_iso(),
        **flags,
    )


# ── Convenience constructors ──────────────────────────────────────────────────

def neutral_engine_trust() -> EngineTrust:
    """
    Return a fully-healthy trust object used as default before any source fetch.
    All flags active, all sources marked LIVE with age=0.
    """
    now = _now_utc_iso()
    sc = SourceTrust("SC", SourceLevel.LIVE, age_minutes=0.0, fetched_at=now, message="Assuming fresh (pre-fetch)")
    bl = SourceTrust("BL", SourceLevel.LIVE, age_minutes=0.0, fetched_at=now, message="Assuming fresh (pre-fetch)")
    pr = SourceTrust("PR", SourceLevel.LIVE, age_minutes=0.0, fetched_at=now, message="Assuming fresh (pre-fetch)")
    return EngineTrust(
        sc=sc, bl=bl, pr=pr,
        state=EngineState.FULL,
        computed_at=now,
    )


def unavailable_engine_trust(reason: str = "") -> EngineTrust:
    """Return a fully-blocked trust object (used on critical startup failure)."""
    now = _now_utc_iso()
    msg = reason or "Source unavailable"
    sc = SourceTrust("SC", SourceLevel.UNAVAILABLE, fetched_at=now, message=msg)
    bl = SourceTrust("BL", SourceLevel.UNAVAILABLE, fetched_at=now, message=msg)
    pr = SourceTrust("PR", SourceLevel.UNAVAILABLE, fetched_at=now, message=msg)
    return EngineTrust(
        sc=sc, bl=bl, pr=pr,
        state=EngineState.BLOCKED,
        computed_at=now,
        statcast_active=False,
        ev_display_active=False,
        escalation_active=False,
        ranking_active=False,
        lineup_filter_active=False,
    )


# ── Freshness scoring ─────────────────────────────────────────────────────────

def source_freshness_score(trust: SourceTrust) -> float:
    """
    Compute a 0.0–1.0 freshness score for a single source.
    1.0 = freshly live; 0.0 = unavailable.
    Used by analysis tools and monitoring dashboards.
    """
    level_base = {
        SourceLevel.LIVE:        1.00,
        SourceLevel.CACHED:      0.80,
        SourceLevel.STALE:       0.40,
        SourceLevel.FALLBACK:    0.50,
        SourceLevel.DEGRADED:    0.30,
        SourceLevel.UNAVAILABLE: 0.00,
    }[trust.level]

    if trust.age_minutes is None or trust.level == SourceLevel.UNAVAILABLE:
        return level_base

    # Linearly decay within the STALE band
    if trust.level == SourceLevel.STALE:
        if trust.source == "SC":
            decay = max(0.0, 1.0 - (trust.age_minutes - SC_LIVE_TTL_MIN) / (SC_STALE_DISABLE_MIN - SC_LIVE_TTL_MIN))
        elif trust.source == "BL":
            decay = max(0.0, 1.0 - (trust.age_minutes - BL_LIVE_TTL_MIN) / (BL_STALE_FILTER_MIN - BL_LIVE_TTL_MIN))
        else:
            decay = max(0.0, 1.0 - (trust.age_minutes - PR_LIVE_TTL_MIN) / (PR_STALE_HIDE_EV_MIN - PR_LIVE_TTL_MIN))
        return round(level_base * (0.5 + 0.5 * decay), 3)

    return level_base


def engine_freshness_score(trust: EngineTrust) -> float:
    """
    Composite 0.0–1.0 freshness score for the full engine.
    Weighted: BL=40% (lineup critical), SC=35%, PR=25%.
    """
    return round(
        0.40 * source_freshness_score(trust.bl)
        + 0.35 * source_freshness_score(trust.sc)
        + 0.25 * source_freshness_score(trust.pr),
        3,
    )


# ── Validation helpers ────────────────────────────────────────────────────────

def validate_source_trust(trust: SourceTrust) -> list[str]:
    """Return list of validation errors for a SourceTrust object."""
    errors: list[str] = []
    valid_sources = {"SC", "BL", "PR"}
    if trust.source not in valid_sources:
        errors.append(f"Invalid source '{trust.source}' — must be SC, BL, or PR")
    if not isinstance(trust.level, SourceLevel):
        errors.append(f"Invalid level '{trust.level}'")
    if trust.age_minutes is not None and trust.age_minutes < 0:
        errors.append(f"Negative age_minutes ({trust.age_minutes:.1f})")
    return errors


def validate_engine_trust(trust: EngineTrust) -> list[str]:
    """Return list of validation errors for an EngineTrust object."""
    errors: list[str] = []
    for src in (trust.sc, trust.bl, trust.pr):
        errors.extend(validate_source_trust(src))

    # Verify penalty flags are consistent with declared state
    if trust.state == EngineState.BLOCKED and trust.ranking_active:
        errors.append("BLOCKED state but ranking_active=True — inconsistent")
    if trust.state == EngineState.RESTRICTED and trust.escalation_active:
        errors.append("RESTRICTED state but escalation_active=True — inconsistent")
    if trust.bl.level == SourceLevel.UNAVAILABLE and trust.lineup_filter_active:
        errors.append("BL unavailable but lineup_filter_active=True — inconsistent")

    return errors


# ── Global singleton ──────────────────────────────────────────────────────────
#
# The pipeline sets this once per run; app.py reads it for UX rendering.
# All access must go through get/set; never read _current_trust directly.

_current_trust: Optional[EngineTrust] = None


def set_engine_trust(trust: EngineTrust) -> None:
    """Store the current engine trust state. Called by pipeline.py after source fetches."""
    global _current_trust
    errors = validate_engine_trust(trust)
    if errors:
        print(f"[trust] WARNING — trust object has {len(errors)} validation error(s): {errors[0]}")
    _current_trust = trust


def get_engine_trust() -> EngineTrust:
    """Return current engine trust state. Returns neutral_engine_trust() if not yet set."""
    return _current_trust if _current_trust is not None else neutral_engine_trust()


def reset_engine_trust() -> None:
    """Clear stored trust state (used in tests and between pipeline runs)."""
    global _current_trust
    _current_trust = None
