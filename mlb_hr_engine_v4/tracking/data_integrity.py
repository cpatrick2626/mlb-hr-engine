"""
Data integrity checker — Session 26.

Validates pick_tracker.csv for common data quality issues:
  - duplicate picks
  - missing critical fields
  - stale unsettled picks
  - P&L computation accuracy
  - settlement consistency
  - CLV field completeness

Usage:
  from tracking.data_integrity import run_integrity_check
  report = run_integrity_check(verbose=True)
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional


LOG_PATH    = Path(__file__).parent / "pick_tracker.csv"
RESULTS_CSV = Path(__file__).parent / "results.csv"
CLV_LOG     = Path(__file__).parent / "clv_log.csv"


def run_integrity_check(verbose: bool = True) -> dict:
    """
    Run all integrity checks and return structured report.

    Returns dict with keys:
      issues        - list of issue dicts (level, category, message, count)
      summary       - human-readable summary string
      status        - "OK" | "WARNINGS" | "ERRORS"
      stats         - descriptive statistics
    """
    rows = _load_rows()
    issues: list[dict] = []

    stats = _compute_stats(rows)

    # ── Check 1: Duplicate picks ─────────────────────────────────────────────
    issues.extend(_check_duplicates(rows))

    # ── Check 2: Missing critical fields ─────────────────────────────────────
    issues.extend(_check_missing_fields(rows))

    # ── Check 3: Stale unsettled picks ────────────────────────────────────────
    issues.extend(_check_stale_picks(rows))

    # ── Check 4: P&L accuracy ─────────────────────────────────────────────────
    issues.extend(_check_pnl_accuracy(rows))

    # ── Check 5: Settlement completeness ──────────────────────────────────────
    issues.extend(_check_settlement_completeness(rows))

    # ── Check 6: CLV field completeness ──────────────────────────────────────
    issues.extend(_check_clv_completeness(rows))

    # ── Check 7: Probability range validity ──────────────────────────────────
    issues.extend(_check_prob_ranges(rows))

    # ── Check 8: American odds validity ──────────────────────────────────────
    issues.extend(_check_odds_validity(rows))

    # ── Status determination ──────────────────────────────────────────────────
    n_errors   = sum(1 for i in issues if i["level"] == "ERROR")
    n_warnings = sum(1 for i in issues if i["level"] == "WARNING")
    n_infos    = sum(1 for i in issues if i["level"] == "INFO")

    if n_errors > 0:
        status = "ERRORS"
    elif n_warnings > 0:
        status = "WARNINGS"
    else:
        status = "OK"

    summary = (
        f"Status: {status} | "
        f"{stats['total_rows']} rows ({stats['settled']} settled, "
        f"{stats['pending']} pending, {stats['void']} void) | "
        f"Issues: {n_errors} errors, {n_warnings} warnings, {n_infos} info"
    )

    if verbose:
        _print_report(summary, issues, stats)

    return {
        "issues":  issues,
        "summary": summary,
        "status":  status,
        "stats":   stats,
    }


# ── Individual checks ─────────────────────────────────────────────────────────

def _check_duplicates(rows: list[dict]) -> list[dict]:
    issues = []

    # Dedup by pick_id
    seen_ids: dict[str, int] = defaultdict(int)
    for r in rows:
        pid = r.get("pick_id", "")
        if pid:
            seen_ids[pid] += 1

    dup_ids = {k: v for k, v in seen_ids.items() if v > 1}
    if dup_ids:
        issues.append({
            "level":    "ERROR",
            "category": "duplicates",
            "message":  f"{len(dup_ids)} duplicate pick_ids found (total {sum(dup_ids.values())} affected rows)",
            "count":    len(dup_ids),
            "detail":   list(dup_ids.items())[:5],
        })

    # Dedup by (date, player, tab) for rows without pick_id
    seen_keys: dict[tuple, int] = defaultdict(int)
    for r in rows:
        if r.get("pick_id"):
            continue   # already checked by pick_id
        key = (r.get("date",""), r.get("player_name",""), r.get("source_tab",""))
        seen_keys[key] += 1

    dup_keys = {k: v for k, v in seen_keys.items() if v > 1}
    if dup_keys:
        issues.append({
            "level":    "WARNING",
            "category": "duplicates",
            "message":  f"{len(dup_keys)} potential duplicate picks (no pick_id, same date+player+tab)",
            "count":    len(dup_keys),
            "detail":   [f"{k[0]}/{k[1]}" for k in list(dup_keys.keys())[:5]],
        })

    return issues


def _check_missing_fields(rows: list[dict]) -> list[dict]:
    issues = []
    critical_fields = ["date", "player_name", "american_odds", "model_prob_pct"]
    important_fields = ["sportsbook", "best_odds", "market_prob_pct", "engine_version"]

    for field in critical_fields:
        missing = sum(1 for r in rows if not r.get(field))
        if missing > 0:
            issues.append({
                "level":    "ERROR",
                "category": "missing_fields",
                "message":  f"Critical field '{field}' missing in {missing}/{len(rows)} rows",
                "count":    missing,
            })

    for field in important_fields:
        missing = sum(1 for r in rows if not r.get(field))
        if missing > 0:
            pct = missing / len(rows) * 100 if rows else 0
            level = "WARNING" if pct > 50 else "INFO"
            issues.append({
                "level":    level,
                "category": "missing_fields",
                "message":  f"Field '{field}' missing in {missing}/{len(rows)} rows ({pct:.0f}%) — populate for full analytics",
                "count":    missing,
            })

    return issues


def _check_stale_picks(rows: list[dict]) -> list[dict]:
    issues = []
    cutoff_warn    = (date.today() - timedelta(days=3)).isoformat()
    cutoff_error   = (date.today() - timedelta(days=7)).isoformat()

    stale_warn  = [r for r in rows
                   if r.get("hr_result", "") == ""
                   and r.get("date", "") < cutoff_warn
                   and r.get("date", "") >= cutoff_error]
    stale_error = [r for r in rows
                   if r.get("hr_result", "") == ""
                   and r.get("date", "") < cutoff_error]

    if stale_error:
        issues.append({
            "level":    "ERROR",
            "category": "stale_picks",
            "message":  f"{len(stale_error)} picks from >7 days ago are still unsettled — run settle_pick_tracker.py or mark void",
            "count":    len(stale_error),
            "detail":   sorted(set(r.get("date","") for r in stale_error))[-5:],
        })
    if stale_warn:
        issues.append({
            "level":    "WARNING",
            "category": "stale_picks",
            "message":  f"{len(stale_warn)} picks from 3-7 days ago unsettled",
            "count":    len(stale_warn),
        })

    return issues


def _check_pnl_accuracy(rows: list[dict]) -> list[dict]:
    issues = []
    mismatch = 0
    mismatch_examples = []

    for r in rows:
        hr = r.get("hr_result", "")
        pl_stored = r.get("profit_loss", "")
        if hr not in ("0", "1") or not pl_stored:
            continue
        try:
            odds = int(float(r.get("american_odds", "0") or "0"))
            bet  = float(r.get("bet_dollars", "10") or "10")
            pl   = float(pl_stored)
        except (ValueError, TypeError):
            continue

        if odds == 0 or bet == 0:
            continue

        hit_hr = hr == "1"
        expected_pl = (bet * odds / 100 if odds > 0 else bet * 100 / abs(odds)) if hit_hr else -bet

        if abs(pl - expected_pl) > 0.05:  # 5 cent tolerance for rounding
            mismatch += 1
            if len(mismatch_examples) < 3:
                mismatch_examples.append(
                    f"{r.get('date','')} {r.get('player_name','')} "
                    f"odds={odds} bet={bet:.2f} stored={pl:.2f} expected={expected_pl:.2f}"
                )

    if mismatch > 0:
        issues.append({
            "level":    "WARNING",
            "category": "pnl_accuracy",
            "message":  f"{mismatch} rows have P&L mismatches vs expected from odds+bet_dollars",
            "count":    mismatch,
            "detail":   mismatch_examples,
        })

    return issues


def _check_settlement_completeness(rows: list[dict]) -> list[dict]:
    issues = []
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    two_days_ago = (date.today() - timedelta(days=2)).isoformat()

    # Check if yesterday's picks are settled
    yday_rows = [r for r in rows if r.get("date", "") == yesterday]
    yday_unsettled = [r for r in yday_rows if r.get("hr_result", "") == ""]
    if yday_unsettled:
        issues.append({
            "level":    "WARNING",
            "category": "settlement",
            "message":  f"{len(yday_unsettled)} picks from yesterday ({yesterday}) not yet settled — run: py -3.12 settle_pick_tracker.py {yesterday}",
            "count":    len(yday_unsettled),
        })

    return issues


def _check_clv_completeness(rows: list[dict]) -> list[dict]:
    issues = []
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if not settled:
        return issues

    # Check CLV fields
    has_open_implied = sum(1 for r in settled if r.get("open_implied_pct"))
    has_close_odds   = sum(1 for r in settled if r.get("close_odds"))
    has_clv_pp       = sum(1 for r in settled if r.get("clv_pp"))

    n = len(settled)

    if has_open_implied == 0:
        issues.append({
            "level":    "INFO",
            "category": "clv_completeness",
            "message":  f"No picks have open_implied_pct — CLV tracking not yet active for existing picks",
            "count":    n,
        })
    elif has_close_odds == 0:
        issues.append({
            "level":    "INFO",
            "category": "clv_completeness",
            "message":  f"{has_open_implied}/{n} picks have opening odds but 0 have closing lines — run capture_closing_lines.py before game time",
            "count":    n - has_open_implied,
        })
    elif has_clv_pp < n:
        pct = has_clv_pp / n * 100
        issues.append({
            "level":    "INFO",
            "category": "clv_completeness",
            "message":  f"CLV computed for {has_clv_pp}/{n} settled picks ({pct:.0f}%) — {n - has_clv_pp} missing closing lines",
            "count":    n - has_clv_pp,
        })

    return issues


def _check_prob_ranges(rows: list[dict]) -> list[dict]:
    issues = []
    out_of_range = []
    for r in rows:
        mp = r.get("model_prob_pct", "")
        if not mp:
            continue
        try:
            p = float(mp)
        except (ValueError, TypeError):
            continue
        if p < 0 or p > 100:
            out_of_range.append(f"{r.get('date','')} {r.get('player_name','')} prob={p:.2f}%")

    if out_of_range:
        issues.append({
            "level":    "ERROR",
            "category": "data_range",
            "message":  f"{len(out_of_range)} rows have model_prob_pct outside [0,100]",
            "count":    len(out_of_range),
            "detail":   out_of_range[:3],
        })

    return issues


def _check_odds_validity(rows: list[dict]) -> list[dict]:
    issues = []
    invalid = []
    for r in rows:
        odds_str = r.get("american_odds", "")
        if not odds_str:
            continue
        try:
            odds = int(float(odds_str))
        except (ValueError, TypeError):
            continue
        if odds != 0 and -100 < odds < 100:
            invalid.append(f"{r.get('date','')} {r.get('player_name','')} odds={odds}")

    if invalid:
        issues.append({
            "level":    "WARNING",
            "category": "odds_validity",
            "message":  f"{len(invalid)} rows have invalid American odds (-100 < odds < 100)",
            "count":    len(invalid),
            "detail":   invalid[:3],
        })

    return issues


# ── Stats ─────────────────────────────────────────────────────────────────────

def _compute_stats(rows: list[dict]) -> dict:
    total    = len(rows)
    settled  = sum(1 for r in rows if r.get("hr_result") in ("0", "1"))
    pending  = sum(1 for r in rows if r.get("hr_result", "") == "")
    void     = sum(1 for r in rows if r.get("hr_result") == "void")
    wins     = sum(1 for r in rows if r.get("hr_result") == "1")
    with_bet = sum(1 for r in rows
                   if r.get("hr_result") in ("0","1")
                   and _safe_float(r.get("bet_dollars")) > 0
                   and int(float(r.get("american_odds","0") or "0")) != 0)

    dates = sorted(set(r.get("date","") for r in rows if r.get("date","")))

    with_sportsbook     = sum(1 for r in rows if r.get("sportsbook",""))
    with_engine_version = sum(1 for r in rows if r.get("engine_version",""))
    with_clv            = sum(1 for r in rows if r.get("clv_pp",""))

    return {
        "total_rows":      total,
        "settled":         settled,
        "pending":         pending,
        "void":            void,
        "wins":            wins,
        "with_real_bet":   with_bet,
        "date_range":      f"{dates[0]} → {dates[-1]}" if len(dates) >= 2 else (dates[0] if dates else "—"),
        "n_dates":         len(dates),
        "with_sportsbook": with_sportsbook,
        "with_engine_ver": with_engine_version,
        "with_clv":        with_clv,
        "schema_pct_s25":  round(with_engine_version / total * 100, 1) if total else 0,
        "clv_pct":         round(with_clv / total * 100, 1) if total else 0,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(val, default=0.0) -> float:
    try:
        return float(val) if val and str(val).strip() not in ("","--") else default
    except (ValueError, TypeError):
        return default


def _load_rows() -> list[dict]:
    rows = []
    if LOG_PATH.exists():
        with open(LOG_PATH, newline="", encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    if RESULTS_CSV.exists():
        with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return list(rows)


def _print_report(summary: str, issues: list[dict], stats: dict) -> None:
    W = 80
    print(f"\n{'='*W}")
    print("  DATA INTEGRITY REPORT")
    print(f"{'='*W}")
    print(f"  {summary}")
    print()

    # Stats table
    print(f"  {'Metric':<30} {'Value'}")
    print(f"  {'-'*50}")
    print(f"  {'Total rows':<30} {stats['total_rows']}")
    print(f"  {'Settled':<30} {stats['settled']}")
    print(f"  {'Pending':<30} {stats['pending']}")
    print(f"  {'Void':<30} {stats['void']}")
    print(f"  {'With real bet':<30} {stats['with_real_bet']}")
    print(f"  {'Date range':<30} {stats['date_range']}")
    print(f"  {'Session 25 schema %':<30} {stats['schema_pct_s25']:.0f}%")
    print(f"  {'CLV data %':<30} {stats['clv_pct']:.0f}%")
    print()

    if not issues:
        print("  ✓ No integrity issues found.")
    else:
        for iss in sorted(issues, key=lambda x: {"ERROR":0,"WARNING":1,"INFO":2}.get(x["level"],3)):
            tag = f"[{iss['level']}]"
            print(f"  {tag:<12} {iss['message']}")
            if iss.get("detail"):
                for d in iss["detail"][:3]:
                    print(f"  {'':12}   → {d}")

    print(f"{'='*W}\n")
