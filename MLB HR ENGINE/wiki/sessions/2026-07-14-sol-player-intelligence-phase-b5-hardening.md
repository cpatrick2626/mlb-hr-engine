# SOL Player Intelligence — Phase B5 Batter Detail Hardening

Date: 2026-07-14  
Status: PASS — code validated and deploy held for July 16

## Scope

Final backend hardening phase for the additive, display-only `GET /api/batter-detail` endpoint built in B1–B4. This phase changes reliability behavior only: cache identity/TTL, graceful degradation, module failure isolation, fixed contract shape, and contract coverage. It does not change field meanings, thresholds, tactical outcomes, damage scaling, sample gates, MAIN/JIG scoring, or `/api/slate`.

## Hardening completed

- Display cache key is now `(slate_date, batter_id, pitcher_id, game_pk, effective_batter_side, pitcher_hand, source_season)`.
- Display entries expire after six hours. Expired entries are removed and a cache miss performs a clean display-only fetch.
- Fresh source-equivalent season profiles can be reused across contexts, but each matchup/game receives its own cache entry. The same batter in two doubleheader games cannot collide.
- Missing/failed persisted-slate reads return a well-formed all-Gap HTTP 200 response instead of cascading into an endpoint error.
- Batter recent cache, pitcher recent cache, Savant pitch profile, pitcher arsenal snapshot, and tactical verdict are isolated so one failure degrades only its module.
- Exceptional pitch-profile and verdict fallbacks use the same metadata keys as live responses.
- Upstream Savant response objects are closed on both success and failure.
- No failed/empty Savant response is cached.

## Contract

The response always retains the same top-level/module keys:

- `meta`
- `threat`
- `statcast`
- `splits`
- `discipline`
- `environment`
- `pitcher`
- `arsenal`
- `fatigue`
- `pitch_profile`
- `pitch_mix_verdict`
- `pitch_mix_exploit_pitches`
- `pitch_mix_verdict_meta`
- `recent`

Unavailable values remain null/empty according to their existing field type and carry `availability=Gap`; no values are fabricated. The four ratified verdict outcomes and all B3/B4 display thresholds are unchanged.

## Validation

- Focused contract/unit suite: 11/11 PASS.
- Covered full-data, fully degraded, partial module availability, HTTP 200 valid JSON under total cache failure, stable key shape, doubleheader row/cache distinctness, six-hour TTL expiry, independent xwOBA/barrel/whiff sample gates, all four verdict outcomes, module failure isolation, and scoring-cache non-mutation.
- `python -m py_compile` passed for the client, API route, and both test files.
- Protected source hashes remained unchanged for `_build_slate_payload`, `_jig_score`, `_true_matchup_score`, `get_slate`, `clients/pitch_mix.py`, and `clients/arsenal.py`.
- `/api/slate` is unchanged.
- `_BATTER_PT_CACHE` is not read, written, or warmed by the hardening path.
- Graphify was stale relative to current commits, so current files were inspected directly and Graphify was not queried.

## Latency follow-up

The PA-ending and all-pitches Savant requests remain sequential and independently fail-safe, each with a 20-second timeout. Parallelization is deferred as a separate performance task; B5 does not change execution strategy.

## Deployment hold

Do not deploy B5 independently. Deploy B3, B4, and B5 together on July 16, then verify JIG order before beginning frontend Player Intelligence surfaces.

