# SOL Player Intelligence Phase B1 - Batter Detail API

Date: 2026-07-14
Status: Built and validated, not committed, not pushed, not deployed

## Production/API change

- Added public read-only `GET /api/batter-detail?batter_id=&pitcher_id=&game_pk=`.
- The response is grouped into `threat`, `statcast`, `splits`, `discipline`,
  `environment`, `pitcher`, `arsenal`, `fatigue`, and `recent`.
- Aggregate values come only from persisted `pipeline_runs` player/slate state.
- Recent batter games and pitcher starts are read only when already present in
  the process-local MLB game-log caches. A cache miss returns `[]` with `Gap`;
  the endpoint never fetches MLB StatsAPI data.
- Every module reports source, `Live`/`Stale`/`Gap` freshness, field
  availability, and display labels.

## Integrity boundaries

- `/api/slate` implementation and payload shape are unchanged.
- `_build_slate_payload`, `_jig_score`, and `_true_matchup_score` are unchanged.
- The endpoint does not call pipeline, scoring, arsenal, pitch-mix, weather,
  park, platoon, fatigue, or calibration computation.
- `_BATTER_PT_CACHE` and pitcher Savant scoring/display caches remain unchanged
  across endpoint execution.
- `xiso` is labeled `xISO`; no `iso` field is emitted by the statcast module.
- Hand splits are labeled actual SLG vs RHP/LHP.
- `woba` is explicit `null`/`Gap`; no substitute is fabricated.
- `maxev` is labeled max exit velocity, never max pitch velocity.

## Validation

- `python -m py_compile api/main.py`: PASS.
- FastAPI `TestClient` cached response: HTTP 200, JSON, all nine modules present.
- Mocked cache-only response and cache-miss paths: PASS; no external fetch.
- Historical persisted 2026-07-11 slate trace: PASS and correctly marked `Stale`.
- HEAD/worktree function hashes match for `/api/slate`, `_build_slate_payload`,
  `_jig_score`, and `_true_matchup_score`.
- Existing `tests.test_pitcher_detail`: 3/4 PASS. The failing assertion is a
  pre-existing pitcher-detail/display-only cache-isolation regression in
  `clients/pitch_mix.py`; B1 does not call or modify that path.

## Operational note

Persisted raw aggregate player state currently lives under `all_by_model`
(limited to 50 rows); all slate rows still receive the fields already present
in `slate_cache`, while raw-only fields outside that persisted set report
`Gap`. B1 does not change cache persistence or `/api/slate`.
