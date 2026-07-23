# 2026-07-22 — TCC four-filter payload passthrough

Status: built and validated locally; not committed, pushed, or deployed.

## Scope

- Added `short_form_hr`, `pitcher_hr_allowed`, and `streak_factor` to MAIN slate leaderboard rows as additive display/filter values.
- Added `hvy_modifier` to JIG slate leaderboard rows only.
- Wired the matching TCC controls through draft state, defaults, room filtering, active-filter counts, and existing room persistence.
- `streak_factor` remains a pipeline scoring input applied once to `adjusted_rate`; the frontend only compares its emitted value against a filter threshold.
- `pitcher_hr_allowed` is the raw season count. Only `pitcher_hr9` participates in scoring.

## Durable source finding

`_jig_score()` reads pitch-mix inputs but does not construct or retain the canonical pitch-mix context dictionary. Therefore, JIG serialization now obtains `hvy_modifier` from the existing `load_hvy_context()` path and emits only that context value. It does not expose `hvy_score` or `pitch_type_damage_pct`.

## Validation

- Modified Python modules compile.
- A real local `GET /api/slate` response built from the latest stored slate returned all four values at their expected types and scales.
- Matching live-production rows retained identical `model_prob` and `jigScore` values.
- Deterministic tests passed for all four new predicates, the seven previously wired controls, and ISO/Barrel%/HH% core filters.
- Browser validation confirmed APPLY changes the Matrix row set, room values persist on reopen, and RESET restores defaults. JIG Matchup Modifier remained JIG-only.
- The broader engine suite reported 47 passed and one unrelated, reproducible pitcher-detail expectation failure.

## Deployment boundary

- `mlb_hr_engine_v4/api/main.py` and `mlb_hr_engine_v4/pipeline.py` require an operator-authorized Fly deploy.
- The two frontend asset changes follow the Vercel frontend path after operator-authorized commits/push.
