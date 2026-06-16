"""
Supabase read/write layer for pipeline results and beta invites.

pipeline_runs  — one row per date, stores full JSON payload
beta_invites   — invite codes you generate manually
beta_users     — users who have redeemed a code
"""

import os
from typing import Optional

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
