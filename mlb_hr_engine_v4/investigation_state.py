"""
Session-state ownership helpers for persistent tactical investigations.

This module keeps investigation context lightweight and route-safe. It stores
only small identifiers/metadata in st.session_state; it does not hydrate data,
trigger reruns, or execute engine-specific work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import streamlit as st


INVESTIGATION_STATE_KEY = "investigation_state"


@dataclass(frozen=True)
class ActivePlayerContext:
    active_player_id: Any = None
    active_player_name: str = ""
    active_game_pk: Any = None
    game_id: Any = None
    origin_engine: str = ""
    origin_route: str = ""
    last_viewed: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActiveGameContext:
    active_game_pk: Any = None
    game_id: Any = None
    home_team: str = ""
    away_team: str = ""
    game_time_utc: str = ""
    pitcher_id: Any = None
    pitcher_name: str = ""
    last_viewed: str = ""


@dataclass(frozen=True)
class EscalationQueueState:
    targets: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = ""


@dataclass(frozen=True)
class InvestigationState:
    active_player_id: Any = None
    active_player_name: str = ""
    active_game_pk: Any = None
    game_id: Any = None
    origin_engine: str = ""
    origin_route: str = ""
    current_route: str = ""
    escalation_level: str = "none"
    investigation_status: str = "idle"
    last_viewed: str = ""
    trust_state: Any = None
    notes: str = ""
    active_player: dict[str, Any] = field(default_factory=dict)
    active_game: dict[str, Any] = field(default_factory=dict)
    escalation_queue: dict[str, Any] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _empty_state() -> dict[str, Any]:
    state = asdict(InvestigationState())
    state["escalation_queue"] = asdict(EscalationQueueState())
    return state


def _infer_engine(origin_engine: str | None, origin_route: str | None) -> str:
    raw = (origin_engine or origin_route or "").strip()
    if not raw:
        return ""
    upper = raw.upper()
    if "JIG" in upper:
        return "JIG"
    if "MAIN" in upper or "COMMAND CENTER" in upper or "FULL SLATE" in upper:
        return "MAIN"
    if "ADVANCED" in upper:
        return "ADVANCED_STRATEGIES"
    return upper.replace(" ", "_")


def init_investigation_state() -> dict[str, Any]:
    """Create the canonical investigation state without overwriting live context."""
    state = st.session_state.setdefault(INVESTIGATION_STATE_KEY, _empty_state())
    defaults = _empty_state()
    for key, value in defaults.items():
        state.setdefault(key, value)
    state.setdefault("escalation_queue", asdict(EscalationQueueState()))
    state["escalation_queue"].setdefault("targets", [])
    state["escalation_queue"].setdefault("updated_at", "")
    return state


def get_investigation_state() -> dict[str, Any]:
    """Return the canonical investigation state dictionary."""
    return init_investigation_state()


def record_route_context(active_route: str) -> dict[str, Any]:
    """Track route continuity without hydrating inactive engines."""
    state = init_investigation_state()
    if active_route and state.get("current_route") != active_route:
        state["current_route"] = active_route
    return state


def record_active_player(
    player: dict[str, Any],
    *,
    origin_engine: str | None = None,
    origin_route: str | None = None,
    escalation_level: str | None = None,
    investigation_status: str = "active",
) -> dict[str, Any]:
    """Persist the active player/game context for route-safe investigation flow."""
    if not isinstance(player, dict):
        return init_investigation_state()

    state = init_investigation_state()
    now = _now_iso()
    player_id = _first_present(player, "player_id", "batter_id", "mlb_id")
    player_name = str(_first_present(player, "player_name", "name") or "")
    game_pk = _first_present(player, "game_pk", "active_game_pk")
    game_id = _first_present(player, "game_id", "active_game_id") or game_pk
    engine = _infer_engine(origin_engine, origin_route)

    player_ctx = ActivePlayerContext(
        active_player_id=player_id,
        active_player_name=player_name,
        active_game_pk=game_pk,
        game_id=game_id,
        origin_engine=engine,
        origin_route=origin_route or "",
        last_viewed=now,
        metadata={
            "team": player.get("team", ""),
            "opponent": player.get("opponent", ""),
            "pitcher_id": player.get("pitcher_id"),
            "pitcher_name": player.get("pitcher_name", ""),
            "lineup_spot": player.get("lineup_spot"),
        },
    )
    game_ctx = ActiveGameContext(
        active_game_pk=game_pk,
        game_id=game_id,
        home_team=str(player.get("home_team", "") or ""),
        away_team=str(player.get("away_team", "") or player.get("team", "") or ""),
        game_time_utc=str(player.get("game_time_utc", "") or ""),
        pitcher_id=player.get("pitcher_id"),
        pitcher_name=str(player.get("pitcher_name", "") or ""),
        last_viewed=now,
    )

    state.update(
        {
            "active_player_id": player_id,
            "active_player_name": player_name,
            "active_game_pk": game_pk,
            "game_id": game_id,
            "origin_engine": engine,
            "origin_route": origin_route or "",
            "escalation_level": escalation_level or state.get("escalation_level", "none"),
            "investigation_status": investigation_status,
            "last_viewed": now,
            "active_player": asdict(player_ctx),
            "active_game": asdict(game_ctx),
        }
    )
    return state


def _target_identity(target: dict[str, Any]) -> str:
    player_id = _first_present(target, "target_id", "active_player_id", "player_id", "batter_id", "mlb_id")
    player_name = str(_first_present(target, "active_player_name", "player_name", "name") or "").strip()
    game_id = _first_present(target, "active_game_pk", "game_pk", "game_id") or "no_game"
    if player_id not in (None, ""):
        return f"{player_id}:{game_id}"
    safe_name = "_".join(player_name.lower().split()) if player_name else "unknown"
    return f"{safe_name}:{game_id}"


def add_escalation_target(
    target: dict[str, Any],
    *,
    origin_engine: str | None = None,
    origin_route: str | None = None,
    escalation_level: str = "watch",
    investigation_status: str = "queued",
    trust_state: Any = None,
    notes: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add or update one deterministic escalation target."""
    if not isinstance(target, dict):
        raise TypeError("Escalation target must be a dictionary.")

    state = init_investigation_state()
    queue = state["escalation_queue"]
    targets = list(queue.get("targets", []))
    now = _now_iso()
    engine = _infer_engine(origin_engine, origin_route)
    target_id = _target_identity(target)

    next_target = {
        "target_id": target_id,
        "active_player_id": _first_present(target, "active_player_id", "player_id", "batter_id", "mlb_id"),
        "active_player_name": str(_first_present(target, "active_player_name", "player_name", "name") or ""),
        "active_game_pk": _first_present(target, "active_game_pk", "game_pk"),
        "game_id": _first_present(target, "game_id", "active_game_pk", "game_pk"),
        "origin_engine": engine,
        "origin_route": origin_route or "",
        "escalation_level": escalation_level,
        "investigation_status": investigation_status,
        "trust_state": trust_state,
        "notes": notes,
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
    }

    for idx, existing in enumerate(targets):
        if existing.get("target_id") == target_id:
            merged = {**existing, **next_target}
            merged["created_at"] = existing.get("created_at", now)
            merged["metadata"] = {**existing.get("metadata", {}), **(metadata or {})}
            targets[idx] = merged
            break
    else:
        targets.append(next_target)

    queue["targets"] = targets
    queue["updated_at"] = now
    return next_target


def remove_escalation_target(target_id: str) -> bool:
    """Remove a queued escalation target by deterministic target_id."""
    state = init_investigation_state()
    queue = state["escalation_queue"]
    targets = list(queue.get("targets", []))
    kept = [target for target in targets if target.get("target_id") != target_id]
    if len(kept) == len(targets):
        return False
    queue["targets"] = kept
    queue["updated_at"] = _now_iso()
    return True


def get_escalation_queue() -> dict[str, Any]:
    """Return the tactical escalation queue state."""
    return init_investigation_state()["escalation_queue"]
