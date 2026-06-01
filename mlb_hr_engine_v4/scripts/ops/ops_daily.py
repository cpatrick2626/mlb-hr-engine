"""
ops_daily.py — Daily operational orchestration — Session 26.

Runs all daily operational tasks in sequence:
  1. Settle yesterday's picks (MLB Stats API)
  2. Run data integrity check
  3. Run calibration drift monitor
  4. Capture closing lines / compute CLV (if odds available)
  5. Generate daily report → reports/daily_YYYY-MM-DD.txt

Usage:
  py -3.12 ops_daily.py                     # run full daily ops for yesterday
  py -3.12 ops_daily.py 2026-05-14          # run for specific date
  py -3.12 ops_daily.py --skip-settle       # skip settlement (already done)
  py -3.12 ops_daily.py --skip-clv          # skip CLV capture (no API key)
  py -3.12 ops_daily.py --report-only       # just generate report, skip external calls
  py -3.12 ops_daily.py --help

Run this script every morning, ideally via Windows Task Scheduler or a startup hook.
"""

import io
import sys
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def main():
    # ── Parse args ─────────────────────────────────────────────────────────────
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    skip_settle  = "--skip-settle" in args
    skip_clv     = "--skip-clv" in args
    report_only  = "--report-only" in args
    if report_only:
        skip_settle = skip_clv = True

    # Target date: yesterday by default
    date_args = [a for a in args if not a.startswith("--") and len(a) == 10 and a[4] == "-"]
    settle_date = date_args[0] if date_args else (date.today() - timedelta(days=1)).isoformat()

    run_ts  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today   = date.today().isoformat()

    # Capture report output in a buffer as well as printing
    buf = io.StringIO()

    def out(msg=""):
        print(msg)
        buf.write(msg + "\n")

    W = 76
    out(f"\n{'='*W}")
    out(f"  DAILY OPERATIONS — {run_ts}")
    out(f"  Settle date: {settle_date}")
    out(f"{'='*W}")

    # ── Phase 1: Settlement ────────────────────────────────────────────────────
    out(f"\n[PHASE 1] Settlement — {settle_date}")
    out(f"  {'─'*60}")
    settlement_result = None
    if skip_settle:
        out("  Skipped (--skip-settle)")
    else:
        settlement_result = _run_settlement(settle_date, out)

    # ── Phase 2: Data integrity ────────────────────────────────────────────────
    out(f"\n[PHASE 2] Data Integrity")
    out(f"  {'─'*60}")
    try:
        from tracking.data_integrity import run_integrity_check
        integrity = run_integrity_check(verbose=False)
        out(f"  {integrity['summary']}")
        errors   = [i for i in integrity["issues"] if i["level"] == "ERROR"]
        warnings = [i for i in integrity["issues"] if i["level"] == "WARNING"]
        if errors:
            out(f"\n  ERRORS ({len(errors)}):")
            for e in errors:
                out(f"    [ERROR] {e['message']}")
        if warnings:
            out(f"\n  WARNINGS ({len(warnings)}):")
            for w in warnings[:5]:
                out(f"    [WARN]  {w['message']}")
    except Exception as e:
        out(f"  [FAILED] {e}")

    # ── Phase 3: Drift monitor ────────────────────────────────────────────────
    out(f"\n[PHASE 3] Calibration Drift Monitor")
    out(f"  {'─'*60}")
    drift_result = None
    try:
        from tracking.drift_monitor import DriftMonitor
        dm = DriftMonitor()
        drift_result = dm.run()
        out(f"  {drift_result['summary']}")
        if drift_result["alerts"]:
            crit = [a for a in drift_result["alerts"] if a["level"] == "CRITICAL"]
            warn = [a for a in drift_result["alerts"] if a["level"] == "WARNING"]
            if crit:
                out(f"\n  CRITICAL ALERTS:")
                for a in crit:
                    out(f"    {a['message']}")
            if warn:
                out(f"\n  WARNING ALERTS:")
                for a in warn[:5]:
                    out(f"    {a['message']}")
        else:
            out(f"  No drift alerts. Calibration stable.")
    except Exception as e:
        out(f"  [FAILED] {e}")

    # ── Phase 4: CLV capture ──────────────────────────────────────────────────
    out(f"\n[PHASE 4] CLV Capture")
    out(f"  {'─'*60}")
    clv_result = {}
    if skip_clv:
        out("  Skipped (--skip-clv)")
    else:
        clv_result = _run_clv_capture(today, out)

    # ── Phase 5: CLV summary ──────────────────────────────────────────────────
    out(f"\n[PHASE 5] CLV Summary")
    out(f"  {'─'*60}")
    try:
        from tracking.clv import clv_summary, load_all
        clv_rows = load_all()
        cs = clv_summary(clv_rows)
        if cs["picks_with_clv"] == 0:
            out("  No CLV data yet. Run capture_closing_lines.py before game time.")
        else:
            out(f"  Picks with CLV : {cs['picks_with_clv']}")
            out(f"  Avg CLV        : {cs['avg_clv_pp']:+.3f}pp")
            if cs.get("avg_clv_pct_rel") is not None:
                out(f"  Avg CLV (rel)  : {cs['avg_clv_pct_rel']:+.2f}%")
            out(f"  Beats close    : {cs['pct_beats_close']:.1f}%")
            out(f"  Verdict        : {cs['verdict']}")
            out(f"  Detail         : {cs['verdict_detail']}")
    except Exception as e:
        out(f"  [FAILED] {e}")

    # ── Phase 6: ROI snapshot ─────────────────────────────────────────────────
    out(f"\n[PHASE 6] Live ROI Snapshot")
    out(f"  {'─'*60}")
    try:
        from tracking.pick_tracker import total_summary
        ts = total_summary()
        decided = ts["decided"]
        if decided == 0:
            out("  No settled picks with real bets yet.")
        else:
            out(f"  Settled picks  : {decided}")
            out(f"  Win rate       : {ts['win_rate']*100:.1f}%")
            out(f"  ROI            : {ts['roi']:+.1f}%")
            out(f"  Net P&L        : ${ts['profit']:+.2f}")
            out(f"  Total wagered  : ${ts['wagered']:.2f}")
    except Exception as e:
        out(f"  [FAILED] {e}")

    # ── Summary and alerts ────────────────────────────────────────────────────
    out(f"\n{'='*W}")
    out(f"  DAILY OPS COMPLETE — {run_ts}")

    # Determine overall status
    drift_status = drift_result.get("status", "UNKNOWN") if drift_result else "UNKNOWN"
    alerts_needed = []

    if drift_result and drift_result.get("n_crit", 0) > 0:
        alerts_needed.append(f"DRIFT CRITICAL: {drift_result['n_crit']} calibration alert(s)")
    if drift_result and drift_result.get("n_warn", 0) > 0:
        alerts_needed.append(f"DRIFT WARNING: {drift_result['n_warn']} calibration warning(s)")

    if alerts_needed:
        out(f"\n  ⚠ ACTION REQUIRED:")
        for a in alerts_needed:
            out(f"    • {a}")
    else:
        out(f"\n  ✓ No action required. All systems nominal.")

    out(f"\n  Next run: tomorrow morning (settle {today})")
    out(f"  CLV capture: run capture_closing_lines.py ~30 min before first pitch")
    out(f"{'='*W}\n")

    # ── Save report ────────────────────────────────────────────────────────────
    report_path = REPORTS_DIR / f"daily_{today}.txt"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print(f"  Report saved: {report_path}")
    except Exception as e:
        print(f"  [WARN] Could not save report: {e}")

    # ── Archive old reports (keep 90 days) ─────────────────────────────────────
    _cleanup_old_reports(REPORTS_DIR, keep_days=90)


# ── Phase runners ─────────────────────────────────────────────────────────────

def _run_settlement(settle_date: str, out) -> dict:
    """Run settlement for a specific date. Returns summary dict."""
    try:
        import importlib.util, importlib
        # Import settle_pick_tracker.py from root
        root = Path(__file__).parent
        spec = importlib.util.spec_from_file_location("settle_pick_tracker",
                                                        root / "settle_pick_tracker.py")
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        fields, rows = mod._load()
        result = mod.settle_date(settle_date, rows, fields, verbose=False)
        mod._save(fields, rows)

        n_new    = result.get("settled", 0)
        n_void   = result.get("dnp", 0)
        n_total  = sum(1 for r in rows if r.get("hr_result") in ("0", "1"))

        out(f"  Settled {n_new} new picks ({n_void} void/DNP)")
        out(f"  Cumulative settled: {n_total}")

        from tracking.pick_tracker import total_summary
        cum = total_summary()
        if cum.get("decided", 0) > 0:
            out(f"  Win rate: {cum.get('win_rate',0)*100:.1f}% | "
                f"ROI: {cum.get('roi',0):+.1f}% | "
                f"n={cum.get('decided',0)}")
        return result
    except Exception as e:
        out(f"  [FAILED] {e}")
        return {}


def _run_clv_capture(date_str: str, out) -> dict:
    """Capture closing lines for today. Returns summary dict."""
    try:
        import config
        if not config.ODDS_API_KEY:
            out("  Skipped — no ODDS_API_KEY configured")
            return {}

        from clients import odds_api as _odds_api
        from engine.vig import no_vig_prob_for_book
        from tracking import pick_tracker as _pt
        from tracking import line_snapshots as _snaps
        import unicodedata

        def _norm(name: str) -> str:
            return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()

        props_raw, source_label, quota = _odds_api.get_hr_odds_all_games()
        if not props_raw:
            out(f"  No odds available: {_odds_api.get_last_error()}")
            return {}

        out(f"  Fetched {len(props_raw)} odds from {source_label}")

        n_saved = _snaps.save_snapshots(props_raw, snapshot_type="closing", date_str=date_str)
        out(f"  Saved {n_saved} closing snapshots")

        best_odds: dict[str, tuple[int, str]] = {}
        for p in props_raw:
            name  = _norm(p.get("player_name", ""))
            price = p.get("price")
            book  = p.get("bookmaker", "")
            if not name or not price:
                continue
            try:
                price = int(price)
            except (ValueError, TypeError):
                continue
            if -100 < price < 100:
                continue
            if name not in best_odds or price > best_odds[name][0]:
                best_odds[name] = (price, book)

        _pt._migrate_schema()
        rows = _pt._load_all()
        date_picks = [r for r in rows if r.get("date") == date_str]

        n_updated = 0
        clv_vals  = []

        for row in rows:
            if row.get("date") != date_str:
                continue
            if row.get("close_odds"):
                continue
            pname = _norm(row.get("player_name", ""))
            if pname not in best_odds:
                continue

            close_am, close_book = best_odds[pname]
            sportsbook = row.get("sportsbook", "") or close_book
            try:
                close_nv = no_vig_prob_for_book(close_am, sportsbook)
            except Exception:
                continue

            row["close_odds"]       = str(close_am)
            row["close_no_vig_pct"] = f"{close_nv * 100:.3f}"
            n_updated += 1

            open_nv_str = row.get("open_no_vig_pct", "")
            try:
                open_nv = float(open_nv_str) / 100.0 if open_nv_str else 0.0
            except (ValueError, TypeError):
                open_nv = 0.0

            if open_nv <= 0:
                odds_str = row.get("best_odds") or row.get("american_odds") or ""
                try:
                    open_am = int(float(odds_str))
                    open_nv = no_vig_prob_for_book(open_am, sportsbook) if abs(open_am) >= 100 else 0.0
                    if open_nv > 0:
                        row["open_no_vig_pct"]  = f"{open_nv * 100:.3f}"
                        imp = _pt._american_to_implied(open_am)
                        row["open_implied_pct"] = f"{imp * 100:.3f}"
                except (ValueError, TypeError):
                    pass

            if open_nv > 0 and close_nv > 0:
                clv_pp  = (close_nv - open_nv) * 100
                clv_pp  = max(-100.0, min(100.0, clv_pp))
                clv_rel = (clv_pp / (open_nv * 100)) * 100
                row["clv_pp"]      = f"{clv_pp:.3f}"
                row["clv_pct_rel"] = f"{clv_rel:.2f}"
                clv_vals.append(clv_pp)

        if n_updated > 0:
            _pt._rewrite(rows)

        if clv_vals:
            avg = sum(clv_vals) / len(clv_vals)
            beats = sum(1 for v in clv_vals if v > 0)
            out(f"  CLV computed for {len(clv_vals)} picks | "
                f"Avg: {avg:+.3f}pp | Beats close: {beats}/{len(clv_vals)} "
                f"({beats/len(clv_vals)*100:.1f}%)")
        elif n_updated > 0:
            out(f"  Updated {n_updated} picks with closing odds (no opening odds for CLV)")
        else:
            out(f"  No picks matched current odds (picks may already have closing data)")

        if quota.get("remaining") is not None:
            out(f"  API quota remaining: {quota['remaining']}")

        return {"n_updated": n_updated, "n_clv": len(clv_vals)}
    except Exception as e:
        out(f"  [FAILED] {e}")
        return {}


def _cleanup_old_reports(reports_dir: Path, keep_days: int = 90) -> None:
    cutoff = (date.today() - timedelta(days=keep_days)).isoformat()
    for f in reports_dir.glob("daily_*.txt"):
        # Extract date from filename: daily_YYYY-MM-DD.txt
        stem = f.stem  # "daily_2026-01-01"
        if len(stem) >= 11:
            file_date = stem[-10:]
            if file_date < cutoff:
                try:
                    f.unlink()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
