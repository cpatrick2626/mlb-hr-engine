"""Navigation state — single-source routing authority.

Owns active_route (T1) and active_sub_room (T2) session-state keys.
active_route is the sole authoritative section key — active_section removed.
Does NOT touch layout, content routing, or rendering.
"""
from __future__ import annotations

from typing import Any, MutableMapping

# ── Section registry ──────────────────────────────────────────────────────────
SECTION_MAIN = "MAIN"
SECTION_JIG = "JIG"
SECTION_STRATEGY = "ADVANCED_STRATEGIES"
SECTION_HITS = "HITS"
SECTION_PERFORMANCE = "PERFORMANCE"

SECTIONS: tuple[str, ...] = (
    SECTION_MAIN,
    SECTION_JIG,
    SECTION_STRATEGY,
    SECTION_HITS,
    SECTION_PERFORMANCE,
)

# ── Ordered sub-room registry per section ─────────────────────────────────────
# STRATEGY / HITS / PERFORMANCE are direct sections — no sub-room ownership.
SUB_ROOMS: dict[str, tuple[str, ...]] = {
    SECTION_MAIN: (
        "Full Slate",
        "Command Center",
        "Top Targets",
        "Match Edge",
        "Portfolio",
    ),
    SECTION_JIG: (
        "JIG Builder",
        "Top Targets",
        "Match Edge",
        "Full Slate",
        "Portfolio",
    ),
    SECTION_STRATEGY: (),
    SECTION_HITS: (),
    SECTION_PERFORMANCE: (),
}

# ── Default sub-room per section ──────────────────────────────────────────────
SECTION_DEFAULTS: dict[str, str] = {
    SECTION_MAIN: "Full Slate",
    SECTION_JIG: "JIG Builder",
    SECTION_STRATEGY: "",
    SECTION_HITS: "",
    SECTION_PERFORMANCE: "",
}

_ACTIVE_SECTION_KEY = "active_route"
_ACTIVE_SUB_ROOM_KEY = "active_sub_room"


# ── Initializer ───────────────────────────────────────────────────────────────

def init_nav_state(state: MutableMapping[str, Any]) -> None:
    """Initialize active_route and active_sub_room without overwriting valid values."""
    current_section = state.get(_ACTIVE_SECTION_KEY)
    if current_section not in SECTIONS:
        state[_ACTIVE_SECTION_KEY] = SECTION_MAIN

    section = state[_ACTIVE_SECTION_KEY]
    current_sub = state.get(_ACTIVE_SUB_ROOM_KEY)
    valid_subs = SUB_ROOMS.get(section, ())
    if not current_sub or (valid_subs and current_sub not in valid_subs):
        state[_ACTIVE_SUB_ROOM_KEY] = SECTION_DEFAULTS.get(section, "")


# ── Getters ───────────────────────────────────────────────────────────────────

def get_active_section(state: MutableMapping[str, Any]) -> str:
    return str(state.get(_ACTIVE_SECTION_KEY, SECTION_MAIN))


def get_active_sub_room(state: MutableMapping[str, Any]) -> str:
    return str(state.get(_ACTIVE_SUB_ROOM_KEY, ""))


# ── Setters ───────────────────────────────────────────────────────────────────

def set_active_section(state: MutableMapping[str, Any], section: str) -> str:
    """Set section. Resets active_sub_room to section default only when section changes."""
    if section not in SECTIONS:
        section = SECTION_MAIN
    prev = state.get(_ACTIVE_SECTION_KEY)
    state[_ACTIVE_SECTION_KEY] = section
    if section != prev:
        state[_ACTIVE_SUB_ROOM_KEY] = SECTION_DEFAULTS.get(section, "")
    return section


def set_active_sub_room(state: MutableMapping[str, Any], sub_room: str) -> str:
    """Set active sub-room within the current section."""
    state[_ACTIVE_SUB_ROOM_KEY] = sub_room
    return sub_room


# ── Helpers ───────────────────────────────────────────────────────────────────

def sub_rooms_for_section(section: str) -> tuple[str, ...]:
    return SUB_ROOMS.get(section, ())


def has_sub_rooms(section: str) -> bool:
    return bool(SUB_ROOMS.get(section))
