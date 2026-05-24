"""
2026 YTD HR comparison: actual (from CSV) vs engine formula prediction.

For each player in homeruns.csv:
  1. Fetch 2026 season stats from MLB Stats API
  2. Run base_hr_rate() + statcast_blended_rate() (batter-side formula, no park/pitcher/weather)
  3. Predicted HRs = model_rate × season_PA
  4. Compare to hr_total in CSV; also show Savant xHR for reference

Run from repo root:
    python compare_2026_hrs.py
    python compare_2026_hrs.py --min-pa 50    # filter low-sample players
    python compare_2026_hrs.py --min-hr 3     # only players with 3+ actual HRs
"""

import sys
import csv
import math
import time
import argparse
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

import config as _cfg
_cfg.CURRENT_SEASON = 2026

from clients import statcast as statcast_client
from engine import probability as prob

MLB_API  = "https://statsapi.mlb.com/api/v1"
SESSION  = requests.Session()
SESSION.headers.update({"User-Agent": "Codex-HR-Engine/2026-compare"})
CSV_PATH = Path.home() / "Downloads" / "homeruns.csv"


# ── Load CSV ──────────────────────────────────────────────────────────────────

def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pid = int(r["player_id"])
            hr_total = int(r["hr_total"]) if r["hr_total"].strip() else 0
            xhr = float(r["xhr"]) if r["xhr"].strip() else 0.0
            rows.append({
                "player_id":  pid,
                "name":       r["player"],
                "team":       r["team_abbrev"],
                "hr_total":   hr_total,
                "xhr":        xhr,
                "xhr_diff":   float(r["xhr_diff"]) if r["xhr_diff"].strip() else 0.0,
            })
    return rows


# ── Fetch 2026 season stats ───────────────────────────────────────────────────

def fetch_season_stats(player_ids: list[int]) -> dict[int, dict]:
    """Batch-fetch 2026 hitting stats for a list of player IDs."""
    stats = {}
    chunk_size = 50
    for i in range(0, len(player_ids), chunk_size):
        chunk = player_ids[i:i + chunk_size]
        ids_str = ",".join(str(pid) for pid in chunk)
        try:
            resp = SESSION.get(
                f"{MLB_API}/people",
                params={"personIds": ids_str, "hydrate": "stats(group=hitting,type=season,season=2026)"},
                timeout=30,
            )
            resp.raise_for_status()
            for person in resp.json().get("people", []):
                pid = person["id"]
                for stat_group in person.get("stats", []):
                    splits = stat_group.get("splits", [])
                    if not splits:
                        continue
                    st = splits[0].get("stat", {})
                    stats[pid] = st
        except Exception as e:
            print(f"  Warning: batch fetch error for chunk {i//chunk_size}: {e}")
        time.sleep(0.2)
    return stats


# ── Model ─────────────────────────────────────────────────────────────────────

def _fake_recent(season_stats: dict) -> dict:
    return season_stats


def run_model(players: list[dict], season_stats: dict, sc_data: dict) -> list[dict]:
    results = []
    for p in players:
        pid = p["player_id"]
        ss  = season_stats.get(pid, {})
        rs  = _fake_recent(ss)

        season_pa  = int(ss.get("plateAppearances", 0)) if ss else 0
        season_hr  = int(ss.get("homeRuns", 0)) if ss else 0

        if season_pa == 0:
            # No 2026 stats fetched — use CSV hr_total as actual, mark as no-data
            results.append({
                **p,
                "season_pa":    0,
                "season_hr_api": 0,
                "model_rate":   None,
                "predicted_hr": None,
                "diff":         None,
                "power_mult":   None,
                "sc_source":    "none",
                "no_data":      True,
            })
            continue

        power_mult = statcast_client.batter_power_multiplier(pid, sc_data)
        raw_rate   = prob.base_hr_rate(ss, rs, statcast_mult=power_mult)

        sc_stats   = sc_data.get(pid, {})
        sc_pa      = sc_stats.get("pa", 0)
        sc_source  = sc_stats.get("statcast_source", "none")

        model_rate = prob.statcast_blended_rate(
            raw_rate, power_mult, season_pa,
            statcast_pa=sc_pa, statcast_source=sc_source,
        )

        predicted_hr = model_rate * season_pa
        # Actual from API (should match CSV hr_total closely; use CSV as authoritative)
        actual_hr = p["hr_total"]
        diff = predicted_hr - actual_hr

        results.append({
            **p,
            "season_pa":     season_pa,
            "season_hr_api": season_hr,
            "model_rate":    round(model_rate, 5),
            "predicted_hr":  round(predicted_hr, 1),
            "diff":          round(diff, 1),
            "power_mult":    round(power_mult, 3),
            "sc_source":     sc_source,
            "no_data":       False,
        })
    return results


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(results: list[dict]) -> dict:
    valid = [r for r in results if not r["no_data"] and r["diff"] is not None]
    if not valid:
        return {}
    n      = len(valid)
    diffs  = [r["diff"] for r in valid]
    mae    = sum(abs(d) for d in diffs) / n
    rmse   = math.sqrt(sum(d**2 for d in diffs) / n)
    bias   = sum(diffs) / n
    over   = sum(1 for d in diffs if d > 0)
    under  = sum(1 for d in diffs if d < 0)

    # Pearson on rate-space (avoids PA-scaling distortion in correlation)
    actuals = [r["hr_total"] / r["season_pa"] for r in valid]
    models  = [r["model_rate"] for r in valid]
    ma, aa  = sum(models) / n, sum(actuals) / n
    num     = sum((m - ma) * (a - aa) for m, a in zip(models, actuals))
    dm      = math.sqrt(sum((m - ma)**2 for m in models))
    da      = math.sqrt(sum((a - aa)**2 for a in actuals))
    corr    = num / (dm * da) if dm * da else 0.0

    return {"n": n, "mae": mae, "rmse": rmse, "bias": bias,
            "corr": corr, "over": over, "under": under}


# ── Display ───────────────────────────────────────────────────────────────────

_HDR = (f"  {'PLAYER':<28} {'TEAM':>4}  {'PA':>5}  "
        f"{'ACTUAL':>6}  {'xHR':>5}  {'ENGINE':>6}  {'DIFF':>6}  {'MULT':>5}  SC")
_SEP = "-" * 100


def _fmt_diff(d) -> str:
    if d is None:
        return "   n/a"
    return f"{d:+.1f}"


def print_report(results: list[dict], metrics: dict, min_pa: int, min_hr: int) -> None:
    print()
    print("=" * 100)
    print("  2026 YTD  |  Actual HRs  vs  Engine Prediction  (batter formula, no park/pitcher/weather)")
    print(f"  League constants: HR/PA={_cfg.LEAGUE_AVG_HR_PA}  HR/FB={_cfg.LEAGUE_HR_FB}  ISO={_cfg.LEAGUE_AVG_ISO}")
    if metrics:
        print(f"  Players evaluated: {metrics['n']}  |  MAE: {metrics['mae']:.2f} HR  |  "
              f"r={metrics['corr']:+.4f}  |  Bias: {metrics['bias']:+.2f} HR  |  "
              f"Over/Under: {metrics['over']}/{metrics['under']}")
    print("=" * 100)

    # Filter for display
    display = [r for r in results if not r["no_data"] and r["season_pa"] >= min_pa and r["hr_total"] >= min_hr]
    display.sort(key=lambda x: x["hr_total"], reverse=True)

    # ── Top over-predictions (engine > actual)
    over_list  = sorted([r for r in display if r["diff"] and r["diff"] > 0],
                        key=lambda x: x["diff"], reverse=True)[:15]
    under_list = sorted([r for r in display if r["diff"] and r["diff"] < 0],
                        key=lambda x: x["diff"])[:15]

    for label, subset in [
        ("TOP OVER-PREDICTIONS  (engine predicts more HRs than actual)", over_list),
        ("TOP UNDER-PREDICTIONS  (engine predicts fewer HRs than actual)", under_list),
    ]:
        print()
        print(f"  {label}")
        print(_SEP)
        print(_HDR)
        print(_SEP)
        for r in subset:
            sc_tag = {"current": "C", "blended": "B", "prior": "P"}.get(r["sc_source"], "-")
            print(f"  {r['name']:<28} {r['team']:>4}  {r['season_pa']:>5}  "
                  f"{r['hr_total']:>6}  {r['xhr']:>5.1f}  {r['predicted_hr']:>6.1f}  "
                  f"{_fmt_diff(r['diff']):>6}  {r['power_mult']:>5.3f}  {sc_tag}")
        print(_SEP)

    # ── Full table sorted by actual HRs
    print()
    print("  ALL PLAYERS — sorted by actual HR total (desc)")
    print(_SEP)
    print(_HDR)
    print(_SEP)
    for r in display:
        if r["no_data"]:
            continue
        sc_tag = {"current": "C", "blended": "B", "prior": "P"}.get(r["sc_source"], "-")
        print(f"  {r['name']:<28} {r['team']:>4}  {r['season_pa']:>5}  "
              f"{r['hr_total']:>6}  {r['xhr']:>5.1f}  {r['predicted_hr']:>6.1f}  "
              f"{_fmt_diff(r['diff']):>6}  {r['power_mult']:>5.3f}  {sc_tag}")
    print(_SEP)

    # ── No-data players
    no_data = [r for r in results if r["no_data"] and r["hr_total"] >= min_hr]
    if no_data:
        print()
        print(f"  NO 2026 STATS FOUND ({len(no_data)} players — likely injured/minors):")
        for r in no_data:
            print(f"    {r['name']:<28} {r['team']:>4}  actual={r['hr_total']}  xHR={r['xhr']:.1f}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-pa",  type=int, default=30,  help="Min 2026 PA to include (default 30)")
    parser.add_argument("--min-hr",  type=int, default=1,   help="Min actual HRs to show (default 1)")
    args = parser.parse_args()

    print(f"Loading CSV: {CSV_PATH}")
    players = load_csv(CSV_PATH)
    print(f"  -> {len(players)} players in CSV")

    player_ids = [p["player_id"] for p in players]

    print("Fetching 2026 season stats from MLB Stats API...")
    season_stats = fetch_season_stats(player_ids)
    print(f"  -> {len(season_stats)} players with 2026 stats")

    print("Fetching 2026 Statcast leaderboard (current + prior fallback)...")
    sc_data = statcast_client.get_batter_statcast(
        year=2026, player_ids=set(player_ids)
    )
    print(f"  -> {len(sc_data)} players in Statcast dataset")

    print("Running model...")
    results = run_model(players, season_stats, sc_data)

    valid = [r for r in results if not r["no_data"] and r["season_pa"] >= args.min_pa]
    metrics = compute_metrics(valid)
    print_report(results, metrics, min_pa=args.min_pa, min_hr=args.min_hr)


if __name__ == "__main__":
    main()
