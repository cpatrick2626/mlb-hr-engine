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
POST /api/invite/redeem           — redeem invite code (auth required)

The pipeline is normally triggered by GitHub Actions cron (see api/cron.py).
The /api/pipeline/run endpoint is a manual fallback; it runs in a background
task so the HTTP response returns immediately, but note that Fly.io machines
with auto_stop=true may kill the machine before the pipeline completes.
For reliability, always prefer the GH Actions cron path.
"""

import os
import logging
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from api.auth import require_auth, require_beta
from api.cache import get_picks, store_picks, list_runs, redeem_invite

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


# ── Full Slate ─────────────────────────────────────────────────────────────────

@app.get("/api/slate")
async def get_slate():
    """
    Returns today's Full Slate data in React frontend shape.
    No auth required — public endpoint for the React dashboard.
    Runs the pipeline and maps output to LEADERBOARD_ROWS + SLATE_GAMES format.
    """
    try:
        from pipeline import load_game_data
        data = load_game_data()
        players = data.get("all_players", [])

        leaderboard_rows = []
        for p in players:
            model_prob = float(p.get("model_prob") or 0)
            season_pa = int(p.get("season_pa") or 0)
            season_hr = int(p.get("season_hr") or 0)
            hrpa = round(season_hr / season_pa, 3) if season_pa > 0 else None

            if model_prob >= 0.18:   tier = "APEX"
            elif model_prob >= 0.13: tier = "ELITE"
            elif model_prob >= 0.09: tier = "EDGE"
            elif model_prob >= 0.06: tier = "SIGNAL"
            elif model_prob >= 0.03: tier = "WATCH"
            else:                    tier = "COLD"

            mq_map = {"ELITE": "ELITE", "STRONG": "STRONG", "AVG": "AVG",
                      "WEAK": "WEAK", "DANGER": "DANGER"}
            quality = mq_map.get(p.get("matchup_quality", "AVG"), "AVG")

            fd_raw = p.get("fanduel_american")
            odds = (f"+{fd_raw}" if fd_raw and fd_raw > 0
                    else str(fd_raw) if fd_raw else None)

            away = (p.get("opponent") or p.get("team") or "away").upper()
            home = (p.get("home_team") or p.get("team") or "home").upper()
            derived_game_id = f"{away}-{home}".lower().replace(" ", "-")

            leaderboard_rows.append({
                "id":       p.get("player_id") or p.get("player_name", "").lower().replace(" ", "-"),
                "name":     p.get("player_name"),
                "teamAbbr": p.get("team"),
                "bats":     p.get("batter_side"),
                "quality":  quality,
                "pa":       season_pa,
                "avg":      p.get("batting_avg"),
                "slg":      p.get("actual_slg"),
                "babip":    p.get("babip"),
                "gb":       p.get("gb_pct"),
                "hh":       p.get("hard_hit"),
                "ld":       p.get("ld_pct"),
                "barrel":   p.get("barrel_pct"),
                "ev":       p.get("exit_velo"),
                "la":       p.get("avg_launch_angle"),
                "pull":     p.get("pull_pct"),
                "center":   p.get("center_pct"),
                "opphr":    p.get("pitcher_hr9"),
                "xwoba":    p.get("xwoba"),
                "hrpa":     hrpa,
                "hrprob":   round(model_prob * 100, 1),
                "tier":     tier,
                "gameId":   derived_game_id,
                "odds":     odds,
                "hr":       season_hr,
            })

        seen_games = {}
        for p in players:
            _away = (p.get("opponent") or p.get("team") or "away").upper()
            _home = (p.get("home_team") or p.get("team") or "home").upper()
            gid = f"{_away}-{_home}".lower().replace(" ", "-")
            if gid not in seen_games:
                seen_games[gid] = {
                    "id":       gid,
                    "away":     p.get("opponent", ""),
                    "home":     p.get("home_team", p.get("team", "")),
                    "park":     p.get("venue", ""),
                    "time":     p.get("game_time", ""),
                    "weather":  p.get("weather", ""),
                    "wind":     p.get("wind", ""),
                    "hrFactor": float(p.get("park_factor") or 1.0),
                    "teams":    [],
                }

        import datetime as _dt
        return {
            "leaderboard_rows": leaderboard_rows,
            "slate_games":      list(seen_games.values()),
            "generated_at":     _dt.datetime.utcnow().isoformat(),
        }

    except Exception as e:
        log.error(f"[/api/slate] {e}", exc_info=True)
        return {"error": str(e), "leaderboard_rows": [], "slate_games": []}


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
    return {
        "date":            target_date,
        "ran_at":          _dt.utcnow().isoformat() + "Z",
        "ranked":          serializable(data.get("ranked", [])),
        "all_by_model":    serializable(data.get("all_by_model", []))[:50],
        "auto_parlays":    data.get("auto_parlays", {}),
        "profile_parlays": data.get("profile_parlays", {}),
        "stats":           data.get("stats", {}),
    }
