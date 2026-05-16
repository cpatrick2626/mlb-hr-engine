"""
Closing Line Value (CLV) tracker.

CLV measures whether the odds at the time you pick were better or worse
than the closing line. If your picks consistently beat the closing line,
the model is sharp — the market agrees with you after seeing more info.

Workflow:
  1. log_opening_lines(picks) saves odds at time of pick (morning)
  2. fetch_closing_lines() pulls final odds before first pitch
  3. compute_clv() calculates edge gained/lost vs close
  4. Results written to tracking/clv_log.csv

CLV > 0 consistently means: you're getting better prices than sharp money.
CLV < 0 consistently means: the market moved against you (bad sign for model).
"""

import csv
import os
import unicodedata
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import requests

import config

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Codex-HR-Engine/clv"})

CLV_LOG = Path(__file__).parent / "clv_log.csv"

CLV_FIELDS = [
    "date", "player_name", "team", "model_prob_pct",
    "opening_american", "opening_implied_pct",
    "closing_american", "closing_implied_pct",
    "clv_pct", "notes",
]


def log_opening_lines(picks: list[dict]) -> None:
    """Save pick odds at time of model run (the 'opening' line for CLV purposes)."""
    today = date.today().isoformat()
    existing = _existing_dates()
    if today in existing:
        return

    rows = []
    for p in picks:
        odds = p.get("best_american")
        if not odds:
            continue
        implied = _implied(odds)
        rows.append({
            "date":                today,
            "player_name":         p["player_name"],
            "team":                p.get("team", ""),
            "model_prob_pct":      f"{p.get('model_prob', 0)*100:.2f}",
            "opening_american":    odds,
            "opening_implied_pct": f"{implied*100:.2f}",
            "closing_american":    "",
            "closing_implied_pct": "",
            "clv_pct":             "",
            "notes":               "",
        })

    _append(rows)


def fetch_and_compute_clv(target_date: Optional[str] = None) -> list[dict]:
    """
    For picks logged on target_date, fetch closing odds from the Odds API
    and compute CLV. Updates clv_log.csv with results.
    """
    date_str = target_date or date.today().isoformat()
    picks = _load_picks_for_date(date_str)
    if not picks:
        return []

    # Try to fetch current odds for these players
    closing = _fetch_current_hr_odds()

    updated = []
    for pick in picks:
        name = pick["player_name"]
        close_odds = closing.get(_normalize(name))
        if close_odds is None:
            updated.append({**pick, "notes": "closing line unavailable"})
            continue

        try:
            open_implied = float(pick.get("opening_implied_pct", 0)) / 100.0
        except (ValueError, TypeError):
            open_implied = 0.0
        close_implied = _implied(close_odds)
        # CLV = how much the market moved vs the price we locked in.
        # Positive = close implied > open implied = we got better odds than the close.
        # Raw implied-prob difference is correct here — vig is symmetric across both
        # endpoints so dividing it out would compress CLV without adding accuracy.
        clv = (close_implied - open_implied) * 100  # positive = we got better price
        clv = max(-100.0, min(100.0, clv))  # sanity bounds: ±100% is physically impossible

        updated.append({
            **pick,
            "closing_american":    close_odds,
            "closing_implied_pct": f"{close_implied*100:.2f}",
            "clv_pct":             f"{clv:.2f}",
        })

    _rewrite(date_str, updated)
    return updated


def clv_summary() -> dict:
    """Aggregate CLV stats across all logged picks."""
    if not CLV_LOG.exists():
        return {}

    clv_vals = []
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get("clv_pct", "")
            if val:
                try:
                    clv_vals.append(float(val))
                except ValueError:
                    pass

    if not clv_vals:
        return {}

    avg = sum(clv_vals) / len(clv_vals)
    positive = sum(1 for v in clv_vals if v > 0)
    return {
        "picks_with_clv": len(clv_vals),
        "avg_clv_pct":    round(avg, 2),
        "pct_beating_close": round(positive / len(clv_vals) * 100, 1),
        "verdict": "SHARP" if avg > 0.5 else ("NEUTRAL" if avg > -0.5 else "SOFT"),
    }


# ── Internal ──────────────────────────────────────────────────────────────────

def _implied(american: int) -> float:
    if american > 0:
        return 100 / (american + 100)
    return abs(american) / (abs(american) + 100)


def _normalize(name: str) -> str:
    """Fold accents and lowercase for robust name matching (e.g. 'José' → 'jose')."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()


def _append(rows: list[dict]) -> None:
    existing: list[dict] = []
    if CLV_LOG.exists():
        with open(CLV_LOG, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    _atomic_write(existing + rows)


def _load_picks_for_date(date_str: str) -> list[dict]:
    if not CLV_LOG.exists():
        return []
    rows = []
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date") == date_str:
                rows.append(dict(row))
    return rows


def _rewrite(date_str: str, updated: list[dict]) -> None:
    all_rows: list[dict] = []
    if CLV_LOG.exists():
        with open(CLV_LOG, newline="", encoding="utf-8") as f:
            all_rows = [r for r in csv.DictReader(f) if r.get("date") != date_str]
    all_rows.extend(updated)
    _atomic_write(all_rows)


def _atomic_write(rows: list[dict]) -> None:
    tmp = CLV_LOG.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CLV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, CLV_LOG)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def _existing_dates() -> set[str]:
    if not CLV_LOG.exists():
        return set()
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {r.get("date", "") for r in reader}


def _fetch_current_hr_odds() -> dict[str, int]:
    """Best available HR odds keyed by normalized player name (today's games only)."""
    if not config.ODDS_API_KEY:
        return {}
    try:
        # Filter to today's ET window — mirrors the identical logic in odds_api._get_events()
        # so CLV pulls the same games the main pipeline priced.
        now_utc = datetime.now(timezone.utc)
        now_et  = now_utc - timedelta(hours=4)   # EDT (Apr–Oct)
        et_midnight_utc = now_et.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=4)
        today_start = et_midnight_utc + timedelta(hours=9)   # ~5 AM ET
        today_end   = today_start + timedelta(hours=23)      # ~4 AM next-day ET
        resp = _SESSION.get(
            "https://api.the-odds-api.com/v4/sports/baseball_mlb/events",
            params={
                "apiKey":             config.ODDS_API_KEY,
                "dateFormat":         "iso",
                "commenceTimeFrom":   today_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commenceTimeTo":     today_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=12,
        )
        events = resp.json() if resp.status_code == 200 else []
        best: dict[str, int] = {}
        for event in events:
            r2 = _SESSION.get(
                f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{event['id']}/odds",
                params={"apiKey": config.ODDS_API_KEY, "regions": "us",
                        "markets": "batter_home_runs", "oddsFormat": "american"},
                timeout=12,
            )
            if r2.status_code != 200:
                continue
            for book in r2.json().get("bookmakers", []):
                for mkt in book.get("markets", []):
                    for o in mkt.get("outcomes", []):
                        if o.get("point") == 0.5:
                            name = _normalize(o.get("description", ""))
                            price = int(o.get("price", 0))
                            if name and (name not in best or price > best[name]):
                                best[name] = price
        return best
    except Exception as e:
        print(f"[clv] odds fetch failed: {e}")
        return {}
