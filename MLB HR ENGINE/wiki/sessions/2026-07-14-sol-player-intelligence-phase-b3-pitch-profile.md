# SOL Player Intelligence Phase B3 - Batter Pitch Profile

Date: 2026-07-14
Status: Built for validation; do not deploy before July 16 live-slate JIG-order proof

## Production/API change

- `/api/batter-detail` now exposes additive `pitch_profile.rows` data for batter
  xwOBA and barrel percentage by canonical pitch type and opposing pitcher hand.
- The display fetch uses Baseball Savant PA-ending batter rows. Current live
  source validation confirmed `estimated_woba_using_speedangle` and
  `launch_speed_angle` are present.
- xwOBA requires at least 10 observations. Barrel percentage uses tracked
  contact as its denominator and requires at least 5 contacts. Thin or missing
  cells return `null` with `Gap`; no metric is fabricated.
- Whiff percentage remains explicitly deferred to Phase B4 because it requires
  all-pitches data.

## Isolation boundary

- New module: `clients/batter_pitch_profile.py`.
- New cache: `_BATTER_PITCH_PROFILE_DISPLAY_CACHE`, keyed independently by
  batter, pitcher hand, and season.
- The production consumer is only `/api/batter-detail`.
- `clients/pitch_mix.py`, `_BATTER_PT_CACHE`, `_jig_score`,
  `arsenal_matchup_factor`, `arsenal_edge.py`, `_true_matchup_score`, pipeline
  scoring, and `/api/slate` remain protected and unchanged.

## Deployment hold

Build and unit validation are allowed during the break. Deployment remains on
hold until the July 16 live slate proves JIG ordering is unchanged.

## Validation checkpoint

- Live Savant column probe (Aaron Judge, 2026): 215 PA-ending rows;
  `estimated_woba_using_speedangle` present/non-empty on 215 and
  `launch_speed_angle` present/non-empty on 143 tracked contacts.
- Focused B3 unittest module: 4/4 PASS, covering canonical aliases, cache hits,
  thin-sample gaps, missing-column gaps, failed-fetch no-poison behavior, and
  endpoint integration.
- `py_compile` for the new client, API module, and focused tests: PASS.
- AST caller trace: the only production consumer of
  `get_batter_pitch_profile_display` is `/api/batter-detail`; its internal fetch
  and cache remain local to the new module.
- Runtime fixture check: `_BATTER_PT_CACHE` identical before/after.
- Baseline SHA-256 hashes unchanged for `_build_slate_payload`, `_jig_score`,
  `_true_matchup_score`, `arsenal_matchup_factor`, `get_slate`, and the complete
  `clients/pitch_mix.py` file. This also preserves `/api/slate` assembly and
  response behavior.
- Adjacent legacy `tests.test_pitcher_detail`: 3/4 PASS. Its unchanged failure
  is the pre-existing expectation that a pitcher scoring cache stays empty
  after display hydration; B3 does not call or modify that path.
