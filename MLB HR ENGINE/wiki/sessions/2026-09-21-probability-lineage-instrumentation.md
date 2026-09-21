# 2026-09-21 — MAIN probability-lineage instrumentation

## Status

BUILT / VALIDATED / NOT COMMITTED / NOT PUSHED / NOT DEPLOYED

- Base: `origin/main` at `1a49252ec9fa8fc35d7b0c4419ae52f264dc02b1`
- Isolated branch: `codex/probability-lineage-stage2`
- Worktree: `C:\MLB HR Engine\worktrees\probability-lineage-stage2`
- Stage 2 commit `ca3a4b8` was not used or deployed.

## What changed

The existing MAIN scoring chain now captures values at the point where each value is used. The trace is attached only to the copied warehouse payload at `batter_stat_history.raw_payload.probability_lineage`. It is not added to the live player object or any API response.

Snapshot identity remains the existing database primary key:

- `slate_date`
- `run_ts`
- `batter_id`
- `game_pk`

The nested lineage contains:

- `schema_version`, `snapshot_kind`
- `pre_scale_model_prob`
- `effective_prob_scale`, `adaptive_apply_status`
- `post_scale_pre_calibration_prob`
- `calibration_branch`
- `calibration_barrel_rate`, `elite_barrel_threshold`, `elite_threshold_met`
- `platt_a`, `platt_b`
- `post_platt_prob`, `warehouse_isotonic_status`, `final_model_prob`
- `calibration_fingerprint_sha256`, `calibration_enabled`, `calibration_method`, `warehouse_isotonic_enabled`
- `adaptive_artifact_path`, `adaptive_artifact_sha256`, `adaptive_load_status`, `adaptive_source_kind`
- `source_lane`, `source_trigger`, `git_sha`, `image_identity`, `machine_version`, `run_id`

`warehouse_isotonic_status` records the actual live branch: `DISABLED`, `ARTIFACT_UNAVAILABLE`, or `APPLIED`.

## Lane behavior

The adaptive reader, path resolution, bounds, cache, and artifact were not changed.

- GitHub scheduled runs still use the missing-artifact fallback `prob_scale=1.0`.
- Fly still reads `/data/learned_adjustments.json` through `TRACKING_DATA_DIR=/data`, preserving `prob_scale=1.12`.
- Local/manual runs use their existing local artifact or the existing `1.0` fallback.

The runtime provenance helper reads the same cached effective scale used by `apply_prob_scale()`. It hashes the existing artifact for identity but does not write it.

## Numerical containment

No coefficient, clamp, rounding operation, branch predicate, tier/rank, projected-probability chain, JIG/AEE/HVY/TM surface, EDGE/EV/CLV calculation, or API serializer changed.

Regression tests compare the instrumented MAIN chain against a frozen copy of the pre-instrumentation chain for:

- scales `1.0` and `1.12`
- raw probabilities `0.001` through `0.290`
- barrel rates `0.0`, `0.0999`, `0.10`, and `0.20`
- 2,320 total combinations using exact float hexadecimal equality

Golden boundary cases also cover standard Platt, elite Platt, the elite barrel threshold, and the `0.29` scale clamp.

## Runtime containment repair

The lineage map now skips rows whose `player_id` or `game_pk` is missing or non-numeric. The player remains in the live slate; a warning identifies the skipped warehouse-only lineage key. No ID is inferred.

Runtime provenance construction is also contained. If it fails, scoring proceeds through the unchanged adaptive/calibration chain, a warning is logged, and warehouse lineage capture is withheld for that run rather than storing unverified provenance.

## Storage and migration

No migration is required. Migration 009 already defines `raw_payload` as non-null JSONB. The warehouse write remains asynchronous and non-fatal. If lineage is missing or untrusted, only the nested `probability_lineage` metadata is omitted; the normal MAIN snapshot is still preserved. JIG sparse snapshot writes are unchanged and do not claim the MAIN lineage.

## Validation

- Focused probability-lineage, runtime-provenance, and warehouse-lineage tests: 10 passed.
- Full discovery: 141 collected; 139 passed; 2 failed. The unrelated existing failures remain:
  - Community fixture.
  - pitcher-detail fixture.
- `git diff --check`: passed.
- No live provider, Supabase, database, cache, deployment, or network mutation was performed.

## Files

Code:

- `mlb_hr_engine_v4/engine/calibration.py`
- `mlb_hr_engine_v4/pipeline.py`
- `mlb_hr_engine_v4/tracking/runtime_provenance.py`
- `mlb_hr_engine_v4/tests/test_probability_lineage.py`
- `mlb_hr_engine_v4/tests/test_runtime_provenance.py`
- `mlb_hr_engine_v4/tests/test_warehouse_probability_lineage.py`

Wiki:

- `MLB HR ENGINE/wiki/log.md`
- `MLB HR ENGINE/wiki/sessions/2026-09-21-probability-lineage-instrumentation.md`

## Release boundary

This work is not production-active, and it makes no canonical scale decision: GitHub remains at `1.0`, while Fly remains at `1.12`. Code and wiki commits must remain separate if later authorized. Push and deployment require separate operator authorization. Do not deploy `ca3a4b8`; it changes scale authority and would collapse the intentional GitHub/Fly mismatch.

GRAPHIFY STATUS: STALE. The graph artifact was absent in the clean worktree and the primary checkout graph predates the audited source, so direct source inspection was used.
