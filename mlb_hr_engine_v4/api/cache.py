"""
Supabase read/write layer for pipeline results and beta invites.

pipeline_runs  — one row per date, stores full JSON payload
beta_invites   — invite codes you generate manually
beta_users     — users who have redeemed a code
tickets        — one row per operator-submitted FD parlay
legs           — one row per player per ticket (frozen engine snapshot)
"""

import os
from datetime import date as _date, datetime as _dt, timezone as _timezone
from typing import Optional
from zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")


def today_et() -> _date:
    """Current calendar date in Eastern Time. Anchors all default 'which day'
    slate-date resolution — server/runner clocks are UTC, where the date rolls
    over at 8pm ET and would otherwise point at tomorrow's slate."""
    return _dt.now(_ET).date()


_supa = None


def _client():
    global _supa
    if _supa is None:
        from supabase import create_client
        _supa = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _supa


# ── Picks cache ───────────────────────────────────────────────────────────────

def get_picks(date_str: str) -> Optional[dict]:
    """Return cached pipeline payload for date_str, or None."""
    result = (
        _client()
        .table("pipeline_runs")
        .select("payload")
        .eq("date", date_str)
        .execute()
    )
    return result.data[0]["payload"] if result.data else None


def get_latest_picks() -> Optional[dict]:
    """Return cached pipeline payload for the most-recent stored date, or None."""
    result = (
        _client()
        .table("pipeline_runs")
        .select("payload")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0]["payload"] if result.data else None


def store_picks(date_str: str, payload: dict) -> None:
    """Upsert pipeline payload for date_str."""
    _client().table("pipeline_runs").upsert(
        {"date": date_str, "payload": payload},
        on_conflict="date",
    ).execute()


def insert_picks(
    date_str: str,
    picks: list,
    source_tab: str = "cron",
    engine_version: str = "v4",
) -> int:
    """Upsert qualified picks into the picks table. Returns count of rows submitted."""
    if not picks:
        return 0
    rows = []
    for p in picks:
        model_prob  = float(p.get("model_prob") or 0)
        market_prob = float(p.get("market_no_vig_prob") or 0)
        rows.append({
            "date":             date_str,
            "player_id":        p.get("player_id"),
            "player_name":      p.get("player_name"),
            "team":             p.get("team"),
            "opponent":         p.get("opponent"),
            "pitcher":          p.get("pitcher_name"),
            "lineup_spot":      p.get("lineup_spot"),
            "model_prob_pct":   round(model_prob  * 100, 3),
            "market_prob_pct":  round(market_prob * 100, 3),
            "ev_pct":           p.get("ev_pct"),
            "edge_pct":         p.get("edge_pct"),
            "american_odds":    p.get("best_american"),
            "bet_dollars":      p.get("bet_dollars"),
            "barrel_pct":       p.get("barrel_pct"),
            "xslg":             p.get("xslg"),
            "park_factor":      p.get("park_factor"),
            "pitcher_factor":   p.get("pitcher_factor"),
            "confidence_tier":  p.get("confidence_tier"),
            "qualified":        True,
            "filter_reasons":   p.get("filter_reasons") or [],
            "source_tab":       source_tab,
            "engine_version":   engine_version,
        })
    _client().table("picks").upsert(
        rows, on_conflict="date,player_id,source_tab"
    ).execute()
    return len(rows)


def list_runs(limit: int = 30) -> list:
    """Return the most recent N pipeline run dates."""
    result = (
        _client()
        .table("pipeline_runs")
        .select("date, payload->stats")
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


# ── Beta invite / user management ─────────────────────────────────────────────

def redeem_invite(code: str, user_id: str) -> bool:
    """
    Mark invite code as used and add user to beta_users.
    Returns True on success, False if code is invalid or already used.
    """
    result = (
        _client()
        .table("beta_invites")
        .select("code")
        .eq("code", code.upper())
        .is_("used_by", "null")
        .execute()
    )
    if not result.data:
        return False

    _client().table("beta_invites").update(
        {"used_by": user_id, "used_at": "now()"}
    ).eq("code", code.upper()).execute()

    _client().table("beta_users").upsert(
        {"user_id": user_id}, on_conflict="user_id"
    ).execute()

    return True


# ── Ticket / Data Capture ─────────────────────────────────────────────────────

def _slate_date_from_generated_at(engine_generated_at: Optional[str]) -> str:
    """
    ET date of the slate the operator was viewing, derived from the slate
    payload's generated_at. Handles '...Z' and '+00:00' ISO forms; a naive
    timestamp is treated as UTC. Falls back to the current ET clock when
    absent/unparseable — an after-midnight capture of a stale board keeps
    the board's date, not the clock's.
    """
    if engine_generated_at:
        try:
            ts = _dt.fromisoformat(engine_generated_at.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=_timezone.utc)
            return ts.astimezone(_ET).date().isoformat()
        except ValueError:
            pass
    return _dt.now(_ET).date().isoformat()


def add_leg(
    ticket_id: Optional[str],
    board: str,
    player_name: str,
    model_prob: float,
    tier: str,
    model_tier_rank: int,
    engine_generated_at: Optional[str],
    user_id: Optional[str] = None,
    player_id: Optional[str] = None,
    team: Optional[str] = None,
    opponent: Optional[str] = None,
    pitcher: Optional[str] = None,
    market_odds_american: Optional[int] = None,
    market_prob: Optional[float] = None,
    signal_snapshot: Optional[dict] = None,
) -> dict:
    """
    Add one leg to a ticket.
    ticket_id None/empty → opens a new ticket (status='building') first.
    Raises ValueError("ticket not building") if the ticket exists but is not in 'building' status.
    Returns {ticket_id, leg_id}. WRITE-SEPARATE: touches only tickets/legs.
    """
    client = _client()

    if not ticket_id:
        slate_date = _slate_date_from_generated_at(engine_generated_at)
        ticket_row: dict = {
            "date":   slate_date,
            "board":  board,
            "status": "building",
        }
        if user_id:
            ticket_row["user_id"] = user_id
        res = client.table("tickets").insert(ticket_row).execute()
        ticket_id = res.data[0]["ticket_id"]
    else:
        t_res = client.table("tickets").select("date, status").eq("ticket_id", ticket_id).execute()
        if not t_res.data:
            raise ValueError(f"ticket {ticket_id} not found")
        t_data = t_res.data[0]
        if t_data.get("status") != "building":
            raise ValueError("ticket not building")
        slate_date = t_data["date"] or _dt.now(_ET).date().isoformat()

    leg_row: dict = {
        "ticket_id":            ticket_id,
        "player_name":          player_name,
        "player_id":            player_id,
        "team":                 team,
        "opponent":             opponent,
        "pitcher":              pitcher,
        "model_prob":           model_prob,
        "tier":                 tier,
        "model_tier_rank":      model_tier_rank,
        "engine_generated_at":  engine_generated_at or None,
        "market_odds_american": market_odds_american,
        "market_prob":          market_prob,
        "leg_date":             slate_date,
    }
    # Key included only when present so snapshot-less inserts keep working
    # even before migration 006 has run.
    if signal_snapshot is not None:
        leg_row["signal_snapshot"] = signal_snapshot
    leg_res = client.table("legs").insert(leg_row).execute()
    leg_id = leg_res.data[0]["leg_id"]

    return {"ticket_id": ticket_id, "leg_id": leg_id}


def ledger_legs(
    user_id: str,
    lane: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list:
    """
    SELECT-only ledger query (D5). Settled + void legs for one user's tickets
    on one lane, newest first. `board` lives on tickets, not legs — the inner
    join both scopes the rows and supplies the flattened `board` field.
    Case-insensitive board match ('main'/'MAIN' both stored historically).
    Read-only: no writes anywhere in this path.
    """
    q = (
        _client()
        .table("legs")
        .select(
            "leg_id, leg_date, player_name, model_prob, tier, hr_result, "
            "settlement_status, settled_at, signal_snapshot, "
            "tickets!inner(board, user_id)"
        )
        .eq("tickets.user_id", user_id)
        .ilike("tickets.board", lane)
        .eq("removed", False)
        .in_("settlement_status", ["settled", "void"])
        .order("leg_date", desc=True)
    )
    if date_from:
        q = q.gte("leg_date", date_from)
    if date_to:
        q = q.lte("leg_date", date_to)
    rows = q.execute().data or []
    for r in rows:
        ticket = r.pop("tickets", None) or {}
        r["board"] = ticket.get("board")
    return rows


def ledger_pending_count(
    user_id: str,
    lane: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> int:
    """Count of still-pending legs in the same ledger scope. Read-only."""
    q = (
        _client()
        .table("legs")
        .select("leg_id, tickets!inner(user_id)", count="exact")
        .eq("tickets.user_id", user_id)
        .ilike("tickets.board", lane)
        .eq("removed", False)
        .eq("settlement_status", "pending")
    )
    if date_from:
        q = q.gte("leg_date", date_from)
    if date_to:
        q = q.lte("leg_date", date_to)
    res = q.execute()
    return res.count if res.count is not None else 0


def complete_ticket(ticket_id: str, user_id: Optional[str] = None, stake: Optional[float] = None) -> dict:
    """
    Finalize ticket: fd_deployed=True, status='pending', completed_at=now(), num_legs=count.
    Counts only non-removed legs. Writes stake if provided. Returns {ticket_id, num_legs, fd_deployed}.
    """
    client = _client()

    if user_id:
        owns = (
            client.table("tickets")
            .select("ticket_id")
            .eq("ticket_id", ticket_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not owns.data:
            raise ValueError(f"ticket {ticket_id} not found for user")

    count_res = (
        client.table("legs")
        .select("leg_id", count="exact")
        .eq("ticket_id", ticket_id)
        .eq("removed", False)
        .execute()
    )
    num_legs = count_res.count if count_res.count is not None else 0

    update_payload = {
        "fd_deployed":  True,
        "status":       "pending",
        "completed_at": _dt.utcnow().isoformat() + "Z",
        "num_legs":     num_legs,
    }
    if stake is not None:
        update_payload["stake"] = stake

    client.table("tickets").update(update_payload).eq("ticket_id", ticket_id).execute()

    return {"ticket_id": ticket_id, "num_legs": num_legs, "fd_deployed": True}


def remove_leg(leg_id: str, user_id: Optional[str] = None) -> dict:
    """
    Soft-delete a leg: sets legs.removed = true.
    Ownership-checked via the leg's parent ticket. Never hard-deletes.
    Raises LookupError if leg not found. Raises PermissionError if user doesn't own the ticket.
    Returns {leg_id, removed: True}.
    """
    client = _client()

    leg_res = (
        client.table("legs")
        .select("leg_id, ticket_id")
        .eq("leg_id", leg_id)
        .execute()
    )
    if not leg_res.data:
        raise LookupError(f"leg {leg_id} not found")

    ticket_id = leg_res.data[0]["ticket_id"]

    if user_id:
        owns = (
            client.table("tickets")
            .select("ticket_id")
            .eq("ticket_id", ticket_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not owns.data:
            raise PermissionError(f"ticket {ticket_id} not found for user")

    client.table("legs").update({"removed": True}).eq("leg_id", leg_id).execute()
    return {"leg_id": leg_id, "removed": True}
