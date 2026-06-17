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

The pipeline is normally triggered by GitHub Actions cron (see api/cron.py).
The /api/pipeline/run endpoint is a manual fallback; it runs in a background
task so the HTTP response returns immediately, but note that Fly.io machines
with auto_stop=true may kill the machine before the pipeline completes.
For reliability, always prefer the GH Actions cron path.
"""

import os
import copy
import logging
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from api.auth import require_auth, require_beta
from api.cache import get_picks, store_picks, list_runs, redeem_invite
from clients.arsenal import get_pitcher_arsenal, arsenal_matchup_factor
from clients.pitch_mix import get_batter_vs_pitches, get_pitcher_pitch_stats
from config import FS_TIER_THRESHOLDS
from roles import classify_role

log = logging.getLogger("uvicorn.error")

app = FastAPI(title="MLB HR Engine", version="4.0", docs_url="/docs")

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
    return _picks_or_404(date.today().strftime("%Y-%m-%d"))


@app.get("/api/picks/{date_str}")
async def picks_by_date(date_str: str, user=Depends(require_beta)):
    try:
        date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Use YYYY-MM-DD format.")
    return _picks_or_404(date_str)


@app.get("/api/strategies")
async def strategies(date_str: str = None, user=Depends(require_beta)):
    d = date_str or date.today().strftime("%Y-%m-%d")
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
    target = date.today().strftime("%Y-%m-%d")
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
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
    try:
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


def _jig_score(player: dict, arsenal_data: dict | None = None) -> float:
    """
    JIG tactical exploit score.
    Inputs: raw Statcast contact/power profile + optional
    arsenal/pitch-mix signals.
    No model_prob. No HVY modifier (display-only per doctrine).
    """
    def _f(key):
        v = player.get(key, 0)
        if isinstance(v, str):
            v = v.replace("%", "").strip()
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    # --- Contact/power base (0.78 weight) ---
    # Percent-scale stats normalized to 0-1 so they share the decimal
    # scale of xSLG/xISO (Candidate D correction).
    xslg        = _f("xslg")        * 0.20
    barrel      = (_f("barrel_pct") / 100.0) * 0.17
    xiso        = _f("xiso")        * 0.12
    pull_air    = (_f("pull_air_pct") / 100.0) * 0.11
    hard_hit    = (_f("hard_hit") / 100.0)    * 0.11
    sweet_spot  = (_f("sweet_spot_pct") / 100.0) * 0.07
    base_score  = xslg + barrel + xiso + pull_air + hard_hit + sweet_spot

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
            batter_vs       = get_batter_vs_pitches(batter_id, batter_side)
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
    return ((base_score + hr_term) * stab) + tactical


# ── Full Slate ─────────────────────────────────────────────────────────────────

def _build_slate_payload(data: dict) -> dict:
    """
    Map pipeline data → React frontend shape.
    Returns leaderboard_rows, leaderboard_rows_jig, slate_games, generated_at, date.
    Does NOT include from_cache / cache_age_minutes — caller adds those.
    """
    import datetime as _dt
    players = data.get("all_players", [])

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
                  "WEAK": "WEAK", "DANGER": "DANGER"}
        quality = mq_map.get(p.get("matchup_quality", "AVG"), "AVG")

        fd_raw = p.get("fanduel_american")
        odds = (f"+{fd_raw}" if fd_raw and fd_raw > 0
                else str(fd_raw) if fd_raw else None)

        away = (p.get("opponent") or p.get("team") or "away").upper()
        home = (p.get("home_team") or p.get("team") or "home").upper()
        derived_game_id = f"{away}-{home}".lower().replace(" ", "-")

        role = classify_role(p, tier)
        leaderboard_rows.append({
            "id":       p.get("player_id") or p.get("player_name", "").lower().replace(" ", "-"),
            "name":     p.get("player_name"),
            "teamAbbr": p.get("team"),
            "bats":     p.get("batter_side"),
            "quality":  quality,
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
            "opphr":    p.get("pitcher_hr9"),
            "xwoba":    _rate(p.get("xwoba")),
            "hrpa":     hrpa,
            "hrprob":   round(model_prob * 100, 1),
            "model_prob": round(model_prob, 4),
            "tier":     tier,
            "gameId":   derived_game_id,
            "odds":     odds,
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
            "hrfb":     _flt(p.get("hr_rate")),
            "pitcher_name":      p.get("pitcher_name", None),
            "pitcher_confirmed": p.get("pitcher_confirmed", False),
            "pitcher_id":        p.get("pitcher_id", None),
            "pitcher_hand":      p.get("pitcher_hand", None),
            "pitcher_era":       p.get("pitcher_era"),
            "pitcher_whip":      p.get("pitcher_whip"),
            "pitcher_k_pct":     p.get("pitcher_k_pct"),
            "pitcher_bb_pct":    p.get("pitcher_bb_pct"),
            "pitcher_barrel_allowed": p.get("pitcher_barrel_allowed"),
            "pitcher_hh_allowed":     p.get("pitcher_hh_allowed"),
            "pitcher_fb_allowed":     p.get("pitcher_fb_allowed"),
            "pitcher_gb_allowed":     p.get("pitcher_gb_allowed"),
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

    # JIG list — same players, sorted by tactical score descending
    try:
        _arsenal_data = get_pitcher_arsenal(_dt.datetime.now().year)
        # Key lookup by stable player_id (same scheme as row "id") to avoid
        # same-name collisions; fall back to name slug when player_id absent.
        players_by_id = {
            (p.get("player_id")
             or (p.get("player_name") or "").lower().replace(" ", "-")): p
            for p in players
        }
        jig_rows = [copy.copy(r) for r in leaderboard_rows]
        for r in jig_rows:
            p = players_by_id.get(r.get("id"), {})
            r["jigScore"] = _jig_score(p, arsenal_data=_arsenal_data)
            jig_role = classify_role(p, r.get("tier", ""))
            r["advantage"] = jig_role["advantage"]
            r["wildcard"]  = jig_role["wildcard"]
        jig_rows.sort(key=lambda r: r["jigScore"], reverse=True)
    except Exception as e:
        log.error("JIG row build failed: %s", e, exc_info=True)
        jig_rows = []

    seen_games = {}
    for p in players:
        _away = (p.get("opponent") or p.get("team") or "away").upper()
        _home = (p.get("home_team") or p.get("team") or "home").upper()
        gid = f"{_away}-{_home}".lower().replace(" ", "-")
        if gid not in seen_games:
            _w = p.get("weather")
            _weather_str = (
                f"{_w.get('temp_f', '')}°F · {_w.get('wind_mph', '')} mph"
                if isinstance(_w, dict)
                else str(_w) if _w else ""
            )
            seen_games[gid] = {
                "id":       gid,
                "away":     p.get("opponent", ""),
                "home":     p.get("home_team", p.get("team", "")),
                "park":     p.get("venue", ""),
                "time":     p.get("game_time", ""),
                "weather":  _weather_str,
                "wind":     p.get("wind", ""),
                "hrFactor": round(float(p.get("park_factor") or 1.0), 3),
                "teams":    [p.get("opponent", ""), p.get("home_team", p.get("team", ""))],
            }

    return {
        "leaderboard_rows":     leaderboard_rows,
        "leaderboard_rows_jig": jig_rows,
        "slate_games":          list(seen_games.values()),
        "generated_at":         _dt.datetime.utcnow().isoformat(),
        "date":                 date.today().strftime("%Y-%m-%d"),
        "fs_tier_thresholds":   dict(FS_TIER_THRESHOLDS),
    }


@app.get("/api/slate")
async def get_slate():
    """
    Returns today's Full Slate data in React frontend shape.
    No auth required — public endpoint for the React dashboard.
    Cache-first: serves slate_cache from today's pipeline run if fresh (≤12 h).
    Falls back to live load_game_data() if cache is missing, stale, or date-mismatched.
    """
    import datetime as _dt
    today = date.today().strftime("%Y-%m-%d")

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
                            }
                        else:
                            log.info("[/api/slate] cache stale | age=%dm — falling through to live", age_minutes)
                    except Exception as e:
                        log.warning("[/api/slate] cache parse error: %s — falling through", e)
    except Exception as e:
        log.warning("[/api/slate] cache lookup error: %s — falling through to live", e)

    # ── Live fallback ───────────────────────────────────────────────────────────
    try:
        from pipeline import load_game_data
        data = load_game_data()
        payload = _build_slate_payload(data)
        return {
            **payload,
            "from_cache":        False,
            "cache_age_minutes": 0,
        }
    except Exception as e:
        log.error(f"[/api/slate] {e}", exc_info=True)
        return {
            "error":                str(e),
            "leaderboard_rows":     [],
            "leaderboard_rows_jig": [],
            "slate_games":          [],
            "from_cache":           False,
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
        result["arsenal"] = [
            {
                "code":  p.get("pitch_type", ""),
                "name":  p.get("pitch_name", p.get("pitch_type", "")),
                "usage": round(float(p.get("pitch_pct") or p.get("pitch_usage_pct") or 0) * 100, 1),
                "velo":  round(float(p.get("avg_speed") or 0), 1) or None,
                "whiff": round(float(p.get("whiff_pct") or 0) * 100, 1) if p.get("whiff_pct") is not None else None,
            }
            for p in raw_list
            if (p.get("pitch_pct") or p.get("pitch_usage_pct") or 0) > 0.01
        ]
        result["arsenal"].sort(key=lambda x: x["usage"], reverse=True)
    except Exception as e:
        log.warning("pitcher-detail arsenal failed pid=%s: %s", pitcher_id, e)
        result["arsenal"] = []

    # Pitcher pitch stats vs effective batter side
    try:
        pitch_stats = get_pitcher_pitch_stats(pitcher_id, effective_batter_side)
        result["pitch_stats"] = pitch_stats
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

    return result


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
