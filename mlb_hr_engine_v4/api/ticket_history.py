"""Read-only ticket history with date-batched MLB schedule context."""

from __future__ import annotations

import copy
import logging
from collections.abc import Callable

from api.settle_legs import _get as resolver_get


log = logging.getLogger("uvicorn.error")

_TICKET_SELECT = (
    "ticket_id,date,board,ticket_type,num_legs,status,fd_deployed,"
    "created_at,completed_at,settled_at,"
    "legs(leg_id,leg_date,player_name,player_id,team,opponent,pitcher,"
    "hr_result,settlement_status,removed)"
)


def schedule_for_date(date_str: str) -> list[dict]:
    """Fetch one date using the settlement resolver's retrying schedule client."""
    data = resolver_get(
        "/schedule",
        {"sportId": 1, "date": date_str, "hydrate": "team,linescore"},
    )
    games: list[dict] = []
    for entry in data.get("dates", []):
        if entry.get("date") != date_str:
            continue
        games.extend(entry.get("games", []))
    return games


def get_my_tickets(
    client,
    user_id: str,
    schedule_fetcher: Callable[[str], list[dict]] | None = None,
) -> list[dict]:
    """Select one user's tickets and attach game context without any writes."""
    schedule_fetcher = schedule_fetcher or schedule_for_date
    result = (
        client.table("tickets")
        .select(_TICKET_SELECT)
        .eq("user_id", user_id)
        .eq("legs.removed", False)
        .order("created_at", desc=True)
        .execute()
    )
    source_tickets = result.data or []
    context_dates: set[str] = set()

    for ticket in source_tickets:
        active_legs = [
            leg for leg in (ticket.get("legs") or []) if not leg.get("removed", False)
        ]
        for leg in active_legs:
            date_str = str(leg.get("leg_date") or ticket.get("date") or "")
            if not date_str:
                continue
            context_dates.add(date_str)

    schedules: dict[str, list[dict]] = {}
    for date_str in sorted(context_dates):
        try:
            schedules[date_str] = schedule_fetcher(date_str)
        except Exception as exc:
            log.warning("[my-tickets] schedule fetch failed for %s: %s", date_str, exc)

    return [_clean_ticket(ticket, schedules) for ticket in source_tickets]


def _clean_ticket(
    ticket: dict,
    schedules: dict[str, list[dict]],
) -> dict:
    clean = {
        key: copy.deepcopy(ticket.get(key))
        for key in (
            "ticket_id",
            "date",
            "board",
            "ticket_type",
            "num_legs",
            "status",
            "fd_deployed",
            "created_at",
            "completed_at",
            "settled_at",
        )
    }
    clean["legs"] = [
        _clean_leg(leg, ticket.get("date"), schedules)
        for leg in (ticket.get("legs") or [])
        if not leg.get("removed", False)
    ]
    return clean


def _clean_leg(
    leg: dict,
    ticket_date: str | None,
    schedules: dict[str, list[dict]],
) -> dict:
    date_str = str(leg.get("leg_date") or ticket_date or "")
    game = _match_game(
        schedules.get(date_str, []),
        leg.get("team"),
        leg.get("opponent"),
    )
    clean = {
        "leg_id": leg.get("leg_id"),
        "player_name": leg.get("player_name"),
        "player_id": leg.get("player_id"),
        "team": leg.get("team"),
        "opponent": leg.get("opponent"),
        "pitcher": leg.get("pitcher"),
        "hr_result": leg.get("hr_result"),
        "settlement_status": leg.get("settlement_status") or "pending",
        "game_status": _game_status(game) if game else None,
        "linescore": _linescore(game),
        # Live-state join key (Phase 1 program). None when the leg's team+date
        # doesn't resolve to exactly one game — e.g. a doubleheader where
        # opponent alone can't disambiguate. Callers must treat None as
        # "don't poll this leg" rather than guessing a game_pk.
        "game_pk": game.get("gamePk") if game else None,
    }
    return clean


def _match_game(games: list[dict], team: str | None, opponent: str | None) -> dict | None:
    team_abbr = _abbr(team)
    opponent_abbr = _abbr(opponent)
    if not team_abbr:
        return None

    candidates = [game for game in games if team_abbr in _game_teams(game)]
    if opponent_abbr:
        opponent_matches = [
            game for game in candidates if opponent_abbr in _game_teams(game)
        ]
        if opponent_matches:
            candidates = opponent_matches
    return candidates[0] if len(candidates) == 1 else None


def _abbr(value: str | None) -> str:
    return str(value or "").strip().upper()


def _game_teams(game: dict) -> set[str]:
    teams = game.get("teams", {})
    return {
        _abbr(teams.get(side, {}).get("team", {}).get("abbreviation"))
        for side in ("home", "away")
    } - {""}


def _game_status(game: dict) -> str:
    abstract = game.get("status", {}).get("abstractGameState", "")
    if abstract == "Final":
        return "Final"
    if abstract == "Live":
        return "In Progress"
    return "Scheduled"


def _linescore(game: dict | None) -> dict:
    game = game or {}
    teams = game.get("teams", {})
    raw = game.get("linescore", {}) or {}
    raw_totals = raw.get("teams", {})

    totals: dict[str, dict] = {}
    for side in ("away", "home"):
        total = raw_totals.get(side, {})
        totals[side] = {
            "team": teams.get(side, {}).get("team", {}).get("abbreviation"),
            "runs": total.get("runs"),
            "hits": total.get("hits"),
            "errors": total.get("errors"),
        }

    innings = []
    for inning in raw.get("innings", []):
        innings.append({
            "inning": inning.get("num"),
            "away": inning.get("away", {}).get("runs"),
            "home": inning.get("home", {}).get("runs"),
        })
    return {"innings": innings, "totals": totals}
