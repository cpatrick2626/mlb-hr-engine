"""Supervised learning-loop analysis — READ-ONLY on all scoring surfaces.

Reads settled legs (legs.model_prob + legs.hr_result) and labeled warehouse
rows (batter_stat_history.hr_outcome count) to compute calibration, Brier
score, ECE, per-bucket predicted-vs-actual, and rank-based AUC. Writes ONE
row per run_date to learning_metrics. Never reads or modifies scoring,
config, calibration, learned_adjustments.json, or prob_scale.

Protected surfaces NOT touched:
  - pipeline scoring, model_prob derivation, prob_scale
  - learned_adjustments.json, auto_learn.py (remains frozen)
  - config.py calibration constants
  - MAIN/JIG separation
  - legs.hr_result, batter_stat_history.hr_outcome (read-only here)

Usage (from mlb_hr_engine_v4/):
    python -m api.learning_analysis            # dry-run — prints metrics, zero writes
    python -m api.learning_analysis --commit   # writes one metrics row
    python -m api.learning_analysis --commit --date 2026-07-22  # explicit run_date
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Load .env from the mlb_hr_engine_v4/ directory regardless of cwd (matches
# the pattern used by analyze_live_calibration.py and api/cron.py).
_HERE = Path(__file__).resolve().parent.parent  # → mlb_hr_engine_v4/
try:
    from dotenv import load_dotenv
    load_dotenv(_HERE / ".env")
except ImportError:
    pass  # dotenv not installed; rely on environment already set

# Minimum settled legs before flagging for human refit review.
REFIT_THRESHOLD = 500

# Probability buckets for per-band calibration reporting.
_BUCKETS = [
    (0.00, 0.05),
    (0.05, 0.10),
    (0.10, 0.15),
    (0.15, 0.20),
    (0.20, 0.25),
    (0.25, 1.01),  # upper sentinel; displayed as 1.0
]


# ── Data fetch (read-only) ────────────────────────────────────────────────────

def _fetch_settled_legs(client) -> list[dict]:
    """Read settled legs with valid hr_result from the legs table."""
    result = (
        client.table("legs")
        .select("leg_id,leg_date,model_prob,hr_result")
        .eq("settlement_status", "settled")
        .in_("hr_result", [0, 1])
        .execute()
    )
    return result.data or []


def _fetch_labeled_warehouse_count(client) -> int:
    """Count batter_stat_history rows with a confirmed hr_outcome label."""
    result = (
        client.table("batter_stat_history")
        .select("hr_outcome", count="exact")
        .in_("hr_outcome", [0, 1])
        .execute()
    )
    return result.count or 0


# ── Metric computation (pure functions) ───────────────────────────────────────

def _parse_pairs(legs: list[dict]) -> list[tuple[float, int]]:
    """Extract (model_prob, hr_result) pairs, dropping malformed rows."""
    pairs: list[tuple[float, int]] = []
    for row in legs:
        try:
            p = float(row["model_prob"])
            y = int(row["hr_result"])
        except (TypeError, ValueError, KeyError):
            continue
        if not (0.0 <= p <= 1.0) or y not in (0, 1):
            continue
        pairs.append((p, y))
    return pairs


def _brier_score(pairs: list[tuple[float, int]]) -> Optional[float]:
    if not pairs:
        return None
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def _ece(pairs: list[tuple[float, int]], n_bins: int = 10) -> Optional[float]:
    """Expected Calibration Error with equal-width bins."""
    if not pairs:
        return None
    bins: dict[int, list] = {i: [] for i in range(n_bins)}
    for p, y in pairs:
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))
    n = len(pairs)
    ece = 0.0
    for bucket_pairs in bins.values():
        if not bucket_pairs:
            continue
        mean_p = sum(p for p, _ in bucket_pairs) / len(bucket_pairs)
        actual = sum(y for _, y in bucket_pairs) / len(bucket_pairs)
        ece += (len(bucket_pairs) / n) * abs(mean_p - actual)
    return ece


def _compute_bucket_data(pairs: list[tuple[float, int]]) -> list[dict]:
    result = []
    for lo, hi in _BUCKETS:
        subset = [(p, y) for p, y in pairs if lo <= p < hi]
        count = len(subset)
        mean_pred = round(sum(p for p, _ in subset) / count, 5) if count else None
        actual_rate = round(sum(y for _, y in subset) / count, 5) if count else None
        result.append({
            "bucket_low": lo,
            "bucket_high": round(hi, 2) if hi < 1.01 else 1.0,
            "count": count,
            "mean_pred": mean_pred,
            "actual_rate": actual_rate,
        })
    return result


def _auc_mann_whitney(pairs: list[tuple[float, int]]) -> Optional[float]:
    """Rank-based AUC via Mann-Whitney U. Pure Python — no sklearn dependency."""
    positives = [p for p, y in pairs if y == 1]
    negatives = [p for p, y in pairs if y == 0]
    if not positives or not negatives:
        return None
    concordant = sum(
        1.0 if pp > pn else (0.5 if pp == pn else 0.0)
        for pp in positives
        for pn in negatives
    )
    return concordant / (len(positives) * len(negatives))


def compute_metrics(
    legs: list[dict],
    labeled_warehouse_count: int,
    run_date: str,
) -> dict:
    """Compute all metrics. Returns a dict ready to upsert into learning_metrics."""
    pairs = _parse_pairs(legs)
    n = len(pairs)

    if n == 0:
        mean_pred = None
        actual_rate = None
        brier = None
        ece = None
        auc = None
    else:
        mean_pred = round(sum(p for p, _ in pairs) / n, 5)
        actual_rate = round(sum(y for _, y in pairs) / n, 5)
        brier_raw = _brier_score(pairs)
        brier = round(brier_raw, 6) if brier_raw is not None else None
        ece_raw = _ece(pairs)
        ece = round(ece_raw, 6) if ece_raw is not None else None
        auc_raw = _auc_mann_whitney(pairs)
        auc = round(auc_raw, 5) if auc_raw is not None else None

    buckets = _compute_bucket_data(pairs)

    return {
        "run_date": run_date,
        "settled_legs_count": n,
        "labeled_warehouse_rows": labeled_warehouse_count,
        "mean_predicted_prob": mean_pred,
        "actual_hr_rate": actual_rate,
        "brier_score": brier,
        "ece": ece,
        "bucket_data": buckets,
        "discrimination_auc": auc,
        "ready_for_refit_review": n >= REFIT_THRESHOLD,
        "notes": f"refit_threshold={REFIT_THRESHOLD}",
    }


# ── DB write (metrics table only) ────────────────────────────────────────────

def _row_exists(run_date: str, client) -> bool:
    result = (
        client.table("learning_metrics")
        .select("run_date")
        .eq("run_date", run_date)
        .execute()
    )
    return bool(result.data)


def _write_metrics(metrics: dict, client) -> None:
    # Serialize bucket_data list → JSON string for jsonb storage
    row = {**metrics, "bucket_data": json.dumps(metrics["bucket_data"])}
    client.table("learning_metrics").upsert(row, on_conflict="run_date").execute()


# ── Output ────────────────────────────────────────────────────────────────────

def _print_metrics(metrics: dict) -> None:
    print(f"[learning-analysis] run_date:               {metrics['run_date']}")
    print(f"[learning-analysis] settled_legs_count:     {metrics['settled_legs_count']}")
    print(f"[learning-analysis] labeled_warehouse_rows: {metrics['labeled_warehouse_rows']}")
    print(f"[learning-analysis] mean_predicted_prob:    {metrics['mean_predicted_prob']}")
    print(f"[learning-analysis] actual_hr_rate:         {metrics['actual_hr_rate']}")
    print(f"[learning-analysis] brier_score:            {metrics['brier_score']}")
    print(f"[learning-analysis] ece:                    {metrics['ece']}")
    print(f"[learning-analysis] discrimination_auc:     {metrics['discrimination_auc']}")
    print(f"[learning-analysis] ready_for_refit_review: {metrics['ready_for_refit_review']}")
    print("[learning-analysis] bucket_data:")
    for b in metrics["bucket_data"]:
        lo = b["bucket_low"]
        hi = b["bucket_high"]
        n = b["count"]
        mp = b["mean_pred"]
        ar = b["actual_rate"]
        print(f"  [{lo:.2f}-{hi:.2f}]  n={n:>4}  mean_pred={mp}  actual_rate={ar}")


# ── Report (view latest stored row) ──────────────────────────────────────────

def _fetch_latest_metrics(client) -> Optional[dict]:
    result = (
        client.table("learning_metrics")
        .select("*")
        .order("run_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def _print_stored_metrics(row: dict) -> None:
    print(f"[learning-analysis] latest stored run_date:        {row.get('run_date')}")
    print(f"[learning-analysis] run_ts:                        {row.get('run_ts')}")
    print(f"[learning-analysis] settled_legs_count:            {row.get('settled_legs_count')}")
    print(f"[learning-analysis] labeled_warehouse_rows:        {row.get('labeled_warehouse_rows')}")
    print(f"[learning-analysis] mean_predicted_prob:           {row.get('mean_predicted_prob')}")
    print(f"[learning-analysis] actual_hr_rate:                {row.get('actual_hr_rate')}")
    print(f"[learning-analysis] brier_score:                   {row.get('brier_score')}")
    print(f"[learning-analysis] ece:                           {row.get('ece')}")
    print(f"[learning-analysis] discrimination_auc:            {row.get('discrimination_auc')}")
    print(f"[learning-analysis] ready_for_refit_review:        {row.get('ready_for_refit_review')}")
    print(f"[learning-analysis] notes:                         {row.get('notes')}")
    buckets = row.get("bucket_data")
    if isinstance(buckets, str):
        try:
            buckets = json.loads(buckets)
        except (json.JSONDecodeError, TypeError):
            buckets = None
    if buckets:
        print("[learning-analysis] bucket_data:")
        for b in buckets:
            lo = b.get("bucket_low", "?")
            hi = b.get("bucket_high", "?")
            n  = b.get("count", 0)
            mp = b.get("mean_pred")
            ar = b.get("actual_rate")
            print(f"  [{lo:.2f}-{hi:.2f}]  n={n:>4}  mean_pred={mp}  actual_rate={ar}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Supervised learning-loop analysis — read-only on scoring"
    )
    parser.add_argument(
        "--commit", action="store_true",
        help="Write one metrics row to learning_metrics (default: dry-run, no DB write)",
    )
    parser.add_argument(
        "--date", metavar="YYYY-MM-DD",
        help="run_date to record (default: today ET)",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Print the latest stored metrics row from learning_metrics and exit",
    )
    args = parser.parse_args()

    from api.cache import _client, today_et

    if args.report:
        client = _client()
        row = _fetch_latest_metrics(client)
        if row is None:
            print("[learning-analysis] no rows in learning_metrics yet")
        else:
            _print_stored_metrics(row)
        return

    run_date = args.date or today_et().isoformat()
    mode = "COMMIT" if args.commit else "DRY-RUN"

    print(f"[learning-analysis] {mode}  run_date={run_date}")

    client = _client()

    print("[learning-analysis] fetching settled legs…")
    legs = _fetch_settled_legs(client)
    print(f"[learning-analysis] raw settled legs fetched: {len(legs)}")

    print("[learning-analysis] fetching labeled warehouse rows…")
    warehouse_count = _fetch_labeled_warehouse_count(client)

    metrics = compute_metrics(legs, warehouse_count, run_date)
    _print_metrics(metrics)

    if not args.commit:
        print("[learning-analysis] DRY-RUN complete — zero writes")
        return

    existing = _row_exists(run_date, client)
    _write_metrics(metrics, client)
    action = "updated" if existing else "wrote"
    print(f"[learning-analysis] {action} metrics row for run_date={run_date}")
    if metrics["ready_for_refit_review"]:
        print(
            f"[learning-analysis] *** REFIT REVIEW FLAG ***  "
            f"settled_legs_count={metrics['settled_legs_count']} >= threshold={REFIT_THRESHOLD}  "
            f"— human operator decision required before any calibration change"
        )
    else:
        remaining = REFIT_THRESHOLD - metrics["settled_legs_count"]
        print(
            f"[learning-analysis] refit flag: NOT READY  "
            f"({remaining} more settled legs needed to reach threshold={REFIT_THRESHOLD})"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[learning-analysis] FAILED: {exc}", file=sys.stderr)
        raise
