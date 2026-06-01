"""
Closing Line Value (CLV) tracker — Session 26 full rebuild.

CLV is the primary long-run edge validation metric for sharp betting:
  + positive CLV consistently → model finds value before the market does
  - negative CLV consistently → market disagrees, model is mispriced

Formula (no-vig, more accurate than raw implied):
  open_no_vig  = no_vig_prob_for_book(best_odds, sportsbook)
  close_no_vig = no_vig_prob_for_book(close_odds, sportsbook)
  clv_pp       = (close_no_vig - open_no_vig) × 100
                 positive = close moved toward our pick = we got better price = sharp

  clv_pct_rel  = clv_pp / (open_no_vig × 100) × 100
                 relative CLV, independent of odds level

Workflow:
  1. Morning     : log_opening_lines(picks) → clv_log.csv + line_snapshots.py
  2. Pre-game    : fetch_and_compute_clv(date) → pulls closing lines, computes CLV
  3. Analysis    : clv_summary() / clv_by_segment() → segmented breakdowns
  4. Daily ops   : called automatically by ops_daily.py
"""

from __future__ import annotations

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

# Full CLV log schema (Session 26)
CLV_FIELDS = [
    "date",
    "player_name",
    "team",
    "sportsbook",
    "model_prob_pct",
    "barrel_pct",
    "ev_pct",
    "edge_pct",
    # Opening line
    "opening_american",
    "opening_implied_pct",    # raw vigged implied × 100
    "opening_no_vig_pct",     # no-vig probability × 100
    # Closing line
    "closing_american",
    "closing_implied_pct",
    "closing_no_vig_pct",
    # CLV
    "clv_pp",                 # (close_no_vig - open_no_vig) × 100; + = sharp
    "clv_pct_rel",            # clv_pp / open_no_vig × 100 (relative)
    "beats_close",            # "1" if clv_pp > 0 else "0"
    # Metadata
    "notes",
    "logged_at",
]


# ── Public API ────────────────────────────────────────────────────────────────

def log_opening_lines(picks: list[dict], date_str: Optional[str] = None) -> int:
    """
    Save picks' odds as opening lines (best odds at time of model run).
    Skips if picks for this date already logged.

    Args:
        picks: player dicts from pipeline; must have best_american / fanduel_american
        date_str: ISO date string (default: today)

    Returns:
        Count of new rows written.
    """
    date_str = date_str or date.today().isoformat()
    existing = _existing_dates()
    if date_str in existing:
        return 0

    rows = []
    for p in picks:
        american = _best_american_odds(p)
        if not american:
            continue
        book  = p.get("best_book") or p.get("sportsbook") or ""
        nvp   = _no_vig(american, book)
        imp   = _implied(american)
        ts    = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "date":                date_str,
            "player_name":         p.get("player_name", ""),
            "team":                p.get("team", ""),
            "sportsbook":          book,
            "model_prob_pct":      f"{p.get('model_prob', 0) * 100:.2f}",
            "barrel_pct":          f"{_f(p, 'barrel_pct'):.2f}",
            "ev_pct":              f"{_f(p, 'ev_pct'):.2f}",
            "edge_pct":            f"{_f(p, 'edge_pct'):.2f}",
            "opening_american":    american,
            "opening_implied_pct": f"{imp * 100:.3f}",
            "opening_no_vig_pct":  f"{nvp * 100:.3f}",
            "closing_american":    "",
            "closing_implied_pct": "",
            "closing_no_vig_pct":  "",
            "clv_pp":              "",
            "clv_pct_rel":         "",
            "beats_close":         "",
            "notes":               "",
            "logged_at":           ts,
        })

        # Also save to line_snapshots for full history
        try:
            from tracking.line_snapshots import save_snapshots
            save_snapshots([{
                "player_name": p.get("player_name", ""),
                "team":        p.get("team", ""),
                "price":       american,
                "bookmaker":   book,
                "game_id":     p.get("game_id", ""),
            }], snapshot_type="opening", date_str=date_str)
        except Exception:
            pass

    if rows:
        _append(rows)
    return len(rows)


def fetch_and_compute_clv(
    target_date: Optional[str] = None,
    snapshot_type: str = "closing",
) -> list[dict]:
    """
    Fetch current odds and compute CLV for picks on target_date.
    Updates clv_log.csv with closing odds + CLV fields.

    Args:
        target_date: ISO date (default: today)
        snapshot_type: "closing" | "pre_game" (label for this snapshot)

    Returns:
        List of updated CLV dicts for the date.
    """
    date_str = target_date or date.today().isoformat()
    picks = _load_picks_for_date(date_str)
    if not picks:
        return []

    # Fetch current odds from The Odds API
    live_odds = _fetch_current_hr_odds()
    if not live_odds:
        return picks   # return existing (possibly incomplete) rows unchanged

    # Save as snapshots
    try:
        from tracking.line_snapshots import save_snapshots
        snap_props = [{"player_name": name, "price": odds, "bookmaker": ""}
                      for name, odds in live_odds.items()]
        save_snapshots(snap_props, snapshot_type=snapshot_type, date_str=date_str)
    except Exception:
        pass

    updated = []
    for pick in picks:
        # If already has CLV computed and this is just an extra snapshot, don't overwrite
        if pick.get("clv_pp") and snapshot_type == "opening":
            updated.append(pick)
            continue

        name = pick.get("player_name", "")
        close_odds = live_odds.get(_norm(name))
        if close_odds is None:
            updated.append({**pick, "notes": pick.get("notes","") or "closing line unavailable"})
            continue

        book = pick.get("sportsbook", "")
        close_nvp  = _no_vig(close_odds, book)
        close_imp  = _implied(close_odds)

        # Opening no-vig (recompute from stored opening_implied if opening_no_vig absent)
        open_nvp_str = pick.get("opening_no_vig_pct", "")
        if open_nvp_str:
            try:
                open_nvp = float(open_nvp_str) / 100.0
            except (ValueError, TypeError):
                open_nvp = 0.0
        else:
            open_american = pick.get("opening_american")
            if open_american:
                try:
                    open_nvp = _no_vig(int(open_american), book)
                except (ValueError, TypeError):
                    open_nvp = 0.0
            else:
                open_nvp = 0.0

        if open_nvp <= 0.0:
            updated.append({**pick, "notes": "opening no-vig unavailable"})
            continue

        # CLV computation
        clv_pp  = (close_nvp - open_nvp) * 100          # + = we got better price
        clv_pp  = max(-100.0, min(100.0, clv_pp))        # sanity bounds
        clv_rel = (clv_pp / (open_nvp * 100)) * 100 if open_nvp > 0 else 0.0
        clv_rel = max(-200.0, min(200.0, clv_rel))

        updated.append({
            **pick,
            "closing_american":    close_odds,
            "closing_implied_pct": f"{close_imp * 100:.3f}",
            "closing_no_vig_pct":  f"{close_nvp * 100:.3f}",
            "clv_pp":              f"{clv_pp:.3f}",
            "clv_pct_rel":         f"{clv_rel:.2f}",
            "beats_close":         "1" if clv_pp > 0 else "0",
        })

    _rewrite(date_str, updated)
    return updated


def clv_summary(rows: Optional[list[dict]] = None) -> dict:
    """
    Aggregate CLV statistics across all picks with computed CLV.

    Args:
        rows: pre-loaded CLV log rows (default: loads clv_log.csv)

    Returns:
        dict with overall CLV stats and verdict.
    """
    if rows is None:
        rows = _load_all_clv()

    vals = []
    beats = 0
    for r in rows:
        raw = r.get("clv_pp", "")
        if not raw:
            continue
        try:
            v = float(raw)
            vals.append(v)
            if v > 0:
                beats += 1
        except ValueError:
            continue

    if not vals:
        return {
            "picks_with_clv":    0,
            "avg_clv_pp":        None,
            "avg_clv_pct_rel":   None,
            "pct_beats_close":   None,
            "verdict":           "NO_DATA",
            "verdict_detail":    "No CLV data available. Run capture_closing_lines.py before game time.",
        }

    n   = len(vals)
    avg = sum(vals) / n
    pct = beats / n * 100

    # Relative CLV (if available)
    rel_vals = []
    for r in rows:
        raw = r.get("clv_pct_rel", "")
        if raw:
            try:
                rel_vals.append(float(raw))
            except ValueError:
                pass
    avg_rel = sum(rel_vals) / len(rel_vals) if rel_vals else None

    # Verdict
    if avg > 1.0:
        verdict = "SHARP"
        detail  = f"Model consistently beats closing line by {avg:.2f}pp — strong long-run edge signal."
    elif avg > 0.0:
        verdict = "SLIGHTLY SHARP"
        detail  = f"Model marginally beats close by {avg:.2f}pp — directionally good, monitor as n grows."
    elif avg > -1.0:
        verdict = "NEUTRAL"
        detail  = f"CLV near zero ({avg:.2f}pp) — model and market roughly agree."
    else:
        verdict = "SOFT"
        detail  = f"Model behind closing line by {abs(avg):.2f}pp — market disagrees or edge is shrinking."

    return {
        "picks_with_clv":  n,
        "avg_clv_pp":      round(avg, 3),
        "avg_clv_pct_rel": round(avg_rel, 2) if avg_rel is not None else None,
        "pct_beats_close": round(pct, 1),
        "verdict":         verdict,
        "verdict_detail":  detail,
    }


def clv_by_segment(segment_fn, rows: Optional[list[dict]] = None) -> list[dict]:
    """
    Compute CLV by segment using a key function.

    Args:
        segment_fn: callable(row) → segment_key (str) or None to skip
        rows: pre-loaded CLV rows (default: loads clv_log.csv)

    Returns:
        List of dicts: {segment, n, avg_clv_pp, avg_clv_pct_rel, pct_beats_close}
        sorted by n descending.
    """
    if rows is None:
        rows = _load_all_clv()

    agg: dict[str, list[float]] = {}
    for r in rows:
        raw = r.get("clv_pp", "")
        if not raw:
            continue
        try:
            clv = float(raw)
        except ValueError:
            continue
        key = segment_fn(r)
        if key is None:
            continue
        if key not in agg:
            agg[key] = []
        agg[key].append(clv)

    result = []
    for key, vals in agg.items():
        n     = len(vals)
        avg   = sum(vals) / n
        beats = sum(1 for v in vals if v > 0)
        result.append({
            "segment":        key,
            "n":              n,
            "avg_clv_pp":     round(avg, 3),
            "pct_beats_close":round(beats / n * 100, 1),
        })
    return sorted(result, key=lambda x: x["n"], reverse=True)


def clv_by_barrel(rows: Optional[list[dict]] = None) -> list[dict]:
    """CLV broken down by barrel tier."""
    def fn(r):
        try:
            b = float(r.get("barrel_pct", 0) or 0)
        except (ValueError, TypeError):
            return None
        if b < 4:    return "barrel<4%"
        if b < 6:    return "barrel 4-6%"
        if b < 8:    return "barrel 6-8%"
        if b < 10:   return "barrel 8-10%"
        if b < 12:   return "barrel 10-12%"
        return "barrel 12%+"
    return clv_by_segment(fn, rows)


def clv_by_book(rows: Optional[list[dict]] = None) -> list[dict]:
    """CLV broken down by sportsbook."""
    def fn(r):
        b = r.get("sportsbook", "").strip()
        return b if b else "unknown"
    return clv_by_segment(fn, rows)


def clv_by_ev_range(rows: Optional[list[dict]] = None) -> list[dict]:
    """CLV broken down by EV% range."""
    def fn(r):
        try:
            ev = float(r.get("ev_pct", 0) or 0)
        except (ValueError, TypeError):
            return None
        if ev < 2:    return "EV<2%"
        if ev < 4:    return "EV 2-4%"
        if ev < 6:    return "EV 4-6%"
        if ev < 10:   return "EV 6-10%"
        return "EV 10%+"
    return clv_by_segment(fn, rows)


def clv_by_odds_range(rows: Optional[list[dict]] = None) -> list[dict]:
    """CLV broken down by opening American odds."""
    def fn(r):
        try:
            odds = int(float(r.get("opening_american", 0) or 0))
        except (ValueError, TypeError):
            return None
        if odds <= 0:   return None
        if odds < 300:  return "+100-299"
        if odds < 500:  return "+300-499"
        if odds < 700:  return "+500-699"
        if odds < 1000: return "+700-999"
        return "+1000+"
    return clv_by_segment(fn, rows)


def print_clv_report(rows: Optional[list[dict]] = None) -> None:
    """Print formatted CLV summary to stdout."""
    if rows is None:
        rows = _load_all_clv()

    summary = clv_summary(rows)
    n = summary["picks_with_clv"]

    print(f"\n{'='*70}")
    print("  CLOSING LINE VALUE (CLV) REPORT")
    print(f"{'='*70}")

    if n == 0:
        print(f"  {summary['verdict_detail']}")
        print(f"{'='*70}\n")
        return

    print(f"  Picks with CLV:  {n}")
    print(f"  Avg CLV:         {summary['avg_clv_pp']:+.3f} pp")
    if summary['avg_clv_pct_rel'] is not None:
        print(f"  Avg CLV (rel):   {summary['avg_clv_pct_rel']:+.2f}%")
    print(f"  Beats close:     {summary['pct_beats_close']:.1f}%  (>50% = sharp)")
    print(f"  Verdict:         {summary['verdict']}")
    print(f"  Detail:          {summary['verdict_detail']}")

    # Barrel breakdown
    barrel = clv_by_barrel(rows)
    if barrel:
        print(f"\n  By Barrel Tier:")
        print(f"  {'Tier':<20} {'n':>5} {'Avg CLV':>10} {'Beats%':>8}")
        print(f"  {'-'*46}")
        for s in barrel:
            flag = " ← target" if "10%" in s["segment"] or "12%" in s["segment"] else ""
            print(f"  {s['segment']:<20} {s['n']:>5} {s['avg_clv_pp']:>+10.3f} {s['pct_beats_close']:>7.1f}%{flag}")

    # Book breakdown
    book = clv_by_book(rows)
    if book and any(s["segment"] != "unknown" for s in book):
        print(f"\n  By Sportsbook:")
        print(f"  {'Book':<20} {'n':>5} {'Avg CLV':>10} {'Beats%':>8}")
        print(f"  {'-'*46}")
        for s in book:
            if s["n"] >= 5:
                print(f"  {s['segment']:<20} {s['n']:>5} {s['avg_clv_pp']:>+10.3f} {s['pct_beats_close']:>7.1f}%")

    print(f"{'='*70}\n")


def load_all() -> list[dict]:
    """Public accessor for clv_log.csv rows."""
    return _load_all_clv()


# ── Internal ──────────────────────────────────────────────────────────────────

def _no_vig(american: int, book: str = "") -> float:
    """No-vig probability using book-specific vig model."""
    try:
        from engine.vig import no_vig_prob_for_book
        return no_vig_prob_for_book(american, book)
    except ImportError:
        imp = _implied(american)
        return imp / (1.0 + config.VIG_FACTOR)


def _implied(american: int) -> float:
    if american > 0:
        return 100.0 / (american + 100.0)
    return abs(american) / (abs(american) + 100.0)


def _best_american_odds(player: dict) -> Optional[int]:
    """Extract best American odds from player dict."""
    for key in ("best_american", "fanduel_american", "draftkings_american",
                "betrivers_american", "betonlineag_american"):
        v = player.get(key)
        if v:
            try:
                odds = int(v)
                if odds >= 100 or odds <= -100:
                    return odds
            except (ValueError, TypeError):
                pass
    return None


def _f(player: dict, key: str, default: float = 0.0) -> float:
    try:
        v = player.get(key)
        return float(str(v).replace("%","").strip()) if v is not None else default
    except (ValueError, TypeError):
        return default


def _norm(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()


def _load_all_clv() -> list[dict]:
    if not CLV_LOG.exists():
        return []
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_picks_for_date(date_str: str) -> list[dict]:
    return [r for r in _load_all_clv() if r.get("date") == date_str]


def _existing_dates() -> set[str]:
    if not CLV_LOG.exists():
        return set()
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        return {r.get("date", "") for r in csv.DictReader(f)}


def _append(rows: list[dict]) -> None:
    existing = _load_all_clv()
    _atomic_write(existing + rows)


def _rewrite(date_str: str, updated: list[dict]) -> None:
    other = [r for r in _load_all_clv() if r.get("date") != date_str]
    _atomic_write(other + updated)


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


def _fetch_current_hr_odds() -> dict[str, int]:
    """Best available HR Over odds keyed by normalized player name."""
    if not config.ODDS_API_KEY:
        return {}
    try:
        now_utc  = datetime.now(timezone.utc)
        now_et   = now_utc - timedelta(hours=4)
        midnight_utc = now_et.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=4)
        today_start  = midnight_utc + timedelta(hours=9)
        today_end    = today_start  + timedelta(hours=23)

        resp = _SESSION.get(
            "https://api.the-odds-api.com/v4/sports/baseball_mlb/events",
            params={
                "apiKey":           config.ODDS_API_KEY,
                "dateFormat":       "iso",
                "commenceTimeFrom": today_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commenceTimeTo":   today_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=12,
        )
        if resp.status_code != 200:
            print(f"[clv] events fetch failed: {resp.status_code}")
            return {}

        events = resp.json()
        best: dict[str, int] = {}

        for event in events:
            r2 = _SESSION.get(
                f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{event['id']}/odds",
                params={
                    "apiKey":      config.ODDS_API_KEY,
                    "regions":     "us",
                    "markets":     "batter_home_runs",
                    "oddsFormat":  "american",
                },
                timeout=12,
            )
            if r2.status_code != 200:
                continue
            for book in r2.json().get("bookmakers", []):
                for mkt in book.get("markets", []):
                    for o in mkt.get("outcomes", []):
                        if o.get("point") != 0.5:
                            continue
                        if o.get("name", "") == "Under":
                            continue
                        name  = _norm(o.get("description", ""))
                        price = o.get("price")
                        if not name or not price:
                            continue
                        try:
                            price = int(price)
                        except (ValueError, TypeError):
                            continue
                        if -100 < price < 100:
                            continue
                        if name not in best or price > best[name]:
                            best[name] = price
        return best
    except Exception as e:
        print(f"[clv] fetch failed: {e}")
        return {}
