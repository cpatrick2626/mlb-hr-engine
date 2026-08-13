"""
Fit isotonic recalibration of final displayed model_prob against labeled
batter_stat_history warehouse outcomes, and produce a full BEFORE/AFTER report.

READ-ONLY vs the database. Writes:
  - fit_warehouse_isotonic_output.txt   (report, next to this script)
  - warehouse_isotonic_candidate.json   (fitted curve artifact, next to this script;
                                         NOT loaded by any runtime path until ratified
                                         and moved/wired explicitly)

Chain context (documented, not changed here):
  raw game_hr_probability
    -> adaptive_weights.apply_prob_scale (learned prob_scale, currently 1.12)
    -> engine.calibration.apply_calibration (Platt, currently enabled)
    -> FINAL model_prob (displayed + captured into batter_stat_history.raw_payload)

The isotonic here is fitted on that FINAL stored model_prob, so if ratified it
composes AFTER the existing chain (fit input == production input; no
double-correction; board ranking preserved exactly by monotonicity).

Run from inside mlb_hr_engine_v4/ so load_dotenv() finds .env:
  cd mlb_hr_engine_v4 && python scripts/analysis/fit_warehouse_isotonic.py
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OUT_DIR = Path(__file__).resolve().parent
REPORT_PATH = OUT_DIR / "fit_warehouse_isotonic_output.txt"
ARTIFACT_PATH = OUT_DIR / "warehouse_isotonic_candidate.json"

# Current MAIN tier cutoffs (config.FS_TIER_THRESHOLDS) — read for reporting only.
sys.path.insert(0, str(OUT_DIR.parent.parent))
import config  # noqa: E402

TIER_ORDER = ["APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD"]


def fetch_labeled_rows():
    from supabase import create_client

    client = create_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
    )
    dates_result = (
        client.table("batter_stat_history")
        .select("slate_date")
        .in_("hr_outcome", [0, 1])
        .order("slate_date", desc=False)
        .limit(1)
        .execute()
    )
    if not dates_result.data:
        raise SystemExit("no labeled rows found")
    from datetime import date, timedelta

    first = date.fromisoformat(dates_result.data[0]["slate_date"])
    rows, page_size = [], 1000
    day = first
    while day <= date.today():
        page = 0
        while True:
            result = (
                client.table("batter_stat_history")
                .select(
                    "slate_date,run_ts,batter_id,game_pk,hr_outcome,"
                    "model_prob:raw_payload->>model_prob,"
                    "player_name:raw_payload->>player_name,"
                    "tier:raw_payload->>tier,"
                    "team:raw_payload->>team"
                )
                .eq("slate_date", day.isoformat())
                .in_("hr_outcome", [0, 1])
                .order("run_ts", desc=False)
                .range(page * page_size, (page + 1) * page_size - 1)
                .execute()
            )
            batch = result.data or []
            rows.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
        day += timedelta(days=1)
    out = []
    for r in rows:
        try:
            p = float(r["model_prob"])
        except (TypeError, ValueError):
            continue
        if not (0.0 < p <= 1.0):
            continue
        r["model_prob"] = p
        r["hr_outcome"] = int(r["hr_outcome"])
        out.append(r)
    return out


def dedup_latest(rows):
    """Latest snapshot per (batter_id, game_pk) — what the board finally showed."""
    best = {}
    for r in rows:  # rows arrive ordered by run_ts asc; later overwrites earlier
        best[(r["batter_id"], r["game_pk"])] = r
    return list(best.values())


def auc(pairs):
    """Mann-Whitney AUC with average-rank tie handling."""
    n1 = sum(y for _, y in pairs)
    n0 = len(pairs) - n1
    if n1 == 0 or n0 == 0:
        return None
    ranked = sorted(pairs, key=lambda t: t[0])
    r1, i = 0.0, 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and ranked[j][0] == ranked[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0  # ranks are 1-based; block [i+1 .. j]
        r1 += avg_rank * sum(y for _, y in ranked[i:j])
        i = j
    return (r1 - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def pava_fit(pairs):
    """Weighted pool-adjacent-violators on exact predicted values.

    Returns (breakpoints, values): block-mean x and fitted y per merged block,
    deduplicated so values are strictly increasing (flat neighbours merged).
    """
    groups = defaultdict(lambda: [0, 0])  # p -> [n, hr_sum]
    for p, y in pairs:
        groups[p][0] += 1
        groups[p][1] += y
    xs = sorted(groups)
    # blocks: [sum_w, sum_wy, sum_wx]
    blocks = [[groups[x][0], float(groups[x][1]), groups[x][0] * x] for x in xs]
    merged = []
    for b in blocks:
        merged.append(b)
        while len(merged) >= 2 and (
            merged[-2][1] / merged[-2][0] >= merged[-1][1] / merged[-1][0]
        ):
            w2, y2, x2 = merged.pop()
            merged[-1][0] += w2
            merged[-1][1] += y2
            merged[-1][2] += x2
        # strict >= merge keeps fitted values strictly increasing across blocks
    breakpoints = [b[2] / b[0] for b in merged]
    values = [b[1] / b[0] for b in merged]
    return breakpoints, values


def iso_apply(p, breakpoints, values):
    """Piecewise-linear interpolation between block centres (mirrors
    engine.calibration.isotonic_scale, incl. edge extrapolation)."""
    n = len(breakpoints)
    if n == 1:
        return values[0]
    if p <= breakpoints[0]:
        slope = (values[1] - values[0]) / (breakpoints[1] - breakpoints[0])
        return max(1e-4, values[0] + slope * (p - breakpoints[0]))
    if p >= breakpoints[-1]:
        slope = (values[-1] - values[-2]) / (breakpoints[-1] - breakpoints[-2])
        return min(1.0 - 1e-4, values[-1] + slope * (p - breakpoints[-1]))
    for i in range(n - 1):
        if breakpoints[i] <= p < breakpoints[i + 1]:
            t = (p - breakpoints[i]) / (breakpoints[i + 1] - breakpoints[i])
            return values[i] + t * (values[i + 1] - values[i])
    return p


def tier_of(p, thresholds):
    for t in TIER_ORDER:
        if p >= thresholds[t]:
            return t
    return "COLD"


def reliability_table(pairs, edges):
    lines = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = [(p, y) for p, y in pairs if lo <= p < hi]
        if not sub:
            lines.append(f"  {lo:5.2f}-{hi:4.2f}      0        --        --")
            continue
        mp = sum(p for p, _ in sub) / len(sub)
        ob = sum(y for _, y in sub) / len(sub)
        lines.append(
            f"  {lo:5.2f}-{hi:4.2f}  {len(sub):5d}   {mp*100:6.2f}%   {ob*100:6.2f}%   {(mp-ob)*100:+6.2f}pp"
        )
    return "\n".join(lines)


def brier(pairs):
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def analyze(label, rows, report):
    pairs = [(r["model_prob"], r["hr_outcome"]) for r in rows]
    n = len(pairs)
    obs = sum(y for _, y in pairs) / n
    mean_pred = sum(p for p, _ in pairs) / n
    auc_before = auc(pairs)

    bp, vals = pava_fit(pairs)
    cal_pairs = [(iso_apply(p, bp, vals), y) for p, y in pairs]
    mean_cal = sum(p for p, _ in cal_pairs) / n
    auc_after = auc(cal_pairs)

    edges = [0.0, 0.04, 0.07, 0.11, 0.16, 0.20, 0.25, 1.01]
    report.append(f"\n{'='*70}\nDATASET: {label}  (n={n})\n{'='*70}")
    report.append(f"  mean predicted (stored final model_prob): {mean_pred*100:.2f}%")
    report.append(f"  observed HR rate:                         {obs*100:.2f}%")
    report.append(f"  AUC before: {auc_before:.4f}")
    report.append(f"  Brier before: {brier(pairs):.5f}")
    report.append(f"\n  Isotonic fit: {len(bp)} monotone blocks")
    report.append(f"  mean calibrated: {mean_cal*100:.2f}%  (target = observed {obs*100:.2f}%)")
    report.append(f"  AUC after:  {auc_after:.4f}   (delta {auc_after-auc_before:+.5f})")
    report.append(f"  Brier after:  {brier(cal_pairs):.5f}")
    report.append("\n  Reliability BEFORE (bin, n, mean pred, observed, gap):")
    report.append(reliability_table(pairs, edges))
    report.append("\n  Reliability AFTER:")
    report.append(reliability_table(cal_pairs, edges))

    # Tier occupancy: current cutoffs on before-probs vs iso-mapped cutoffs on after-probs
    old_t = dict(config.FS_TIER_THRESHOLDS)
    new_t = {t: (0.0 if old_t[t] == 0.0 else round(iso_apply(old_t[t], bp, vals), 4))
             for t in TIER_ORDER}
    report.append("\n  Tier cutoffs (old -> iso-mapped candidate):")
    for t in TIER_ORDER:
        report.append(f"    {t:6s}  {old_t[t]:.2f}  ->  {new_t[t]:.4f}")
    before_counts = defaultdict(int)
    after_counts = defaultdict(int)
    for (p, _), (cp, _) in zip(pairs, cal_pairs):
        before_counts[tier_of(p, old_t)] += 1
        after_counts[tier_of(cp, new_t)] += 1
    report.append("\n  Tier occupancy   before   after(iso-mapped cutoffs)")
    for t in TIER_ORDER:
        report.append(f"    {t:6s}       {before_counts[t]:6d}   {after_counts[t]:6d}")
    return bp, vals, {
        "n": n, "observed": obs, "mean_pred": mean_pred, "mean_cal": mean_cal,
        "auc_before": auc_before, "auc_after": auc_after, "new_tiers": new_t,
    }


def main():
    rows = fetch_labeled_rows()
    report = [
        "WAREHOUSE ISOTONIC RECALIBRATION — fit + BEFORE/AFTER",
        f"generated: {datetime.now(timezone.utc).isoformat()}",
        f"labeled snapshot rows fetched: {len(rows)}",
    ]
    dedup = dedup_latest(rows)

    bp, vals, summary = analyze(
        "DEDUP — latest snapshot per unique batter-game (primary)", dedup, report
    )
    analyze("ALL SNAPSHOTS (secondary, duplicate-weighted)", rows, report)

    # Sample players — latest slate, spread across probability range
    latest = max(r["slate_date"] for r in dedup)
    slate = sorted(
        (r for r in dedup if r["slate_date"] == latest),
        key=lambda r: -r["model_prob"],
    )
    picks = slate[:5] + slate[len(slate)//2 - 2: len(slate)//2 + 1] + slate[-2:]
    report.append(f"\n  Sample players (slate {latest}): old prob -> calibrated, old tier -> new tier")
    old_t = dict(config.FS_TIER_THRESHOLDS)
    for r in picks:
        cp = iso_apply(r["model_prob"], bp, vals)
        report.append(
            f"    {str(r.get('player_name'))[:24]:24s} {r['model_prob']*100:6.2f}% -> {cp*100:5.2f}%"
            f"   {tier_of(r['model_prob'], old_t):6s} -> {tier_of(cp, summary['new_tiers']):6s}"
        )

    artifact = {
        "fitted_at": datetime.now(timezone.utc).isoformat(),
        "source": "batter_stat_history dedup latest-snapshot per batter-game",
        "n_rows": summary["n"],
        "observed_rate": summary["observed"],
        "mean_pred_before": summary["mean_pred"],
        "mean_pred_after": summary["mean_cal"],
        "auc_before": summary["auc_before"],
        "auc_after": summary["auc_after"],
        "fit_input": "final displayed model_prob (post prob_scale, post Platt)",
        "apply_point": "compose AFTER engine.calibration.apply_calibration",
        "breakpoints": [round(x, 6) for x in bp],
        "values": [round(v, 6) for v in vals],
        "candidate_tier_cutoffs": summary["new_tiers"],
        "status": "CANDIDATE — not wired into runtime; awaiting operator ratification",
    }
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    text = "\n".join(report) + "\n"
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(text)
    print(f"[artifact] {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
