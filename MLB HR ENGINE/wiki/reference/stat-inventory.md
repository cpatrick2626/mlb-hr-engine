# Stat Inventory Reference — HR Engine v4

**Date:** 2026-07-21
**Audited by:** Claude Code — direct inspection of `pipeline.py`, `api/main.py`, `statcast.py`, `ranker.py`, `roles.py`, `filters.py`, `engine/ev.py`
**Reflects:** Audited state of the 2026-07-21 production payload
**Primary payload shape:** `leaderboard_rows[]` from `/api/slate`

---

## Conventions

### API key vs pipeline key

Two naming layers exist:

- **Pipeline key** — key in the Python player dict built by `pipeline.py:_build_player_profile()`
- **API key** — key in the serialized `leaderboard_rows` dict built by `api/main.py:_build_slate_payload()` and consumed by the React frontend

This document uses **API keys** throughout. The pipeline key is noted where it differs. Some pipeline-internal fields never reach the API — those are listed in their sections as "internal only."

### D/S flag

- **SCORING** — field is read by the Poisson model formula, EV/edge computation, filter rules, or confidence scoring. A change here changes bet recommendations.
- **JIG-SCORING** — read only by the JIG tactical score (`_jig_score()`). Not part of MAIN.
- **DISPLAY** — display-only; never read by scoring, EV, filters, or ranking. Changes here do not affect bet recommendations.
- **DISPLAY+ROLE** — display-only for model/JIG scoring but also read by `roles.py` for role flag assignment.
- **DEAD** — key exists in the payload but is always `None`; no source is fetched or computed.

### Dual field: `opphr` / `pitcher_hr9`

Per `known-gaps.md`: `opphr` and `pitcher_hr9` are the same computed value (pitcher HR/9 from MLB Stats API) emitted under two different keys in the same `leaderboard_rows` row. Not a divergence in value — same number, dual emission.

---

## A. Identity & Game Context

| API Key | Pipeline Key | Label | Source | D/S |
|---------|-------------|-------|--------|-----|
| `id` | `player_id` (or name slug) | Player ID | Derived: MLBAM player_id or name slug | DISPLAY |
| `name` | `player_name` | Player Name | MLB Stats API (schedule hydration) | DISPLAY |
| `teamAbbr` | `team` | Team Abbreviation | MLB Schedule | DISPLAY |
| `bats` | `batter_side` | Batter Handedness (L/R/S) | MLB Stats API player info | SCORING (platoon_factor) |
| `pitcher_name` | `pitcher_name` | Starting Pitcher Name | MLB Schedule / Stats API | DISPLAY |
| `pitcher_id` | `pitcher_id` | Pitcher MLBAM ID | MLB Schedule / Stats API | SCORING (all pitcher factors) |
| `pitcher_hand` | `pitcher_hand` | Pitcher Handedness (L/R) | MLB Stats API player info | SCORING (platoon_factor) |
| `pitcher_confirmed` | `pitcher_confirmed` | Pitcher Announced Flag | Derived: `pitcher_id is not None` | DISPLAY — NOTE: misnomer; means "probable" not confirmed; see `known-gaps.md` |
| `lineup_confirmed` | `lineup_confirmed` | Lineup Posted Flag | Derived: `lineup_spot is not None` | SCORING (×0.82 penalty when False) |
| `lineup_spot` | `lineup_spot` | Batting Order Position (1–9) | MLB Schedule | SCORING (expected_pa) |
| `gameId` | Derived | Game Slug | Derived: `away-home[-game_pk]` (DH gets game_pk suffix) | DISPLAY |
| `game_pk` | `game_pk` | MLB Game Primary Key | MLB Schedule | DISPLAY |
| `gameStartUtc` | `game_time_utc` | Game Start (UTC ISO string) | MLB Schedule | DISPLAY |
| `gameStatus` | `game_status` | Game Status | MLB Schedule | DISPLAY |
| `_board` | — | Board Identity | Derived: `"main"` or `"jig"` | DISPLAY (internal routing) |

---

## B. MAIN Model Probability & Scoring

These fields directly compute or gate `model_prob`. Changes here change bet recommendations.

### Emitted in API payload

| API Key | Pipeline Key | Label | Source | D/S |
|---------|-------------|-------|--------|-----|
| `model_prob` | `model_prob` | MAIN HR Probability (0–1 decimal) | Poisson `1−e^(−λ)` → `adaptive_weights.apply_prob_scale()` → `calibration.apply_calibration()` | **SCORING** |
| `hrprob` | Derived | HR Prob % (0–100) | `model_prob × 100` | **SCORING** (primary sort key in leaderboard_rows) |
| `tier` | Derived | FS Tier | Derived from model_prob vs `config.FS_TIER_THRESHOLDS`: APEX / ELITE / EDGE / SIGNAL / WATCH / COLD | **SCORING** (rank + display) |
| `model_tier_rank` | `model_tier_rank` | Tier Rank (numeric) | Rank within tier by model_prob | DISPLAY |
| `model_prob_projected` | `model_prob_projected` | Projected Model Prob (0–1) | Same formula with typical-slot PA; `None` when no pitcher announced | DISPLAY |
| `hrprob_projected` | `hrprob_projected` | Projected HR Prob % | `model_prob_projected × 100` | DISPLAY |
| `projected_pa_source` | `projected_pa_source` | Projection PA Source | `"confirmed"` / `"typical-slot"` / `"default"` | DISPLAY |

### Internal scoring factors (pipeline dict only — NOT in API payload)

| Pipeline Key | Label | Source | Role |
|-------------|-------|--------|------|
| `hr_rate` | Blended HR Rate | MLB Stats + Statcast blended | SCORING intermediate |
| `raw_hr_rate` | Pre-Statcast HR Rate | MLB Stats baseline only | SCORING intermediate |
| `statcast_power_mult` | Power Multiplier | Statcast 7-signal composite (see Section E) | SCORING |
| `park_factor` | Park HR Factor | `data/park_factors.py` (batter-hand adjusted) | SCORING + Filter Rule 4 |
| `pitcher_factor` | Pitcher Combined Factor | `engine/probability.pitcher_combined_factor()` | SCORING + Filter Rule 6 |
| `weather_factor` | Weather Factor | `clients/weather.py`: temp × wind × humidity | SCORING + Filter Rule 5 |
| `platoon_factor` | Platoon Factor | MLB Stats platoon splits + batter/pitcher handedness | SCORING |
| `h2h_factor` | H2H Career Multiplier | `clients/pitch_mix.get_h2h()` | SCORING |
| `streak_factor` | Hot Streak Factor | MLB Stats recent / short-form PA and HR rate | SCORING |
| `k_factor` | K Suppressor | MLB Stats season strikeout rate | SCORING |
| `early_season_suppressor` | Early Season PA Discount | PA-based linear ramp | SCORING |
| `expected_pa` | Expected Plate Appearances | Lineup spot → `engine/probability.expected_pa()` | SCORING |
| `fatigue_factor` | Pitcher Fatigue Factor | `pitcher_days_rest` → `engine/probability.pitcher_fatigue_factor()` | SCORING |
| `statcast_source` | Statcast Coverage Tier | `"current"` / `"blended"` / `"prior"` / `"none"` | SCORING (confidence_score bonus) |
| `interaction` | Batter × Pitcher Synergy | Non-additive interaction term (batter excess × pitcher excess × coeff) | SCORING intermediate |

---

## C. Odds / Market Fields

| API Key | Pipeline Key | Label | Source | D/S |
|---------|-------------|-------|--------|-----|
| `odds` | Derived from `fanduel_american` | FanDuel Odds (formatted string, e.g. `+250`) | The Odds API (FanDuel book) | DISPLAY |
| — | `ev_pct` | Expected Value % | `engine/ev.expected_value_pct()` (odds-capped at 1.4× market) | **SCORING** (Filter Rule 1) |
| — | `edge_pct` | Edge vs No-Vig Market % | `engine/ev.edge_pct()` | **SCORING** (Filter Rule 2 + confidence) |
| — | `confidence` | Confidence Score (0–100) | `engine/probability.confidence_score()` | **SCORING** (confidence tier + ranking scale) |
| — | `bet_dollars` | Bet Size Recommendation | `engine/sizing.bet_dollars()` | DISPLAY |
| — | `market_no_vig_prob` | No-Vig Market Probability | Odds API → `engine/market.market_summary()` (dynamic vig when enabled) | **SCORING** (EV/edge baseline) |
| — | `best_american` | Best Available Odds (American) | Odds API (best price across all books) | **SCORING** (Filter Rule 7 gate) |
| — | `n_books` | Books Quoting | Odds API | SCORING (confidence_score) |

Note: `best_american`, `best_bookmaker`, `all_prices`, `n_books`, `prices_by_book`, `market_no_vig_prob`, `market_no_vig_prob_fixed`, `vig_by_book`, `market_implied_avg`, `fanduel_american` are in the pipeline player dict and in the `/api/picks/{date}` payload, but are **not emitted** in `leaderboard_rows` from `/api/slate`. The slate payload only carries `odds` (formatted FD string).

---

## D. Season Stats (MLB Stats API)

Source: `clients/mlb_stats.py` — bulk group fetch for current season; `get_player_recent_stats()` for 14-day window.

| API Key | Pipeline Key | Label | Source | D/S |
|---------|-------------|-------|--------|-----|
| `pa` | `season_pa` | Season Plate Appearances | MLB Stats API season group | SCORING (PA gates, confidence, early-season suppressor) |
| `hr` | `season_hr` | Season Home Runs | MLB Stats API | DISPLAY |
| `avg` | `batting_avg` | Batting Average (H/AB) | MLB Stats API (computed from hits/atBats) | DISPLAY |
| `slg` | `actual_slg` | Slugging % (TB/AB) | MLB Stats API (computed from counting stats) | DISPLAY |
| `obp` | `actual_obp` | On-Base % (H+BB+HBP/PA approx.) | MLB Stats API (computed; SF excluded — not in bulk group) | DISPLAY |
| `babip` | `babip` | BABIP | MLB Stats API (computed) | DISPLAY |
| `hrpa` | Derived | HR/PA Rate (decimal) | `season_hr / season_pa` | DISPLAY |
| `hrfb` | `hrfb` | HR/FB % | `season_hr / (season_hr + air_outs) × 100` | DISPLAY |
| `bbpct` | `batter_bb_pct × 100` | Walk % | MLB Stats API (baseOnBalls / season_pa) | DISPLAY |
| `kpct` | `batter_k_pct × 100` | Strikeout % | MLB Stats API (strikeOuts / season_pa) | DISPLAY |
| `recent_form_games` | `recent_form_games` | Last 5 Game Logs | MLB Stats API game log cache: `[{date, hr, avg, slg, pa}]` | DISPLAY |

**Internal pipeline season stat fields not in API payload:**
- `recent_pa` — read by soft_flags (⚠ Limited recent data gate)
- `short_form_pa`, `short_form_hr` — 14-day window; read by `streak_factor` and confidence soft flag

---

## E. Statcast Batter Contact Profile (Savant)

Sources: `/leaderboard/statcast` (barrel%, exit velo, HH%, sweet spot%, max EV, avg launch angle, xSLG, PA), `/leaderboard/batted-ball` (GB%, FB%, LD%, PU%, pull%, straight%, oppo%), `/leaderboard/expected_statistics` (xSLG, xwOBA, xBA). Three-tier prior-year coverage: current / blended / prior-year.

Pipeline internal key is `sc_stats` dict from `batter_data[player_id]`. Passed to `statcast_client.statcast_summary()` which formats values as strings ("12.5%") before they enter the player profile.

| API Key | Savant / Pipeline Key | Label | D/S |
|---------|----------------------|-------|-----|
| `barrel` | `barrel_rate` | Barrel % | **SCORING** (40% of power_mult) + DISPLAY+ROLE (PRIME, EXPLOSIVE, ADVANTAGE, WILDCARD gates) |
| `ev` | `exit_velocity_avg` | Avg Exit Velocity (mph) | **SCORING** (4% of power_mult) |
| `hh` | `hard_hit_pct` | Hard Hit % (EV > 95 mph) | **SCORING** (8% of power_mult) |
| `sweet` | `sweet_spot_pct` | Sweet Spot % (LA 8–32°) | **SCORING** (10% of power_mult) |
| `fb` | `fb_pct` | Fly Ball % | **SCORING** (20% of power_mult; quality-gated by barrel%) |
| `pull` | `pull_pct` | Pull % | **SCORING** (10% of power_mult; also used in wind_factor via `batter_side`) |
| `gb` | `gb_pct` | Ground Ball % | DISPLAY (also used in `fly_ball_adjusted_park_factor()`) |
| `ld` | `ld_pct` | Line Drive % | DISPLAY |
| `oppo` | `oppo_pct` | Opposite-Field % | DISPLAY |
| `center` | Derived: `1 − pull − oppo` | Center % | DISPLAY |
| `la` | `avg_launch_angle` | Avg Launch Angle (°) | DISPLAY |
| `maxev` | `max_ev` | Max Exit Velocity (mph) | DISPLAY+ROLE (EXPLOSIVE gate: max_ev ≥ threshold; WILDCARD gate) |
| `pullair` | Derived: `pull × (fb + ld)` | Pull Air % | JIG-SCORING (15% of jig base) + DISPLAY+ROLE (EXPLOSIVE, WILDCARD gates) |

---

## F. Expected Stats (Savant expected_statistics)

| API Key | Savant Field | Label | D/S |
|---------|-------------|-------|-----|
| `xslg` | `xslg` | Expected SLG | **SCORING** (8% of power_mult) + **JIG-SCORING** (25% of jig base) + DISPLAY |
| `iso` | Derived: `xslg − xba` | xISO (expected isolated power) | **JIG-SCORING** (15% of jig base) + DISPLAY |
| `xwoba` | `xwoba` | Expected wOBA | DISPLAY |
| `woba` | — | wOBA | **DEAD** — always `None`; no source wired; xwoba is the live proxy |

**Internal pipeline fields not in API payload:**
- `xba` — fetched from Savant expected_statistics and used to compute `xiso` (xslg − xba); not directly emitted in leaderboard_rows
- `xslg_diff` (xslg − actual_slg) — computed in pipeline, NOT emitted

---

## G. Bat-Tracking Fields (Savant bat-tracking leaderboard) — DISPLAY ONLY

Source: `clients/statcast.get_bat_tracking()` → `/leaderboard/bat-tracking`. Fetched as a fifth parallel data source in the pipeline. All five fields are display-only for model and JIG scoring. `blast` is additionally read by `roles.py` for the EXPLOSIVE gate.

| API Key | Savant Raw Field | Label |
|---------|-----------------|-------|
| `fast` | `hard_swing_rate` | Hard Swing % |
| `squp` | `squared_up_per_swing` | Squared-Up % |
| `blast` | `blast_per_swing` | Blast % (DISPLAY+ROLE: EXPLOSIVE gate) |
| `comp` | `percent_swings_competitive` | Competitive Swing % |
| `batspeed` | `avg_bat_speed` | Avg Bat Speed (mph) |

---

## H. Matchup / Computed Display Fields

| API Key | Pipeline Key | Label | Derivation | D/S |
|---------|-------------|-------|-----------|-----|
| `quality` | `matchup_quality` | Matchup Quality (batter axis) | `_matchup_quality_tier()`: model_prob thresholds → ELITE / STRONG / AVG / WEAK | DISPLAY |
| `pitcherVuln` | `pitcher_vuln` | Pitcher Vulnerability (pitcher axis) | `_pitcher_vulnerability_tier()`: pitcher_hr9 ≥ 2.2 → TARGET; else NEUTRAL | DISPLAY |
| `true_matchup_score` | — | True Matchup Score (0–100) | `0.40 × model_prob_n + 0.30 × aee_edge_n + 0.20 × aee_conf + 0.10 × vuln_n` | DISPLAY |
| `tm_projected` | — | TM Projected | Same formula with `model_prob_projected` substituted | DISPLAY |
| `h2h_factor` | `h2h_factor` | H2H Career Multiplier | `clients/pitch_mix.get_h2h()` | **SCORING** (used in pipeline) — also emitted for display |

---

## I. Batter Splits — DISPLAY ONLY

Source: `clients/mlb_stats.get_player_platoon_splits()` (current season) and `get_player_multiseason_splits()`. The 30-PA reliability rule is applied at consumption by the frontend; the backend emits splits at any PA count.

**Faced-hand splits** (the hand currently faced by this batter today):

`vs_hand` (L / R / null), `vs_hand_avg`, `vs_hand_slg`, `vs_hand_iso`, `vs_hand_hr`, `vs_hand_hr_pa`, `vs_hand_pa`

**Full LHP splits**: `vs_lhp_avg`, `vs_lhp_slg`, `vs_lhp_iso`, `vs_lhp_hr`, `vs_lhp_hr_pa`, `vs_lhp_pa`

**Full RHP splits**: `vs_rhp_avg`, `vs_rhp_slg`, `vs_rhp_iso`, `vs_rhp_hr`, `vs_rhp_hr_pa`, `vs_rhp_pa`

**Multi-season**: `multi_season_vs_hand` — dict of multi-season aggregates vs faced hand

All splits are DISPLAY ONLY. Never read by model_prob, JIG score, EV, filters, or ranking.

---

## J. Recent Form — DISPLAY ONLY

| API Key | Label | Source |
|---------|-------|--------|
| `recent_form_games` | Last ≤5 Game Logs | MLB Stats API game log cache: `[{date, hr, avg, slg, pa}]` — up to 5 most-recent games |

---

## K. Pitcher Context

| API Key | Pipeline Key | Label | Source | D/S |
|---------|-------------|-------|--------|-----|
| `opphr` | `pitcher_hr9` | Pitcher HR/9 (key 1 of 2) | MLB Stats API: `(season_hr / IP) × 9`; 0.0 when IP < 5 | DISPLAY + used in `confidence_score()` gate + `pitcher_vuln` derivation |
| `pitcher_hr9` | `pitcher_hr9` | Pitcher HR/9 (key 2 of 2, duplicate) | Same value as `opphr` — dual emission; see `known-gaps.md` | DISPLAY |
| `pitcher_era` | `pitcher_era` | ERA | MLB Stats API pitcher season stats | DISPLAY |
| `pitcher_whip` | `pitcher_whip` | WHIP | MLB Stats API | DISPLAY |
| `pitcher_k_pct` | `pitcher_k_pct` | Pitcher K% | MLB Stats API: `strikeOuts / battersFaced × 100` | DISPLAY |
| `pitcher_bb_pct` | `pitcher_bb_pct` | Pitcher BB% | MLB Stats API: `baseOnBalls / battersFaced × 100` | DISPLAY |
| `pitcher_barrel_allowed` | `pitcher_barrel_allowed` | Barrel% Allowed | Savant pitcher leaderboard | DISPLAY + used in `_true_matchup_score()` (vuln component) |
| `pitcher_hh_allowed` | `pitcher_hh_allowed` | Hard Hit% Allowed | Savant pitcher leaderboard | DISPLAY |
| `pitcher_fb_allowed` | `pitcher_fb_allowed` | FB% Allowed | Savant pitcher leaderboard | DISPLAY |
| `pitcher_gb_allowed` | `pitcher_gb_allowed` | GB% Allowed | Savant pitcher leaderboard | DISPLAY |

**Internal pipeline pitcher scoring factors (not in API payload):**

| Pipeline Key | Label | Role |
|-------------|-------|------|
| `pitcher_factor` | Combined pitcher factor (0.55–1.60) | **SCORING** + Filter Rule 6 |
| `sc_pit_fac` | Statcast contact suppressor (40% weight in pitcher_factor) | SCORING intermediate |
| `k_gb_fac` | K/GB suppressor | SCORING intermediate |
| `hr_fb_fac` | HR/FB pitcher factor | SCORING intermediate |
| `recent_pit_fac` | Pitcher recent-form factor | SCORING intermediate |
| `fatigue_fac` | Pitcher fatigue (days rest) | SCORING intermediate |
| `pitcher_days_rest` | Days since last outing | SCORING intermediate |

---

## L. JIG / Tactical Fields (JIG board only)

The JIG score is computed in `api/main.py:_jig_score()` from the player dict and arsenal data. It is not computed in `pipeline.py`. No MAIN scoring fields are touched.

| API Key | Label | Source | D/S |
|---------|-------|--------|-----|
| `jigScore` | JIG Tactical Score (0–100+, uncapped) | `_jig_score()`: xSLG (25%) + barrel (20%) + xISO (15%) + pull_air (15%) + HH (15%) + sweet (10%) + PA stab + HR/PA term + arsenal signal + pitch-dmg signal + pitch-mix signal | **JIG-SCORING** |
| `jigTier` | JIG Tier | Derived from jigScore vs `config.JIG_TIER_THRESHOLDS` (0–100 bands): APEX ≥88 / ELITE ≥75 / EDGE ≥60 / SIGNAL ≥40 / WATCH ≥20 / COLD <20 | DISPLAY (JIG board) |
| `jigscore_projected` | JIG Projected Score | `jigScore` when `pitcher_confirmed=True`; `null` otherwise | DISPLAY |

---

## M. Arsenal Edge (AEE) Fields

Added by `engine/arsenal_edge.compute_aee_score()` after the JIG build phase. Appended to all rows (MAIN + JIG) via `r.update(_aee)`.

| API Key | Label | Source | D/S |
|---------|-------|--------|-----|
| `arsenal_edge_score` | AEE Score (0–10) | Arsenal matchup quality vs batter contact profile | DISPLAY + used in `true_matchup_score` (30% weight) |
| `arsenal_edge_confidence` | AEE Confidence (0–1) | PA-based signal reliability | DISPLAY + used in `true_matchup_score` (20% weight) |
| `arsenal_edge_label` | AEE Verdict Label | Text verdict string | DISPLAY |

---

## N. Role Flags

Derived by `roles.py:classify_role()` from existing row fields. Non-exclusive — a player may hold multiple flags simultaneously. Never modifies `model_prob`, `score`, `tier`, or any sort key.

| API Key | Label | Gate | Tiers Eligible | D/S |
|---------|-------|------|---------------|-----|
| `prime` | PRIME | barrel ≥ threshold AND xslg ≥ threshold AND HH% ≥ threshold AND EV ≥ threshold | APEX or ELITE only | DISPLAY |
| `explosive` | EXPLOSIVE | max_ev ≥ threshold AND barrel ≥ threshold AND (blast ≥ threshold OR pull_air ≥ threshold) | All tiers | DISPLAY |
| `advantage` | ADVANTAGE | xslg ≥ threshold OR barrel ≥ threshold | Non-top-tiers only | DISPLAY (JIG-surfaced) |
| `wildcard` | WILDCARD | ≥1 of {max_ev, barrel, xslg, pull_air} clears threshold | Non-top-tiers only | DISPLAY (JIG-surfaced) |

Thresholds live in `config.py` under `ROLE_PRIME_*`, `ROLE_EXPLOSIVE_*`, `ROLE_ADVANTAGE_*`, `ROLE_WILDCARD_*`. Top-tier gate uses `config.ROLE_TOP_TIERS`.

---

## O. FanDuel Handoff Fields — DISPLAY ONLY

| API Key | Pipeline Key | Label | Source |
|---------|-------------|-------|--------|
| `fd_event_link` | `fd_event_link` | FanDuel Event URL | Odds API FD deep-link map; `null` when unmapped |
| `fd_bet_link` | `fd_bet_link` | FanDuel Outcome Bet URL (rare) | Odds API FD outcome-level links; `null` in most cases |

Note: `fd_event_sid` is in the pipeline player dict but is NOT emitted in `leaderboard_rows`. It appears in the `/api/picks/{date}` response.

---

## P. DEAD / NULL Fields

These keys are present in every `leaderboard_rows` object but are always `None` — the source is never fetched or the derivation is not implemented.

| API Key | Intended Label | Status |
|---------|---------------|--------|
| `woba` | wOBA | Stubbed `None` — no source wired. `xwoba` is the live proxy. |
| `whiff` | Whiff % | Stubbed `None` — pitch-level data not fetched from leaderboard endpoints. |
| `swstr` | Swinging Strike % | Stubbed `None` — pitch-level data not fetched. |
| `pullbrl` | Pull Barrel % | Stubbed `None` — derived metric not implemented. |

---

## Q. Fields in Pipeline Dict But NOT in `/api/slate` Payload

These are computed in `pipeline.py` and stored in the player dict but are filtered out by `_build_slate_payload()` or `serializable()`. They are accessible in the `/api/picks/{date}` payload under `all_players`.

| Pipeline Key | Label | Why excluded from /api/slate |
|-------------|-------|------------------------------|
| `weather` | Weather dict (temp_f, wind_mph, wind_deg, humidity_pct) | Stripped by `serializable()`; only a summary string is included in `slate_games` |
| `best_american` | Best available odds (American int) | In picks payload; not in slate payload |
| `best_bookmaker` | Best book name | In picks payload |
| `all_prices` | All book prices list | In picks payload |
| `prices_by_book` | {book: price} dict | In picks payload |
| `market_no_vig_prob` | No-vig market probability | In picks payload |
| `market_no_vig_prob_fixed` | Fixed-vig version | In picks payload |
| `vig_by_book` | {book: vig fraction} | In picks payload |
| `market_implied_avg` | Market implied prob avg | In picks payload |
| `fanduel_american` | FD odds (int) | Converted to formatted string `odds` in slate payload |
| `ev_pct` | EV% | In picks payload; not in slate payload |
| `edge_pct` | Edge% | In picks payload |
| `confidence` | Confidence score | In picks payload |
| `bet_dollars` | Bet size | In picks payload |
| `confidence_tier` | S/A/B/C tier | In picks payload |
| `rank` | Final rank (qualified picks) | In picks payload `ranked` list |
| `score` | Composite score | In picks payload |
| `filter_reasons` | Filter failure reasons | In picks payload |
| `soft_flags` | Non-disqualifying cautions | In picks payload |
| `xba` | Expected BA | Not emitted (used internally for xISO derivation) |
| `xslg_diff` | xSLG − actual SLG | Not emitted |
| `has_statcast` | Statcast coverage boolean | Not emitted |
| `statcast_source` | Statcast tier (current/blended/prior/none) | Not emitted in slate payload |
| `fd_event_sid` | FanDuel event SID | Not in slate payload |
| `multi_season_splits` (raw) | Multi-season split dict | Emitted as `multi_season_vs_hand` |

---

## R. PropFinder Comparison

> ⚠️ **INCOMPLETE — Luna inventory not found in repo/wiki as of 2026-07-21.**
>
> The task that produced this document referenced "the Luna inventory" as the authoritative PropFinder stat set for this comparison. That document was not found anywhere in `MLB HR ENGINE/wiki/`, session notes, or the repo. The sections below are structured placeholders only. Do NOT treat the PropFinder column as audited until the Luna inventory is located and this section is updated.

### Engine stats that map to common prop-research categories

The following engine fields cover territory that most HR prop research tools track:

| Engine Field(s) | Category |
|----------------|---------|
| `hrprob` / `model_prob` | Model HR probability |
| `hr`, `hrpa`, `hrfb` | Season HR production rate |
| `avg`, `slg`, `obp`, `babip` | Traditional batting rates |
| `barrel`, `ev`, `hh`, `sweet`, `fb`, `pull` | Statcast contact profile |
| `xslg`, `iso`, `xwoba` | Expected / quality metrics |
| `opphr` / `pitcher_hr9`, `pitcher_era`, `pitcher_whip`, `pitcher_k_pct`, `pitcher_barrel_allowed` | Pitcher context |
| `vs_hand_*`, `vs_lhp_*`, `vs_rhp_*`, `multi_season_vs_hand` | Handedness splits |
| `recent_form_games` | Recent form / hot-cold |
| `odds` | Market line |
| `quality`, `pitcherVuln` | Matchup classification |
| Weather summary string in `slate_games` | Game-level weather |
| `hrFactor` in `slate_games` | Park factor |

### Known unfetched / dead fields in our engine

These are confirmed absent or dead in the engine as of 2026-07-21. Many are standard prop-research inputs that third-party tools may carry:

| Field | Status in Engine |
|-------|-----------------|
| `woba` (traditional) | **DEAD** — always `None`; `xwoba` is the proxy |
| `whiff` / `swstr` | **DEAD** — stubbed `None`; pitch-level leaderboard not fetched |
| `pullbrl` (pull barrel%) | **DEAD** — stubbed `None`; not implemented |
| xFIP | **NOT FETCHED** — known gap (`known-gaps.md`); K/GB suppressor used instead |
| Sprint speed | **NOT FETCHED** — no source wired |
| Chase rate / O-Swing% / Z-Swing% | **NOT FETCHED** — pitch-level discipline metrics not in leaderboard pull |
| Contact% | **NOT FETCHED** |
| Zone% | **NOT FETCHED** |
| Pitcher velocity per pitch type | **NOT FETCHED** — confirmed gap (`known-gaps.md` Arsenal Velocity entry); endpoint carries no velocity column |
| Traditional ISO (SLG − AVG) | **NOT EMITTED** — engine computes `xISO` (xslg − xba); traditional ISO not emitted |
| Line movement / opening odds | **NOT FETCHED** — no CLV-style tracking in slate payload |

### Engine extras PropFinder tools typically lack

These are engine-specific fields unlikely to appear in standard prop-research tools:

- `jigScore` / `jigTier` — JIG tactical exploit score (contact + arsenal + pitch-mix composite)
- `arsenal_edge_score` / `arsenal_edge_confidence` / `arsenal_edge_label` — pitch-type arsenal edge
- `true_matchup_score` / `tm_projected` — True Matchup Score (TM; model + AEE + vuln composite)
- `model_prob_projected` / `hrprob_projected` — pre-lineup projected probability with typical-slot PA
- `h2h_factor` — career batter vs. pitcher head-to-head multiplier
- `batspeed`, `blast`, `fast`, `squp`, `comp` — Savant bat-tracking fields
- `pullair` (pull × (fb + ld)) — directional power compound
- `prime` / `explosive` / `advantage` / `wildcard` — role flags
- `confidence_tier` (S/A/B/C) — EV × Edge × data-quality signal tier
- `ev_pct`, `edge_pct` — explicit EV and edge vs. no-vig market
- Platt-calibrated probability output with `prob_scale` adaptive adjustment
- `multi_season_vs_hand` — multi-season vs-hand aggregate splits

---

*To complete Section R: locate the Luna inventory document, identify PropFinder's confirmed stat set, and replace the placeholder tables above with the audited match/gap/extra lists. Update the date line at the top of this file when the section is filled.*
