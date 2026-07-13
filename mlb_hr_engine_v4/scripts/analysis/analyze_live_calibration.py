"""
analyze_live_calibration.py  —  S2 predicted-vs-actual calibration rollup
=========================================================================
Audit #1 spec: buckets SETTLED picks by their FROZEN model_prob (the value
logged at pick time — never recomputed) and reports, per band:
    n, avg_predicted, actual_hr_rate, diff (actual - predicted).

Two band views per source:
  1. FS_TIER_THRESHOLDS bands (APEX/ELITE/EDGE/SIGNAL/WATCH/COLD) from config.py
  2. 5pp calibration buckets (same layout as analyze_calibration.py BUCKETS)

Sources (each reported separately — lanes are never blended):
  * CSV lane   — tracking/results.csv      (settled qualified picks)
  *            — tracking/pick_tracker.csv (settled pick-tracker rows, incl. no-odds calibration rows)
  * Legs lane  — Supabase legs table (settled, non-removed; frozen model_prob + hr_result)
                 Skipped gracefully if SUPABASE_URL / SUPABASE_SERVICE_KEY are unavailable.

REPORT-ONLY: reads data, prints tables, writes analyze_live_calibration_output.txt
next to this script. Never modifies thresholds, scores, config, or any data file.

Usage
-----
  python mlb_hr_engine_v4/scripts/analysis/analyze_live_calibration.py
"""

import csv
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent   # → mlb_hr_engine_v4/
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")   # explicit path — script may run from any cwd

from config import FS_TIER_THRESHOLDS
from tracking._paths import DATA_DIR

REPORT_PATH = Path(__file__).parent / "analyze_live_calibration_output.txt"

# 5pp buckets — same layout as analyze_calibration.py BUCKETS
BUCKETS_5PP = [
    (0.00, 0.05, "0-5%"),
    (0.05, 0.10, "5-10%"),
    (0.10, 0.15, "10-15%"),
    (0.15, 0.20, "15-20%"),
    (0.20, 0.25, "20-25%"),
    (0.25, 0.30, "25-30%"),
    (0.30, 1.01, "30%+"),
]

SMALL_SAMPLE_TOTAL  = 200   # operator rule: no threshold/calibration change below this
SMALL_SAMPLE_BUCKET = 30


def _tier_of(prob: float) -> str:
    for tier, thr in sorted(FS_TIER_THRESHOLDS.items(), key=lambda kv: -kv[1]):
        if prob >= thr:
            return tier
    return "COLD"


def _rollup_tiers(rows: list[tuple[float, int]]) -> list[dict]:
    tiers = sorted(FS_TIER_THRESHOLDS.items(), key=lambda kv: -kv[1])
    out = []
    for tier, thr in tiers:
        sel = [(p, h) for p, h in rows if _tier_of(p) == tier]
        out.append(_band_stats(f"{tier} (>={thr:.2f})", sel))
    return out


def _rollup_5pp(rows: list[tuple[float, int]]) -> list[dict]:
    out = []
    for lo, hi, label in BUCKETS_5PP:
        sel = [(p, h) for p, h in rows if lo <= p < hi]
        out.append(_band_stats(label, sel))
    return out


def _band_stats(label: str, sel: list[tuple[float, int]]) -> dict:
    n = len(sel)
    avg_pred = sum(p for p, _ in sel) / n if n else 0.0
    actual   = sum(h for _, h in sel) / n if n else 0.0
    return {"band": label, "n": n, "avg_pred": avg_pred,
            "actual": actual, "diff": actual - avg_pred}


def _fmt_table(title: str, stats: list[dict], total_n: int, out: list[str]) -> None:
    out.append(f"\n  {title}")
    out.append(f"  {'band':<16} {'n':>5} {'avg_pred':>9} {'actual':>8} {'diff':>8}  flags")
    out.append("  " + "-" * 60)
    for s in stats:
        if s["n"] == 0:
            out.append(f"  {s['band']:<16} {0:>5} {'--':>9} {'--':>8} {'--':>8}")
            continue
        flags = []
        if s["n"] < SMALL_SAMPLE_BUCKET:
            flags.append(f"small n<{SMALL_SAMPLE_BUCKET}")
        if abs(s["diff"]) >= 0.05 and s["n"] >= SMALL_SAMPLE_BUCKET:
            flags.append("LARGE DIFF")
        out.append(
            f"  {s['band']:<16} {s['n']:>5} {s['avg_pred']:>8.1%} "
            f"{s['actual']:>7.1%} {s['diff']:>+7.1%}  {', '.join(flags)}"
        )
    if total_n < SMALL_SAMPLE_TOTAL:
        out.append(f"  [caveat] total n={total_n} < {SMALL_SAMPLE_TOTAL} — "
                   "no threshold/calibration action permitted on this sample")


# ── Source loaders — frozen model_prob + settled outcome only ─────────────────

def load_results_csv() -> list[tuple[float, int]]:
    path = DATA_DIR / "results.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r.get("hr_result", "") not in ("0", "1"):
                continue   # skip void / unsettled
            try:
                prob = float(r.get("model_prob_pct", "") or "") / 100.0
            except ValueError:
                continue
            rows.append((prob, int(r["hr_result"])))
    return rows


def load_pick_tracker_csv() -> list[tuple[float, int]]:
    path = DATA_DIR / "pick_tracker.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r.get("hr_result", "").strip() not in ("0", "1"):
                continue
            try:
                prob = float(r.get("model_prob_pct", "") or "") / 100.0
            except ValueError:
                continue
            rows.append((prob, int(r["hr_result"])))
    return rows


def load_supabase_legs() -> list[tuple[float, int]] | None:
    """Settled, non-removed legs. Returns None (not []) when creds are missing."""
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY")):
        return None
    try:
        from supabase import create_client
        client = create_client(os.environ["SUPABASE_URL"],
                               os.environ["SUPABASE_SERVICE_KEY"])
        res = (client.table("legs")
               .select("model_prob, hr_result")
               .eq("settlement_status", "settled")
               .eq("removed", False)
               .not_.is_("hr_result", "null")
               .execute())
    except Exception as exc:
        print(f"  [legs] Supabase fetch failed: {exc}")
        return None
    rows = []
    for r in res.data or []:
        try:
            rows.append((float(r["model_prob"]), int(r["hr_result"])))
        except (TypeError, ValueError):
            continue
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    out: list[str] = []
    out.append("=" * 66)
    out.append("  LIVE CALIBRATION ROLLUP — frozen model_prob vs actual HR rate")
    out.append(f"  data dir: {DATA_DIR}")
    out.append("=" * 66)

    sources = [
        ("CSV lane — results.csv (settled qualified picks)", load_results_csv()),
        ("CSV lane — pick_tracker.csv (settled tracker rows)", load_pick_tracker_csv()),
        ("Legs lane — Supabase legs (settled, non-removed)", load_supabase_legs()),
    ]

    for title, rows in sources:
        out.append(f"\n{'-' * 66}\nSOURCE: {title}")
        if rows is None:
            out.append("  skipped — Supabase credentials unavailable")
            continue
        if not rows:
            out.append("  no settled rows found")
            continue
        out.append(f"  settled rows: {len(rows)}")
        _fmt_table("FS tier bands (FS_TIER_THRESHOLDS)", _rollup_tiers(rows), len(rows), out)
        _fmt_table("5pp buckets", _rollup_5pp(rows), len(rows), out)

    report = "\n".join(out)
    print(report)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\nSaved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
