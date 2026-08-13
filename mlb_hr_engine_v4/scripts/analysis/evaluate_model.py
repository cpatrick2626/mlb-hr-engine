"""Canonical, read-only evaluation harness for MLB HR Engine ``model_prob``.

The canonical evaluation population is fixed by policy:

1. one row per ``(slate_date, batter_id, game_pk)``;
2. the latest snapshot whose ``game_status`` is exactly ``Preview`` and whose
   ``run_ts`` is strictly earlier than ``game_time_utc``;
3. a finite ``model_prob`` in [0, 1] paired with ``hr_outcome`` in {0, 1}.

``model_prob`` is read from ``batter_stat_history.raw_payload`` exactly as it
was captured. The harness never imports or replays a current scoring or
calibration function, so it cannot rewrite history or leak a later fit into an
earlier prediction. Database access is SELECT-only and the script writes no
files.

The AUC confidence interval uses a slate-date cluster bootstrap because rows
within the same slate are correlated. The temporal split is also date-based:
the earliest 70% of distinct dates are the development/reference period and
the latest 30% are the untouched evaluation period. No model is fitted here.

Examples (from ``mlb_hr_engine_v4``):

    python scripts/analysis/evaluate_model.py
    python scripts/analysis/evaluate_model.py --start-date 2026-07-22 \
        --end-date 2026-08-06 --bootstrap-samples 5000 --seed 20260807
    python scripts/analysis/evaluate_model.py --json

Required environment variables (loaded from ``mlb_hr_engine_v4/.env`` when
present): ``SUPABASE_URL`` and ``SUPABASE_SERVICE_KEY``.
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
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

from dotenv import load_dotenv


DEFAULT_BOOTSTRAP_SAMPLES = 5_000
DEFAULT_SEED = 20_260_807
TEMPORAL_REFERENCE_FRACTION = 0.70
TIER_ORDER = ("APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD")


@dataclass(frozen=True)
class EvalRow:
    slate_date: str
    run_ts: datetime
    batter_id: int
    game_pk: int
    game_time_utc: datetime
    game_status: str
    model_prob: float
    hr_outcome: int
    tier: str | None
    model_tier_rank: str | None

    @property
    def key(self) -> tuple[str, int, int]:
        return (self.slate_date, self.batter_id, self.game_pk)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate recorded model_prob on the canonical pre-start warehouse population."
    )
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=DEFAULT_BOOTSTRAP_SAMPLES,
        help=f"slate-date cluster bootstrap replicates (default: {DEFAULT_BOOTSTRAP_SAMPLES})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"bootstrap RNG seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=1_000,
        help="Supabase page size, 1..1000 (default: 1000)",
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


def _load_client():
    engine_root = Path(__file__).resolve().parents[2]
    load_dotenv(engine_root / ".env")
    missing = [
        name
        for name in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        raise SystemExit(f"missing required environment variable(s): {', '.join(missing)}")
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SystemExit("supabase package is required to run this harness") from exc
    return create_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
    )


def _labeled_date_bound(client, *, descending: bool) -> date:
    result = (
        client.table("batter_stat_history")
        .select("slate_date")
        .in_("hr_outcome", [0, 1])
        .order("slate_date", desc=descending)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        raise SystemExit("no labeled batter_stat_history rows found")
    return date.fromisoformat(rows[0]["slate_date"])


def fetch_labeled_rows(
    client,
    *,
    start_date: date | None,
    end_date: date | None,
    page_size: int,
) -> tuple[list[dict], date, date]:
    """Fetch labeled warehouse rows with stable composite ordering.

    Pagination is performed one slate date at a time. Ordering by run timestamp,
    batter, and game makes page boundaries deterministic even though every row
    in a pipeline snapshot shares the same ``run_ts``.
    """

    first_labeled = _labeled_date_bound(client, descending=False)
    last_labeled = _labeled_date_bound(client, descending=True)
    first = max(first_labeled, start_date) if start_date else first_labeled
    last = min(last_labeled, end_date) if end_date else last_labeled
    if first > last:
        raise SystemExit(
            f"requested date range has no labeled data ({first_labeled} through {last_labeled})"
        )

    select_fields = (
        "slate_date,run_ts,batter_id,game_pk,hr_outcome,"
        "model_prob:raw_payload->>model_prob,"
        "game_time_utc:raw_payload->>game_time_utc,"
        "game_status:raw_payload->>game_status,"
        "model_tier_rank:raw_payload->>model_tier_rank"
    )
    rows: list[dict] = []
    day = first
    while day <= last:
        page = 0
        while True:
            lo = page * page_size
            batch = (
                client.table("batter_stat_history")
                .select(select_fields)
                .eq("slate_date", day.isoformat())
                .in_("hr_outcome", [0, 1])
                .order("run_ts", desc=False)
                .order("batter_id", desc=False)
                .order("game_pk", desc=False)
                .range(lo, lo + page_size - 1)
                .execute()
            ).data or []
            rows.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
        day += timedelta(days=1)
    return rows, first, last


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


def _parse_tier(model_tier_rank: object) -> str | None:
    if not isinstance(model_tier_rank, str) or not model_tier_rank.strip():
        return None
    candidate = model_tier_rank.strip().split()[0].upper()
    return candidate if candidate in TIER_ORDER else None


def parse_valid_rows(raw_rows: Sequence[dict]) -> tuple[list[EvalRow], Counter]:
    diagnostics: Counter = Counter(fetched_labeled_rows=len(raw_rows))
    valid: list[EvalRow] = []
    for raw in raw_rows:
        try:
            slate_date = date.fromisoformat(str(raw.get("slate_date"))).isoformat()
            batter_id = int(raw["batter_id"])
            game_pk = int(raw["game_pk"])
            outcome = int(raw["hr_outcome"])
            probability = float(raw["model_prob"])
        except (KeyError, TypeError, ValueError):
            diagnostics["invalid_identity_probability_or_outcome"] += 1
            continue
        if outcome not in (0, 1) or not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            diagnostics["invalid_identity_probability_or_outcome"] += 1
            continue

        run_ts = _parse_utc(raw.get("run_ts"))
        game_time = _parse_utc(raw.get("game_time_utc"))
        if run_ts is None:
            diagnostics["missing_or_invalid_run_ts"] += 1
            continue
        if game_time is None:
            diagnostics["missing_or_invalid_game_time_utc"] += 1
            continue

        rank = raw.get("model_tier_rank")
        valid.append(
            EvalRow(
                slate_date=slate_date,
                run_ts=run_ts,
                batter_id=batter_id,
                game_pk=game_pk,
                game_time_utc=game_time,
                game_status=str(raw.get("game_status") or ""),
                model_prob=probability,
                hr_outcome=outcome,
                tier=_parse_tier(rank),
                model_tier_rank=str(rank) if rank is not None else None,
            )
        )
    diagnostics["valid_scored_labeled_snapshots"] = len(valid)
    return valid, diagnostics


def latest_per_key(rows: Iterable[EvalRow]) -> list[EvalRow]:
    latest: dict[tuple[str, int, int], EvalRow] = {}
    for row in rows:
        prior = latest.get(row.key)
        if prior is None or row.run_ts > prior.run_ts:
            latest[row.key] = row
    return sorted(latest.values(), key=lambda row: (row.slate_date, row.batter_id, row.game_pk))


def canonicalize(rows: Sequence[EvalRow], diagnostics: Counter) -> list[EvalRow]:
    all_keys = {row.key for row in rows}
    diagnostics["unique_batter_games_any_snapshot"] = len(all_keys)
    diagnostics["non_preview_snapshots"] = sum(row.game_status != "Preview" for row in rows)
    diagnostics["preview_at_or_after_start"] = sum(
        row.game_status == "Preview" and row.run_ts >= row.game_time_utc for row in rows
    )
    candidates = [
        row
        for row in rows
        if row.game_status == "Preview" and row.run_ts < row.game_time_utc
    ]
    canonical = latest_per_key(candidates)
    diagnostics["canonical_candidate_snapshots"] = len(candidates)
    diagnostics["canonical_duplicate_snapshots_removed"] = len(candidates) - len(canonical)
    diagnostics["canonical_rows"] = len(canonical)
    diagnostics["unique_batter_games_without_canonical_row"] = len(all_keys) - len(canonical)
    return canonical


def weighted_auc(
    rows_sorted_by_score: Sequence[EvalRow], date_weights: dict[str, int] | None = None
) -> float | None:
    """Tie-aware weighted Mann-Whitney AUC.

    ``date_weights`` supplies cluster-bootstrap multiplicities. Sorting is done
    once outside bootstrap loops; every replicate is then linear in row count.
    """

    weights = date_weights or {}
    default_weight = 1 if date_weights is None else 0
    total_pos = sum(
        (weights.get(row.slate_date, default_weight) * row.hr_outcome)
        for row in rows_sorted_by_score
    )
    total = sum(weights.get(row.slate_date, default_weight) for row in rows_sorted_by_score)
    total_neg = total - total_pos
    if total_pos <= 0 or total_neg <= 0:
        return None

    concordance = 0.0
    negative_weight_below = 0
    index = 0
    while index < len(rows_sorted_by_score):
        end = index + 1
        score = rows_sorted_by_score[index].model_prob
        while end < len(rows_sorted_by_score) and rows_sorted_by_score[end].model_prob == score:
            end += 1
        group_pos = 0
        group_neg = 0
        for row in rows_sorted_by_score[index:end]:
            weight = weights.get(row.slate_date, default_weight)
            if row.hr_outcome:
                group_pos += weight
            else:
                group_neg += weight
        concordance += group_pos * (negative_weight_below + 0.5 * group_neg)
        negative_weight_below += group_neg
        index = end
    return concordance / (total_pos * total_neg)


def _percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("cannot compute a percentile of an empty sequence")
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    fraction = position - lower
    return values[lower] * (1.0 - fraction) + values[upper] * fraction


def cluster_bootstrap_auc(
    rows: Sequence[EvalRow], *, samples: int, seed: int
) -> dict[str, float | int | None]:
    sorted_rows = sorted(rows, key=lambda row: row.model_prob)
    dates = sorted({row.slate_date for row in rows})
    point = weighted_auc(sorted_rows)
    if point is None or len(dates) < 2:
        return {
            "auc": point,
            "ci_low": None,
            "ci_high": None,
            "successful_replicates": 0,
            "requested_replicates": samples,
            "seed": seed,
            "clusters": len(dates),
        }

    rng = random.Random(seed)
    boot: list[float] = []
    for _ in range(samples):
        date_weights = Counter(rng.choice(dates) for _ in dates)
        value = weighted_auc(sorted_rows, date_weights)
        if value is not None:
            boot.append(value)
    boot.sort()
    if not boot:
        low = high = None
    else:
        low = _percentile(boot, 0.025)
        high = _percentile(boot, 0.975)
    return {
        "auc": point,
        "ci_low": low,
        "ci_high": high,
        "successful_replicates": len(boot),
        "requested_replicates": samples,
        "seed": seed,
        "clusters": len(dates),
    }


def calibration_deciles(rows: Sequence[EvalRow]) -> tuple[list[dict], float]:
    ordered = sorted(rows, key=lambda row: (row.model_prob, row.slate_date, row.batter_id, row.game_pk))
    total = len(ordered)
    deciles: list[dict] = []
    ece = 0.0
    for decile in range(10):
        lo = decile * total // 10
        hi = (decile + 1) * total // 10
        subset = ordered[lo:hi]
        if not subset:
            continue
        mean_pred = sum(row.model_prob for row in subset) / len(subset)
        observed = sum(row.hr_outcome for row in subset) / len(subset)
        gap = mean_pred - observed
        ece += (len(subset) / total) * abs(gap)
        deciles.append(
            {
                "decile": decile + 1,
                "n": len(subset),
                "hrs": sum(row.hr_outcome for row in subset),
                "min_pred": subset[0].model_prob,
                "max_pred": subset[-1].model_prob,
                "mean_pred": mean_pred,
                "observed_rate": observed,
                "gap": gap,
            }
        )
    return deciles, ece


def score_metrics(
    rows: Sequence[EvalRow], *, bootstrap_samples: int, seed: int
) -> dict:
    if not rows:
        raise ValueError("evaluation population is empty")
    n = len(rows)
    positives = sum(row.hr_outcome for row in rows)
    base_rate = positives / n
    mean_pred = sum(row.model_prob for row in rows) / n
    brier = sum((row.model_prob - row.hr_outcome) ** 2 for row in rows) / n
    base_brier = sum((base_rate - row.hr_outcome) ** 2 for row in rows) / n
    brier_skill = None if base_brier == 0 else 1.0 - brier / base_brier
    deciles, ece = calibration_deciles(rows)
    return {
        "n": n,
        "positives": positives,
        "negatives": n - positives,
        "date_start": min(row.slate_date for row in rows),
        "date_end": max(row.slate_date for row in rows),
        "distinct_dates": len({row.slate_date for row in rows}),
        "mean_predicted": mean_pred,
        "observed_rate": base_rate,
        "brier": brier,
        "base_rate_brier": base_brier,
        "brier_skill": brier_skill,
        "ece_deciles": ece,
        "auc_cluster_bootstrap": cluster_bootstrap_auc(
            rows, samples=bootstrap_samples, seed=seed
        ),
        "calibration_deciles": deciles,
    }


def tier_metrics(rows: Sequence[EvalRow]) -> dict:
    grouped: dict[str, list[EvalRow]] = defaultdict(list)
    for row in rows:
        if row.tier:
            grouped[row.tier].append(row)
    results: list[dict] = []
    for index, tier in enumerate(TIER_ORDER):
        subset = grouped.get(tier, [])
        below = TIER_ORDER[index + 1] if index + 1 < len(TIER_ORDER) else None
        below_rows = grouped.get(below, []) if below else []
        rate = sum(row.hr_outcome for row in subset) / len(subset) if subset else None
        below_rate = (
            sum(row.hr_outcome for row in below_rows) / len(below_rows) if below_rows else None
        )
        results.append(
            {
                "tier": tier,
                "n": len(subset),
                "hrs": sum(row.hr_outcome for row in subset),
                "observed_rate": rate,
                "below_tier": below,
                "lift_vs_below_pp": (
                    None if rate is None or below_rate is None else (rate - below_rate) * 100.0
                ),
                "orders_above_below": (
                    None if rate is None or below_rate is None else rate > below_rate
                ),
            }
        )
    classified = sum(len(grouped[tier]) for tier in TIER_ORDER)
    return {
        "source": "captured raw_payload.model_tier_rank prefix; no current thresholds replayed",
        "classified_rows": classified,
        "unclassified_rows": len(rows) - classified,
        "tiers": results,
    }


def temporal_split(rows: Sequence[EvalRow]) -> tuple[list[EvalRow], list[EvalRow], dict]:
    dates = sorted({row.slate_date for row in rows})
    if len(dates) < 2:
        raise ValueError("temporal holdout requires at least two distinct slate dates")
    cut = int(len(dates) * TEMPORAL_REFERENCE_FRACTION)
    cut = max(1, min(len(dates) - 1, cut))
    reference_dates = set(dates[:cut])
    reference = [row for row in rows if row.slate_date in reference_dates]
    holdout = [row for row in rows if row.slate_date not in reference_dates]
    return reference, holdout, {
        "requested_reference_fraction": TEMPORAL_REFERENCE_FRACTION,
        "reference_dates": dates[:cut],
        "holdout_dates": dates[cut:],
        "note": "date split only; no model or calibration fit is performed by this harness",
    }


def canonical_fingerprint(rows: Sequence[EvalRow]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item.key):
        record = {
            "slate_date": row.slate_date,
            "run_ts": row.run_ts.isoformat(),
            "batter_id": row.batter_id,
            "game_pk": row.game_pk,
            "game_time_utc": row.game_time_utc.isoformat(),
            "game_status": row.game_status,
            "model_prob": row.model_prob,
            "hr_outcome": row.hr_outcome,
            "model_tier_rank": row.model_tier_rank,
        }
        digest.update(json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def alternate_population_diagnostics(rows: Sequence[EvalRow]) -> list[dict]:
    populations = [
        (
            "all_labeled_snapshots",
            "Repeated run_ts snapshots; no status/time canonicalization.",
            list(rows),
        ),
        (
            "latest_snapshot_any_status_or_time",
            "One latest row per batter-game, including Live/post-start captures.",
            latest_per_key(rows),
        ),
        (
            "latest_strict_prestart_any_status",
            "One latest run_ts < game_time_utc row per batter-game; Live status is not excluded.",
            latest_per_key(row for row in rows if row.run_ts < row.game_time_utc),
        ),
        (
            "canonical_preview_strict_prestart",
            "One latest Preview row strictly before game_time_utc per batter-game.",
            latest_per_key(
                row
                for row in rows
                if row.game_status == "Preview" and row.run_ts < row.game_time_utc
            ),
        ),
    ]
    output = []
    for name, definition, population in populations:
        auc = weighted_auc(sorted(population, key=lambda row: row.model_prob))
        output.append(
            {
                "name": name,
                "definition": definition,
                "n": len(population),
                "positives": sum(row.hr_outcome for row in population),
                "auc": auc,
                "status_counts": dict(sorted(Counter(row.game_status for row in population).items())),
            }
        )
    return output


def build_report(
    raw_rows: Sequence[dict],
    *,
    fetched_start: date,
    fetched_end: date,
    bootstrap_samples: int,
    seed: int,
) -> dict:
    valid_rows, diagnostics = parse_valid_rows(raw_rows)
    canonical = canonicalize(valid_rows, diagnostics)
    if not canonical:
        raise SystemExit("canonical population is empty")
    reference, holdout, split_definition = temporal_split(canonical)
    overall = score_metrics(canonical, bootstrap_samples=bootstrap_samples, seed=seed)
    reference_metrics = score_metrics(
        reference, bootstrap_samples=bootstrap_samples, seed=seed + 1
    )
    holdout_metrics = score_metrics(
        holdout, bootstrap_samples=bootstrap_samples, seed=seed + 2
    )
    return {
        "harness": {
            "script": str(Path(__file__).resolve()),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "database_access": "SELECT-only",
            "probability_source": "batter_stat_history.raw_payload.model_prob as captured; no scoring transform replayed",
            "canonical_definition": [
                "one row per (slate_date, batter_id, game_pk)",
                "latest game_status='Preview' snapshot",
                "run_ts strictly less than game_time_utc",
                "finite model_prob in [0,1] paired with hr_outcome in {0,1}",
            ],
            "fetched_date_start": fetched_start.isoformat(),
            "fetched_date_end": fetched_end.isoformat(),
            "bootstrap_method": "percentile cluster bootstrap resampling slate_date",
            "bootstrap_samples": bootstrap_samples,
            "seed": seed,
            "canonical_sha256": canonical_fingerprint(canonical),
        },
        "diagnostics": dict(diagnostics),
        "canonical": overall,
        "per_tier": tier_metrics(canonical),
        "temporal_split": {
            "definition": split_definition,
            "reference": reference_metrics,
            "holdout": holdout_metrics,
        },
        "alternate_populations": alternate_population_diagnostics(valid_rows),
    }


def _pct(value: float | None, digits: int = 2) -> str:
    return "--" if value is None else f"{value * 100:.{digits}f}%"


def _auc_ci(metrics: dict) -> str:
    auc = metrics["auc_cluster_bootstrap"]
    if auc["auc"] is None:
        return "--"
    return f"{auc['auc']:.4f} [{auc['ci_low']:.4f}, {auc['ci_high']:.4f}]"


def render_text(report: dict) -> str:
    h = report["harness"]
    d = report["diagnostics"]
    c = report["canonical"]
    lines = [
        "MLB HR ENGINE — CANONICAL MODEL EVALUATION",
        "=" * 78,
        "CANONICAL POPULATION",
        "  one row per (slate_date, batter_id, game_pk)",
        "  latest game_status='Preview' prediction with run_ts < game_time_utc",
        "  captured model_prob in [0,1] paired with hr_outcome in {0,1}",
        f"  fetched labeled date range: {h['fetched_date_start']} through {h['fetched_date_end']}",
        f"  canonical date range: {c['date_start']} through {c['date_end']} ({c['distinct_dates']} slates)",
        f"  n={c['n']:,}  HRs={c['positives']:,}  non-HRs={c['negatives']:,}",
        f"  canonical SHA-256: {h['canonical_sha256']}",
        "",
        "OVERALL METRICS",
        f"  AUC (95% slate-date cluster-bootstrap CI): {_auc_ci(c)}",
        f"  mean predicted: {_pct(c['mean_predicted'])}",
        f"  observed HR rate: {_pct(c['observed_rate'])}",
        f"  ECE (prediction deciles): {_pct(c['ece_deciles'])}",
        f"  Brier: {c['brier']:.6f}",
        f"  base-rate Brier: {c['base_rate_brier']:.6f}",
        f"  Brier skill vs base rate: {_pct(c['brier_skill'])}",
        "",
        "CALIBRATION BY PREDICTION DECILE (D1=lowest, D10=highest)",
        "  decile     n   HRs        range       mean pred   observed       gap",
    ]
    for item in c["calibration_deciles"]:
        lines.append(
            f"  D{item['decile']:<2d}    {item['n']:5d} {item['hrs']:5d}  "
            f"{_pct(item['min_pred']):>7s}-{_pct(item['max_pred']):<7s}  "
            f"{_pct(item['mean_pred']):>9s}  {_pct(item['observed_rate']):>9s}  "
            f"{item['gap'] * 100:+8.2f}pp"
        )

    tier = report["per_tier"]
    lines.extend(
        [
            "",
            "PER-TIER OBSERVED HR RATE",
            f"  source: {tier['source']}",
            f"  classified={tier['classified_rows']:,}  unclassified={tier['unclassified_rows']:,}",
            "  tier        n   HRs   observed   lift vs next tier   orders?",
        ]
    )
    for item in tier["tiers"]:
        lift = "--" if item["lift_vs_below_pp"] is None else f"{item['lift_vs_below_pp']:+.2f}pp"
        ordered = (
            "--"
            if item["orders_above_below"] is None
            else ("YES" if item["orders_above_below"] else "NO")
        )
        lines.append(
            f"  {item['tier']:<6s}  {item['n']:6d} {item['hrs']:5d}  "
            f"{_pct(item['observed_rate']):>8s}  {lift:>17s}  {ordered:>7s}"
        )

    temporal = report["temporal_split"]
    ref = temporal["reference"]
    hold = temporal["holdout"]
    lines.extend(
        [
            "",
            "TEMPORAL HOLDOUT (date-based; no fitting performed)",
            "  period       dates                  n   HRs          AUC [95% CI]   Brier   BSS",
            f"  reference    {ref['date_start']}..{ref['date_end']}  {ref['n']:5d} {ref['positives']:5d}  "
            f"{_auc_ci(ref):>22s}  {ref['brier']:.5f}  {_pct(ref['brier_skill']):>7s}",
            f"  holdout      {hold['date_start']}..{hold['date_end']}  {hold['n']:5d} {hold['positives']:5d}  "
            f"{_auc_ci(hold):>22s}  {hold['brier']:.5f}  {_pct(hold['brier_skill']):>7s}",
            "",
            "POPULATION RECONCILIATION DIAGNOSTICS",
            "  population                                n   HRs      AUC   statuses",
        ]
    )
    for item in report["alternate_populations"]:
        statuses = ", ".join(f"{k}={v}" for k, v in item["status_counts"].items())
        lines.append(
            f"  {item['name']:<39s} {item['n']:6d} {item['positives']:5d}  "
            f"{item['auc']:.4f}   {statuses}"
        )

    lines.extend(
        [
            "",
            "FILTER DIAGNOSTICS",
            f"  fetched labeled rows: {d.get('fetched_labeled_rows', 0):,}",
            f"  valid scored/labeled snapshots: {d.get('valid_scored_labeled_snapshots', 0):,}",
            f"  canonical candidate snapshots: {d.get('canonical_candidate_snapshots', 0):,}",
            f"  duplicate canonical candidates removed: {d.get('canonical_duplicate_snapshots_removed', 0):,}",
            f"  batter-games with no canonical row: {d.get('unique_batter_games_without_canonical_row', 0):,}",
            f"  Preview snapshots at/after start excluded: {d.get('preview_at_or_after_start', 0):,}",
            f"  non-Preview snapshots excluded: {d.get('non_preview_snapshots', 0):,}",
            "",
            f"REPRODUCE: --start-date {h['fetched_date_start']} --end-date {h['fetched_date_end']} "
            f"--bootstrap-samples {h['bootstrap_samples']} --seed {h['seed']}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    client = _load_client()
    raw_rows, fetched_start, fetched_end = fetch_labeled_rows(
        client,
        start_date=args.start_date,
        end_date=args.end_date,
        page_size=args.page_size,
    )
    report = build_report(
        raw_rows,
        fetched_start=fetched_start,
        fetched_end=fetched_end,
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
