# SOL Player Intelligence Phase B4 - Whiff and Tactical Contracts

Date: 2026-07-14
Status: PASS - built and pushed; deployment held for July 16 live-slate proof
Code commit: `81854e4`

## Production/API contract

- `/api/batter-detail` `pitch_profile.rows` now add batter whiff percentage by
  canonical pitch type from a separate all-pitches Baseball Savant query.
- Whiff percentage is `whiffs / swings * 100`. It requires at least 15 swings
  per pitch type; thinner samples return `null` with `Gap`.
- Each row now exposes `xwoba`, `barrel_pct`, `whiff_pct`, `pill`,
  `pill_thin_sample`, xwOBA-based `damage`, sample counts, and availability.
- Thin xwOBA samples receive a visible `NEUTRAL` pill with
  `pill_thin_sample: true`; damage remains `null`/`Gap`.
- Top-level additive fields are `pitch_mix_verdict`,
  `pitch_mix_exploit_pitches`, and `pitch_mix_verdict_meta`.
- Pitcher usage comes only from a display snapshot owned by the existing
  `/api/pitcher-detail` arsenal response. If it is unavailable, the verdict is
  `null` with `Gap`; `/api/batter-detail` never warms or reads a scoring cache.

## Ratified display-only constants

- `EXPLOIT`: gate-qualified xwOBA >= .380.
- `HUNT`: gate-qualified .340 <= xwOBA < .380.
- `NEUTRAL`: xwOBA < .340, or thin xwOBA sample with a thin marker.
- Damage: `clamp((xwOBA - .200) / (.500 - .200) * 100, 0, 100)`.
- Top usage: pitcher usage >= 20%.
- `DEPLOY`: top-usage EXPLOIT.
- `WATCHLIST`: lower-usage EXPLOIT, top-usage HUNT, or a mixed edge.
- `SCRATCH`: every top-usage pitch is fully measured below .340.
- `HOLD`: fully measured neutral arsenal with no pitch reaching 20% usage.
- Missing main-arsenal xwOBA or missing pitcher usage produces a null/Gap
  verdict rather than a guess.

All constants live together in `clients/batter_pitch_profile.py`. These labels
and damage values are display-only and do not feed sorting, MAIN, JIG, AEE, or
any other scoring path.

## Live sourcing proof

The July 14 live probe for Aaron Judge (MLB id 592450, 2026 regular season)
returned 1,131 all-pitches rows versus 261 PA-ending rows. The all-pitches CSV
contained `pitch_type`, `description`, `type`, `p_throws`, `game_year`,
`game_pk`, `at_bat_number`, and `pitch_number`. Observed swing/whiff descriptors
included `swinging_strike`, `swinging_strike_blocked`, `foul`, `foul_tip`, and
`hit_into_play`.

The isolated live profile returned whiff data. One gate-qualified FF row versus
RHP was xwOBA .360, barrel 31.2%, whiff 22.7%, HUNT, damage 53.3, from 31 xwOBA
observations, 16 contacts, 75 swings, and 17 whiffs. A two-swing KC sample
returned `whiff_pct: null` with `Gap`.

## Isolation and validation

- Production call chain: `/api/batter-detail` ->
  `get_batter_pitch_profile_display` -> isolated PA-ending/all-pitches fetches.
- The all-pitches fetch omits `hfAB`; the B3 xwOBA/barrel fetch retains its
  PA-ending `hfAB` filter.
- `_BATTER_PITCH_PROFILE_DISPLAY_CACHE` is isolated from
  `clients.pitch_mix._BATTER_PT_CACHE`.
- `_PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE` contains only serialized display rows
  from `/api/pitcher-detail`; the B4 endpoint does not call or read the arsenal
  scoring cache.
- `clients/pitch_mix.py` SHA-256 remained
  `afb7facc5a6c70b8472223dbb0226f784ac56b5066a3ff539ec5082a37e70caa`.
- Protected source hashes for `_build_slate_payload`, `_jig_score`,
  `_true_matchup_score`, `arsenal_matchup_factor`, and `get_slate` were
  unchanged. `/api/slate` was unchanged.
- `engine/arsenal_edge.py` remained byte-identical.
- Focused B4 unittest module: 6/6 PASS.
- `py_compile` for the B4 client, API module, and tests: PASS.
- Adjacent `tests.test_pitcher_detail`: 3/4 PASS. The unchanged failure is the
  pre-existing scoring-cache expectation already recorded by B3; B4 does not
  modify or call that path.
- Graphify was stale, so validation used current file/AST evidence instead of a
  stale graph.

## Repository checkpoint

Repo truth showed the B3 client/test/API base still uncommitted when B4 began,
despite the task context describing B3 as committed. The authorized B4 code
commit therefore contains that prerequisite B3 base plus the final B4 changes.
The separate untracked B3 wiki note was not staged.

## Deployment hold

Do not deploy before July 16. Deploy B3+B4 together only after a live slate is
available, verify JIG ordering is unchanged, and then build the frontend Pitch
Type Destruction grid and Pitch Mix verdict surfaces.

