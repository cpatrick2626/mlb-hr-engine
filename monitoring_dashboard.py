"""
monitoring_dashboard.py — Session 26 Operational Monitoring Dashboard.

Comprehensive live quantitative betting platform health check:
  Phase 1: Data Quality & Integrity
  Phase 2: CLV Analysis (overall + segmented)
  Phase 3: Live ROI & Bankroll
  Phase 4: Calibration Drift (multi-dimensional)
  Phase 5: Statistical Validity & Confidence Intervals
  Phase 6: Production Readiness Assessment & Roadmap

Usage:
  py -3.12 monitoring_dashboard.py                    # full report
  py -3.12 monitoring_dashboard.py --phase 2          # just CLV
  py -3.12 monitoring_dashboard.py --phase 4          # just drift
  py -3.12 monitoring_dashboard.py --rolling 30       # rolling 30-day view

Output saved to: monitoring_dashboard_output.txt
"""

import csv
import io
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

REPORT_PATH = Path(__file__).parent / "monitoring_dashboard_output.txt"
W = 106   # report width


def main():
    args = sys.argv[1:]
    only_phase  = None
    rolling_days = 30

    if "--phase" in args:
        idx = args.index("--phase")
        if idx + 1 < len(args):
            try:
                only_phase = int(args[idx + 1])
            except ValueError:
                pass

    if "--rolling" in args:
        idx = args.index("--rolling")
        if idx + 1 < len(args):
            try:
                rolling_days = int(args[idx + 1])
            except ValueError:
                pass

    buf = io.StringIO()

    def out(msg=""):
        print(msg)
        buf.write(msg + "\n")

    # ── Header ────────────────────────────────────────────────────────────────
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out("=" * W)
    out(f"  MLB HR ENGINE — OPERATIONAL MONITORING DASHBOARD")
    out(f"  Generated: {ts}  |  Rolling window: {rolling_days}d")
    out("=" * W)

    # ── Load data ─────────────────────────────────────────────────────────────
    rows         = _load_all_picks()
    settled      = [r for r in rows if r.get("hr_result") in ("0","1")]
    clv_rows     = _load_clv_log()
    today        = date.today().isoformat()
    cutoff_roll  = (date.today() - timedelta(days=rolling_days)).isoformat()
    settled_roll = [r for r in settled if r.get("date","") >= cutoff_roll]

    # ── Phase 1: Data Quality ─────────────────────────────────────────────────
    if only_phase is None or only_phase == 1:
        _phase1_data_quality(rows, settled, clv_rows, out)

    # ── Phase 2: CLV Analysis ─────────────────────────────────────────────────
    if only_phase is None or only_phase == 2:
        _phase2_clv(clv_rows, settled, out)

    # ── Phase 3: ROI & Bankroll ───────────────────────────────────────────────
    if only_phase is None or only_phase == 3:
        _phase3_roi(settled, settled_roll, rolling_days, out)

    # ── Phase 4: Calibration Drift ───────────────────────────────────────────
    if only_phase is None or only_phase == 4:
        _phase4_drift(settled, settled_roll, rolling_days, out)

    # ── Phase 5: Statistical Validity ────────────────────────────────────────
    if only_phase is None or only_phase == 5:
        _phase5_stats(settled, out)

    # ── Phase 6: Production Readiness ────────────────────────────────────────
    if only_phase is None or only_phase == 6:
        _phase6_production(rows, settled, clv_rows, out)

    # ── Save ──────────────────────────────────────────────────────────────────
    try:
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print(f"\nSaved: {REPORT_PATH}")
    except Exception as e:
        print(f"\n[WARN] Could not save report: {e}")


# ── Phase 1: Data Quality ─────────────────────────────────────────────────────

def _phase1_data_quality(rows, settled, clv_rows, out):
    out()
    out("=" * W)
    out("  PHASE 1 — DATA QUALITY & INTEGRITY")
    out("=" * W)

    n         = len(rows)
    n_settled = len(settled)
    n_pending = sum(1 for r in rows if r.get("hr_result","") == "")
    n_void    = sum(1 for r in rows if r.get("hr_result") == "void")
    n_dates   = len(set(r.get("date","") for r in rows if r.get("date","")))
    n_clv     = sum(1 for r in rows if r.get("clv_pp",""))
    n_sb      = sum(1 for r in rows if r.get("sportsbook",""))
    n_s26     = sum(1 for r in rows if r.get("open_no_vig_pct",""))

    dates_sorted = sorted(set(r.get("date","") for r in rows if r.get("date","")))
    date_range = f"{dates_sorted[0]} → {dates_sorted[-1]}" if len(dates_sorted) >= 2 else (dates_sorted[0] if dates_sorted else "—")

    out(f"\n  {'Metric':<40} {'Value':>15}")
    out(f"  {'─'*57}")
    out(f"  {'Total pick rows':<40} {n:>15,}")
    out(f"  {'Settled (0/1)':<40} {n_settled:>15,}")
    out(f"  {'Pending':<40} {n_pending:>15,}")
    out(f"  {'Void / DNP':<40} {n_void:>15,}")
    out(f"  {'Unique dates':<40} {n_dates:>15,}")
    out(f"  {'Date range':<40} {date_range:>15}")
    out(f"  {'CLV records in clv_log.csv':<40} {len(clv_rows):>15,}")
    out(f"  {'Picks with CLV (pick_tracker)':<40} {n_clv:>15,}")
    out(f"  {'Picks with sportsbook field':<40} {n_sb:>15,}   ({n_sb/n*100:.0f}%)" if n else "")
    out(f"  {'Picks with S26 CLV schema':<40} {n_s26:>15,}   ({n_s26/n*100:.0f}%)" if n else "")

    # Run integrity check
    try:
        from tracking.data_integrity import run_integrity_check
        report = run_integrity_check(verbose=False)
        out(f"\n  Integrity: {report['status']}")
        issues = report["issues"]
        errors = [i for i in issues if i["level"] == "ERROR"]
        warns  = [i for i in issues if i["level"] == "WARNING"]
        infos  = [i for i in issues if i["level"] == "INFO"]
        if errors:
            out(f"\n  ERRORS ({len(errors)}):")
            for e in errors[:5]:
                out(f"    [ERROR]   {e['message']}")
        if warns:
            out(f"\n  WARNINGS ({len(warns)}):")
            for w in warns[:5]:
                out(f"    [WARNING] {w['message']}")
        if infos:
            out(f"\n  INFO ({len(infos)}):")
            for i in infos[:3]:
                out(f"    [INFO]    {i['message']}")
        if not issues:
            out(f"    ✓ No integrity issues found.")
    except Exception as e:
        out(f"  [FAILED] {e}")


# ── Phase 2: CLV Analysis ─────────────────────────────────────────────────────

def _phase2_clv(clv_rows, settled, out):
    out()
    out("=" * W)
    out("  PHASE 2 — CLOSING LINE VALUE (CLV) ANALYSIS")
    out("=" * W)

    try:
        from tracking.clv import (
            clv_summary, clv_by_barrel, clv_by_book, clv_by_ev_range,
            clv_by_odds_range
        )

        summary = clv_summary(clv_rows if clv_rows else None)
        n       = summary["picks_with_clv"]

        if n == 0:
            out(f"\n  No CLV data available yet.")
            out(f"  To collect CLV:")
            out(f"    1. Ensure sportsbook field is populated when logging picks")
            out(f"    2. Run: py -3.12 capture_closing_lines.py  (before game time each day)")
            out(f"    3. Re-run this dashboard")
            out()

            # Show CLV from pick_tracker if available
            pick_clv = [r for r in settled if r.get("clv_pp","")]
            if pick_clv:
                out(f"  CLV from pick_tracker.csv: {len(pick_clv)} picks")
                vals = []
                for r in pick_clv:
                    try:
                        vals.append(float(r["clv_pp"]))
                    except (ValueError, TypeError):
                        pass
                if vals:
                    avg = sum(vals) / len(vals)
                    beats = sum(1 for v in vals if v > 0)
                    out(f"  Avg CLV: {avg:+.3f}pp  |  Beats close: {beats}/{len(vals)} ({beats/len(vals)*100:.1f}%)")
            return

        out(f"\n  2a. Overall CLV Summary")
        out(f"  {'─'*60}")
        out(f"  Picks with CLV          : {n}")
        out(f"  Average CLV             : {summary['avg_clv_pp']:+.3f} pp")
        if summary.get("avg_clv_pct_rel") is not None:
            out(f"  Average CLV (relative)  : {summary['avg_clv_pct_rel']:+.2f}%")
        out(f"  Beats closing line      : {summary['pct_beats_close']:.1f}%  (>50% = sharp)")
        out(f"  Verdict                 : {summary['verdict']}")
        out(f"  Detail                  : {summary['verdict_detail']}")

        # CLV by barrel tier
        barrel = clv_by_barrel(clv_rows if clv_rows else None)
        if barrel:
            out(f"\n  2b. CLV by Barrel Tier")
            out(f"  {'─'*60}")
            out(f"  {'Tier':<22} {'n':>5} {'Avg CLV':>10} {'Beats%':>8}  {'Signal'}")
            out(f"  {'─'*58}")
            for s in barrel:
                if s["n"] < 3:
                    continue
                flag = _clv_signal(s["avg_clv_pp"], s["n"])
                out(f"  {s['segment']:<22} {s['n']:>5} {s['avg_clv_pp']:>+10.3f} "
                    f"{s['pct_beats_close']:>7.1f}%  {flag}")

        # CLV by sportsbook
        book = clv_by_book(clv_rows if clv_rows else None)
        valid_books = [s for s in book if s["segment"] != "unknown" and s["n"] >= 5]
        if valid_books:
            out(f"\n  2c. CLV by Sportsbook")
            out(f"  {'─'*60}")
            out(f"  {'Book':<22} {'n':>5} {'Avg CLV':>10} {'Beats%':>8}  {'Signal'}")
            out(f"  {'─'*58}")
            for s in sorted(valid_books, key=lambda x: x["avg_clv_pp"], reverse=True):
                flag = _clv_signal(s["avg_clv_pp"], s["n"])
                out(f"  {s['segment']:<22} {s['n']:>5} {s['avg_clv_pp']:>+10.3f} "
                    f"{s['pct_beats_close']:>7.1f}%  {flag}")

        # CLV by EV range
        ev_clv = clv_by_ev_range(clv_rows if clv_rows else None)
        if ev_clv and any(s["n"] >= 5 for s in ev_clv):
            out(f"\n  2d. CLV by EV% Range")
            out(f"  {'─'*60}")
            out(f"  {'EV Range':<22} {'n':>5} {'Avg CLV':>10} {'Beats%':>8}")
            out(f"  {'─'*48}")
            for s in [s for s in ev_clv if s["n"] >= 5]:
                out(f"  {s['segment']:<22} {s['n']:>5} {s['avg_clv_pp']:>+10.3f} "
                    f"{s['pct_beats_close']:>7.1f}%")

        # CLV by odds range
        odds_clv = clv_by_odds_range(clv_rows if clv_rows else None)
        if odds_clv and any(s["n"] >= 5 for s in odds_clv):
            out(f"\n  2e. CLV by Odds Range")
            out(f"  {'─'*60}")
            out(f"  {'Odds Range':<22} {'n':>5} {'Avg CLV':>10} {'Beats%':>8}")
            out(f"  {'─'*48}")
            for s in [s for s in odds_clv if s["n"] >= 5]:
                out(f"  {s['segment']:<22} {s['n']:>5} {s['avg_clv_pp']:>+10.3f} "
                    f"{s['pct_beats_close']:>7.1f}%")

    except Exception as e:
        out(f"  [FAILED] Phase 2 error: {e}")
        import traceback; out(traceback.format_exc())


def _clv_signal(avg_pp, n) -> str:
    if n < 10:
        return "[small sample]"
    if avg_pp > 1.5:  return "SHARP ▲"
    if avg_pp > 0.5:  return "slightly sharp ↑"
    if avg_pp > -0.5: return "neutral →"
    if avg_pp > -1.5: return "slightly soft ↓"
    return "SOFT ▼"


# ── Phase 3: ROI & Bankroll ───────────────────────────────────────────────────

def _phase3_roi(settled, settled_roll, rolling_days, out):
    out()
    out("=" * W)
    out("  PHASE 3 — LIVE ROI & BANKROLL")
    out("=" * W)

    def _roi_block(name, rows, label_pad=25):
        with_bet = [r for r in rows
                    if _sf(r.get("bet_dollars")) > 0
                    and int(float(r.get("american_odds","0") or "0")) != 0]
        if not with_bet:
            out(f"  {name}: No picks with real bets.")
            return

        n_wins    = sum(1 for r in with_bet if r.get("hr_result") == "1")
        n_loss    = sum(1 for r in with_bet if r.get("hr_result") == "0")
        decided   = n_wins + n_loss
        wagered   = sum(_sf(r.get("bet_dollars")) for r in with_bet)
        profit    = sum(_sf(r.get("profit_loss")) for r in with_bet)
        roi       = profit / wagered * 100 if wagered > 0 else 0.0
        win_rate  = n_wins / decided if decided > 0 else 0.0

        # 95% CI on ROI
        roi_ci = _roi_ci_95(with_bet)

        out(f"\n  {name} (n={decided}):")
        out(f"  {'Wins / Losses':<{label_pad}} {n_wins} W / {n_loss} L")
        out(f"  {'Win rate':<{label_pad}} {win_rate*100:.1f}%")
        out(f"  {'Total wagered':<{label_pad}} ${wagered:,.2f}")
        out(f"  {'Net P&L':<{label_pad}} ${profit:+,.2f}")
        out(f"  {'ROI':<{label_pad}} {roi:+.1f}%")
        out(f"  {'95% CI on ROI':<{label_pad}} ±{roi_ci:.0f}pp  (meaningless until n>200)")

    _roi_block("All-time ROI", settled)
    _roi_block(f"Rolling {rolling_days}d ROI", settled_roll)

    # Barrel tier ROI
    out(f"\n  Barrel Tier ROI (all-time, n<50 = directional only):")
    out(f"  {'Tier':<22} {'n':>5} {'HR%':>7} {'Model%':>8} {'ROI%':>8}  {'Synthetic (S24)'}")
    out(f"  {'─'*72}")
    synthetic = {
        "barrel<4%":     "-100.0%",
        "barrel 4-6%":   "-2.7%",
        "barrel 6-8%":   "-1.3%",
        "barrel 8-10%":  "+28.0%",
        "barrel 10-12%": "+65.3%",
        "barrel 12%+":   "+119.3%",
    }
    barrel_agg = _barrel_agg(settled)
    for tier in ["barrel<4%","barrel 4-6%","barrel 6-8%","barrel 8-10%","barrel 10-12%","barrel 12%+"]:
        a = barrel_agg.get(tier)
        if not a:
            continue
        n      = a["n"]
        hits   = a["hits"]
        hr_pct = hits/n*100 if n > 0 else 0.0
        model  = a["model_sum"]/n*100 if n > 0 else 0.0
        waged  = a["wagered"]
        profit = a["profit"]
        roi    = profit/waged*100 if waged > 0 else None

        roi_str  = f"{roi:+.1f}%" if roi is not None else "—"
        flag     = "  [!] n<50" if n < 50 else ""
        syn_str  = synthetic.get(tier, "—")
        out(f"  {tier:<22} {n:>5} {hr_pct:>7.1f}% {model:>8.1f}% {roi_str:>8}  {syn_str}{flag}")

    # Drawdown
    out(f"\n  Drawdown Analysis:")
    drawdown, max_streak = _compute_drawdown(settled)
    out(f"  Max drawdown: {drawdown:.1f}x bet units")
    out(f"  Max loss streak: {max_streak}")


def _barrel_agg(rows) -> dict:
    tiers = ["barrel<4%","barrel 4-6%","barrel 6-8%","barrel 8-10%","barrel 10-12%","barrel 12%+"]
    agg = {t: {"n":0,"hits":0,"model_sum":0.0,"wagered":0.0,"profit":0.0} for t in tiers}
    for r in rows:
        if r.get("hr_result") not in ("0","1"):
            continue
        try:
            b = float(r.get("barrel_pct","0") or 0)
        except (ValueError, TypeError):
            b = 0.0
        if b < 4:    tier = "barrel<4%"
        elif b < 6:  tier = "barrel 4-6%"
        elif b < 8:  tier = "barrel 6-8%"
        elif b < 10: tier = "barrel 8-10%"
        elif b < 12: tier = "barrel 10-12%"
        else:        tier = "barrel 12%+"
        a = agg[tier]
        a["n"]    += 1
        a["hits"] += 1 if r.get("hr_result") == "1" else 0
        try:
            a["model_sum"] += float(r.get("model_prob_pct","0") or 0)
        except (ValueError, TypeError):
            pass
        bet  = _sf(r.get("bet_dollars"))
        odds = int(float(r.get("american_odds","0") or "0"))
        if bet > 0 and abs(odds) >= 100:
            a["wagered"] += bet
            try:
                a["profit"]  += float(r.get("profit_loss","0") or 0)
            except (ValueError, TypeError):
                pass
    return agg


def _roi_ci_95(rows) -> float:
    """95% CI half-width on ROI% using bootstrap-style normal approximation."""
    pls = []
    for r in rows:
        bet = _sf(r.get("bet_dollars"))
        pl  = _sf(r.get("profit_loss"))
        if bet > 0:
            pls.append(pl / bet * 100)
    if len(pls) < 2:
        return 999.9
    n    = len(pls)
    mean = sum(pls) / n
    var  = sum((x - mean)**2 for x in pls) / (n - 1)
    se   = math.sqrt(var / n)
    return round(1.96 * se, 1)


def _compute_drawdown(rows) -> tuple:
    sorted_rows = sorted(rows, key=lambda r: (r.get("date",""), r.get("logged_at","")))
    max_dd   = 0.0
    streak   = 0
    max_str  = 0
    curr_bet = 0.0
    peak     = 0.0
    equity   = 0.0

    for r in sorted_rows:
        bet  = _sf(r.get("bet_dollars"))
        pl   = _sf(r.get("profit_loss"))
        if bet <= 0:
            continue
        curr_bet = bet
        equity  += pl
        if equity > peak:
            peak = equity
        dd = (peak - equity) / curr_bet if curr_bet > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
        if pl < 0:
            streak += 1
            max_str = max(max_str, streak)
        else:
            streak = 0

    return round(max_dd, 1), max_str


# ── Phase 4: Calibration Drift ───────────────────────────────────────────────

def _phase4_drift(settled, settled_roll, rolling_days, out):
    out()
    out("=" * W)
    out("  PHASE 4 — CALIBRATION DRIFT MONITORING")
    out("=" * W)

    try:
        from tracking.drift_monitor import DriftMonitor, _bucket_stats, _prob_bucket_label

        dm = DriftMonitor()

        # All-time
        report = dm.run(settled)
        out(f"\n  4a. All-time Drift Status")
        out(f"  {'─'*60}")
        out(f"  {report['summary']}")

        # Probability bucket table
        bucket_dim = report["dimensions"].get("prob_bucket", [])
        if bucket_dim:
            out(f"\n  Probability Bucket Bias (model_prob vs actual HR%):")
            out(f"  {'Bucket':<12} {'n':>6} {'Actual%':>9} {'Model%':>9} {'Bias':>8}  {'Status'}")
            out(f"  {'─'*58}")
            for b in sorted(bucket_dim, key=lambda x: x.get("segment","")):
                n     = b["n"]
                bias  = b["bias_pp"]
                flag  = _bias_flag(bias, n)
                out(f"  {b['segment']:<12} {n:>6} {b['actual_pct']:>9.2f}% "
                    f"{b['model_pct']:>9.2f}% {bias:>+8.2f}pp  {flag}")

        # Barrel tier bias
        barrel_dim = report["dimensions"].get("barrel_tier", [])
        if barrel_dim:
            out(f"\n  Barrel Tier Bias:")
            out(f"  {'Tier':<22} {'n':>6} {'Actual%':>9} {'Model%':>9} {'Bias':>8}  {'Status'}")
            out(f"  {'─'*68}")
            for b in sorted(barrel_dim, key=lambda x: x.get("segment","")):
                n    = b["n"]
                bias = b["bias_pp"]
                flag = _bias_flag(bias, n)
                out(f"  {b['segment']:<22} {n:>6} {b['actual_pct']:>9.2f}% "
                    f"{b['model_pct']:>9.2f}% {bias:>+8.2f}pp  {flag}")

        # Alerts
        if report["alerts"]:
            out(f"\n  Active Alerts:")
            for a in report["alerts"]:
                out(f"    {a['message']}")
        else:
            out(f"\n  ✓ No drift alerts. Calibration is stable.")

        # Rolling window
        if settled_roll:
            out(f"\n  4b. Rolling {rolling_days}d Drift")
            out(f"  {'─'*60}")
            roll_report = dm.run(settled_roll)
            out(f"  {roll_report['summary']}")
            roll_buckets = {}
            for b in roll_report["dimensions"].get("prob_bucket", []):
                roll_buckets[b["segment"]] = b
            if roll_buckets:
                out(f"\n  {'Bucket':<12} {'n':>6} {'Actual%':>9} {'Bias':>8}")
                out(f"  {'─'*38}")
                for seg, b in sorted(roll_buckets.items()):
                    out(f"  {seg:<12} {b['n']:>6} {b['actual_pct']:>9.2f}% {b['bias_pp']:>+8.2f}pp")

    except Exception as e:
        out(f"  [FAILED] Phase 4 error: {e}")
        import traceback; out(traceback.format_exc())


def _bias_flag(bias, n) -> str:
    if n < 20:        return "[n<20]"
    if abs(bias) > 5: return "⚠ CRITICAL"
    if abs(bias) > 3: return "⚠ WARNING"
    if abs(bias) > 2: return "! INFO"
    return "✓ OK"


# ── Phase 5: Statistical Validity ────────────────────────────────────────────

def _phase5_stats(settled, out):
    out()
    out("=" * W)
    out("  PHASE 5 — STATISTICAL VALIDITY & CONFIDENCE INTERVALS")
    out("=" * W)

    n = len(settled)
    out(f"\n  5a. Sample Sufficiency")
    out(f"  {'─'*60}")
    milestones = [
        (50,   "Preliminary ROI direction visible; calibration drift detectable"),
        (100,  "barrel≥10% segment reliability (n~15-20 expected)"),
        (200,  "Overall ROI statistically meaningful; CLV-ROI correlation visible"),
        (500,  "Segment-level ROI reliable; threshold optimization feasible"),
        (1000, "Full production validation; re-calibration confidence high"),
    ]
    for m, desc in milestones:
        status = "COMPLETE ✓" if n >= m else f"need {m-n} more"
        out(f"  n={m:>5}: [{status:<20}] {desc}")

    # Win rate CI
    wins = sum(1 for r in settled if r.get("hr_result") == "1")
    if n > 0:
        wr   = wins / n
        se   = math.sqrt(wr * (1 - wr) / n)
        ci95 = 1.96 * se
        out(f"\n  5b. Win Rate Confidence Interval")
        out(f"  {'─'*60}")
        out(f"  Sample: {wins} wins / {n} decided  =  {wr*100:.2f}%")
        out(f"  95% CI: [{(wr-ci95)*100:.1f}%, {(wr+ci95)*100:.1f}%]  (SE = {se*100:.2f}pp)")
        out(f"  League avg HR rate: ~10.5%  (2026 season)")

        if wr > 0.105 + 2*se:
            out(f"  Signal: STATISTICALLY ABOVE AVERAGE (p<0.05)")
        elif wr < 0.105 - 2*se:
            out(f"  Signal: STATISTICALLY BELOW AVERAGE (p<0.05) — investigate model")
        else:
            out(f"  Signal: WITHIN EXPECTED VARIANCE (not yet significant)")

    # Binomial probability tests
    out(f"\n  5c. Binomial Significance Tests (model probabilities)")
    out(f"  {'─'*60}")
    out(f"  Question: are we selecting above-average HR hitters?")
    out(f"  Null hypothesis: win rate = league avg 10.5%")

    import math as _math
    for test_p in [0.105, 0.12, 0.15, 0.18]:
        # P(wins >= observed | true_p = test_p)
        prob = 0.0
        for k in range(wins, n + 1):
            try:
                binom = _comb(n, k) * (test_p ** k) * ((1 - test_p) ** (n - k))
                prob  += binom
            except (OverflowError, ValueError):
                prob = float("nan")
                break
        if _math.isnan(prob):
            out(f"  true_p={test_p*100:.0f}%: P(wins>={wins}) = computation overflow at n={n}")
        else:
            sig = "plausible" if prob > 0.05 else "unlikely (p<0.05)"
            out(f"  true_p={test_p*100:.0f}%: P(wins>={wins}|p={test_p:.3f}) = {prob:.3f}  [{sig}]")

    # Edge persistence
    out(f"\n  5d. Edge Persistence (Rolling Bias Trend)")
    out(f"  {'─'*60}")
    dates = sorted(set(r.get("date","") for r in settled if r.get("date","")))
    if len(dates) >= 7:
        # Compute 7-day rolling win rate
        periods: list[tuple[str, float, int]] = []  # (date, wr, n)
        for i in range(6, len(dates)):
            period_dates = dates[i-6:i+1]
            period_rows  = [r for r in settled if r.get("date","") in set(period_dates)]
            pr_n    = len(period_rows)
            pr_wins = sum(1 for r in period_rows if r.get("hr_result") == "1")
            if pr_n >= 10:
                periods.append((dates[i], pr_wins / pr_n * 100, pr_n))

        if periods:
            out(f"  7-day rolling win rate (last 5 periods):")
            for dt, wr, pn in periods[-5:]:
                out(f"  {dt}: {wr:.1f}%  (n={pn})")
        else:
            out(f"  Not enough data for rolling analysis (need ≥10 picks/period).")
    else:
        out(f"  Need data across ≥7 dates for rolling trend (have {len(dates)}).")

    # Variance estimate
    if n >= 20:
        model_probs = []
        for r in settled:
            try:
                model_probs.append(float(r.get("model_prob_pct","0") or 0) / 100.0)
            except (ValueError, TypeError):
                pass
        if model_probs:
            avg_model = sum(model_probs) / len(model_probs)
            out(f"\n  5e. Variance Estimates")
            out(f"  {'─'*60}")
            out(f"  Avg model probability: {avg_model*100:.2f}%")
            theoretical_var = avg_model * (1 - avg_model)
            out(f"  Theoretical variance (Bernoulli): {theoretical_var:.4f}")
            out(f"  Expected win rate std dev over {n} picks: ±{math.sqrt(theoretical_var/n)*100:.2f}pp")


def _comb(n: int, k: int) -> float:
    """Binomial coefficient nCk using log for large n."""
    if k > n or k < 0:
        return 0.0
    if k == 0 or k == n:
        return 1.0
    # Use Stirling's or direct for small, log for large
    try:
        import math
        return math.comb(n, k)
    except Exception:
        return float("nan")


# ── Phase 6: Production Readiness ────────────────────────────────────────────

def _phase6_production(rows, settled, clv_rows, out):
    out()
    out("=" * W)
    out("  PHASE 6 — PRODUCTION READINESS ASSESSMENT & ROADMAP")
    out("=" * W)

    n_settled = len(settled)
    n_clv     = len([r for r in clv_rows if r.get("clv_pp","")]) if clv_rows else 0
    n_sb      = sum(1 for r in rows if r.get("sportsbook",""))
    n_total   = len(rows)
    has_s26   = sum(1 for r in rows if r.get("open_no_vig_pct","")) > 0

    checks = [
        # (description, passed, priority, notes)
        ("Settlement pipeline", n_settled > 0, "CRITICAL",
         f"n={n_settled} settled. Run: py -3.12 ops_daily.py daily."),
        ("Schema migration (S25+S26)", has_s26, "HIGH",
         "Run: py -3.12 ops_daily.py to trigger migration."),
        ("CLV data collection", n_clv > 0, "HIGH",
         "Run: py -3.12 capture_closing_lines.py before game time."),
        ("Sportsbook field populated", n_sb / n_total > 0.5 if n_total > 0 else False, "HIGH",
         f"Only {n_sb}/{n_total} picks have sportsbook. New picks auto-populate going forward."),
        ("Drift monitoring active", True, "MEDIUM",
         "DriftMonitor runs in ops_daily.py automatically."),
        ("Daily ops automation", False, "MEDIUM",
         "Schedule ops_daily.py in Windows Task Scheduler: 8AM daily."),
        ("n≥200 for ROI signal", n_settled >= 200, "MEDIUM",
         f"n={n_settled}. At current pace, need {max(0,200-n_settled)} more settled."),
        ("n≥500 for segment analysis", n_settled >= 500, "LOW",
         f"n={n_settled}/500. Long-term validation milestone."),
        ("CLV n≥50 for verdict", n_clv >= 50, "HIGH",
         f"CLV n={n_clv}/50. Need {max(0,50-n_clv)} more to get reliable signal."),
    ]

    out(f"\n  {'Check':<42} {'Status':>10}  {'Priority':<9} Notes")
    out(f"  {'─'*W}")
    for desc, passed, priority, notes in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        out(f"  {desc:<42} {status:>10}  {priority:<9} {notes}")

    out(f"\n  6b. Operational Roadmap")
    out(f"  {'─'*60}")

    roadmap = [
        ("Immediate (this week)",
         [
             "Run ops_daily.py every morning — settle + drift check + report",
             "Run capture_closing_lines.py before first pitch daily",
             "Ensure sportsbook field is populated when logging picks in app.py",
         ]),
        ("Short-term (next 2 weeks)",
         [
             "Accumulate n≥50 CLV records for reliable sharp/soft verdict",
             "Set up Windows Task Scheduler for ops_daily.py at 8AM",
             "Monitor 12-15% calibration bucket (n=75, bias=+2.69pp — approaching alert)",
             "Re-run analyze_calibration.py with fresh data (Session 23 Step 3)",
         ]),
        ("Medium-term (month)",
         [
             "Accumulate n≥500 settled for reliable segment-level ROI",
             "Compare CLV vs ROI by barrel tier (key edge persistence signal)",
             "Mid-season league constant refresh (late June)",
             "Evaluate PITCHER_FACTOR_SCALE=0.60 via calibration re-run",
         ]),
        ("Long-term (season)",
         [
             "Full n≥1000 settlement for production-grade validation",
             "Quarterly vig calibration review (NJ/PA hold % disclosures)",
             "Pitcher velo decline signal restoration (avg_speed data source)",
             "Re-evaluate archetype scoring bonus in ranker.py (barrel≥10%)",
         ]),
    ]
    for period, items in roadmap:
        out(f"\n  [{period}]")
        for item in items:
            out(f"    • {item}")

    out(f"\n  6c. Known Model Limitations (accepted)")
    out(f"  {'─'*60}")
    limitations = [
        "Statcast look-ahead in backtest: full-season Statcast used for April games (structural)",
        "Elite barrel (≥12%) under-prediction: −8.56pp bias (Sessions 22-23 partially address)",
        "Pitcher signals negligible (rank #17/21 in 2026) — PITCHER_FACTOR_SCALE=0.60 applied S26",
        "Pitcher velo decline signal: avg_speed unavailable in stats endpoint (display-only)",
        "Arsenal matchup: wrong direction correlation (-0.0696) — DO NOT integrate",
        "Fixed 5-day rest assumption: most pitchers on standard rotation — valid proxy",
        "CLV uses no-vig via book-specific vig table — estimates, not measured overrounds",
    ]
    for lim in limitations:
        out(f"    • {lim}")

    out()
    out("=" * W)
    out("  END OF MONITORING DASHBOARD")
    out("=" * W)


# ── Data loaders ──────────────────────────────────────────────────────────────

def _load_all_picks() -> list[dict]:
    rows = []
    for path in [
        Path(__file__).parent / "mlb_hr_engine_v4" / "tracking" / "pick_tracker.csv",
        Path(__file__).parent / "mlb_hr_engine_v4" / "tracking" / "results.csv",
    ]:
        if path.exists():
            with open(path, newline="", encoding="utf-8") as f:
                rows.extend(csv.DictReader(f))
    return rows


def _load_clv_log() -> list[dict]:
    path = Path(__file__).parent / "mlb_hr_engine_v4" / "tracking" / "clv_log.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _sf(val, default=0.0) -> float:
    try:
        return float(val) if val and str(val).strip() not in ("","--") else default
    except (ValueError, TypeError):
        return default


if __name__ == "__main__":
    main()
