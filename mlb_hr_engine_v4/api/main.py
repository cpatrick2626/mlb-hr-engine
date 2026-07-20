"""
MLB HR Engine — FastAPI backend

Endpoints
---------
GET  /health                      — health check (no auth)
GET  /api/picks/today             — today's ranked picks (beta required)
GET  /api/picks/{date}            — picks for YYYY-MM-DD (beta required)
GET  /api/strategies?date=…       — parlays + strategy data (beta required)
GET  /api/runs                    — recent pipeline run history (beta required)
POST /api/pipeline/run            — trigger pipeline (X-Cron-Secret header)
POST /api/ops/settle              — settle pick_tracker.csv outcomes (X-Cron-Secret header)
POST /api/ops/clv-capture         — fetch closing odds + compute CLV (X-Cron-Secret header)
POST /api/invite/redeem           — redeem invite code (auth required)
POST /api/tickets/leg             — add leg to ticket; null ticket_id opens new ticket (JWT required — Phase 1)
POST /api/tickets/leg/remove      — soft-delete a leg (sets removed=true); ownership-checked (JWT required — Phase A)
POST /api/tickets/complete        — finalize ticket, set fd_deployed=true (JWT required — Phase 1)
POST /api/fd-event                — record a FanDuel handoff click (JWT required)
GET  /api/ledger?lane=main|jig    — settled/void legs + hit-rate buckets, per user per lane (JWT required — Phase S2/D5)
GET  /api/builds                  — list caller's named TCC builds (JWT required)
POST /api/builds                  — create/update caller's named TCC build (JWT required)
DELETE /api/builds/{build_id}     — delete caller's own TCC build (JWT required)

The pipeline is normally triggered by GitHub Actions cron (see api/cron.py).
The /api/pipeline/run endpoint is a manual fallback; it runs in a background
task so the HTTP response returns immediately, but note that Fly.io machines
with auto_stop=true may kill the machine before the pipeline completes.
For reliability, always prefer the GH Actions cron path.
"""

import os
import copy
import json
import logging
from datetime import date, datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from api.auth import require_auth, require_beta
from api.cache import _client as supabase_client, get_picks, get_latest_picks, store_picks, list_runs, redeem_invite, add_leg, complete_ticket, remove_leg, ledger_legs, ledger_pending_count, today_et
from clients.arsenal import get_pitcher_arsenal, arsenal_matchup_factor
from clients.batter_pitch_profile import (
    empty_batter_pitch_profile_display,
    empty_pitch_mix_verdict_display,
    get_batter_pitch_profile_display,
    pitch_mix_verdict_display,
)
from clients.pitch_mix import canonical_pitch_type, get_batter_vs_pitches, get_pitcher_pitch_stats
from config import FS_TIER_THRESHOLDS, JIG_TIER_THRESHOLDS
from roles import classify_role

log = logging.getLogger("uvicorn.error")

app = FastAPI(title="MLB HR Engine", version="4.0", docs_url="/docs")

# Display-only bridge between the existing /api/pitcher-detail arsenal payload
# and /api/batter-detail's B4 verdict. It is separate from every scoring cache.
_PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE: dict[int, list[dict]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your Vercel domain once it's known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CRON_SECRET = os.environ.get("CRON_SECRET", "")


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Picks ──────────────────────────────────────────────────────────────────────

@app.get("/api/picks/today")
async def picks_today(user=Depends(require_beta)):
    return _picks_or_404(today_et().strftime("%Y-%m-%d"))


@app.get("/api/picks/{date_str}")
async def picks_by_date(date_str: str, user=Depends(require_beta)):
    try:
        date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Use YYYY-MM-DD format.")
    return _picks_or_404(date_str)


@app.get("/api/strategies")
async def strategies(date_str: str = None, user=Depends(require_beta)):
    d = date_str or today_et().strftime("%Y-%m-%d")
    cached = get_picks(d)
    if not cached:
        raise HTTPException(status_code=404, detail=f"No data for {d}.")
    return {
        "date": d,
        "auto_parlays":    cached.get("auto_parlays", {}),
        "profile_parlays": cached.get("profile_parlays", {}),
    }


@app.get("/api/runs")
async def recent_runs(user=Depends(require_beta)):
    return {"runs": list_runs(30)}


# ── Pipeline trigger ───────────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
async def trigger_pipeline(request: Request, background_tasks: BackgroundTasks):
    """
    Trigger the daily pipeline. Requires X-Cron-Secret header.
    Returns immediately; pipeline runs in background.
    Prefer GitHub Actions cron over this endpoint for reliability.
    """
    secret = request.headers.get("X-Cron-Secret", "")
    if not CRON_SECRET or secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    target = today_et().strftime("%Y-%m-%d")
    background_tasks.add_task(_run_pipeline, target)
    return {"status": "queued", "date": target}


# ── Ops: settlement ───────────────────────────────────────────────────────────

@app.post("/api/ops/settle")
async def ops_settle(request: Request, background_tasks: BackgroundTasks):
    """
    Settle pick_tracker.csv outcomes for all past dates.
    Requires X-Cron-Secret header. Returns immediately; work runs in background.
    Called by GitHub Actions daily_settle.yml (overnight, after final scores available).
    """
    secret = request.headers.get("X-Cron-Secret", "")
    if not CRON_SECRET or secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    background_tasks.add_task(_run_settle)
    return {"status": "queued"}


async def _run_settle():
    import sys, os as _os
    try:
        _app = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
        if _app not in sys.path:
            sys.path.insert(0, _app)
        from tracking import pnl
        summary = pnl.settle_all_unsettled()
        total = sum(v for k, v in summary.items() if not k.startswith("_"))
        expired = summary.get("_expired", 0)
        log.info("[ops/settle] settled %d picks into results.csv; expired=%d; detail=%s", total, expired, summary)
    except BaseException as exc:
        log.error("[ops/settle] failed: %s", exc, exc_info=True)


# ── Ops: CLV capture ──────────────────────────────────────────────────────────

@app.post("/api/ops/clv-capture")
async def ops_clv_capture(request: Request, background_tasks: BackgroundTasks):
    """
    Fetch current HR odds and compute CLV for today's picks.
    Requires X-Cron-Secret header. Returns immediately; work runs in background.
    Called twice daily by GitHub Actions clv_capture.yml:
      - 12:30 ET (16:30 UTC) — captures closing lines before day games (~1pm ET FP)
      - 6:30 PM ET (22:30 UTC) — captures closing lines before night games (~7pm ET FP)
    """
    secret = request.headers.get("X-Cron-Secret", "")
    if not CRON_SECRET or secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    background_tasks.add_task(_run_clv_capture)
    return {"status": "queued"}


async def _run_clv_capture():
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
    try:
        from tracking.clv import fetch_and_compute_clv
        rows = fetch_and_compute_clv()
        computed = [r for r in rows if r.get("clv_pp") is not None]
        if computed:
            log.info("[ops/clv-capture] CLV computed for %d rows", len(computed))
        else:
            log.warning(
                "[ops/clv-capture] 0 CLV rows computed (no live odds or key missing); "
                "%d existing rows returned unchanged",
                len(rows),
            )
    except Exception as exc:
        log.error("[ops/clv-capture] failed: %s", exc, exc_info=True)


# ── Beta invite ────────────────────────────────────────────────────────────────

@app.post("/api/invite/redeem")
async def redeem(body: dict, user=Depends(require_auth)):
    code = (body.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="code is required")
    user_id = user.get("sub")
    if not redeem_invite(code, user_id):
        raise HTTPException(status_code=400, detail="Invalid or already-used invite code.")
    return {"status": "ok", "message": "Beta access granted!"}


# ── Ticket capture ─────────────────────────────────────────────────────────────
# Phase 2: user_id stamped on new ticket rows (nullable; NOT NULL + RLS deferred to Phase 3).

@app.post("/api/tickets/leg")
async def ticket_add_leg(body: dict, user=Depends(require_auth)):
    required = {"board", "name", "model_prob", "tier", "generated_at"}
    missing = required - body.keys()
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {sorted(missing)}")
    signal_snapshot = body.get("signal_snapshot")
    if signal_snapshot is not None:
        if not isinstance(signal_snapshot, dict):
            raise HTTPException(status_code=422, detail="signal_snapshot must be a JSON object")
        if len(json.dumps(signal_snapshot)) > 16384:
            raise HTTPException(status_code=422, detail="signal_snapshot too large (>16KB)")
    try:
        result = add_leg(
            ticket_id=body.get("ticket_id") or None,
            board=body["board"],
            player_name=body["name"],
            model_prob=float(body["model_prob"]),
            tier=body["tier"],
            model_tier_rank=(
                int(body["model_tier_rank"])
                if body.get("model_tier_rank") is not None
                else None
            ),
            engine_generated_at=body.get("generated_at"),
            user_id=user.get("sub"),
            player_id=body.get("player_id") or None,
            team=body.get("team") or None,
            opponent=body.get("opponent") or None,
            pitcher=body.get("pitcher") or None,
            market_odds_american=(
                int(body["market_odds_american"])
                if body.get("market_odds_american") is not None
                else None
            ),
            market_prob=(
                float(body["market_prob"])
                if body.get("market_prob") is not None
                else None
            ),
            signal_snapshot=signal_snapshot,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not building" in msg:
            raise HTTPException(status_code=409, detail="Ticket is not in building status")
        raise HTTPException(status_code=404, detail=msg)
    return {"status": "ok", **result}


@app.post("/api/tickets/complete")
async def ticket_complete(body: dict, user=Depends(require_auth)):
    ticket_id = body.get("ticket_id")
    if not ticket_id:
        raise HTTPException(status_code=400, detail="ticket_id is required")
    raw_stake = body.get("stake")
    stake = float(raw_stake) if raw_stake is not None else None
    result = complete_ticket(ticket_id, user_id=user.get("sub"), stake=stake)
    return {"status": "ok", **result}


# ── FanDuel handoff capture (Phase 1) ─────────────────────────────────────

@app.post("/api/fd-event")
async def record_fd_event(body: dict, user=Depends(require_auth)):
    """Record an FD handoff initiation; this is not proof of bet placement."""
    player_id = body.get("player_id")
    source_surface = body.get("source_surface")
    idempotency_key = body.get("idempotency_key")
    board = body.get("board")

    if player_id is None or isinstance(player_id, bool) or not str(player_id).strip():
        raise HTTPException(status_code=400, detail="player_id is required")
    if not isinstance(source_surface, str) or not source_surface.strip():
        raise HTTPException(status_code=400, detail="source_surface is required")
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="idempotency_key is required")
    if board is not None and (not isinstance(board, str) or not board.strip()):
        raise HTTPException(status_code=422, detail="board must be a non-empty string or null")

    slate_date = body.get("slate_date")
    if slate_date is None:
        event_date = today_et()
    else:
        try:
            event_date = date.fromisoformat(slate_date)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="slate_date must be YYYY-MM-DD")

    row = {
        "user_id": user.get("sub"),
        "player_id": str(player_id).strip(),
        "slate_date": event_date.isoformat(),
        "event_type": "handoff_initiated",
        "source_surface": source_surface.strip(),
        "board": board.strip() if board is not None else None,
        "idempotency_key": idempotency_key.strip(),
    }
    result = (
        supabase_client()
        .table("fd_events")
        .upsert(
            row,
            on_conflict="user_id,idempotency_key",
            ignore_duplicates=True,
        )
        .execute()
    )
    created = bool(result.data)
    return {
        "status": "ok",
        "event": "handoff_initiated",
        "created": created,
        "duplicate": not created,
        "slate_date": event_date.isoformat(),
    }


# ── Ledger (Phase S2 / D5 — read-only) ────────────────────────────────────────

_LEDGER_SNAPSHOT_DIMS = ("aei_verdict", "alignment", "rank_signal_used")


def _ledger_buckets(settled_rows: list) -> dict:
    """
    Hit-rate rollups over settled-only legs (voids already excluded by caller).
    v1 bucket set: aei_verdict, alignment, rank_signal_used (from signal_snapshot)
    + tier (from the legs.tier column). Legs without a snapshot land in an
    explicit 'no_snapshot' bucket under each snapshot dimension — never dropped.
    """
    def bump(dim: dict, key: str, hit: int) -> None:
        b = dim.setdefault(key, {"n": 0, "hits": 0})
        b["n"] += 1
        b["hits"] += hit

    dims: dict = {d: {} for d in _LEDGER_SNAPSHOT_DIMS}
    dims["tier"] = {}

    for r in settled_rows:
        hit = 1 if r.get("hr_result") == 1 else 0
        snap = r.get("signal_snapshot")
        if snap is None:
            for d in _LEDGER_SNAPSHOT_DIMS:
                bump(dims[d], "no_snapshot", hit)
        else:
            aei = snap.get("aei") or {}
            verdict = aei.get("verdict")
            bump(dims["aei_verdict"], str(verdict) if verdict is not None else "null", hit)
            alignment = aei.get("alignment")
            bump(dims["alignment"], "null" if alignment is None else str(bool(alignment)).lower(), hit)
            rank_signal = snap.get("rank_signal_used")
            bump(dims["rank_signal_used"], str(rank_signal) if rank_signal is not None else "null", hit)
        tier = r.get("tier")
        bump(dims["tier"], str(tier) if tier is not None else "null", hit)

    for dim in dims.values():
        for b in dim.values():
            b["hit_rate"] = round(b["hits"] / b["n"], 4) if b["n"] else None
    return dims


@app.get("/api/ledger")
async def ledger(
    lane: str = Query(None),
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
    user=Depends(require_auth),
):
    """
    Settled/void legs + per-lane hit-rate buckets for the authenticated user.
    lane is REQUIRED (main|jig) — no merged view; per-lane grading is doctrine.
    user_id comes from the JWT sub, never from the query string.
    Voids appear in `legs` and meta.total_void but are excluded from bucket rates.
    Reports only, never tunes: figures cover LOGGED picks; the fd_deployed
    distinction is future work (D6).
    """
    if lane not in ("main", "jig"):
        raise HTTPException(
            status_code=422,
            detail="lane is required and must be 'main' or 'jig' (no merged view — per-lane doctrine)",
        )
    for label, val in (("from", from_date), ("to", to_date)):
        if val is not None:
            try:
                date.fromisoformat(val)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"'{label}' must be YYYY-MM-DD")

    user_id = user.get("sub")
    legs = ledger_legs(user_id, lane, date_from=from_date, date_to=to_date)

    settled = [r for r in legs if r.get("settlement_status") == "settled" and r.get("hr_result") is not None]
    total_void = sum(1 for r in legs if r.get("settlement_status") == "void")

    return {
        "legs": legs,
        "buckets": _ledger_buckets(settled),
        "meta": {
            "lane": lane,
            "total_settled": len(settled),
            "total_void": total_void,
            "total_pending": ledger_pending_count(user_id, lane, date_from=from_date, date_to=to_date),
            "small_sample": len(settled) < 200,
            "note": "logged picks; fd_deployed distinction is future work (D6).",
        },
    }


@app.post("/api/tickets/leg/remove")
async def ticket_remove_leg(body: dict, user=Depends(require_auth)):
    leg_id = body.get("leg_id")
    if not leg_id:
        raise HTTPException(status_code=400, detail="leg_id is required")
    try:
        result = remove_leg(leg_id, user_id=user.get("sub"))
    except LookupError:
        raise HTTPException(status_code=404, detail="Leg not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized for this leg")
    return {"status": "ok", **result}


# ── TCC build persistence ──────────────────────────────────────────────────────

_TCC_BUILD_COLUMNS = (
    "build_id,name,main_filters,jig_filters,schema_version,created_at,updated_at"
)


@app.get("/api/builds")
async def list_tcc_builds(user=Depends(require_auth)):
    """List only the authenticated caller's saved TCC builds."""
    user_id = user.get("sub")
    result = (
        supabase_client()
        .table("tcc_builds")
        .select(_TCC_BUILD_COLUMNS)
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return {"builds": result.data or []}


@app.post("/api/builds")
async def save_tcc_build(body: dict, user=Depends(require_auth)):
    """Upsert one named build; ownership and schema version are server-stamped."""
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        raise HTTPException(status_code=400, detail="name is required")

    missing = {key for key in ("main_filters", "jig_filters") if key not in body}
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {sorted(missing)}")
    if not isinstance(body["main_filters"], dict):
        raise HTTPException(status_code=422, detail="main_filters must be a JSON object")
    if not isinstance(body["jig_filters"], dict):
        raise HTTPException(status_code=422, detail="jig_filters must be a JSON object")

    row = {
        "user_id": user.get("sub"),
        "name": name.strip(),
        "main_filters": body["main_filters"],
        "jig_filters": body["jig_filters"],
        "schema_version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = (
        supabase_client()
        .table("tcc_builds")
        .upsert(row, on_conflict="user_id,name")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Build save returned no row")
    return {"status": "ok", "build": result.data[0]}


@app.delete("/api/builds/{build_id}")
async def delete_tcc_build(build_id: str, user=Depends(require_auth)):
    """Delete a build only after confirming it belongs to the JWT subject."""
    user_id = user.get("sub")
    existing = (
        supabase_client()
        .table("tcc_builds")
        .select("build_id,user_id")
        .eq("build_id", build_id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Build not found")
    if existing.data[0].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this build")

    (
        supabase_client()
        .table("tcc_builds")
        .delete()
        .eq("build_id", build_id)
        .eq("user_id", user_id)
        .execute()
    )
    return {"status": "ok", "build_id": build_id, "deleted": True}


def _pct(val):
    """Strip % suffix and return float, or None if missing."""
    if val is None:
        return None
    try:
        return round(float(str(val).replace("%", "").strip()), 1)
    except (ValueError, TypeError):
        return None


def _flt(val):
    """Cast to float rounded to 1 decimal, or None if missing. Use for mph/degree-style physical stats."""
    if val is None:
        return None
    try:
        return round(float(str(val).replace("%", "").strip()), 1)
    except (ValueError, TypeError):
        return None


def _rate(val):
    """Cast to float rounded to 3 decimals, or None if missing. Use for decimal-rate stats (avg, slg, obp, etc.)."""
    if val is None:
        return None
    try:
        return round(float(str(val).replace("%", "").strip()), 3)
    except (ValueError, TypeError):
        return None


def _true_matchup_score(row: dict) -> int | None:
    """Composite display score (0–100). Serialization-only — never fed back into scoring/ordering."""
    mp = row.get("model_prob")
    if mp is None:
        return None

    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    hr_prob_n = _clamp(float(mp) / 0.25, 0.0, 1.0)

    raw_edge = row.get("arsenal_edge_score")
    edge_n = _clamp(float(raw_edge) / 10.0, 0.0, 1.0) if raw_edge is not None else 0.0

    raw_conf = row.get("arsenal_edge_confidence")
    conf = _clamp(float(raw_conf), 0.0, 1.0) if raw_conf is not None else 0.0

    hr9 = row.get("pitcher_hr9")
    barrel = row.get("pitcher_barrel_allowed")
    components = []
    if hr9 is not None:
        components.append(_clamp(float(hr9) / 2.0, 0.0, 1.0))
    if barrel is not None:
        components.append(_clamp(float(barrel) / 0.12, 0.0, 1.0))
    vuln_n = sum(components) / len(components) if components else 0.5

    score = 100.0 * (0.40 * hr_prob_n + 0.30 * edge_n + 0.20 * conf + 0.10 * vuln_n)
    return int(round(_clamp(score, 0.0, 100.0)))


def _jig_score(player: dict, arsenal_data: dict | None = None) -> float:
    """
    JIG tactical exploit score.
    Inputs: raw Statcast contact/power profile + optional
    arsenal/pitch-mix signals.
    No model_prob. No HVY modifier (display-only per doctrine).
    Returns 0-100+ index (uncapped by design).
    """
    def _f(key):
        v = player.get(key, 0)
        if isinstance(v, str):
            v = v.replace("%", "").strip()
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    def _n(x: float, center: float, sigma: float) -> float:
        """Linear ramp: 0 at (center-sigma), 0.5 at center, 1 at (center+sigma), clamped [0,1]."""
        return max(0.0, min(1.0, (x - center) / sigma + 0.5))

    # --- Contact/power base — operator weights, _n-normalized, RAW percents ---
    base_score = (
        _n(_f("xslg"),          0.40, 0.15) * 0.25
        + _n(_f("barrel_pct"),  5.0,  6.0)  * 0.20
        + _n(_f("xiso"),        0.15, 0.12) * 0.15
        + _n(_f("pull_air_pct"),12.0, 8.0)  * 0.15
        + _n(_f("hard_hit"),    35.0, 12.0) * 0.15
        + _n(_f("sweet_spot_pct"),28.0, 8.0)* 0.10
    )

    # --- PA stabilization + HR/PA term (Candidate D) ---
    pa = _f("season_pa")
    stab = pa / (pa + 100.0) if pa > 0 else 0.0
    hrpa = (_f("season_hr") / pa) if pa > 0 else 0.0
    hr_term = min(hrpa / 0.08, 1.0) * 0.10

    # --- Tactical signals (0.22 weight) ---
    arsenal_signal  = 0.0
    pitch_dmg_signal = 0.0
    pitch_mix_signal = 0.0

    pitcher_id  = player.get("pitcher_id")
    batter_id   = player.get("batter_id") or player.get("player_id")
    batter_side = player.get("batter_side", "")

    if arsenal_data and pitcher_id:
        try:
            # Arsenal vulnerability [0.82, 1.20] → normalize to [0, 1]
            raw = arsenal_matchup_factor(pitcher_id, arsenal_data, batter_side)
            arsenal_signal = ((raw - 0.82) / (1.20 - 0.82)) * 0.12
        except Exception as e:
            log.warning("JIG arsenal_signal fallback | player=%s pitcher=%s err=%s",
                player.get("player_name", "?"), pitcher_id, e)
            arsenal_signal = 0.0
    else:
        if not pitcher_id:
            log.debug("JIG tactical signals skipped | player=%s no pitcher_id",
                player.get("player_name", "?"))

    if pitcher_id and batter_id:
        try:
            # Batter damage vs pitch types: weighted avg hr_rate
            # across pitcher's pitch mix, batter-side filtered
            pitcher_pitches = get_pitcher_pitch_stats(pitcher_id, batter_side)
            batter_vs       = get_batter_vs_pitches(batter_id, player.get("pitcher_hand", ""))
            dmg = 0.0
            total_pct = 0.0
            for pitch_type, pdata in pitcher_pitches.items():
                usage = pdata.get("pitch_pct", 0)
                bvp   = batter_vs.get(pitch_type, {})
                hr_r  = bvp.get("hr_rate") or 0
                dmg  += usage * hr_r
                total_pct += usage
            if total_pct > 0:
                dmg /= total_pct
            # Normalize: league avg hr_rate ~0.03, cap at 0.12
            pitch_dmg_signal = min(dmg / 0.12, 1.0) * 0.06
        except Exception as e:
            log.warning("JIG pitch_dmg_signal fallback | player=%s pitcher=%s err=%s",
                player.get("player_name", "?"), pitcher_id, e)
            pitch_dmg_signal = 0.0

        try:
            # Pitch-mix weakness: pitcher's worst rv_per100 pitches
            # weighted by usage vs this batter side
            pitcher_pitches = get_pitcher_pitch_stats(pitcher_id, batter_side)
            weakness = 0.0
            total_pct = 0.0
            for pdata in pitcher_pitches.values():
                usage  = pdata.get("pitch_pct", 0)
                rv     = pdata.get("rv_per100", 0) or 0
                # Higher rv_per100 = worse for pitcher = exploit signal
                weakness += usage * max(rv, 0)
                total_pct += usage
            if total_pct > 0:
                weakness /= total_pct
            # Normalize: cap at rv_per100 of 3.0
            pitch_mix_signal = min(weakness / 3.0, 1.0) * 0.04
        except Exception as e:
            log.warning("JIG pitch_mix_signal fallback | player=%s pitcher=%s err=%s",
                player.get("player_name", "?"), pitcher_id, e)
            pitch_mix_signal = 0.0

    tactical = arsenal_signal + pitch_dmg_signal + pitch_mix_signal
    return round(((base_score + hr_term) * stab + tactical) * 100, 2)


# ── Full Slate ─────────────────────────────────────────────────────────────────

def _jig_tier(jig_score: float) -> str:
    """
    JIG-native display tier from jigScore (0-100 scale) via
    config.JIG_TIER_THRESHOLDS. Display-only — never a sort or scoring input.
    Separate from the MAIN `tier` field (model_prob based).
    """
    for t in ("APEX", "ELITE", "EDGE", "SIGNAL", "WATCH"):
        if jig_score >= JIG_TIER_THRESHOLDS[t]:
            return t
    return "COLD"


def _build_slate_payload(data: dict) -> dict:
    """
    Map pipeline data → React frontend shape.
    Returns leaderboard_rows, leaderboard_rows_jig, slate_games, generated_at, date.
    Does NOT include from_cache / cache_age_minutes — caller adds those.
    """
    import datetime as _dt
    players = data.get("all_players", [])

    # DH disambiguation (site A): the same away-home slug can cover two games
    # in a doubleheader. Pre-scan game_pks per base slug; append game_pk only
    # on collision so non-DH slugs stay byte-identical to the legacy form.
    _slug_pks = {}
    for p in players:
        _h = (p.get("home_team") or p.get("team") or "home").upper()
        _o = (p.get("team") or "").upper()
        _pp = (p.get("opponent") or "").upper()
        _a = (_o if _o != _h else _pp) or "away"
        _slug_pks.setdefault(
            f"{_a}-{_h}".lower().replace(" ", "-"), set()
        ).add(p.get("game_pk"))

    def _game_slug(base_slug, game_pk):
        if len(_slug_pks.get(base_slug, ())) > 1 and game_pk:
            return f"{base_slug}-{game_pk}"
        return base_slug

    leaderboard_rows = []
    for p in players:
        model_prob = float(p.get("model_prob") or 0)
        season_pa = int(p.get("season_pa") or 0)
        season_hr = int(p.get("season_hr") or 0)
        hrpa = round(season_hr / season_pa, 3) if season_pa > 0 else None

        tier = next(
            (t for t, thresh in FS_TIER_THRESHOLDS.items() if model_prob >= thresh),
            "COLD",
        )

        mq_map = {"ELITE": "ELITE", "STRONG": "STRONG", "AVG": "AVG",
                  "WEAK": "WEAK"}
        quality = mq_map.get(p.get("matchup_quality", "AVG"), "AVG")

        fd_raw = p.get("fanduel_american")
        odds = (f"+{fd_raw}" if fd_raw and fd_raw > 0
                else str(fd_raw) if fd_raw else None)

        home = (p.get("home_team") or p.get("team") or "home").upper()
        _own = (p.get("team") or "").upper()
        _opp = (p.get("opponent") or "").upper()
        away = (_own if _own != home else _opp) or "away"
        derived_game_id = _game_slug(
            f"{away}-{home}".lower().replace(" ", "-"), p.get("game_pk")
        )

        role = classify_role(p, tier)
        leaderboard_rows.append({
            "id":       p.get("player_id") or p.get("player_name", "").lower().replace(" ", "-"),
            "name":     p.get("player_name"),
            "teamAbbr": p.get("team"),
            "bats":     p.get("batter_side"),
            "quality":  quality,
            "pitcherVuln": p.get("pitcher_vuln", "NEUTRAL"),
            "pa":       season_pa,
            "avg":      _rate(p.get("batting_avg")),
            "slg":      _rate(p.get("actual_slg")),
            "babip":    _rate(p.get("babip")),
            "gb":       _pct(p.get("gb_pct")),
            "hh":       _pct(p.get("hard_hit")),
            "ld":       _pct(p.get("ld_pct")),
            "barrel":   _pct(p.get("barrel_pct")),
            "ev":       _flt(p.get("exit_velo")),
            "la":       _flt(p.get("avg_launch_angle")),
            "pull":     _pct(p.get("pull_pct")),
            "center":   _pct(p.get("center_pct")),
            "oppo":     _pct(p.get("oppo_pct")),
            "opphr":    p.get("pitcher_hr9"),
            "xwoba":    _rate(p.get("xwoba")),
            "hrpa":     hrpa,
            "hrprob":   round(model_prob * 100, 1),
            "model_prob": round(model_prob, 4),
            "tier":     tier,
            "gameId":   derived_game_id,
            # MLB game_pk pass-through (display/identity only — additive, not yet keyed on)
            "game_pk":  p.get("game_pk"),
            "odds":     odds,
            # FanDuel deep links (display/handoff only — additive passthrough)
            "fd_event_link": p.get("fd_event_link"),
            "fd_bet_link":   p.get("fd_bet_link"),
            "hr":       season_hr,
            "iso":      _rate(p.get("xiso")),
            "xslg":     _rate(p.get("xslg")),
            "fb":       _pct(p.get("fb_pct")),
            "sweet":    _pct(p.get("sweet_spot_pct")),
            "obp":      _rate(p.get("actual_obp")),
            "woba":     None,
            "bbpct":    round(p["batter_bb_pct"] * 100, 1) if p.get("batter_bb_pct") is not None else None,
            "kpct":     round(p["batter_k_pct"]  * 100, 1) if p.get("batter_k_pct")  is not None else None,
            "whiff":    None,
            "swstr":    None,
            "pullbrl":  None,
            "pullair":  _pct(p.get("pull_air_pct")),
            "h2h_factor": round(float(p.get("h2h_factor") or 1.0), 4),
            "fast":     p.get("fast"),
            "squp":     p.get("squp"),
            "blast":    p.get("blast"),
            "maxev":    _flt(p.get("max_ev")),
            "hrfb":     _flt(p.get("hrfb")),
            "pitcher_name":      p.get("pitcher_name", None),
            "pitcher_confirmed": p.get("pitcher_confirmed", False),
            "pitcher_id":        p.get("pitcher_id", None),
            "pitcher_hand":      p.get("pitcher_hand", None),
            # MAIN projected display fields (display-only; never read by scoring)
            "lineup_confirmed":    p.get("lineup_confirmed", False),
            "lineup_spot":         p.get("lineup_spot"),
            "model_prob_projected": p.get("model_prob_projected"),
            "hrprob_projected":    p.get("hrprob_projected"),
            "projected_pa_source": p.get("projected_pa_source"),
            "recent_form_games":  p.get("recent_form_games", []),
            # Real hand-specific batter splits (display only — additive passthrough)
            "vs_hand":       p.get("vs_hand"),
            "vs_hand_avg":   p.get("vs_hand_avg"),
            "vs_hand_slg":   p.get("vs_hand_slg"),
            "vs_hand_iso":   p.get("vs_hand_iso"),
            "vs_hand_hr":    p.get("vs_hand_hr"),
            "vs_hand_hr_pa": p.get("vs_hand_hr_pa"),
            "vs_hand_pa":    p.get("vs_hand_pa"),
            "vs_lhp_avg":    p.get("vs_lhp_avg"),
            "vs_lhp_slg":    p.get("vs_lhp_slg"),
            "vs_lhp_iso":    p.get("vs_lhp_iso"),
            "vs_lhp_hr":     p.get("vs_lhp_hr"),
            "vs_lhp_hr_pa":  p.get("vs_lhp_hr_pa"),
            "vs_lhp_pa":     p.get("vs_lhp_pa"),
            "vs_rhp_avg":    p.get("vs_rhp_avg"),
            "vs_rhp_slg":    p.get("vs_rhp_slg"),
            "vs_rhp_iso":    p.get("vs_rhp_iso"),
            "vs_rhp_hr":     p.get("vs_rhp_hr"),
            "vs_rhp_hr_pa":  p.get("vs_rhp_hr_pa"),
            "vs_rhp_pa":     p.get("vs_rhp_pa"),
            # Multi-season vs-hand splits (display only — additive passthrough)
            "multi_season_vs_hand": p.get("multi_season_vs_hand"),
            "pitcher_era":       p.get("pitcher_era"),
            "pitcher_whip":      p.get("pitcher_whip"),
            "pitcher_k_pct":     p.get("pitcher_k_pct"),
            "pitcher_bb_pct":    p.get("pitcher_bb_pct"),
            "pitcher_barrel_allowed": p.get("pitcher_barrel_allowed"),
            "pitcher_hh_allowed":     p.get("pitcher_hh_allowed"),
            "pitcher_fb_allowed":     p.get("pitcher_fb_allowed"),
            "pitcher_gb_allowed":     p.get("pitcher_gb_allowed"),
            "pitcher_hr9":            p.get("pitcher_hr9"),
            "gameStartUtc":      p.get("game_time_utc", ""),
            "gameStatus":        p.get("game_status", "Scheduled"),
            "prime":             role["prime"],
            "explosive":         role["explosive"],
            "advantage":         role["advantage"],
            "wildcard":          role["wildcard"],
        })

    leaderboard_rows.sort(
        key=lambda r: float(r.get("hrprob") or 0),
        reverse=True
    )
    _tier_ctr: dict = {}
    for r in leaderboard_rows:
        t = r.get("tier", "COLD")
        _tier_ctr[t] = _tier_ctr.get(t, 0) + 1
        r["model_tier_rank"] = _tier_ctr[t]
        r["_board"] = "main"

    # JIG list — same players, sorted by tactical score descending
    jig_build_error = False
    try:
        _arsenal_data = get_pitcher_arsenal(_dt.datetime.now().year)
        # Key lookup by (player_id, game_pk) so doubleheader siblings resolve
        # their own game's profile; fall back to name slug when player_id absent,
        # and to player_id-only when game_pk is missing on either side.
        players_by_id = {
            ((p.get("player_id")
              or (p.get("player_name") or "").lower().replace(" ", "-")),
             p.get("game_pk")): p
            for p in players
        }
        players_by_id_fallback = {
            (p.get("player_id")
             or (p.get("player_name") or "").lower().replace(" ", "-")): p
            for p in players
        }
        jig_rows = [copy.copy(r) for r in leaderboard_rows]
        for r in jig_rows:
            p = players_by_id.get((r.get("id"), r.get("game_pk")))
            if p is None:
                p = players_by_id_fallback.get(r.get("id"), {})
            r["jigScore"] = _jig_score(p, arsenal_data=_arsenal_data)
            # JIG-native display tier (additive; MAIN `tier` field untouched)
            r["jigTier"] = _jig_tier(r["jigScore"])
            # JIG projected: same _jig_score with announced pitcher fed in (already the case
            # when pitcher_confirmed=True). Null when no pitcher announced — tactical signals
            # would be 0/neutral; don't fabricate a projected value without pitcher identity.
            r["jigscore_projected"] = r["jigScore"] if p.get("pitcher_confirmed") else None
            jig_role = classify_role(p, r.get("tier", ""))
            r["advantage"] = jig_role["advantage"]
            r["wildcard"]  = jig_role["wildcard"]
        jig_rows.sort(key=lambda r: r["jigScore"], reverse=True)
        _tier_ctr_jig: dict = {}
        for r in jig_rows:
            t = r.get("tier", "COLD")
            _tier_ctr_jig[t] = _tier_ctr_jig.get(t, 0) + 1
            r["model_tier_rank"] = _tier_ctr_jig[t]
            r["_board"] = "jig"
    except Exception as e:
        log.error("JIG row build failed: %s", e, exc_info=True)
        jig_rows = []
        jig_build_error = True

    # AEE precompute — display-only, after JIG so pitch-mix caches are warm
    try:
        from engine.arsenal_edge import compute_aee_score
        _aee_arsenal = get_pitcher_arsenal(_dt.datetime.now().year)  # cache hit
        # Keyed on (player_id, game_pk) so doubleheader siblings get their own
        # game's AEE; player_id-only fallback when game_pk is missing.
        _aee_players = {
            ((p.get("player_id") or (p.get("player_name") or "").lower().replace(" ", "-")),
             p.get("game_pk")): p
            for p in players
        }
        _aee_map: dict[tuple, dict] = {
            pid_gpk: compute_aee_score(p, _aee_arsenal)
            for pid_gpk, p in _aee_players.items()
        }
        _aee_fallback = {pid: aee for (pid, _gpk), aee in _aee_map.items()}
        for r in leaderboard_rows:
            _aee = _aee_map.get((r.get("id"), r.get("game_pk")))
            if _aee is None:
                _aee = _aee_fallback.get(r.get("id"), {})
            r.update(_aee)
        for r in jig_rows:
            _aee = _aee_map.get((r.get("id"), r.get("game_pk")))
            if _aee is None:
                _aee = _aee_fallback.get(r.get("id"), {})
            r.update(_aee)
    except Exception as e:
        log.error("AEE precompute failed: %s", e, exc_info=True)

    # true_matchup_score and tm_projected — additive display fields; computed after AEE
    # so arsenal_edge_score/confidence are already on the row.
    # tm_projected substitutes model_prob_projected into the same formula; all other
    # fields (arsenal, vuln) remain real. Null when no pitcher announced.
    for r in leaderboard_rows:
        r["true_matchup_score"] = _true_matchup_score(r)
        _pmp = r.get("model_prob_projected")
        r["tm_projected"] = (
            _true_matchup_score({**r, "model_prob": _pmp}) if _pmp is not None else None
        )
    for r in jig_rows:
        r["true_matchup_score"] = _true_matchup_score(r)
        _pmp = r.get("model_prob_projected")
        r["tm_projected"] = (
            _true_matchup_score({**r, "model_prob": _pmp}) if _pmp is not None else None
        )

    seen_games = {}
    for p in players:
        _home = (p.get("home_team") or p.get("team") or "home").upper()
        _own  = (p.get("team") or "").upper()
        _opp  = (p.get("opponent") or "").upper()
        _away = (_own if _own != _home else _opp) or "away"
        gid = _game_slug(
            f"{_away}-{_home}".lower().replace(" ", "-"), p.get("game_pk")
        )
        if gid not in seen_games:
            _w = p.get("weather")
            _weather_str = (
                f"{_w.get('temp_f', '')}°F · {_w.get('wind_mph', '')} mph"
                if isinstance(_w, dict)
                else str(_w) if _w else ""
            )
            seen_games[gid] = {
                "id":       gid,
                "away":     _away,
                "home":     _home,
                "park":     p.get("venue", ""),
                "time":     p.get("game_time", ""),
                "weather":  _weather_str,
                "wind":     p.get("wind", ""),
                "hrFactor": round(float(p.get("park_factor") or 1.0), 3),
                "teams":    [_away, _home],
                # MLB game_pk pass-through (additive — cards still keyed by team slug)
                "game_pk":  p.get("game_pk"),
            }

    return {
        "leaderboard_rows":     leaderboard_rows,
        "leaderboard_rows_jig": jig_rows,
        "slate_games":          list(seen_games.values()),
        "generated_at":         _dt.datetime.utcnow().isoformat(),
        "date":                 today_et().strftime("%Y-%m-%d"),
        "fs_tier_thresholds":   dict(FS_TIER_THRESHOLDS),
        "jig_build_error":      jig_build_error,
    }


@app.get("/api/slate")
async def get_slate():
    """
    Returns today's Full Slate data in React frontend shape.
    No auth required — public endpoint for the React dashboard.
    Cache-first: serves slate_cache from today's pipeline run if fresh (≤12 h).
    On miss/stale: serves most-recent stored payload with stale=True (never rebuilds in-request).
    Empty DB (pipeline never run): returns clean error shape with empty rows.
    """
    import datetime as _dt
    today = today_et().strftime("%Y-%m-%d")

    # ── Cache-first path ────────────────────────────────────────────────────────
    try:
        cached = get_picks(today)
        if cached and "slate_cache" in cached:
            sc = cached["slate_cache"]
            sc_date = sc.get("date")
            if sc_date and sc_date != today:
                log.info("[/api/slate] cache date mismatch: cache=%s today=%s — falling through", sc_date, today)
            else:
                gen_at = sc.get("generated_at")
                if gen_at:
                    try:
                        gen_dt = _dt.datetime.fromisoformat(gen_at.replace("Z", ""))
                        age_minutes = int((_dt.datetime.utcnow() - gen_dt).total_seconds() / 60)
                        if age_minutes <= 720:
                            log.info("[/api/slate] cache hit | age=%dm date=%s", age_minutes, today)
                            return {
                                **sc,
                                "from_cache":        True,
                                "cache_age_minutes": age_minutes,
                                "stale":             False,
                            }
                        else:
                            log.info("[/api/slate] cache stale | age=%dm — falling through to live", age_minutes)
                    except Exception as e:
                        log.warning("[/api/slate] cache parse error: %s — falling through", e)
    except Exception as e:
        log.warning("[/api/slate] cache lookup error: %s — falling through to live", e)

    # ── Last-good fallback (never rebuild in-request) ───────────────────────────
    latest = get_latest_picks()
    if latest and "slate_cache" in latest:
        sc = latest["slate_cache"]
        log.info("[/api/slate] serving last-good cache | date=%s stale=True", sc.get("date"))
        return {
            **sc,
            "from_cache":        True,
            "cache_age_minutes": None,
            "stale":             True,
        }
    log.warning("[/api/slate] no slate data in DB — pipeline has not run yet")
    return {
        "error":                "No slate data available. Pipeline has not run yet.",
        "leaderboard_rows":     [],
        "leaderboard_rows_jig": [],
        "slate_games":          [],
        "from_cache":           False,
        "stale":                True,
    }


@app.get("/api/pitcher-detail")
async def get_pitcher_detail(pitcher_id: int, batter_id: int = 0,
                             batter_side: str = "", pitcher_hand: str = ""):
    """
    On-demand pitcher detail for the Pitch Mix Analysis modal.
    Returns: arsenal (pitch types + usage/velo/whiff), pitch_stats, batter_vs_pitches, h2h.
    No auth required — display-only data, not model inputs.
    pitcher_hand: used to derive effective batter side for switch hitters.
    """
    import datetime as _dt

    # Switch hitters bat opposite hand of pitcher
    effective_batter_side = batter_side
    if batter_side == "S" and pitcher_hand:
        effective_batter_side = "R" if pitcher_hand == "L" else "L"

    result: dict = {"pitcher_id": pitcher_id, "batter_id": batter_id,
                    "effective_batter_side": effective_batter_side}

    # Arsenal: get_pitcher_arsenal returns {pid: [{"pitch_type", "pitch_pct", "avg_speed", "whiff_pct", ...}]}
    try:
        year = _dt.datetime.now().year
        all_arsenal = get_pitcher_arsenal(year)
        raw_list = all_arsenal.get(pitcher_id, [])
        arsenal_by_code = {}
        for p in raw_list:
            usage = float(p.get("pitch_pct") or p.get("pitch_usage_pct") or 0)
            if usage <= 0.01:
                continue
            code = canonical_pitch_type(p.get("pitch_type", ""))
            row = {
                "code":  code,
                "name":  p.get("pitch_name", p.get("pitch_type", "")),
                "usage": round(usage * 100, 1),
                "velo":  round(float(p.get("avg_speed") or 0), 1) or None,
                "whiff": round(float(p.get("whiff_pct") or 0) * 100, 1) if p.get("whiff_pct") is not None else None,
            }
            current = arsenal_by_code.get(code)
            if code and (current is None or row["usage"] > current["usage"]):
                arsenal_by_code[code] = row
        result["arsenal"] = list(arsenal_by_code.values())
        result["arsenal"].sort(key=lambda x: x["usage"], reverse=True)
        _PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE[pitcher_id] = copy.deepcopy(
            result["arsenal"],
        )
    except Exception as e:
        log.warning("pitcher-detail arsenal failed pid=%s: %s", pitcher_id, e)
        result["arsenal"] = []
        _PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE.pop(pitcher_id, None)

    # Pitcher pitch stats vs effective batter side
    try:
        pitch_stats = get_pitcher_pitch_stats(
            pitcher_id, effective_batter_side, display_only=True,
        )
        result["pitch_stats"] = {
            canonical_pitch_type(code): stats
            for code, stats in pitch_stats.items()
            if canonical_pitch_type(code)
        }
    except Exception as e:
        log.warning("pitcher-detail pitch_stats failed pid=%s: %s", pitcher_id, e)
        result["pitch_stats"] = {}

    # Batter vs pitches (vs pitcher_hand, not batter_side)
    try:
        bvp = get_batter_vs_pitches(batter_id, pitcher_hand) if batter_id else {}
        result["batter_vs_pitches"] = bvp
    except Exception as e:
        log.warning("pitcher-detail batter_vs_pitches failed bid=%s: %s", batter_id, e)
        result["batter_vs_pitches"] = {}

    # H2H career
    try:
        from clients.pitch_mix import get_h2h as _get_h2h
        h2h_raw = _get_h2h(pitcher_id, batter_id) if batter_id else {}
        result["h2h"] = h2h_raw
    except Exception as e:
        log.warning("pitcher-detail h2h failed pid=%s bid=%s: %s", pitcher_id, batter_id, e)
        result["h2h"] = {}

    # Pitcher recent form: last 5 starts (HR/K/IP/BB)
    try:
        from clients.mlb_stats import _pitcher_game_log_splits, parse_ip
        result["pitcher_recent"] = [
            {
                "date": s.get("date"),
                "hr":   int(s.get("stat", {}).get("homeRuns") or 0),
                "k":    int(s.get("stat", {}).get("strikeOuts") or 0),
                "ip":   parse_ip(s.get("stat", {}).get("inningsPitched")),
                "bb":   int(s.get("stat", {}).get("baseOnBalls") or 0),
            }
            for s in _pitcher_game_log_splits(pitcher_id)[:5]
        ]
    except Exception as e:
        log.warning("pitcher-detail pitcher_recent failed pid=%s: %s", pitcher_id, e)
        result["pitcher_recent"] = []

    # Batter recent form: last 5 games (HR/AVG/SLG/PA)
    try:
        from clients.mlb_stats import _game_log_splits
        batter_recent = []
        for s in (_game_log_splits(batter_id)[:5] if batter_id else []):
            stat = s.get("stat", {})
            ab = int(stat.get("atBats") or 0)
            batter_recent.append({
                "date": s.get("date"),
                "hr":   int(stat.get("homeRuns") or 0),
                "avg":  round(int(stat.get("hits") or 0) / ab, 3) if ab else None,
                "slg":  round(int(stat.get("totalBases") or 0) / ab, 3) if ab else None,
                "pa":   int(stat.get("plateAppearances") or 0),
            })
        result["batter_recent"] = batter_recent
    except Exception as e:
        log.warning("pitcher-detail batter_recent failed bid=%s: %s", batter_id, e)
        result["batter_recent"] = []

    return result


def _detail_module(values: dict, labels: dict, source: str, freshness: str,
                   availability: dict | None = None) -> dict:
    """Attach field-level provenance without changing or deriving stored values."""
    field_availability = availability or {
        key: freshness if value is not None else "Gap"
        for key, value in values.items()
    }
    return {
        **values,
        "_meta": {
            "source": source,
            "freshness": freshness if any(v != "Gap" for v in field_availability.values()) else "Gap",
            "availability": field_availability,
            "labels": labels,
        },
    }


def _display_hr_environment(park_factor, weather_factor) -> float | None:
    """Park-weighted display score; never feeds the model or recomputes inputs."""
    park = _rate(park_factor)
    weather = _rate(weather_factor)
    if park is None or weather is None:
        return None
    park_anchor = 5.0 + 20.0 * (park - 1.0)
    weather_modifier = 10.0 * (weather - 1.0)
    return round(max(0.0, min(10.0, park_anchor + weather_modifier)), 1)


def _handedness_edge_label(bats, pitcher_hand, vs_lhp_slg, vs_rhp_slg) -> str | None:
    """Classify the live faced-hand SLG delta for display only."""
    batter_side = str(bats or "").upper()[:1]
    faced_hand = str(pitcher_hand or "").upper()[:1]
    if batter_side not in {"L", "R", "S"} or faced_hand not in {"L", "R"}:
        return None

    vs_left = _rate(vs_lhp_slg)
    vs_right = _rate(vs_rhp_slg)
    if vs_left is None or vs_right is None:
        return None

    faced_slg = vs_left if faced_hand == "L" else vs_right
    other_slg = vs_right if faced_hand == "L" else vs_left
    delta = faced_slg - other_slg
    if delta >= 0.050:
        return "PLATOON EDGE"
    if delta <= -0.050:
        return "REVERSE"
    return "NEUTRAL"


def _season_pace_projection(season_hr, games_played) -> tuple[int | None, str | None]:
    """Return a guarded 162-game HR pace for display only."""
    try:
        games = int(games_played)
    except (TypeError, ValueError):
        return None, "games unavailable"
    if games < 30:
        return None, f"insufficient games ({games}<30)"

    try:
        pace = float(season_hr) / games * 162
    except (TypeError, ValueError):
        return None, "season HR unavailable"
    if pace > 80:
        return None, "implausible projection"
    return round(pace), None


def _cached_batter_context(batter_id: int, pitcher_id: int = 0,
                           game_pk: int = 0) -> tuple[dict, dict, dict, dict, str]:
    """Read one batter/game from persisted pipeline state; never rebuild the slate."""
    import datetime as _dt

    today = today_et().strftime("%Y-%m-%d")
    payload = None
    freshness = "Stale"
    try:
        payload = get_picks(today)
    except Exception as exc:
        log.warning("batter-detail current cache lookup failed: %s", exc)

    if payload:
        slate_cache = payload.get("slate_cache") or {}
        generated_at = slate_cache.get("generated_at")
        if slate_cache.get("date") == today and generated_at:
            try:
                generated = _dt.datetime.fromisoformat(generated_at.replace("Z", ""))
                if (_dt.datetime.utcnow() - generated).total_seconds() <= 43200:
                    freshness = "Live"
            except (TypeError, ValueError):
                pass
    else:
        try:
            payload = get_latest_picks()
        except Exception as exc:
            log.warning("batter-detail latest cache lookup failed: %s", exc)

    if not isinstance(payload, dict):
        # Upstream/cache outages degrade to the same stable response contract.
        # The detail endpoint is display-only and must never rebuild the slate.
        return {
            "date": today,
            "slate_cache": {"date": today},
        }, {}, {}, {}, "Gap"

    slate_cache = payload.get("slate_cache") or {}

    def _matches(row: dict, id_key: str, allow_legacy_game_gap: bool = False) -> bool:
        if str(row.get(id_key) or "") != str(batter_id):
            return False
        if pitcher_id and str(row.get("pitcher_id") or "") != str(pitcher_id):
            return False
        if game_pk:
            row_game_pk = row.get("game_pk")
            if row_game_pk is None and allow_legacy_game_gap:
                pass
            elif str(row_game_pk or "") != str(game_pk):
                return False
        return True

    persisted_players = (
        payload.get("all_players")
        or payload.get("all_by_model")
        or payload.get("ranked")
        or []
    )
    player_candidates = [
        row for row in persisted_players
        if isinstance(row, dict) and _matches(row, "player_id")
    ]
    slate_candidates = [
        row for row in (slate_cache.get("leaderboard_rows") or [])
        if isinstance(row, dict) and _matches(row, "id", allow_legacy_game_gap=True)
    ]

    if len(player_candidates) > 1 and not game_pk:
        raise HTTPException(
            status_code=409,
            detail="Multiple cached games found for batter_id; game_pk is required.",
        )
    if len(slate_candidates) > 1:
        raise HTTPException(
            status_code=409,
            detail="Multiple cached slate rows match; a game-specific row is required.",
        )
    if not player_candidates and not slate_candidates:
        return payload, {}, {}, {}, "Gap"

    player = player_candidates[0] if player_candidates else {}
    slate_row = slate_candidates[0] if slate_candidates else {}
    resolved_game_pk = game_pk or player.get("game_pk") or slate_row.get("game_pk")
    game = next(
        (
            row for row in (slate_cache.get("slate_games") or [])
            if isinstance(row, dict)
            and resolved_game_pk
            and str(row.get("game_pk") or "") == str(resolved_game_pk)
        ),
        {},
    )
    return payload, player, slate_row, game, freshness


@app.get("/api/batter-detail")
async def get_batter_detail(batter_id: int, pitcher_id: int = 0, game_pk: int = 0):
    """Aggregate detail with an isolated Savant pitch-profile read-through."""
    payload, player, row, game, freshness = _cached_batter_context(
        batter_id, pitcher_id, game_pk,
    )
    weather = player.get("weather") if isinstance(player.get("weather"), dict) else {}
    resolved_pitcher_id = pitcher_id or player.get("pitcher_id") or row.get("pitcher_id")
    resolved_game_pk = game_pk or player.get("game_pk") or row.get("game_pk")
    generated_at = (payload.get("slate_cache") or {}).get("generated_at")

    # Cache-only recent records. Calling the existing game-log helpers on a miss
    # would perform an external MLB StatsAPI request, which B1 explicitly forbids.
    from clients import mlb_stats as _mlb_stats
    batter_cache_hit = False
    pitcher_cache_hit = False
    cached_batter_games = []
    batter_recent = []
    twenty_game_trend = None
    pitcher_recent = []
    try:
        batter_cache_hit = batter_id in _mlb_stats._GAME_LOG_CACHE
        cached_batter_games = _mlb_stats._GAME_LOG_CACHE.get(batter_id, [])
        if not isinstance(cached_batter_games, list):
            raise TypeError("batter game-log cache entry is not a list")
        for split in cached_batter_games[:5]:
            stat = split.get("stat", {})
            ab = int(stat.get("atBats") or 0)
            batter_recent.append({
                "date": split.get("date"),
                "hr": int(stat.get("homeRuns") or 0),
                "avg": round(int(stat.get("hits") or 0) / ab, 3) if ab else None,
                "slg": round(int(stat.get("totalBases") or 0) / ab, 3) if ab else None,
                "pa": int(stat.get("plateAppearances") or 0),
            })
        if cached_batter_games:
            twenty_game_trend = [
                {
                    "date": split.get("date"),
                    "hr": int((split.get("stat") or {}).get("homeRuns") or 0),
                }
                for split in reversed(cached_batter_games[:20])
            ]
    except Exception as exc:
        log.warning("batter-detail batter recent cache failed bid=%s: %s", batter_id, exc)
        batter_cache_hit = False
        cached_batter_games = []
        batter_recent = []
        twenty_game_trend = None

    try:
        pitcher_cache_hit = bool(
            resolved_pitcher_id in _mlb_stats._PITCHER_GAME_LOG_CACHE
            if resolved_pitcher_id else False
        )
        cached_pitcher_games = _mlb_stats._PITCHER_GAME_LOG_CACHE.get(
            resolved_pitcher_id, [],
        )
        if not isinstance(cached_pitcher_games, list):
            raise TypeError("pitcher game-log cache entry is not a list")
        for split in cached_pitcher_games[:5]:
            stat = split.get("stat", {})
            pitcher_recent.append({
                "date": split.get("date"),
                "hr": int(stat.get("homeRuns") or 0),
                "k": int(stat.get("strikeOuts") or 0),
                "ip": _mlb_stats.parse_ip(stat.get("inningsPitched")),
                "bb": int(stat.get("baseOnBalls") or 0),
            })
    except Exception as exc:
        log.warning(
            "batter-detail pitcher recent cache failed pid=%s: %s",
            resolved_pitcher_id, exc,
        )
        pitcher_cache_hit = False
        pitcher_recent = []
    twenty_game_trend_sample_count = len(twenty_game_trend or [])

    season_hr = player.get("season_hr") if player.get("season_hr") is not None else row.get("hr")
    batter_games_played = len(cached_batter_games) if batter_cache_hit else None
    team_games_played_raw = next(
        (
            source.get(key)
            for source in (player, row, game)
            for key in ("team_games_played", "teamGamesPlayed")
            if source.get(key) is not None
        ),
        None,
    )
    try:
        team_games_played = int(team_games_played_raw)
    except (TypeError, ValueError):
        team_games_played = None
    if team_games_played is not None and team_games_played <= 0:
        team_games_played = None
    if team_games_played is not None:
        season_pace_games_used = team_games_played
        season_pace_games_source = "team_games_played_cache"
    else:
        season_pace_games_used = batter_games_played
        season_pace_games_source = (
            "batter_game_log_cache_fallback" if batter_games_played is not None else None
        )
    season_pace_hr, season_pace_reason = _season_pace_projection(
        season_hr, season_pace_games_used,
    )

    actual_avg = _rate(player.get("batting_avg"))
    if actual_avg is None:
        actual_avg = _rate(row.get("avg"))
    actual_slg = _rate(player.get("actual_slg"))
    if actual_slg is None:
        actual_slg = _rate(row.get("slg"))
    actual_iso = (
        round(actual_slg - actual_avg, 3)
        if actual_avg is not None and actual_slg is not None else None
    )

    bats = player.get("batter_side", row.get("bats"))
    pitcher_hand = player.get("pitcher_hand", row.get("pitcher_hand"))
    vs_lhp_slg = player.get("vs_lhp_slg")
    if vs_lhp_slg is None:
        vs_lhp_slg = row.get("vs_lhp_slg")
    vs_rhp_slg = player.get("vs_rhp_slg")
    if vs_rhp_slg is None:
        vs_rhp_slg = row.get("vs_rhp_slg")
    handedness_edge_label = _handedness_edge_label(
        bats, pitcher_hand, vs_lhp_slg, vs_rhp_slg,
    )
    park_factor = player.get("park_factor")
    if park_factor is None:
        park_factor = game.get("hrFactor")
    weather_factor = player.get("weather_factor")

    threat = {
        "hrprob": row.get("hrprob"),
        "model_prob": row.get("model_prob", player.get("model_prob")),
        "tier": row.get("tier"),
        "model_tier_rank": row.get("model_tier_rank"),
        "hrprob_projected": row.get("hrprob_projected", player.get("hrprob_projected")),
        "model_prob_projected": row.get("model_prob_projected", player.get("model_prob_projected")),
        "season_pace_hr": season_pace_hr,
        "season_pace_games_used": season_pace_games_used,
        "season_pace_games_source": season_pace_games_source,
        "season_pace_reason": season_pace_reason,
    }
    statcast = {
        "maxev": row.get("maxev", _flt(player.get("max_ev"))),
        "ev": row.get("ev", _flt(player.get("exit_velo"))),
        "hh": row.get("hh", _pct(player.get("hard_hit"))),
        "barrel": row.get("barrel", _pct(player.get("barrel_pct"))),
        "sweet": row.get("sweet", _pct(player.get("sweet_spot_pct"))),
        "la": row.get("la", _flt(player.get("avg_launch_angle"))),
        "pullair": row.get("pullair", _pct(player.get("pull_air_pct"))),
        "xslg": row.get("xslg", _rate(player.get("xslg"))),
        "xiso": _rate(player.get("xiso")) if player else row.get("iso"),
        "actual_iso": actual_iso,
        "woba": None,
    }
    splits = {
        "actual_slg_vs_rhp": _rate(player.get("vs_rhp_slg")) if player else row.get("vs_rhp_slg"),
        "actual_slg_vs_lhp": _rate(player.get("vs_lhp_slg")) if player else row.get("vs_lhp_slg"),
        "pull": row.get("pull", _pct(player.get("pull_pct"))),
        "center": row.get("center", _pct(player.get("center_pct"))),
        "oppo_pct": _pct(player.get("oppo_pct")) if player else row.get("oppo_pct"),
        "handedness_edge_label": handedness_edge_label,
    }
    discipline = {
        "bbpct": row.get("bbpct"),
        "squp": row.get("squp", player.get("squp")),
    }
    environment = {
        "temp": weather.get("temp_f"),
        "wind": weather.get("wind_mph"),
        "park_factor": park_factor,
        "hrFactor": game.get("hrFactor", park_factor),
        "weather_factor": weather_factor,
        "humidity_pct": weather.get("humidity_pct"),
        "hr_environment_0_10": _display_hr_environment(park_factor, weather_factor),
    }
    pitcher = {
        "pitcher_id": resolved_pitcher_id,
        "pitcher_hr9": player.get("pitcher_hr9", row.get("pitcher_hr9")),
        "opphr": row.get("opphr", player.get("pitcher_hr9")),
        "pitcher_barrel_allowed": player.get(
            "pitcher_barrel_allowed", row.get("pitcher_barrel_allowed")
        ),
        "pitcherVuln": row.get("pitcherVuln", player.get("pitcher_vuln")),
    }
    arsenal = {
        "arsenal_edge_score": row.get("arsenal_edge_score"),
        "arsenal_edge_label": row.get("arsenal_edge_label"),
        "arsenal_edge_key_pitch": row.get("arsenal_edge_key_pitch"),
        "arsenal_edge_confidence": row.get("arsenal_edge_confidence"),
    }
    fatigue = {
        "pitcher_days_rest": player.get("pitcher_days_rest"),
        "fatigue_factor": player.get("fatigue_factor"),
    }
    try:
        pitch_profile = get_batter_pitch_profile_display(
            batter_id,
            pitcher_hand,
            slate_date=(
                payload.get("date")
                or (payload.get("slate_cache") or {}).get("date")
                or ""
            ),
            pitcher_id=int(resolved_pitcher_id or 0),
            game_pk=int(resolved_game_pk or 0),
            batter_side=str(bats or ""),
        )
    except Exception as exc:
        log.warning("batter-detail pitch_profile failed bid=%s: %s", batter_id, exc)
        pitch_profile = empty_batter_pitch_profile_display(
            pitcher_hand,
            reason="endpoint_error",
        )

    # Read-only display snapshot only: never call or read a scoring cache here.
    # /api/pitcher-detail owns this already-serialized usage; absent data = Gap.
    cached_pitcher_arsenal = []
    try:
        if resolved_pitcher_id:
            cached_pitcher_arsenal = copy.deepcopy(
                _PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE.get(int(resolved_pitcher_id), []),
            )
    except Exception as exc:
        log.warning(
            "batter-detail pitcher arsenal snapshot failed pid=%s: %s",
            resolved_pitcher_id, exc,
        )
        cached_pitcher_arsenal = []
    try:
        pitch_mix_verdict = pitch_mix_verdict_display(
            pitch_profile.get("rows", []), cached_pitcher_arsenal,
        )
    except Exception as exc:
        log.warning("batter-detail verdict failed bid=%s: %s", batter_id, exc)
        pitch_mix_verdict = empty_pitch_mix_verdict_display("verdict_error")

    return {
        "meta": {
            "batter_id": batter_id,
            "pitcher_id": resolved_pitcher_id,
            "game_pk": resolved_game_pk,
            "slate_date": payload.get("date") or (payload.get("slate_cache") or {}).get("date"),
            "generated_at": generated_at,
            "freshness": freshness,
            "source": "pipeline_runs.payload + in_process_game_log_cache",
            "display_only": True,
        },
        "threat": _detail_module(threat, {
            "hrprob": "HR threat (0-100)", "model_prob": "MAIN model probability",
            "tier": "MAIN model tier", "model_tier_rank": "HR Threat Rank within tier",
            "hrprob_projected": "Projected HR threat (0-100)",
            "model_prob_projected": "Projected MAIN model probability",
            "season_pace_hr": "On pace (162g)",
            "season_pace_games_used": "Games used for 162-game pace",
            "season_pace_games_source": "Pace denominator source",
            "season_pace_reason": "Reason pace is unavailable",
        }, "pipeline_runs.payload + clients.mlb_stats in-process game-log cache", freshness),
        "statcast": _detail_module(statcast, {
            "maxev": "Max exit velocity", "ev": "Average exit velocity",
            "hh": "Hard-hit rate", "barrel": "Barrel rate", "sweet": "Sweet-spot rate",
            "la": "Average launch angle", "pullair": "Pull-air rate",
            "xslg": "xSLG", "xiso": "xISO", "actual_iso": "ISO (actual)",
            "woba": "wOBA (unavailable in B1)",
        }, "pipeline_runs.payload.persisted_player_state season + statcast aggregates", freshness),
        "splits": _detail_module(splits, {
            "actual_slg_vs_rhp": "Actual SLG vs RHP", "actual_slg_vs_lhp": "Actual SLG vs LHP",
            "pull": "Pull rate", "center": "Center rate", "oppo_pct": "Opposite-field rate",
            "handedness_edge_label": "Live platoon SLG edge",
        }, "pipeline_runs.payload.persisted_player_state", freshness),
        "discipline": _detail_module(discipline, {
            "bbpct": "Walk rate", "squp": "Squared-up rate per swing",
        }, "pipeline_runs.payload.persisted_player_state", freshness),
        "environment": _detail_module(environment, {
            "temp": "Temperature (F)", "wind": "Wind speed (mph)",
            "park_factor": "Park HR factor", "hrFactor": "Park HR factor",
            "weather_factor": "Existing model weather factor (read-only input)",
            "humidity_pct": "Humidity",
            "hr_environment_0_10": "Park-weighted HR environment (0-10, display only)",
        }, "pipeline_runs.payload.persisted_player_state.weather + slate_cache.slate_games", freshness),
        "pitcher": _detail_module(pitcher, {
            "pitcher_id": "MLB pitcher id", "pitcher_hr9": "Pitcher HR/9",
            "opphr": "Opposing pitcher HR/9", "pitcher_barrel_allowed": "Pitcher barrel rate allowed",
            "pitcherVuln": "Pitcher HR-risk tier",
        }, "pipeline_runs.payload.persisted_player_state + slate_cache.leaderboard_rows", freshness),
        "arsenal": _detail_module(arsenal, {
            "arsenal_edge_score": "Arsenal Edge score", "arsenal_edge_label": "Arsenal Edge label",
            "arsenal_edge_key_pitch": "Arsenal Edge key pitch",
            "arsenal_edge_confidence": "Arsenal Edge confidence",
        }, "pipeline_runs.payload.slate_cache.leaderboard_rows", freshness),
        "fatigue": _detail_module(fatigue, {
            "pitcher_days_rest": "Pitcher days rest", "fatigue_factor": "Existing fatigue factor",
        }, "pipeline_runs.payload.persisted_player_state", freshness),
        "pitch_profile": pitch_profile,
        "pitch_mix_verdict": pitch_mix_verdict["label"],
        "pitch_mix_exploit_pitches": pitch_mix_verdict["exploit_pitches"],
        "pitch_mix_verdict_meta": {
            key: value
            for key, value in pitch_mix_verdict.items()
            if key not in {"label", "exploit_pitches"}
        },
        "recent": _detail_module({
            "batter_games": batter_recent,
            "pitcher_starts": pitcher_recent,
            "twenty_game_trend": twenty_game_trend,
            "twenty_game_trend_sample_count": twenty_game_trend_sample_count,
        }, {
            "batter_games": "Last 5 games", "pitcher_starts": "Last 5 starts",
            "twenty_game_trend": "Last 20 cached games, chronological HR trend",
            "twenty_game_trend_sample_count": "Cached games represented in trend",
        }, "clients.mlb_stats in-process game-log caches", freshness, {
            "batter_games": freshness if batter_cache_hit else "Gap",
            "pitcher_starts": freshness if pitcher_cache_hit else "Gap",
            "twenty_game_trend": freshness if twenty_game_trend is not None else "Gap",
            "twenty_game_trend_sample_count": freshness if twenty_game_trend is not None else "Gap",
        }),
    }


# ── Internals ──────────────────────────────────────────────────────────────────

def _picks_or_404(date_str: str) -> dict:
    cached = get_picks(date_str)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail=f"No data for {date_str}. Pipeline hasn't run yet for this date.",
        )
    return {
        "date":           date_str,
        "ranked":         cached.get("ranked", []),
        "all_players":    cached.get("all_by_model", []),
        "stats":          cached.get("stats", {}),
        "auto_parlays":   cached.get("auto_parlays", {}),
        "ran_at":         cached.get("ran_at"),
        "from_cache":     True,
    }


async def _run_pipeline(target_date: str):
    """Background task: run pipeline and store to Supabase."""
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
    from datetime import datetime as _dt
    try:
        from pipeline import load_game_data, serializable
        log.info(f"[pipeline] starting for {target_date}")
        data = load_game_data(target_date)
        payload = _build_payload(target_date, data)
        store_picks(target_date, payload)
        log.info(f"[pipeline] done — {data['stats'].get('qualified', 0)} picks stored")
    except Exception as exc:
        log.error(f"[pipeline] failed: {exc}", exc_info=True)


def _build_payload(target_date: str, data: dict) -> dict:
    from datetime import datetime as _dt
    from pipeline import serializable
    payload = {
        "date":            target_date,
        "ran_at":          _dt.utcnow().isoformat() + "Z",
        "ranked":          serializable(data.get("ranked", [])),
        "all_by_model":    serializable(data.get("all_by_model", []))[:50],
        "auto_parlays":    data.get("auto_parlays", {}),
        "profile_parlays": data.get("profile_parlays", {}),
        "stats":           data.get("stats", {}),
    }
    try:
        payload["slate_cache"] = _build_slate_payload(data)
    except Exception as e:
        log.error("[pipeline] slate_cache build failed: %s", e, exc_info=True)
    return payload
