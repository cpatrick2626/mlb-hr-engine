"""Canonical, read-only JIG evaluation harness for MLB HR Engine.

Mirrors evaluate_model.py's canonical-population methodology applied to the
JIG tactical score (jigScore, jigScore_shadow) instead of model_prob.

DATA SOURCES — two-table join on (slate_date, batter_id, game_pk):
  1. pipeline_runs.payload.slate_cache.leaderboard_rows_jig
       jigScore, jigScore_shadow, jigTier per batter-game per date
  2. batter_stat_history (canonical Preview pre-start rows, same filter as
       evaluate_model.py)
       hr_outcome, model_prob

NOTE ON jigScore NATURE:
  jigScore is a 0–100 tactical index, NOT a probability. Probability
  calibration analysis (predicted rate vs. observed) does not apply. This
  harness reports AUC, per-tier lift, MAIN redundancy (Pearson correlation
  + paired delta AUC), shadow comparison, and temporal holdout.

REDUNDANCY METRIC:
  - Pearson r between jigScore and model_prob on joined rows
  - Paired delta AUC: AUC(MAIN+JIG blend) minus AUC(MAIN alone), with
    the same slate-cluster bootstrap so the delta CI is correlated-correct.
    Blend = 0.5 * model_prob + 0.5 * (jigScore / 100). A positive delta
    with CI above zero means JIG adds discriminative signal over MAIN.

SHADOW:
  jigScore_shadow was added 2026-08-09. Only pipeline_runs rows from that
  date forward will have it. Small-sample note is emitted if n < 200.

Examples (from mlb_hr_engine_v4/):
    python scripts/analysis/evaluate_jig.py
    python scripts/analysis/evaluate_jig.py --start-date 2026-07-22 --end-date 2026-08-09
    python scripts/analysis/evaluate_jig.py --json

Required env vars (loaded from mlb_hr_engine_v4/.env):
    SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv


DEFAULT_BOOTSTRAP_SAMPLES = 5_000
DEFAULT_SEED = 20_260_808
TEMPORAL_REFERENCE_FRACTION = 0.70
JIG_TIER_ORDER = ("APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD")
SHADOW_SMALL_SAMPLE_THRESHOLD = 200


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class JigRow:
    slate_date: str
    batter_id: int
    game_pk: int
    jig_score: float           # live jigScore (0–100)
    jig_score_shadow: float | None  # shadow signal; None on pre-shadow pipeline runs
    jig_tier: str | None
    model_prob: float | None   # from batter_stat_history canonical row
    hr_outcome: int

    @property
    def key(self) -> tuple[str, int, int]:
        return (self.slate_date, self.batter_id, self.game_pk)


# ── CLI ────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate JIG jigScore against HR outcomes via two-table join."
    )
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument(
        "--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES,
        help=f"slate-date cluster bootstrap replicates (default: {DEFAULT_BOOTSTRAP_SAMPLES})",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"bootstrap RNG seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--page-size", type=int, default=1_000,
        help="Supabase page size 1..1000 (default: 1000)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    if args.bootstrap_samples < 100:
        parser.error("--bootstrap-samples must be at least 100")
    if not 1 <= args.page_size <= 1_000:
        parser.error("--page-size must be between 1 and 1000")
    if args.start_date and args.end_date and args.start_date > args.end_date:
        parser.error("--start-date must be on or before --end-date")
    return args


# ── Supabase client ────────────────────────────────────────────────────────────

def _load_client():
    engine_root = Path(__file__).resolve().parents[2]
    load_dotenv(engine_root / ".env")
    missing = [n for n in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY") if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"missing required env var(s): {', '.join(missing)}")
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SystemExit("supabase package required") from exc
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ── Source 1: pipeline_runs → JIG scores ──────────────────────────────────────

def _fetch_jig_from_pipeline_runs(
    client,
    *,
    start_date: date | None,
    end_date: date | None,
    page_size: int,
) -> tuple[dict[tuple[str, int, int], dict], set[str]]:
    """Fetch all jig rows from pipeline_runs.payload.slate_cache.leaderboard_rows_jig.

    Returns:
      jig_by_key: {(slate_date, batter_id, game_pk): {jig_score, jig_score_shadow, jig_tier}}
      dates_seen: set of slate_date strings present in pipeline_runs
    """
    # Fetch pipeline_runs rows within the date range.
    # pipeline_runs is keyed by date (string "YYYY-MM-DD").
    # We fetch date + payload; payload is a large JSON blob.
    query = client.table("pipeline_runs").select("date,payload")
    if start_date:
        query = query.gte("date", start_date.isoformat())
    if end_date:
        query = query.lte("date", end_date.isoformat())
    query = query.order("date", desc=False)

    jig_by_key: dict[tuple[str, int, int], dict] = {}
    dates_seen: set[str] = set()

    offset = 0
    while True:
        batch = query.range(offset, offset + page_size - 1).execute().data or []
        for row in batch:
            slate_date = str(row.get("date") or "")
            if not slate_date:
                continue
            payload = row.get("payload") or {}
            sc = payload.get("slate_cache") or {}
            jig_rows = sc.get("leaderboard_rows_jig") or []
            if not jig_rows:
                continue
            dates_seen.add(slate_date)
            for jr in jig_rows:
                raw_id = jr.get("id")
                game_pk = jr.get("game_pk")
                jig_score = jr.get("jigScore")
                jig_score_shadow = jr.get("jigScore_shadow")  # None pre-2026-08-09
                jig_tier_raw = jr.get("jigTier")

                # Require integer batter_id for reliable join
                try:
                    batter_id = int(raw_id)
                except (TypeError, ValueError):
                    continue  # name-slug fallback — cannot join
                try:
                    game_pk = int(game_pk)
                except (TypeError, ValueError):
                    continue
                if jig_score is None or not math.isfinite(float(jig_score)):
                    continue

                jig_tier = (
                    str(jig_tier_raw).strip().upper()
                    if isinstance(jig_tier_raw, str) and jig_tier_raw.strip()
                    else None
                )
                if jig_tier not in JIG_TIER_ORDER:
                    jig_tier = None

                shadow_val = None
                if jig_score_shadow is not None:
                    try:
                        shadow_val = float(jig_score_shadow)
                        if not math.isfinite(shadow_val):
                            shadow_val = None
                    except (TypeError, ValueError):
                        shadow_val = None

                key = (slate_date, batter_id, game_pk)
                # Keep first occurrence per (date, batter, game) — pipeline_runs
                # is one row per date so duplicates shouldn't arise within a date.
                if key not in jig_by_key:
                    jig_by_key[key] = {
                        "jig_score": float(jig_score),
                        "jig_score_shadow": shadow_val,
                        "jig_tier": jig_tier,
                    }
        if len(batch) < page_size:
            break
        offset += page_size

    return jig_by_key, dates_seen


# ── Source 2: batter_stat_history → hr_outcome + model_prob ───────────────────

def _parse_utc(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fetch_warehouse_rows(
    client,
    *,
    dates: set[str],
    page_size: int,
) -> dict[tuple[str, int, int], dict]:
    """Fetch canonical batter_stat_history rows for the given slate dates.

    Returns:
      warehouse_by_key: {(slate_date, batter_id, game_pk): {model_prob, run_ts,
                          game_time_utc, game_status, hr_outcome}}

    Applies the same Preview/pre-start canonicalization as evaluate_model.py:
    latest game_status='Preview' run_ts strictly before game_time_utc.
    """
    if not dates:
        return {}

    select_fields = (
        "slate_date,run_ts,batter_id,game_pk,hr_outcome,"
        "model_prob:raw_payload->>model_prob,"
        "game_time_utc:raw_payload->>game_time_utc,"
        "game_status:raw_payload->>game_status"
    )

    # Accumulate all candidate snapshots; canonicalize in Python.
    candidates: dict[tuple[str, int, int], list[dict]] = defaultdict(list)

    for slate_date in sorted(dates):
        offset = 0
        while True:
            batch = (
                client.table("batter_stat_history")
                .select(select_fields)
                .eq("slate_date", slate_date)
                .in_("hr_outcome", [0, 1])
                .order("run_ts", desc=False)
                .order("batter_id", desc=False)
                .order("game_pk", desc=False)
                .range(offset, offset + page_size - 1)
                .execute()
            ).data or []
            for raw in batch:
                try:
                    sd = str(raw["slate_date"])
                    bid = int(raw["batter_id"])
                    gpk = int(raw["game_pk"])
                    outcome = int(raw["hr_outcome"])
                except (KeyError, TypeError, ValueError):
                    continue
                if outcome not in (0, 1):
                    continue

                run_ts = _parse_utc(raw.get("run_ts"))
                game_time = _parse_utc(raw.get("game_time_utc"))
                game_status = str(raw.get("game_status") or "")
                if run_ts is None or game_time is None:
                    continue
                if game_status != "Preview" or run_ts >= game_time:
                    continue

                mp_raw = raw.get("model_prob")
                model_prob: float | None = None
                if mp_raw is not None:
                    try:
                        v = float(mp_raw)
                        if math.isfinite(v) and 0.0 <= v <= 1.0:
                            model_prob = v
                    except (TypeError, ValueError):
                        pass

                key = (sd, bid, gpk)
                candidates[key].append({
                    "run_ts": run_ts,
                    "model_prob": model_prob,
                    "hr_outcome": outcome,
                })
            if len(batch) < page_size:
                break
            offset += page_size

    # Pick latest snapshot per key
    warehouse: dict[tuple[str, int, int], dict] = {}
    for key, snaps in candidates.items():
        best = max(snaps, key=lambda s: s["run_ts"])
        warehouse[key] = {"model_prob": best["model_prob"], "hr_outcome": best["hr_outcome"]}
    return warehouse


# ── Join ───────────────────────────────────────────────────────────────────────

def build_joined_rows(
    jig_by_key: dict[tuple[str, int, int], dict],
    warehouse_by_key: dict[tuple[str, int, int], dict],
) -> tuple[list[JigRow], Counter]:
    diag: Counter = Counter(
        jig_snapshots=len(jig_by_key),
        warehouse_canonical_rows=len(warehouse_by_key),
    )
    rows: list[JigRow] = []
    for key, jig in jig_by_key.items():
        wh = warehouse_by_key.get(key)
        if wh is None:
            diag["jig_no_warehouse_match"] += 1
            continue
        diag["joined"] += 1
        rows.append(JigRow(
            slate_date=key[0],
            batter_id=key[1],
            game_pk=key[2],
            jig_score=jig["jig_score"],
            jig_score_shadow=jig["jig_score_shadow"],
            jig_tier=jig["jig_tier"],
            model_prob=wh["model_prob"],
            hr_outcome=wh["hr_outcome"],
        ))
    diag["canonical_rows"] = len(rows)
    return sorted(rows, key=lambda r: r.key), diag


# ── AUC (same logic as evaluate_model.py) ─────────────────────────────────────

def _weighted_auc(rows_sorted_by_score: Sequence, score_fn, date_weights: dict | None = None) -> float | None:
    weights = date_weights or {}
    default_weight = 1 if date_weights is None else 0
    total_pos = sum(
        weights.get(r.slate_date, default_weight) * r.hr_outcome for r in rows_sorted_by_score
    )
    total = sum(weights.get(r.slate_date, default_weight) for r in rows_sorted_by_score)
    total_neg = total - total_pos
    if total_pos <= 0 or total_neg <= 0:
        return None

    concordance = 0.0
    neg_below = 0.0
    i = 0
    while i < len(rows_sorted_by_score):
        j = i + 1
        s = score_fn(rows_sorted_by_score[i])
        while j < len(rows_sorted_by_score) and score_fn(rows_sorted_by_score[j]) == s:
            j += 1
        g_pos = g_neg = 0.0
        for r in rows_sorted_by_score[i:j]:
            w = weights.get(r.slate_date, default_weight)
            if r.hr_outcome:
                g_pos += w
            else:
                g_neg += w
        concordance += g_pos * (neg_below + 0.5 * g_neg)
        neg_below += g_neg
        i = j
    return concordance / (total_pos * total_neg)


def _percentile(values: list[float], p: float) -> float:
    pos = (len(values) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return values[lo]
    return values[lo] * (1.0 - (pos - lo)) + values[hi] * (pos - lo)


def _cluster_bootstrap_auc(
    rows: Sequence[JigRow],
    score_fn,
    *,
    samples: int,
    seed: int,
) -> dict:
    sorted_rows = sorted(rows, key=score_fn)
    dates = sorted({r.slate_date for r in rows})
    point = _weighted_auc(sorted_rows, score_fn)
    if point is None or len(dates) < 2:
        return {"auc": point, "ci_low": None, "ci_high": None,
                "successful_replicates": 0, "requested_replicates": samples,
                "seed": seed, "clusters": len(dates)}
    rng = random.Random(seed)
    boot: list[float] = []
    for _ in range(samples):
        dw = Counter(rng.choice(dates) for _ in dates)
        v = _weighted_auc(sorted_rows, score_fn, dw)
        if v is not None:
            boot.append(v)
    boot.sort()
    return {
        "auc": point,
        "ci_low": _percentile(boot, 0.025) if boot else None,
        "ci_high": _percentile(boot, 0.975) if boot else None,
        "successful_replicates": len(boot),
        "requested_replicates": samples,
        "seed": seed,
        "clusters": len(dates),
    }


# ── Pearson correlation ────────────────────────────────────────────────────────

def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


# ── Tier lift ──────────────────────────────────────────────────────────────────

def _tier_metrics(rows: Sequence[JigRow]) -> dict:
    grouped: dict[str, list[JigRow]] = defaultdict(list)
    for r in rows:
        if r.jig_tier:
            grouped[r.jig_tier].append(r)
    results = []
    for i, tier in enumerate(JIG_TIER_ORDER):
        subset = grouped.get(tier, [])
        below = JIG_TIER_ORDER[i + 1] if i + 1 < len(JIG_TIER_ORDER) else None
        below_rows = grouped.get(below, []) if below else []
        rate = sum(r.hr_outcome for r in subset) / len(subset) if subset else None
        below_rate = sum(r.hr_outcome for r in below_rows) / len(below_rows) if below_rows else None
        results.append({
            "tier": tier,
            "n": len(subset),
            "hrs": sum(r.hr_outcome for r in subset),
            "observed_rate": rate,
            "below_tier": below,
            "lift_vs_below_pp": (
                None if rate is None or below_rate is None else (rate - below_rate) * 100.0
            ),
            "orders_above_below": (
                None if rate is None or below_rate is None else rate > below_rate
            ),
        })
    classified = sum(len(grouped[t]) for t in JIG_TIER_ORDER)
    return {
        "source": "jigTier from pipeline_runs.slate_cache.leaderboard_rows_jig",
        "classified_rows": classified,
        "unclassified_rows": len(rows) - classified,
        "tiers": results,
    }


# ── Temporal split ─────────────────────────────────────────────────────────────

def _temporal_split(rows: Sequence[JigRow]) -> tuple[list[JigRow], list[JigRow], dict]:
    dates = sorted({r.slate_date for r in rows})
    if len(dates) < 2:
        raise ValueError("temporal holdout requires at least two distinct slate dates")
    cut = max(1, min(len(dates) - 1, int(len(dates) * TEMPORAL_REFERENCE_FRACTION)))
    ref_dates = set(dates[:cut])
    ref = [r for r in rows if r.slate_date in ref_dates]
    hold = [r for r in rows if r.slate_date not in ref_dates]
    return ref, hold, {
        "requested_reference_fraction": TEMPORAL_REFERENCE_FRACTION,
        "reference_dates": dates[:cut],
        "holdout_dates": dates[cut:],
        "note": "date split only; no model fit performed",
    }


# ── Redundancy vs MAIN ─────────────────────────────────────────────────────────

def _redundancy_metrics(rows: Sequence[JigRow], *, samples: int, seed: int) -> dict:
    """Correlation between jigScore and model_prob, plus paired delta AUC."""
    paired = [r for r in rows if r.model_prob is not None]
    if not paired:
        return {"n_paired": 0, "note": "no rows with both jigScore and model_prob"}

    jig_vals = [r.jig_score for r in paired]
    prob_vals = [r.model_prob for r in paired]
    corr = _pearson(jig_vals, prob_vals)

    # Paired AUC comparison via shared slate-cluster bootstrap
    # Score functions
    def _score_main(r: JigRow) -> float:
        return r.model_prob  # type: ignore[return-value]

    def _score_combined(r: JigRow) -> float:
        return 0.5 * r.model_prob + 0.5 * (r.jig_score / 100.0)  # type: ignore[operator]

    dates = sorted({r.slate_date for r in paired})
    sorted_main     = sorted(paired, key=_score_main)
    sorted_combined = sorted(paired, key=_score_combined)

    auc_main     = _weighted_auc(sorted_main,     _score_main)
    auc_combined = _weighted_auc(sorted_combined, _score_combined)
    delta_point  = (
        None if auc_main is None or auc_combined is None
        else auc_combined - auc_main
    )

    # Bootstrap delta CI (same slates resampled for both, preserving correlation)
    rng = random.Random(seed)
    delta_boot: list[float] = []
    if len(dates) >= 2 and auc_main is not None:
        for _ in range(samples):
            dw = Counter(rng.choice(dates) for _ in dates)
            vm = _weighted_auc(sorted_main,     _score_main,     dw)
            vc = _weighted_auc(sorted_combined, _score_combined, dw)
            if vm is not None and vc is not None:
                delta_boot.append(vc - vm)
    delta_boot.sort()

    return {
        "n_paired": len(paired),
        "pearson_r_jig_vs_model_prob": corr,
        "auc_main_alone": auc_main,
        "auc_main_plus_jig_blend": auc_combined,
        "delta_auc_point": delta_point,
        "delta_auc_ci_low":  _percentile(delta_boot, 0.025) if len(delta_boot) >= 2 else None,
        "delta_auc_ci_high": _percentile(delta_boot, 0.975) if len(delta_boot) >= 2 else None,
        "delta_bootstrap_replicates": len(delta_boot),
        "blend_formula": "0.5 * model_prob + 0.5 * (jigScore / 100)",
        "interpretation": (
            "positive delta + CI above zero → JIG adds discriminative signal over MAIN; "
            "delta near zero or CI crossing zero → JIG redundant with MAIN; "
            "negative delta → JIG degrades combined ranking"
        ),
    }


# ── Shadow comparison ──────────────────────────────────────────────────────────

def _shadow_metrics(rows: Sequence[JigRow], *, samples: int, seed: int) -> dict:
    shadow_rows = [r for r in rows if r.jig_score_shadow is not None]
    if not shadow_rows:
        return {
            "n_shadow": 0,
            "note": (
                "No jigScore_shadow values found. Shadow was added 2026-08-09. "
                "Accumulate more pipeline runs with the shadow column before re-running."
            ),
        }
    n = len(shadow_rows)
    small_sample = n < SHADOW_SMALL_SAMPLE_THRESHOLD

    def _score_shadow(r: JigRow) -> float:
        return r.jig_score_shadow  # type: ignore[return-value]

    def _score_live(r: JigRow) -> float:
        return r.jig_score

    auc_live   = _cluster_bootstrap_auc(shadow_rows, _score_live,   samples=samples, seed=seed)
    auc_shadow = _cluster_bootstrap_auc(shadow_rows, _score_shadow, samples=samples, seed=seed + 1)

    return {
        "n_shadow": n,
        "small_sample_warning": small_sample,
        "small_sample_threshold": SHADOW_SMALL_SAMPLE_THRESHOLD,
        "auc_live_on_shadow_population":   auc_live,
        "auc_shadow_on_shadow_population": auc_shadow,
        "note": (
            f"Both AUCs computed on the same {n} rows that have jigScore_shadow. "
            "Shadow = rv_per100 pitch-mix signal active; live = dormant (0.0). "
            + ("SMALL SAMPLE — treat as preliminary." if small_sample else "")
        ),
    }


# ── Canonical fingerprint ──────────────────────────────────────────────────────

def _canonical_fingerprint(rows: Sequence[JigRow]) -> str:
    digest = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x.key):
        record = {
            "slate_date": r.slate_date,
            "batter_id": r.batter_id,
            "game_pk": r.game_pk,
            "jig_score": r.jig_score,
            "jig_tier": r.jig_tier,
            "model_prob": r.model_prob,
            "hr_outcome": r.hr_outcome,
        }
        digest.update(json.dumps(record, sort_keys=True, separators=(",", ":")).encode())
        digest.update(b"\n")
    return digest.hexdigest()


# ── Core metrics per population ────────────────────────────────────────────────

def _population_metrics(rows: Sequence[JigRow], *, samples: int, seed: int) -> dict:
    if not rows:
        raise ValueError("population is empty")
    n = len(rows)
    positives = sum(r.hr_outcome for r in rows)
    return {
        "n": n,
        "positives": positives,
        "negatives": n - positives,
        "date_start": min(r.slate_date for r in rows),
        "date_end": max(r.slate_date for r in rows),
        "distinct_dates": len({r.slate_date for r in rows}),
        "observed_rate": positives / n,
        "mean_jig_score": sum(r.jig_score for r in rows) / n,
        "auc_cluster_bootstrap": _cluster_bootstrap_auc(
            rows, lambda r: r.jig_score, samples=samples, seed=seed
        ),
        "calibration_note": (
            "jigScore is a 0–100 tactical index, not a probability. "
            "Traditional calibration (predicted rate vs. observed) does not apply. "
            "Use per-tier lift as the operative performance metric."
        ),
    }


# ── Build full report ──────────────────────────────────────────────────────────

def build_report(
    jig_by_key: dict,
    warehouse_by_key: dict,
    *,
    jig_dates: set[str],
    bootstrap_samples: int,
    seed: int,
) -> dict:
    rows, diag = build_joined_rows(jig_by_key, warehouse_by_key)
    if not rows:
        raise SystemExit(
            "canonical JIG population is empty — no (slate_date, batter_id, game_pk) "
            "keys matched between pipeline_runs.jig_rows and batter_stat_history. "
            "Confirm the pipeline has run for the requested date range and outcomes "
            "have been settled."
        )

    ref, hold, split_def = _temporal_split(rows)

    overall  = _population_metrics(rows, samples=bootstrap_samples, seed=seed)
    ref_met  = _population_metrics(ref,  samples=bootstrap_samples, seed=seed + 1)
    hold_met = _population_metrics(hold, samples=bootstrap_samples, seed=seed + 2)

    return {
        "harness": {
            "script": str(Path(__file__).resolve()),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "database_access": "SELECT-only",
            "jig_score_source": (
                "pipeline_runs.payload.slate_cache.leaderboard_rows_jig[].jigScore "
                "as captured; no scoring transform replayed"
            ),
            "hr_outcome_source": (
                "batter_stat_history: latest game_status='Preview' run_ts < game_time_utc "
                "row per (slate_date, batter_id, game_pk)"
            ),
            "canonical_definition": [
                "one row per (slate_date, batter_id, game_pk)",
                "jigScore from pipeline_runs slate_cache (integer batter_id only)",
                "hr_outcome from batter_stat_history canonical Preview pre-start row",
                "inner join on (slate_date, batter_id, game_pk)",
            ],
            "bootstrap_method": "percentile cluster bootstrap resampling slate_date",
            "bootstrap_samples": bootstrap_samples,
            "seed": seed,
            "canonical_sha256": _canonical_fingerprint(rows),
        },
        "diagnostics": dict(diag),
        "canonical": overall,
        "per_jig_tier": _tier_metrics(rows),
        "redundancy_vs_main": _redundancy_metrics(rows, samples=bootstrap_samples, seed=seed + 10),
        "shadow_comparison": _shadow_metrics(rows, samples=bootstrap_samples, seed=seed + 20),
        "temporal_split": {
            "definition": split_def,
            "reference": ref_met,
            "holdout": hold_met,
        },
    }


# ── Text renderer ──────────────────────────────────────────────────────────────

def _auc_str(auc_dict: dict) -> str:
    a = auc_dict.get("auc")
    lo = auc_dict.get("ci_low")
    hi = auc_dict.get("ci_high")
    if a is None:
        return "--"
    if lo is None or hi is None:
        return f"{a:.4f} [CI unavailable]"
    return f"{a:.4f} [{lo:.4f}, {hi:.4f}]"


def _pct(v: float | None, d: int = 2) -> str:
    return "--" if v is None else f"{v * 100:.{d}f}%"


def render_text(report: dict) -> str:
    h  = report["harness"]
    d  = report["diagnostics"]
    c  = report["canonical"]
    ts = report["temporal_split"]
    ref  = ts["reference"]
    hold = ts["holdout"]
    rd   = report["redundancy_vs_main"]
    sh   = report["shadow_comparison"]
    tier = report["per_jig_tier"]

    lines = [
        "MLB HR ENGINE — JIG EVALUATION HARNESS",
        "=" * 78,
        "DATA SOURCES",
        "  jigScore  : pipeline_runs.payload.slate_cache.leaderboard_rows_jig (as captured)",
        "  hr_outcome: batter_stat_history canonical Preview pre-start row",
        "  join key  : (slate_date, batter_id, game_pk)",
        "",
        "CANONICAL POPULATION",
        f"  n={c['n']:,}  HRs={c['positives']:,}  non-HRs={c['negatives']:,}",
        f"  date range: {c['date_start']} through {c['date_end']} ({c['distinct_dates']} slates)",
        f"  canonical SHA-256: {h['canonical_sha256']}",
        "",
        "DIAGNOSTICS",
        f"  jig snapshots from pipeline_runs       : {d.get('jig_snapshots', 0):,}",
        f"  warehouse canonical rows               : {d.get('warehouse_canonical_rows', 0):,}",
        f"  joined (inner join)                    : {d.get('joined', 0):,}",
        f"  jig rows without warehouse match       : {d.get('jig_no_warehouse_match', 0):,}",
        "",
        "JIG AUC — is jigScore ranking real signal?",
        f"  AUC (95% slate-cluster bootstrap CI): {_auc_str(c['auc_cluster_bootstrap'])}",
        f"  observed HR rate: {_pct(c['observed_rate'])}",
        f"  mean jigScore:    {c['mean_jig_score']:.1f} / 100",
        f"  note: {c['calibration_note']}",
        "",
        "PER-jigTIER OBSERVED HR RATE — do tiers order monotonically?",
        f"  source: {tier['source']}",
        f"  classified={tier['classified_rows']:,}  unclassified={tier['unclassified_rows']:,}",
        "  tier        n   HRs   observed   lift vs next tier   ordered?",
    ]
    for item in tier["tiers"]:
        lift = "--" if item["lift_vs_below_pp"] is None else f"{item['lift_vs_below_pp']:+.2f}pp"
        ordered = "--" if item["orders_above_below"] is None else ("YES" if item["orders_above_below"] else "NO")
        lines.append(
            f"  {item['tier']:<6s}  {item['n']:6d} {item['hrs']:5d}  "
            f"{_pct(item['observed_rate']):>8s}  {lift:>17s}  {ordered:>7s}"
        )

    lines.extend([
        "",
        "REDUNDANCY vs MAIN — does JIG add signal over model_prob?",
        f"  paired rows (both jigScore + model_prob): {rd.get('n_paired', 0):,}",
    ])
    if "note" in rd and rd.get("n_paired", 0) == 0:
        lines.append(f"  {rd['note']}")
    else:
        corr = rd.get("pearson_r_jig_vs_model_prob")
        corr_str = f"{corr:.3f}" if corr is not None else "--"
        lines.extend([
            f"  Pearson r (jigScore vs model_prob): {corr_str}",
            f"  AUC MAIN alone               : {rd['auc_main_alone']:.4f if rd.get('auc_main_alone') is not None else '--'}",
            f"  AUC MAIN + JIG blend         : {rd['auc_main_plus_jig_blend']:.4f if rd.get('auc_main_plus_jig_blend') is not None else '--'}",
        ])
        dp = rd.get("delta_auc_point")
        dl = rd.get("delta_auc_ci_low")
        dh = rd.get("delta_auc_ci_high")
        delta_str = (
            f"{dp:+.4f} [{dl:+.4f}, {dh:+.4f}]"
            if dp is not None and dl is not None and dh is not None
            else ("--" if dp is None else f"{dp:+.4f} [CI unavailable]")
        )
        lines.extend([
            f"  delta AUC (combined − MAIN)  : {delta_str}",
            f"  blend formula: {rd.get('blend_formula', '')}",
            f"  interpretation: {rd.get('interpretation', '')}",
        ])

    lines.extend([
        "",
        "SHADOW COMPARISON — jigScore_shadow vs live jigScore",
        f"  n rows with shadow: {sh.get('n_shadow', 0):,}",
    ])
    if sh.get("n_shadow", 0) == 0:
        lines.append(f"  {sh.get('note', '')}")
    else:
        if sh.get("small_sample_warning"):
            lines.append(f"  *** SMALL SAMPLE (n<{sh['small_sample_threshold']}) — preliminary ***")
        live_sh   = sh.get("auc_live_on_shadow_population", {})
        shadow_sh = sh.get("auc_shadow_on_shadow_population", {})
        lines.extend([
            f"  AUC live   (on shadow pop): {_auc_str(live_sh)}",
            f"  AUC shadow (on shadow pop): {_auc_str(shadow_sh)}",
            f"  note: {sh.get('note', '')}",
        ])

    lines.extend([
        "",
        "TEMPORAL HOLDOUT (date-based; no fitting performed)",
        "  period      dates                  n   HRs        AUC [95% CI]",
        f"  reference   {ref['date_start']}..{ref['date_end']}  "
        f"{ref['n']:5d} {ref['positives']:5d}  {_auc_str(ref['auc_cluster_bootstrap'])}",
        f"  holdout     {hold['date_start']}..{hold['date_end']}  "
        f"{hold['n']:5d} {hold['positives']:5d}  {_auc_str(hold['auc_cluster_bootstrap'])}",
        "",
        f"REPRODUCE: --start-date {c['date_start']} --end-date {c['date_end']} "
        f"--bootstrap-samples {h['bootstrap_samples']} --seed {h['seed']}",
    ])
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = _parse_args()
    client = _load_client()

    print("[evaluate_jig] fetching JIG scores from pipeline_runs ...", file=sys.stderr)
    jig_by_key, jig_dates = _fetch_jig_from_pipeline_runs(
        client,
        start_date=args.start_date,
        end_date=args.end_date,
        page_size=args.page_size,
    )
    if not jig_by_key:
        raise SystemExit(
            "no jigScore rows found in pipeline_runs for the requested date range. "
            "Confirm the pipeline has run and slate_cache was built successfully."
        )
    print(f"[evaluate_jig] {len(jig_by_key):,} jig snapshots across {len(jig_dates)} slates", file=sys.stderr)

    print("[evaluate_jig] fetching canonical warehouse rows (hr_outcome + model_prob) ...", file=sys.stderr)
    warehouse_by_key = _fetch_warehouse_rows(client, dates=jig_dates, page_size=args.page_size)
    print(f"[evaluate_jig] {len(warehouse_by_key):,} canonical warehouse rows", file=sys.stderr)

    report = build_report(
        jig_by_key,
        warehouse_by_key,
        jig_dates=jig_dates,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(render_text(report))


if __name__ == "__main__":
    main()
