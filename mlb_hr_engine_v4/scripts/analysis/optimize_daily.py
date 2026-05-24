"""
optimize_daily.py — Daily portfolio optimizer (Session 27).

Takes today's picks from pick_tracker.csv (or a specified date) and applies
portfolio optimization constraints to produce a filtered bet slate.

The optimizer selects the highest-quality subset of picks while:
  - Capping same-team exposure (default: 4 picks/team)
  - Capping total picks (default: 20/day)
  - Enforcing quality floors (EV%, edge%, optionally barrel%)
  - Diversifying across odds ranges

Usage:
  py -3.12 optimize_daily.py                      # optimize today's picks
  py -3.12 optimize_daily.py --date 2026-05-15     # optimize a specific date
  py -3.12 optimize_daily.py --preset conservative # use conservative constraints
  py -3.12 optimize_daily.py --max-picks 15        # override max picks
  py -3.12 optimize_daily.py --team-cap 3          # override team cap
  py -3.12 optimize_daily.py --min-barrel 6        # require barrel ≥ 6%
  py -3.12 optimize_daily.py --min-ev 4            # raise EV floor to 4%
  py -3.12 optimize_daily.py --show-rejected       # also print rejected picks
  py -3.12 optimize_daily.py --compare             # compare all presets
  py -3.12 optimize_daily.py --help

Presets: conservative | moderate (default) | relaxed | barrel_focused

Output: prints optimized pick slate + saves to portfolio_daily_YYYY-MM-DD.txt
"""

import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT         = Path(__file__).parent
TRACKER_PATH = ROOT / "mlb_hr_engine_v4" / "tracking" / "pick_tracker.csv"
REPORTS_DIR  = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "mlb_hr_engine_v4"))

W = 74


def _load_tracker() -> list[dict]:
    if not TRACKER_PATH.exists():
        return []
    with open(TRACKER_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(str(v).strip()) if v is not None and str(v).strip() != "" else default
    except (ValueError, TypeError):
        return default


def _odds_range(r: dict) -> str:
    o = int(_safe_float(r.get("american_odds") or r.get("best_odds"), 100))
    return f"{'+' if o >= 0 else ''}{o}"


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    # ── Parse arguments ────────────────────────────────────────────────────────
    target_date = None
    for a in args:
        if len(a) == 10 and a[4] == "-" and not a.startswith("--"):
            target_date = a
    if "--date" in args:
        idx = args.index("--date")
        if idx + 1 < len(args):
            target_date = args[idx + 1]

    if not target_date:
        target_date = date.today().isoformat()

    preset_name  = "moderate"
    if "--preset" in args:
        idx = args.index("--preset")
        if idx + 1 < len(args):
            preset_name = args[idx + 1]

    show_rejected = "--show-rejected" in args
    compare_all   = "--compare" in args

    # ── Build constraints ──────────────────────────────────────────────────────
    from portfolio.optimizer import (
        PortfolioConstraints, PortfolioOptimizer,
        CONSTRAINT_PRESETS, composite_score
    )

    if preset_name in CONSTRAINT_PRESETS:
        constraints = CONSTRAINT_PRESETS[preset_name]
    else:
        print(f"  [WARN] Unknown preset '{preset_name}'. Using 'moderate'.")
        constraints = CONSTRAINT_PRESETS["moderate"]
        preset_name = "moderate"

    # Override individual constraints from args
    if "--max-picks" in args:
        idx = args.index("--max-picks")
        if idx + 1 < len(args):
            constraints.max_picks_total = int(args[idx + 1])

    if "--team-cap" in args:
        idx = args.index("--team-cap")
        if idx + 1 < len(args):
            constraints.max_picks_per_team = int(args[idx + 1])

    if "--min-barrel" in args:
        idx = args.index("--min-barrel")
        if idx + 1 < len(args):
            constraints.min_barrel_pct = float(args[idx + 1])

    if "--min-ev" in args:
        idx = args.index("--min-ev")
        if idx + 1 < len(args):
            constraints.min_ev_pct = float(args[idx + 1])

    # ── Load data ──────────────────────────────────────────────────────────────
    all_rows   = _load_tracker()
    day_rows   = [r for r in all_rows if r.get("date") == target_date]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    buf = []

    def out(msg=""):
        print(msg)
        buf.append(msg)

    out(f"\n{'='*W}")
    out(f"  DAILY PORTFOLIO OPTIMIZER — {ts}")
    out(f"  Date: {target_date}  |  Preset: {preset_name}")
    out(f"  Constraints: {constraints.summary()}")
    out(f"{'='*W}")

    if not day_rows:
        out(f"\n  No picks found for {target_date}.")
        out(f"  Run the engine first: py -3.12 main.py  or  streamlit run app.py")
        return

    out(f"\n  Input: {len(day_rows)} picks for {target_date}")

    # ── Compare presets ────────────────────────────────────────────────────────
    if compare_all:
        from portfolio.optimizer import evaluate_constraint_presets
        out(f"\n  PRESET COMPARISON for {target_date}:")
        out(f"\n  {'Preset':<18} {'Selected':>9} {'%sel':>6} {'AvgEV':>7} {'AvgEdge':>8} "
            f"{'AvgBarrel':>10} {'Barrel8+':>9}")
        out(f"  {'─'*72}")
        results = evaluate_constraint_presets(day_rows)
        for r in results:
            out(f"  {r['preset']:<18} {r['n_selected']:>9} {r['pct_selected']:>5.1f}% "
                f"{(r.get('avg_ev_pct') or 0):>6.2f}% {(r.get('avg_edge_pct') or 0):>7.2f}% "
                f"{(r.get('avg_barrel') or 0):>9.2f}% {(r.get('pct_barrel_8+') or 0):>8.1f}%")
        out(f"\n  (Run without --compare to show the selected picks for one preset)")

    # ── Optimize ───────────────────────────────────────────────────────────────
    optimizer = PortfolioOptimizer(constraints=constraints)
    result    = optimizer.optimize(day_rows)

    selected = result["selected"]
    n_sel    = result["n_selected"]
    n_in     = result["n_input"]

    out(f"\n  Result: {n_in} → {n_sel} picks selected")
    out(f"  ({result['n_rejected_quality']} quality-filtered, {result['n_rejected_cap']} cap-rejected)")

    stats     = result["stats"]
    raw_s     = stats["raw"]
    opt_s     = stats["optimized"]

    out(f"\n  Quality comparison:")
    out(f"  {'Metric':<22} {'Raw':>10} {'Optimized':>12}  {'Delta':>8}")
    out(f"  {'─'*55}")

    for label, rk, ok in [
        ("Avg EV%",         "avg_ev_pct",    "avg_ev_pct"),
        ("Avg Edge%",       "avg_edge_pct",  "avg_edge_pct"),
        ("Avg Barrel%",     "avg_barrel",    "avg_barrel"),
        ("Barrel ≥8%",      "pct_barrel_8+", "pct_barrel_8+"),
        ("Avg Confidence",  "avg_confidence","avg_confidence"),
    ]:
        rv = raw_s.get(rk)
        ov = opt_s.get(ok)
        if rv is None and ov is None:
            continue
        rv_s = f"{rv:>8.2f}" if isinstance(rv,(int,float)) else f"{'—':>8}"
        ov_s = f"{ov:>10.2f}" if isinstance(ov,(int,float)) else f"{'—':>10}"
        if isinstance(rv,(int,float)) and isinstance(ov,(int,float)):
            d = ov - rv
            d_s = f"{d:>+8.2f}"
            flag = " ✓" if d > 0.01 else ""
        else:
            d_s, flag = "—", ""
        out(f"  {label:<22} {rv_s} {ov_s}  {d_s}{flag}")

    # ── Print selected picks ───────────────────────────────────────────────────
    if selected:
        out(f"\n  SELECTED PICKS ({n_sel}):")
        out(f"  {'#':>3}  {'Player':<22} {'Team':>4}  {'Odds':>6}  {'Barrel':>7}  "
            f"{'EV%':>5}  {'Edge%':>6}  {'Score':>6}  {'Pitcher'}")
        out(f"  {'─'*82}")

        for i, r in enumerate(sorted(selected, key=lambda x: -x.get("_score", 0)), 1):
            name    = r.get("player_name", "Unknown")[:22]
            team    = (r.get("team") or "—").upper()
            odds    = _odds_range(r)
            barrel  = _safe_float(r.get("barrel_pct"))
            ev      = _safe_float(r.get("ev_pct"))
            edge    = _safe_float(r.get("edge_pct"))
            score   = r.get("_score", 0)
            pitcher = (r.get("pitcher") or "—")[:20]
            bet     = _safe_float(r.get("bet_dollars"))
            bet_s   = f"  ${bet:.2f}" if bet > 0 else ""
            out(f"  {i:>3}.  {name:<22} {team:>4}  {odds:>6}  {barrel:>6.1f}%  "
                f"{ev:>4.1f}%  {edge:>5.1f}%  {score:>6.4f}  {pitcher}{bet_s}")

        # Summary stats
        out(f"\n  Portfolio summary:")
        from collections import Counter
        team_dist = Counter((r.get("team") or "UNK").upper() for r in selected)
        out(f"    Teams represented  : {len(team_dist)}")
        out(f"    Max team exposure  : {max(team_dist.values())} picks ({max(team_dist, key=team_dist.get)})")

        total_bet = sum(_safe_float(r.get("bet_dollars")) for r in selected)
        if total_bet > 0:
            out(f"    Total at stake     : ${total_bet:.2f}")

        barrel_above_8 = sum(1 for r in selected if _safe_float(r.get("barrel_pct")) >= 8)
        out(f"    Barrel ≥8% picks   : {barrel_above_8}/{n_sel} ({barrel_above_8/n_sel*100:.0f}%)")

        from portfolio.exposure import build_exposure_profile, fragility_score, exposure_alerts
        profile  = build_exposure_profile(selected)
        frag     = fragility_score(profile)
        alerts   = exposure_alerts(profile)
        out(f"    Fragility score    : {frag:.1f}/100")
        if alerts:
            out(f"    Alerts             : {len(alerts)}")
            for a in alerts[:2]:
                out(f"      [{a['level']}] {a['message'][:70]}")

    # ── Rejected picks ────────────────────────────────────────────────────────
    if show_rejected and result["rejected"]:
        out(f"\n  REJECTED PICKS ({len(result['rejected'])}):")
        out(f"  {'Player':<22} {'Team':>4}  {'Odds':>6}  {'Barrel':>7}  "
            f"{'EV%':>5}  {'Reason'}")
        out(f"  {'─'*72}")
        for r in result["rejected"][:30]:
            name   = r.get("player_name", "Unknown")[:22]
            team   = (r.get("team") or "—").upper()
            odds   = _odds_range(r)
            barrel = _safe_float(r.get("barrel_pct"))
            ev     = _safe_float(r.get("ev_pct"))
            reason = r.get("_reject_reason", "")[:35]
            out(f"  {name:<22} {team:>4}  {odds:>6}  {barrel:>6.1f}%  {ev:>4.1f}%  {reason}")
        if len(result["rejected"]) > 30:
            out(f"  ... and {len(result['rejected'])-30} more rejected picks")

    out(f"\n{'='*W}")
    out(f"  Capture CLV for this portfolio: py -3.12 capture_closing_lines.py")
    out(f"{'='*W}\n")

    # ── Save output ────────────────────────────────────────────────────────────
    report_path = REPORTS_DIR / f"portfolio_daily_{target_date}.txt"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(buf))
        print(f"  Report saved: {report_path}")
    except Exception as e:
        print(f"  [WARN] Could not save report: {e}")


if __name__ == "__main__":
    main()
