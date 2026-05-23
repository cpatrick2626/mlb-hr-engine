"""Passive navigation continuity helpers for MLB HR Engine.

This module owns the safe runtime subset for navigation restoration,
operator shortlist state, breadcrumb context, interruption notices, and
recovery prompt shells. It does not mutate route ownership or execute
navigation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping
from uuid import uuid4


NAV_RESTORATION_STACK_KEY = "nav_restoration_stack"
NAV_RESTORATION_STACK_MAX_DEPTH = 10
OPERATOR_SHORTLIST_KEY = "operator_shortlist"
OPERATOR_SHORTLIST_MAX_ITEMS = 12
ACTIVE_BREADCRUMB_CONTEXT_KEY = "active_breadcrumb_context"
INTERRUPTION_NOTICE_QUEUE_KEY = "interruption_notice_queue"
RECOVERY_PROMPT_STATE_KEY = "recovery_prompt_state"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_str(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    return bool(value)


def _copy_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _copy_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _ensure_list(state: MutableMapping[str, Any], key: str) -> list[Any]:
    if key in state and isinstance(state[key], list):
        return state[key]
    value = state.get(key, [])
    coerced = _copy_list(value)
    state[key] = coerced
    return coerced


def _ensure_dict(state: MutableMapping[str, Any], key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    value = state.get(key)
    if isinstance(value, dict):
        return value
    coerced = deepcopy(default) if default is not None else {}
    state[key] = coerced
    return coerced


def _default_recovery_prompt_state() -> dict[str, Any]:
    return {
        "visible": False,
        "title": "",
        "message": "",
        "context_ref": {},
        "primary_action_label": "Resume",
        "secondary_action_label": "Cancel",
        "requested_action": "",
        "acknowledged": False,
        "created_at": "",
        "updated_at": "",
    }


def ensure_navigation_continuity_state(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Initialize the dedicated continuity namespaces without touching route ownership."""
    stack = _ensure_list(state, NAV_RESTORATION_STACK_KEY)
    if len(stack) > NAV_RESTORATION_STACK_MAX_DEPTH:
        del stack[: len(stack) - NAV_RESTORATION_STACK_MAX_DEPTH]

    shortlist = _ensure_list(state, OPERATOR_SHORTLIST_KEY)
    if len(shortlist) > OPERATOR_SHORTLIST_MAX_ITEMS:
        del shortlist[: len(shortlist) - OPERATOR_SHORTLIST_MAX_ITEMS]
        _reindex_shortlist(shortlist)

    _ensure_dict(state, ACTIVE_BREADCRUMB_CONTEXT_KEY)
    _ensure_list(state, INTERRUPTION_NOTICE_QUEUE_KEY)
    prompt = _ensure_dict(state, RECOVERY_PROMPT_STATE_KEY, _default_recovery_prompt_state())
    for key, value in _default_recovery_prompt_state().items():
        prompt.setdefault(key, value)
    return state


def _normalize_restoration_snapshot(snapshot: Any, *, strict: bool = False) -> dict[str, Any] | None:
    if not isinstance(snapshot, Mapping):
        if strict:
            raise TypeError("Restoration snapshot must be a mapping.")
        return None

    normalized = {
        "id": _as_str(snapshot.get("id"), str(uuid4())),
        "timestamp": _as_str(snapshot.get("timestamp"), _now_iso()),
        "type": _as_str(snapshot.get("type"), "BROWSE").upper(),
        "engine": _as_str(snapshot.get("engine"), "MAIN").upper(),
        "route": _as_str(snapshot.get("route"), ""),
        "subview": _as_str(snapshot.get("subview"), ""),
        "player_context": _copy_dict(snapshot.get("player_context")),
        "game_context": _copy_dict(snapshot.get("game_context")),
        "escalation_tier": _as_str(snapshot.get("escalation_tier"), ""),
        "filters_ref": _copy_dict(snapshot.get("filters_ref")),
        "sidebar_context_ref": _copy_dict(snapshot.get("sidebar_context_ref")),
        "restore_priority": _as_int(snapshot.get("restore_priority"), 0),
    }
    known_keys = set(normalized)
    extras = {key: deepcopy(value) for key, value in snapshot.items() if key not in known_keys}
    if extras:
        normalized["metadata"] = extras
    return normalized


def validate_restoration_snapshot(snapshot: Any) -> bool:
    return _normalize_restoration_snapshot(snapshot) is not None


def get_restoration_stack_view(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    stack = state.get(NAV_RESTORATION_STACK_KEY, [])
    if not isinstance(stack, list):
        return []
    return [deepcopy(entry) for entry in stack if isinstance(entry, dict)]


def push_restoration_snapshot(state: MutableMapping[str, Any], snapshot: Any) -> dict[str, Any]:
    ensure_navigation_continuity_state(state)
    normalized = _normalize_restoration_snapshot(snapshot, strict=True)
    stack = _ensure_list(state, NAV_RESTORATION_STACK_KEY)
    stack.append(normalized)
    if len(stack) > NAV_RESTORATION_STACK_MAX_DEPTH:
        del stack[: len(stack) - NAV_RESTORATION_STACK_MAX_DEPTH]
    return deepcopy(normalized)


def pop_restoration_snapshot(state: MutableMapping[str, Any]) -> dict[str, Any] | None:
    stack = _ensure_list(state, NAV_RESTORATION_STACK_KEY)
    if not stack:
        return None
    entry = stack.pop()
    return deepcopy(entry) if isinstance(entry, dict) else None


def peek_restoration_snapshot(state: Mapping[str, Any]) -> dict[str, Any] | None:
    stack = state.get(NAV_RESTORATION_STACK_KEY, [])
    if not isinstance(stack, list) or not stack:
        return None
    entry = stack[-1]
    return deepcopy(entry) if isinstance(entry, dict) else None


def clear_restoration_stack(state: MutableMapping[str, Any]) -> None:
    state[NAV_RESTORATION_STACK_KEY] = []


def _shortlist_identity(entry: Mapping[str, Any]) -> str:
    player_id = entry.get("player_id") or entry.get("active_player_id") or entry.get("target_id")
    game_id = entry.get("game_id") or entry.get("active_game_pk") or entry.get("game_pk")
    player_name = _as_str(
        entry.get("player_name") or entry.get("active_player_name") or entry.get("name"),
        "",
    ).strip().lower()
    if player_id not in (None, ""):
        return f"{player_id}:{game_id or 'no_game'}"
    return f"{player_name or 'unknown'}:{game_id or 'no_game'}"


def _normalize_shortlist_item(entry: Any, *, existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(entry, Mapping):
        raise TypeError("Shortlist item must be a mapping.")

    now = _now_iso()
    base = dict(existing or {})
    normalized = {
        "shortlist_id": _as_str(entry.get("shortlist_id"), _shortlist_identity(entry)),
        "player_id": entry.get("player_id") or entry.get("active_player_id") or entry.get("target_id"),
        "player_name": _as_str(entry.get("player_name") or entry.get("active_player_name") or entry.get("name"), ""),
        "game_id": entry.get("game_id") or entry.get("active_game_pk") or entry.get("game_pk"),
        "game_display": _as_str(entry.get("game_display"), ""),
        "engine": _as_str(entry.get("engine") or entry.get("origin_engine") or entry.get("origin_route"), "").upper(),
        "status": _as_str(entry.get("status"), base.get("status", "PARKED")).upper(),
        "priority": _as_int(entry.get("priority"), _as_int(base.get("priority"), 0)),
        "last_reviewed": _as_str(entry.get("last_reviewed"), _as_str(base.get("last_reviewed"), "")),
        "review_count": _as_int(entry.get("review_count"), _as_int(base.get("review_count"), 0)),
        "escalation_seen": _as_bool(entry.get("escalation_seen"), _as_bool(base.get("escalation_seen"), False)),
        "data_updated_since_review": _as_bool(
            entry.get("data_updated_since_review"),
            _as_bool(base.get("data_updated_since_review"), False),
        ),
        "bookmarked": _as_bool(entry.get("bookmarked"), _as_bool(base.get("bookmarked"), False)),
        "notes": _as_str(entry.get("notes"), _as_str(base.get("notes"), ""))[:280],
        "metadata": _copy_dict(entry.get("metadata")) or _copy_dict(base.get("metadata")),
        "created_at": _as_str(entry.get("created_at"), _as_str(base.get("created_at"), now)),
        "updated_at": now,
    }
    extra_keys = {
        key: deepcopy(value)
        for key, value in entry.items()
        if key
        not in {
            "shortlist_id",
            "player_id",
            "active_player_id",
            "target_id",
            "player_name",
            "active_player_name",
            "name",
            "game_id",
            "active_game_pk",
            "game_pk",
            "game_display",
            "engine",
            "origin_engine",
            "origin_route",
            "status",
            "priority",
            "last_reviewed",
            "review_count",
            "escalation_seen",
            "data_updated_since_review",
            "bookmarked",
            "notes",
            "metadata",
            "created_at",
            "updated_at",
        }
    }
    if extra_keys:
        normalized["metadata"].update(extra_keys)
    return normalized


def _reindex_shortlist(items: list[dict[str, Any]]) -> None:
    for idx, item in enumerate(items):
        item["priority"] = idx


def get_operator_shortlist_view(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    shortlist = state.get(OPERATOR_SHORTLIST_KEY, [])
    if not isinstance(shortlist, list):
        return []
    return [deepcopy(item) for item in shortlist if isinstance(item, dict)]


def add_operator_shortlist_item(state: MutableMapping[str, Any], entry: Any) -> dict[str, Any]:
    ensure_navigation_continuity_state(state)
    normalized = _normalize_shortlist_item(entry)
    shortlist = _ensure_list(state, OPERATOR_SHORTLIST_KEY)
    shortlist_id = normalized["shortlist_id"]

    for idx, existing in enumerate(shortlist):
        if isinstance(existing, dict) and existing.get("shortlist_id") == shortlist_id:
            merged = _normalize_shortlist_item(normalized, existing=existing)
            shortlist[idx] = merged
            _reindex_shortlist(shortlist)
            return deepcopy(merged)

    shortlist.append(normalized)
    if len(shortlist) > OPERATOR_SHORTLIST_MAX_ITEMS:
        del shortlist[: len(shortlist) - OPERATOR_SHORTLIST_MAX_ITEMS]
    _reindex_shortlist(shortlist)
    return deepcopy(shortlist[-1])


def remove_operator_shortlist_item(state: MutableMapping[str, Any], shortlist_id: str) -> bool:
    shortlist = _ensure_list(state, OPERATOR_SHORTLIST_KEY)
    kept = [item for item in shortlist if not (isinstance(item, dict) and item.get("shortlist_id") == shortlist_id)]
    if len(kept) == len(shortlist):
        return False
    state[OPERATOR_SHORTLIST_KEY] = kept
    _reindex_shortlist(kept)
    return True


def toggle_operator_shortlist_item(state: MutableMapping[str, Any], entry: Any) -> str:
    normalized = _normalize_shortlist_item(entry)
    shortlist_id = normalized["shortlist_id"]
    shortlist = _ensure_list(state, OPERATOR_SHORTLIST_KEY)
    for existing in shortlist:
        if isinstance(existing, dict) and existing.get("shortlist_id") == shortlist_id:
            remove_operator_shortlist_item(state, shortlist_id)
            return "removed"
    add_operator_shortlist_item(state, normalized)
    return "added"


def reorder_operator_shortlist_item(
    state: MutableMapping[str, Any],
    shortlist_id: str,
    new_index: int,
) -> bool:
    shortlist = _ensure_list(state, OPERATOR_SHORTLIST_KEY)
    current_index = next(
        (idx for idx, item in enumerate(shortlist) if isinstance(item, dict) and item.get("shortlist_id") == shortlist_id),
        None,
    )
    if current_index is None:
        return False

    item = shortlist.pop(current_index)
    target_index = max(0, min(int(new_index), len(shortlist)))
    shortlist.insert(target_index, item)
    _reindex_shortlist(shortlist)
    return True


def set_shortlist_data_updated_flag(
    state: MutableMapping[str, Any],
    shortlist_id: str,
    value: bool = True,
) -> bool:
    shortlist = _ensure_list(state, OPERATOR_SHORTLIST_KEY)
    for item in shortlist:
        if isinstance(item, dict) and item.get("shortlist_id") == shortlist_id:
            item["data_updated_since_review"] = bool(value)
            item["updated_at"] = _now_iso()
            return True
    return False


def build_breadcrumb_context(
    state: Mapping[str, Any],
    *,
    shell_ctx: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    shell_ctx = shell_ctx or {}
    investigation = state.get("investigation_state", {})
    active_route = _as_str(state.get("active_route"), "MAIN").upper()
    active_workspace = _as_str(state.get("active_workspace"), active_route).upper()
    active_route = active_route or "MAIN"
    active_workspace = active_workspace or active_route
    active_player = investigation.get("active_player", {}) if isinstance(investigation, Mapping) else {}
    active_game = investigation.get("active_game", {}) if isinstance(investigation, Mapping) else {}

    game_label = _as_str(
        active_game.get("game_label")
        or active_game.get("game_display")
        or shell_ctx.get("game_display")
        or active_game.get("away_team")
        or active_game.get("game_id"),
        "",
    )
    player_label = _as_str(
        active_player.get("active_player_name")
        or shell_ctx.get("active_player_name")
        or active_player.get("player_name")
        or active_player.get("name"),
        "",
    )
    action_label = _as_str(
        investigation.get("current_route")
        or active_route,
        active_route,
    )
    level_label = active_workspace
    visible_stages = [level_label]
    if game_label:
        visible_stages.append(game_label)
    if player_label:
        visible_stages.append(player_label)
    if action_label:
        visible_stages.append(action_label)
    visible_stages = visible_stages[:4]
    context = {
        "engine": active_workspace,
        "game": game_label,
        "player": player_label,
        "action": action_label,
        "visible_stages": visible_stages,
        "display": " › ".join(visible_stages),
        "updated_at": _now_iso(),
    }
    return context


def get_breadcrumb_view(state: MutableMapping[str, Any], *, shell_ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    context = build_breadcrumb_context(state, shell_ctx=shell_ctx)
    state[ACTIVE_BREADCRUMB_CONTEXT_KEY] = deepcopy(context)
    return context


def get_interruption_notice_view(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    notices = state.get(INTERRUPTION_NOTICE_QUEUE_KEY, [])
    if not isinstance(notices, list):
        return []
    return [deepcopy(item) for item in notices if isinstance(item, dict)]


def queue_interruption_notice(
    state: MutableMapping[str, Any],
    *,
    level: str,
    message: str,
    context_ref: Mapping[str, Any] | None = None,
    source: str = "",
) -> dict[str, Any]:
    ensure_navigation_continuity_state(state)
    notice = {
        "id": str(uuid4()),
        "level": _as_str(level, "ADVISORY").upper(),
        "message": _as_str(message, ""),
        "context_ref": _copy_dict(context_ref),
        "source": _as_str(source, ""),
        "created_at": _now_iso(),
    }
    notices = _ensure_list(state, INTERRUPTION_NOTICE_QUEUE_KEY)
    notices.append(notice)
    return deepcopy(notice)


def clear_interruption_notices(state: MutableMapping[str, Any]) -> None:
    state[INTERRUPTION_NOTICE_QUEUE_KEY] = []


def get_recovery_prompt_view(state: MutableMapping[str, Any]) -> dict[str, Any]:
    ensure_navigation_continuity_state(state)
    return deepcopy(_ensure_dict(state, RECOVERY_PROMPT_STATE_KEY, _default_recovery_prompt_state()))


def set_recovery_prompt(
    state: MutableMapping[str, Any],
    *,
    title: str,
    message: str,
    context_ref: Mapping[str, Any] | None = None,
    primary_action_label: str = "Resume",
    secondary_action_label: str = "Cancel",
) -> dict[str, Any]:
    ensure_navigation_continuity_state(state)
    prompt = _ensure_dict(state, RECOVERY_PROMPT_STATE_KEY, _default_recovery_prompt_state())
    now = _now_iso()
    prompt.update(
        {
            "visible": True,
            "title": _as_str(title, ""),
            "message": _as_str(message, ""),
            "context_ref": _copy_dict(context_ref),
            "primary_action_label": _as_str(primary_action_label, "Resume"),
            "secondary_action_label": _as_str(secondary_action_label, "Cancel"),
            "requested_action": "",
            "acknowledged": False,
            "created_at": prompt.get("created_at") or now,
            "updated_at": now,
        }
    )
    return deepcopy(prompt)


def request_recovery_prompt_action(state: MutableMapping[str, Any], action: str) -> dict[str, Any]:
    prompt = _ensure_dict(state, RECOVERY_PROMPT_STATE_KEY, _default_recovery_prompt_state())
    prompt["requested_action"] = _as_str(action, "").lower()
    prompt["acknowledged"] = True
    prompt["updated_at"] = _now_iso()
    return deepcopy(prompt)


def clear_recovery_prompt(state: MutableMapping[str, Any]) -> dict[str, Any]:
    prompt = _ensure_dict(state, RECOVERY_PROMPT_STATE_KEY, _default_recovery_prompt_state())
    cleared = _default_recovery_prompt_state()
    cleared["updated_at"] = _now_iso()
    state[RECOVERY_PROMPT_STATE_KEY] = cleared
    return deepcopy(cleared)
