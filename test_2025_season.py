"""
2025 full-season batter-only validation.

For every qualified 2025 batter (>= 300 PA):
  1. Compute base_hr_rate() from season stats
  2. Apply statcast power multiplier -> statcast_blended_rate()
  3. Compare model HR/PA vs actual HR/PA

No pitcher, park, weather, or platoon adjustments - isolates the batter-side
rate construction accuracy.

Run from repo root:
    python test_2025_season.py
"""

import sys
import math
import time
import requests
from pathlib import Path

# Use v4 modules
sys.path.insert(0, str(Path(__file__).parent / "codex_hr_engine_v4"))

# Patch config to use 2025 data
import config as _cfg
_cfg.CURRENT_SEASON = 2025

from clients import statcast as statcast_client
from engine import probability as prob

MLB_API  = "https://statsapi.mlb.com/api/v1"
SESSION  = requests.Session()
SESSION.headers.update({"User-Agent": "Codex-HR-Engine-Test/1.0"})
MIN_PA   = 300   # qualified threshold


# -- Fetch ----------------------------------------------------------------------

def fetch_all_2025_batters() -> list[dict]:
    """Pull full-season hitting stats for all 2025 MLB batters, sorted by PA desc."""
    resp = SESSION.get(f"{MLB_API}/stats", params={
        "stats": "season", "group": "hitting",
        "season": 2025, "sportId": 1, "limit": 2000,
        "sortStat": "plateAppearances", "order": "desc",
    }, timeout=30)
    resp.raise_for_status()
    splits = resp.json()["stats"][0]["splits"]
    rows = []
    for s in splits:
        st  = s["stat"]
        pa  = int(st.get("plateAppearances", 0))
        hr  = int(st.get("homeRuns", 0))
        if pa < MIN_PA:
            continue
        rows.append({
            "player_id":  s["player"]["id"],
            "name":       s["player"]["fullName"],
            "team":       s.get("team", {}).get("name", ""),
            "pa":         pa,
            "actual_hr":  hr,
            "actual_rate": hr / pa,
            "season_stats": st,
        })
    return rows


# -- Model ----------------------------------------------------------------------

def _fake_recent(season_stats: dict) -> dict:
    """
    For a full-season test, recent stats = season stats.
    The blending code will just weight recent slightly higher but the data is the same.
    """
    return season_stats


def run_model(batters: list[dict], sc_data: dict[int, dict]) -> list[dict]:
    results = []
    for b in batters:
        pid   = b["player_id"]
        ss    = b["season_stats"]
        rs    = _fake_recent(ss)

        raw_rate   = prob.base_hr_rate(ss, rs)
        power_mult = statcast_client.batter_power_multiplier(pid, sc_data)
        sc_stats   = sc_data.get(pid, {})
        sc_pa      = sc_stats.get("pa", 0)
        sc_source  = sc_stats.get("statcast_source", "current")
        model_rate = prob.statcast_blended_rate(
            raw_rate, power_mult, b["pa"],
            statcast_pa=sc_pa, statcast_source=sc_source,
        )

        has_sc = (pid in sc_data and sc_source == "current")

        results.append({
            **b,
            "raw_rate":    round(raw_rate, 5),
            "power_mult":  round(power_mult, 3),
            "model_rate":  round(model_rate, 5),
            "diff":        round(model_rate - b["actual_rate"], 5),
            "has_sc":      has_sc,
            "barrel_pct":  round(sc_stats.get("barrel_rate", 0) * 100, 1) if has_sc else None,
        })
    return sorted(results, key=lambda x: abs(x["diff"]), reverse=True)


# -- Metrics --------------------------------------------------------------------

def compute_metrics(results: list[dict]) -> dict:
    n      = len(results)
    diffs  = [r["diff"] for r in results]
    actuals = [r["actual_rate"] for r in results]
    models  = [r["model_rate"] for r in results]

    mae    = sum(abs(d) for d in diffs) / n
    rmse   = math.sqrt(sum(d**2 for d in diffs) / n)
    bias   = sum(diffs) / n   # positive = model over-predicts

    # Pearson correlation
    ma  = sum(models) / n
    aa  = sum(actuals) / n
    num = sum((m - ma) * (a - aa) for m, a in zip(models, actuals))
    dm  = math.sqrt(sum((m - ma)**2 for m in models))
    da  = math.sqrt(sum((a - aa)**2 for a in actuals))
    corr = num / (dm * da) if dm * da else 0.0

    over  = sum(1 for d in diffs if d > 0)
    under = sum(1 for d in diffs if d < 0)

    with_sc    = [r for r in results if r["has_sc"]]
    without_sc = [r for r in results if not r["has_sc"]]
    mae_sc     = sum(abs(r["diff"]) for r in with_sc)    / len(with_sc)    if with_sc    else None
    mae_nosc   = sum(abs(r["diff"]) for r in without_sc) / len(without_sc) if without_sc else None

    return {
        "n": n, "mae": mae, "rmse": rmse, "bias": bias, "corr": corr,
        "over": over, "under": under,
        "mae_with_sc": mae_sc, "mae_without_sc": mae_nosc,
        "with_sc": len(with_sc), "without_sc": len(without_sc),
    }


# -- Display --------------------------------------------------------------------



def print_report(results: list[dict], metrics: dict) -> None:
    SEP = "-" * 110

    print()
    print("=" * 110)
    print("  2025 FULL-SEASON BATTER-ONLY VALIDATION  |  Power Multiplier Formula")
    print(f"  Qualified batters (>={MIN_PA} PA): {metrics['n']}   |   "
          f"With Statcast: {metrics['with_sc']}   |   Without: {metrics['without_sc']}")
    print("=" * 110)

    # Aggregate metrics
    print()
    print("AGGREGATE METRICS")
    print(SEP)
    print(f"  Pearson r (model vs actual HR/PA) : {metrics['corr']:+.4f}")
    print(f"  Mean Absolute Error               : {metrics['mae']:.5f}  ({metrics['mae']*100:.3f} pp)")
    print(f"  Root Mean Squared Error           : {metrics['rmse']:.5f}  ({metrics['rmse']*100:.3f} pp)")
    print(f"  Bias (model - actual)             : {metrics['bias']:+.5f}  "
          f"({'over-predicts' if metrics['bias'] > 0 else 'under-predicts'})")
    print(f"  Over-predicted / Under-predicted  : {metrics['over']} / {metrics['under']}")
    if metrics["mae_with_sc"] is not None:
        print(f"  MAE - with Statcast               : {metrics['mae_with_sc']:.5f}")
    if metrics["mae_without_sc"] is not None:
        print(f"  MAE - without Statcast            : {metrics['mae_without_sc']:.5f}")
    print(SEP)

    # Top 20 biggest over-predictions
    over_list  = [r for r in results if r["diff"] > 0][:20]
    under_list = [r for r in results if r["diff"] < 0][:20]

    hdr = (f"  {'PLAYER':<26} {'TEAM':<22} {'PA':>5}  "
           f"{'ACTUAL':>7}  {'MODEL':>7}  {'DIFF':>7}  {'MULT':>6}  {'BARREL':>7}  SC")

    for label, subset in [("BIGGEST OVER-PREDICTIONS (model > actual)", over_list),
                           ("BIGGEST UNDER-PREDICTIONS (model < actual)", under_list)]:
        print()
        print(f"  {label}")
        print(SEP)
        print(hdr)
        print(SEP)
        for r in subset:
            barrel = f"{r['barrel_pct']:.1f}%" if r["barrel_pct"] is not None else "  -  "
            sc_tag = "Y" if r["has_sc"] else " "
            diff_s = f"{r['diff']:+.4f}"
            print(f"  {r['name']:<26} {r['team']:<22} {r['pa']:>5}  "
                  f"{r['actual_rate']:>7.4f}  {r['model_rate']:>7.4f}  "
                  f"{diff_s:>7}  {r['power_mult']:>6.3f}  {barrel:>7}  {sc_tag}")
        print(SEP)

    # All qualified, sorted by actual HR rate (best sluggers first)
    print()
    print("  ALL QUALIFIED BATTERS - sorted by actual HR/PA (desc)")
    print(SEP)
    print(hdr)
    print(SEP)
    by_actual = sorted(results, key=lambda x: x["actual_rate"], reverse=True)
    for r in by_actual:
        barrel = f"{r['barrel_pct']:.1f}%" if r["barrel_pct"] is not None else "  -  "
        sc_tag = "Y" if r["has_sc"] else " "
        diff_s = f"{r['diff']:+.4f}"
        print(f"  {r['name']:<26} {r['team']:<22} {r['pa']:>5}  "
              f"{r['actual_rate']:>7.4f}  {r['model_rate']:>7.4f}  "
              f"{diff_s:>7}  {r['power_mult']:>6.3f}  {barrel:>7}  {sc_tag}")
    print(SEP)
    print()


# -- Main -----------------------------------------------------------------------

def main():
    print("Fetching 2025 MLB batter season stats...")
    batters = fetch_all_2025_batters()
    print(f"  -> {len(batters)} batters with >={MIN_PA} PA")

    print("Fetching 2025 Statcast leaderboard data...")
    sc_data = statcast_client.get_batter_statcast(year=2025)
    print(f"  -> {len(sc_data)} players in Statcast dataset")

    print("Running model...")
    results = run_model(batters, sc_data)

    metrics = compute_metrics(results)
    print_report(results, metrics)


if __name__ == "__main__":
    main()

