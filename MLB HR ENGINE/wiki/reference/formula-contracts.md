# Formula Contracts — HR Engine v4

**Audit date:** 2026-07-21

**Surface:** `/api/slate` player rows (`leaderboard_rows[]` and `leaderboard_rows_jig[]`)

**Method:** direct current-code trace plus a production payload cross-check

**Contract count:** 110 unique player/stat contracts: all 108 emitted MAIN/JIG row keys plus the priority `air` and `ss` aliases
**Change policy:** documentation only. No formula, scoring, pipeline, payload, config, frontend, or deployment change is authorized by this document.

## Reading this reference

- **Internal key** shows `API key <- pipeline/source key` when names differ.
- **Numerator / denominator** describe the value actually emitted. For upstream Savant expected or bat-tracking fields, the engine does not receive event counts; the contract therefore names the upstream population and explicitly says that the local code does not recompute it.
- **Window:** `season*` means current MLB season, except `get_player_season_stats()` replaces the entire batter season row with the prior season when current-season PA is below 30 (`clients/mlb_stats.py:290-335`). `SC blend` means current Statcast at 50+ PA, current/prior linear blend below 50 PA when prior data exists, or prior-only when current data is absent (`clients/statcast.py:81-129`; threshold at `config.py:87-90`). Bat tracking is current-season only with Savant `min=1` (`clients/statcast.py:726-749`).
- **Scope:** `all` means no handedness or pitch-type split. `vs hand` means the faced pitcher hand. `per pitch` means pitch-type scoped.
- **Status:** `MAIN` feeds `model_prob` or a MAIN factor; `JIG` feeds `_jig_score`; `TM` feeds the display-only True Matchup composite; `ROLE/AEE` feeds display-only role or Arsenal Edge classification; `OUTPUT` is derived from scoring but is not an input; `DISPLAY` is not scoring; `DEAD` is always null.
- API normalization is `_pct`/`_flt` to one decimal and `_rate` to three decimals, with missing/unparseable values becoming `None` (`api/main.py:536-563`). The row serializer is `api/main.py:718-876`.

## Contract-risk findings

| Severity | Key / label | Current real contract | Risk |
|---|---|---|---|
| **MISMATCH** | `pullair` / PULLAIR% | `100 × pull_fraction × (fb_fraction + ld_fraction)` (`clients/statcast.py:315-333`) | This is a compound of marginal rates, used as a proxy for pulled airborne BBE / all BBE. It is **not** an observed joint-event count and is **not** PropFinder's pulled-air / all-air-balls definition. The UI title implies an observed pulled-air rate (`frontend/assets/js/full-slate-matrix.js:101`). |
| **MISMATCH** | `iso` / ISO | `xSLG − xBA`, emitted from pipeline `xiso` (`pipeline.py:233-237`, `api/main.py:808`) | The season UI describes generic isolated power/season fallback, but the emitted season value is xISO, not actual `SLG − AVG` (`frontend/assets/js/full-slate-matrix.js:99`). |
| **MISMATCH** | `barrel` / BARREL% | Savant CSV column `brl_pa`, parsed as a percentage (`clients/statcast.py:558-591`) | The source column is barrels per PA; the UI describes generic Barrel rate without naming the denominator (`frontend/assets/js/full-slate-matrix.js:97`). Do not silently interpret it as barrels per BBE. |
| **MISMATCH** | `obp` / OBP | `(H + BB + HBP) / (AB + BB + HBP)` (`pipeline.py:217-232`) | This is an approximation that omits sacrifice flies from the official OBP denominator while the UI label is unqualified OBP (`frontend/assets/js/full-slate-matrix.js:112`). |
| **ALIAS GAP** | `ss` | No `ss` payload key. Current key is `sweet`, displayed as `SS%` (`api/main.py:811`; `frontend/assets/js/full-slate-matrix.js:107`). | A consumer expecting `ss` receives no field. |
| **DERIVED-ONLY** | `air` / AIR% | Frontend-only `round(fb + ld, 1)`; not emitted by the API (`frontend/assets/js/full-slate-matrix.js:125,154,177-178`). | Payload consumers cannot assume `air` exists. |
| **FIXED / CURRENT** | `hrfb` / HR/FB% | `100 × season_hr / (season_hr + season_air_outs)`, null on zero denominator (`pipeline.py:380-385`; `api/main.py:827`). | Current label and formula now align. This is the documented current code, not the older `hr_rate` alias. |

## A. Batter and contact-stat contracts

| Internal key | Display label | Numerator | Denominator | Source / computation | Unit / scale | Window | Hand | Pitch | Null behavior | Minimum sample | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `pa <- season_pa` | PA | MLB `plateAppearances` | n/a count | MLB Stats season group; `pipeline.py:192-196,430`; serialized `api/main.py:748,781` | integer | season* | all | all | zero-PA player is dropped only when recent PA is also zero (`pipeline.py:197-199`) | prior-season replacement if current PA <30 | MAIN + JIG stabilization |
| `hr <- season_hr` | HR | MLB `homeRuns` | n/a count | MLB Stats season group; `pipeline.py:382,430`; `api/main.py:749,807` | integer | season* | all | all | missing coerces to `0` | prior-season replacement if current PA <30 | MAIN + JIG HR term |
| `avg <- batting_avg` | AVG | hits | at-bats | `pipeline.py:373-376,489`; `api/main.py:782` | decimal 0–1, 3 dp | season* | all | all | `0.0` if AB=0 | prior-season replacement if current PA <30 | DISPLAY; analogous raw MLB AVG is used inside MAIN ISO adjustment |
| `slg <- actual_slg` | SLG | `1B + 2×2B + 3×3B + 4×HR` | at-bats | `pipeline.py:217-232,487`; `api/main.py:783` | decimal 0–4, 3 dp | season* | all | all | `0.0` if AB=0 | prior-season replacement if current PA <30 | DISPLAY; raw MLB SLG also informs MAIN `base_hr_rate` |
| `obp <- actual_obp` | OBP | `H + BB + HBP` | `AB + BB + HBP` (**SF omitted**) | `pipeline.py:217-232,488`; `api/main.py:812` | decimal 0–1, 3 dp | season* | all | all | `0.0` if denominator=0 | prior-season replacement if current PA <30 | DISPLAY; **MISMATCH** |
| `babip <- season_babip` | BABIP | `H − HR` | `AB − K − HR + SF` | `pipeline.py:380-388,490`; `api/main.py:784` | decimal 0–1, 3 dp | season* | all | all | `None` if denominator ≤0 | prior-season replacement if current PA <30 | DISPLAY |
| `bbpct <- batter_bb_pct` | BB% | walks | plate appearances | `pipeline.py:495`; scaled in `api/main.py:814` | percentage points, 1 dp | season* | all | all | `None` when PA=0 | prior-season replacement if current PA <30 | DISPLAY; raw context may appear elsewhere, not an input key here |
| `kpct <- batter_k_pct` | K% | strikeouts | plate appearances | `pipeline.py:380,496`; scaled in `api/main.py:815` | percentage points, 1 dp | season* | all | all | `None` when PA=0 | prior-season replacement if current PA <30 | DISPLAY alias; raw K/PA feeds MAIN K suppressor (`engine/probability.py:181-195`) |
| `hrpa` | HR/PA | season HR | season PA | computed in serializer `api/main.py:747-750,796` | decimal 0–1, 3 dp | season* | all | all | `None` when PA=0 | prior-season replacement if current PA <30 | DISPLAY; JIG independently recomputes HR/PA from pipeline counts (`api/main.py:627-631`) |
| `hrfb <- hrfb` | HR/FB% | season HR | `season HR + MLB airOuts` | `pipeline.py:380-385,431`; `api/main.py:827` | percentage points, 1 dp | season* | all | all | `None` when denominator=0 | prior-season replacement if current PA <30 | DISPLAY/filter only; no MAIN/JIG/TM/tier input |
| `barrel <- barrel_pct <- barrel_rate` | BARREL% | Savant barrels | PA, per source column `brl_pa` | Statcast leaderboard CSV `brl_pa`; `clients/statcast.py:460-475,558-591`; summary `:336-365`; serializer `api/main.py:788` | percentage points, 1 dp | SC blend | all | all | missing → `--` → `None` | Savant min=1; scoring copy is PA-stabilized with 60-PA half-life (`config.py:125-136`) | MAIN + JIG + confidence + ROLE/AEE; **denominator-label risk** |
| `hh <- hard_hit <- hard_hit_pct` | HH% | BBE at ≥95 mph | BBE | Statcast leaderboard CSV `ev95percent`; `clients/statcast.py:558-591`; `api/main.py:786` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1; MAIN copy half-life 80 PA | MAIN + JIG + ROLE/AEE |
| `ev <- exit_velo <- exit_velocity_avg` | EV | sum exit velocity of eligible BBE | eligible BBE | Statcast leaderboard `avg_hit_speed`; `clients/statcast.py:558-591`; `api/main.py:789` | mph, 1 dp | SC blend via `exit_velocity_avg` (`clients/statcast.py:66-70,119-126`) | all | all | missing → `None` | Savant min=1; MAIN copy half-life 50 PA | MAIN + ROLE |
| `maxev <- max_ev` | MAX EV | maximum eligible BBE EV | n/a maximum | Statcast leaderboard `max_hit_speed`; `clients/statcast.py:558-591`; `api/main.py:826` | mph, 1 dp | current season if present; prior only when current row absent | all | all | `None` if missing/outside 60–130 mph | Savant min=1 | DISPLAY + ROLE |
| `la <- avg_launch_angle` | LA° | sum launch angle of eligible BBE | eligible BBE | Statcast leaderboard `avg_hit_angle`; `clients/statcast.py:558-590`; `api/main.py:790` | degrees, 1 dp | current season if present; prior only when current row absent | all | all | missing `--` → `None` | Savant min=1 | DISPLAY |
| `xslg` | xSLG | Savant expected total bases | expected-stat AB population | Statcast/expected-stat CSV `xslg`; merge priority `clients/statcast.py:378-414`; parsers `:558-591,655-693`; `api/main.py:809` | decimal, 3 dp | SC blend | all | all | `None` if absent | Savant min=1; MAIN copy half-life 60 PA | MAIN + JIG + ROLE; profile-parlay input |
| `iso <- xiso` | ISO (actually xISO) | `xSLG − xBA` | n/a difference | expected-stat `xslg`/`xba`; `pipeline.py:233-237,485`; `api/main.py:808` | decimal difference, 3 dp | SC blend (`xslg` and `xba`) | all | all | `None` unless both inputs exist | no local gate | JIG; **MISMATCH** with generic ISO label |
| `xwoba` | xwOBA | Savant expected wOBA value sum | wOBA PA population | expected-stat CSV `xwoba`; `clients/statcast.py:655-693`; `pipeline.py:378,491`; `api/main.py:795` | decimal, 3 dp | current if present; prior only if current player absent (`xwoba` is not a blend key) | all | all | `None` if absent | Savant min=1 | DISPLAY |
| `sweet <- sweet_spot_pct` | SS% / Sweet Spot% | BBE with launch angle 8–32° | BBE | Statcast leaderboard `sweet_spot_percent`; `clients/statcast.py:558-590`; `api/main.py:811`; label `frontend/assets/js/full-slate-matrix.js:107` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1; MAIN copy half-life 120 PA | MAIN + JIG; profile-parlay input |
| `ss` (**proposed alias; not emitted**) | SS% | same as `sweet` | same as `sweet` | no serializer key; current contract is `sweet` at `api/main.py:811` | would be percentage points | SC blend | all | all | absent key, not JSON null | n/a | NOT IMPLEMENTED; alias gap |
| `gb <- gb_pct` | GB% | ground-ball BBE | classified BBE | Savant batted-ball CSV `gb_rate`; `clients/statcast.py:481-499,601-652`; `api/main.py:785` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1; no metric-specific scoring stabilization | DISPLAY |
| `fb <- fb_pct` | FB% | fly-ball BBE (Savant rate excludes popups per model comment) | classified BBE | Savant batted-ball CSV `fb_rate`; `clients/statcast.py:601-652`; model note `:217-220`; `api/main.py:810` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1; MAIN copy half-life 150 PA | MAIN; also indirectly creates `pullair` |
| `ld <- ld_pct` | LD% | line-drive BBE | classified BBE | Savant batted-ball CSV `ld_rate`; `clients/statcast.py:601-652`; `api/main.py:787` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1 | DISPLAY; indirectly creates `pullair` |
| `air` (**frontend only**) | AIR% | `FB% + LD%` | classified BBE basis | `frontend/assets/js/full-slate-matrix.js:125,154,177-178` | percentage points, 1 dp | inherited from FB/LD | all | all | `None` if sum is non-finite | inherited | DISPLAY; not emitted |
| `pull <- pull_pct` | PULL% | pull-side BBE | classified BBE | Savant batted-ball CSV `pull_rate`; `clients/statcast.py:601-652`; `api/main.py:791` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1; MAIN copy half-life 100 PA | MAIN; indirectly JIG/ROLE/AEE through `pullair` |
| `center <- center_pct` | CENTER% | residual `1 − pull_fraction − oppo_fraction` | classified BBE | `pipeline.py:390-396,492`; `api/main.py:792` | percentage points, 1 dp | SC blend | all | all | `None` if pull or oppo missing; clamped at 0 | inherited | DISPLAY; note code does not emit fetched `str_pct` |
| `oppo <- oppo_pct` | OPPO% | opposite-field BBE | classified BBE | Savant batted-ball CSV `oppo_rate`; `clients/statcast.py:601-652`; `api/main.py:793` | percentage points, 1 dp | SC blend | all | all | missing → `None` | Savant min=1 | DISPLAY; contributes to residual center only |
| `pullair <- pull_air_pct` | PULLAIR% | proxy `pull_share × airborne_share` | all BBE conceptual scale; no observed joint count | `100 × pull_fraction × (fb_fraction + ld_fraction)` at `clients/statcast.py:315-333`; `api/main.py:819` | percentage points, 1 dp in payload | SC blend inputs | all | all | `None` if any component missing | inherited | JIG + ROLE/AEE → TM indirectly; **MISMATCH vs observed/PropFinder definitions** |
| `fast <- hard_swing_rate` | FAST% | Savant hard swings (75+ mph bat speed) | Savant eligible swings | bat-tracking CSV `hard_swing_rate`; `clients/statcast.py:726-749,752-788,791-837`; `api/main.py:821` | percentage points, 1 dp | current season | all | all | `None` if absent/outside 0–1 raw | Savant min=1 | DISPLAY |
| `squp <- squared_up_per_swing` | SQUP% | squared-up swings | Savant eligible swings | bat-tracking CSV; `clients/statcast.py:752-788,824-826`; `api/main.py:822` | percentage points, 1 dp | current season | all | all | `None` if absent/outside 0–1 raw | Savant min=1 | DISPLAY |
| `blast <- blast_per_swing` | BLAST% | blast swings | Savant eligible swings | bat-tracking CSV; `clients/statcast.py:752-788,827-829`; `api/main.py:823` | percentage points, 1 dp | current season | all | all | `None` if absent/outside 0–1 raw | Savant min=1 | DISPLAY + ROLE EXPLOSIVE |
| `comp <- percent_swings_competitive` | COMP% | competitive swings | Savant eligible swings | bat-tracking CSV; `clients/statcast.py:752-788,830-832`; `api/main.py:824` | percentage points, 1 dp | current season | all | all | `None` if absent/outside 0–1 raw | Savant min=1 | DISPLAY |
| `batspeed <- avg_bat_speed` | BAT SPEED | sum bat speed | Savant eligible/competitive swing population | bat-tracking CSV; `clients/statcast.py:752-788,833-835`; `api/main.py:825` | mph, 1 dp | current season | all | all | `None` if absent/unparseable | Savant min=1 | DISPLAY |
| `woba` | wOBA | none | none | literal `None` in serializer `api/main.py:813` | null | none | none | none | always `null` | none | DEAD / no source |
| `whiff` | WHIFF% | none | none | literal `None` in serializer `api/main.py:816` | null | none | none | none | always `null` | none | DEAD / no source |
| `swstr` | SWSTR% | none | none | literal `None` in serializer `api/main.py:817` | null | none | none | none | always `null` | none | DEAD / no source |
| `pullbrl` | PULLBRL% | none | none | literal `None` in serializer `api/main.py:818` | null | none | none | none | always `null` | none | DEAD / no source |

## B. MAIN output and matchup-context contracts

| Internal key | Display label | Numerator | Denominator | Source / computation | Unit / scale | Window | Hand | Pitch | Null behavior | Minimum sample | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `model_prob` | MAIN HR Probability | `1 − exp(−λ)` after context, lineup penalty, adaptive scale, calibration | probability | `λ = adjusted_hr_rate × capped_context × expected_PA`; `engine/probability.py:428-462`; pipeline sequence `pipeline.py:318-344,473` | decimal 0–0.29 cap | slate/game | matchup | all | pipeline guards return at least `.001`; serializer missing defaults to `0` (`api/main.py:747,798`) | multiple upstream gates | MAIN canonical score/output |
| `hrprob` | HR PROB% | `model_prob × 100` | n/a | `api/main.py:747,797` | percentage points, 1 dp | slate/game | matchup | all | missing model probability becomes `0.0` | inherited | OUTPUT; primary MAIN row sort `api/main.py:878-881` |
| `tier` | MODEL TIER / FS Tier | threshold classification of `model_prob` | n/a | thresholds `config.py:260-270`; serializer `api/main.py:752-755,799` | categorical | slate/game | matchup | all | missing/zero → COLD | none beyond model | OUTPUT; MAIN-derived; JIG inherits this as MODEL TIER |
| `model_tier_rank` | HR Threat Rank ordinal | count encountered within each `tier` after board sort | rows in same tier | MAIN/JIG stamping `api/main.py:882-887,923-928` | integer ordinal | slate | all | all | always assigned to built rows | n/a | OUTPUT; MAIN order uses HR probability, JIG copy is re-numbered after JIG sort |
| `quality <- matchup_quality` | QUALITY | threshold class from model probability, with low-barrel WEAK gate | n/a | `_matchup_quality_tier`; `pipeline.py:82-129,411-417,493`; serialized `api/main.py:757-759,779` | ELITE/STRONG/AVG/WEAK | slate/game | matchup | all | missing values coerce to zero; likely WEAK | none beyond inputs | DISPLAY classification derived from MAIN + barrel |
| `pitcherVuln <- pitcher_vuln` | PITCHER VULN | `pitcher_hr9 >= 2.2` | n/a | `pipeline.py:132-142,494`; `config.py:255-258`; `api/main.py:780` | TARGET/NEUTRAL | season matchup | all | all | missing/zero → NEUTRAL | pitcher HR/9 itself requires 5 IP or emits 0 | DISPLAY; same raw pitcher data already affects MAIN |
| `opphr <- pitcher_hr9` | OPP HR/9 | pitcher HR × 9 | innings pitched | derived `pipeline.py:293-296`; duplicate serialized key `api/main.py:794` | HR per 9 IP, 2 dp upstream | season* pitcher | all | all | emits `0.0`, not null, when IP <5 | 5 IP | DISPLAY duplicate of `pitcher_hr9` |
| `h2h_factor` | H2H Factor | regressed batter-vs-pitcher HR/PA ratio | league HR/PA; confidence by H2H PA | `engine/probability.py:465-492`; computed `pipeline.py:314-316,448`; `api/main.py:820` | multiplier 0.93–1.14, 4 dp | career H2H | exact batter-pitcher | all | absent or <5 PA → 1.0 | 5 PA to move; weight begins after 10 PA, full at 50 | MAIN |
| `model_prob_projected` | Projected MAIN Probability | same MAIN formula using typical/default slot and no 0.82 non-lineup penalty | probability | `pipeline.py:346-371,427`; `api/main.py:835` | decimal | slate/game | matchup | all | `None` with no announced pitcher | pitcher required | DISPLAY projection; never fed into live scoring/EV/filters |
| `hrprob_projected` | Projected HR PROB% | projected probability ×100 | n/a | `pipeline.py:427-429`; `api/main.py:836` | percentage points, 1 dp | slate/game | matchup | all | `None` with no projection | pitcher required | DISPLAY |
| `projected_pa_source` | Projection PA Source | source tag | n/a | confirmed/typical-slot/default branch `pipeline.py:346-371,429`; `api/main.py:837` | categorical | trailing 7-day slot lookup or default | all | all | `None` with no pitcher | pitcher required | DISPLAY |
| `_board` | Board Identity | literal assignment | n/a | MAIN/JIG assignment `api/main.py:887,928` | `main` / `jig` | request | all | all | always present on built rows | n/a | DISPLAY/routing |

## C. Handedness and recent-form contracts

All one-season split display fields are emitted at any PA count; the backend model only receives `vl`/`vr` HR rates at 30+ PA. The frontend applies a 30-PA reliability tag rather than suppressing the values (`clients/mlb_stats.py:457-507`; `pipeline.py:398-470`).

| Internal key | Display label | Numerator | Denominator | Source / computation | Unit / scale | Window | Hand | Pitch | Null behavior | Minimum sample | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `recent_form_games` | Recent Form | per-game HR, H/AB, TB/AB, PA | per game AB where applicable | cached MLB game logs; `pipeline.py:162-183,478`; `api/main.py:838` | array, up to 5 games | latest 5 cached games | all | all | empty array if no cache; per-rate `None` if AB=0 | none | DISPLAY |
| `vs_hand` | Faced Hand | selected pitcher hand | n/a | selection `pipeline.py:401-409,452`; `api/main.py:840` | L/R/null | current season | faced hand | all | `None` if pitcher hand unknown | none | DISPLAY scope marker |
| `vs_hand_avg` | AVG vs Hand | hits | AB | MLB statSplits `avg`; `clients/mlb_stats.py:472-502`; selected `pipeline.py:401-458`; `api/main.py:841` | decimal | current season | faced hand | all | `None` if absent | display at any PA; tag <30 | DISPLAY |
| `vs_hand_slg` | SLG vs Hand | total bases | AB | MLB statSplits `slg`; same trace; `api/main.py:842` | decimal | current season | faced hand | all | `None` if absent | display at any PA; tag <30 | DISPLAY |
| `vs_hand_iso` | ISO vs Hand | split SLG − split AVG | n/a | `clients/mlb_stats.py:491-500`; `api/main.py:843` | decimal difference | current season | faced hand | all | `None` unless AVG and SLG exist | display at any PA; tag <30 | DISPLAY |
| `vs_hand_hr` | HR vs Hand | home runs | count | `clients/mlb_stats.py:485-500`; `api/main.py:844` | integer | current season | faced hand | all | zero if API supplies zero; `None` if no split dict | display at any PA | DISPLAY |
| `vs_hand_hr_pa` | HR/PA vs Hand | split HR | split PA | `clients/mlb_stats.py:485-500`; `api/main.py:845` | decimal, 4 dp | current season | faced hand | all | `None` when PA=0/absent | display at any PA; tag <30 | DISPLAY |
| `vs_hand_pa` | PA vs Hand | plate appearances | count | `clients/mlb_stats.py:485-501`; `api/main.py:846` | integer | current season | faced hand | all | `None` if no split dict | none | DISPLAY/reliability |
| `vs_lhp_avg` | AVG vs LHP | hits | AB | MLB statSplits `vl`; `pipeline.py:401-470`; `api/main.py:847` | decimal | current season | vs LHP | all | `None` if absent | display any PA | DISPLAY |
| `vs_lhp_slg` | SLG vs LHP | total bases | AB | same; `api/main.py:848` | decimal | current season | vs LHP | all | `None` if absent | display any PA | DISPLAY |
| `vs_lhp_iso` | ISO vs LHP | SLG − AVG | n/a | same; `api/main.py:849` | decimal | current season | vs LHP | all | `None` unless inputs exist | display any PA | DISPLAY |
| `vs_lhp_hr` | HR vs LHP | HR | count | same; `api/main.py:850` | integer | current season | vs LHP | all | `None` if absent | display any PA | DISPLAY |
| `vs_lhp_hr_pa` | HR/PA vs LHP | HR | PA | same; `api/main.py:851` | decimal | current season | vs LHP | all | `None` when PA=0/absent | display any PA | DISPLAY |
| `vs_lhp_pa` | PA vs LHP | PA | count | same; `api/main.py:852` | integer | current season | vs LHP | all | `None` if absent | none | DISPLAY |
| `vs_rhp_avg` | AVG vs RHP | hits | AB | MLB statSplits `vr`; `pipeline.py:401-470`; `api/main.py:853` | decimal | current season | vs RHP | all | `None` if absent | display any PA | DISPLAY |
| `vs_rhp_slg` | SLG vs RHP | total bases | AB | same; `api/main.py:854` | decimal | current season | vs RHP | all | `None` if absent | display any PA | DISPLAY |
| `vs_rhp_iso` | ISO vs RHP | SLG − AVG | n/a | same; `api/main.py:855` | decimal | current season | vs RHP | all | `None` unless inputs exist | display any PA | DISPLAY |
| `vs_rhp_hr` | HR vs RHP | HR | count | same; `api/main.py:856` | integer | current season | vs RHP | all | `None` if absent | display any PA | DISPLAY |
| `vs_rhp_hr_pa` | HR/PA vs RHP | HR | PA | same; `api/main.py:857` | decimal | current season | vs RHP | all | `None` when PA=0/absent | display any PA | DISPLAY |
| `vs_rhp_pa` | PA vs RHP | PA | count | same; `api/main.py:858` | integer | current season | vs RHP | all | `None` if absent | none | DISPLAY |
| `multi_season_vs_hand` | Multi-season vs Hand | nested HR/counts and upstream AVG/SLG/OBP; AB/HR = AB ÷ HR | split PA/AB as applicable | MLB statSplits; three-season window `clients/mlb_stats.py:514-580`; `pipeline.py:471-472`; `api/main.py:860` | nested object | current + prior 2 seasons | vl/vr | all | missing seasons/hands omitted; AB/HR `None` when HR=0 | no gate | DISPLAY |

## D. Pitcher-stat contracts

Pitcher season data uses current season with prior-season replacement below 5 IP (`clients/mlb_stats.py:380-425`). Pitcher Statcast uses the same 50-PA/BF current/prior blend policy as batter Statcast (`clients/statcast.py:132-174`).

| Internal key | Display label | Numerator | Denominator | Source / computation | Unit / scale | Window | Hand | Pitch | Null behavior | Minimum sample | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `pitcher_name` | Pitcher | MLB probable pitcher name | n/a | schedule/Stats API; `pipeline.py:254-265,422`; `api/main.py:828` | string | game | opposing pitcher | all | `TBD` pipeline default / serializer `None` default | none | DISPLAY |
| `pitcher_confirmed` | Pitcher Confirmed | `pitcher_id is not None` | n/a | `pipeline.py:422-425`; `api/main.py:829` | boolean | game | opposing pitcher | all | false if no ID | none | DISPLAY; actually “probable/identified,” not official confirmation |
| `pitcher_id` | Pitcher MLBAM ID | MLB ID | n/a | schedule hydration; `pipeline.py:254-265,422`; `api/main.py:830` | integer | game | opposing pitcher | all | `None` if unavailable | none | identity/input routing |
| `pitcher_hand` | Pitcher Hand | MLB `pitchHand.code` | n/a | `pipeline.py:264-265,450`; `api/main.py:831` | L/R | current player info | opposing pitcher | all | empty/`None` if unavailable | none | MAIN platoon + JIG pitch data selection |
| `pitcher_era` | Pitcher ERA | earned runs ×9 | innings pitched | upstream MLB Stats season value; pass-through `pipeline.py:499-501`; `api/main.py:861` | runs/9 | season* pitcher | all | all | `None` if absent | prior replacement below 5 IP | DISPLAY |
| `pitcher_whip` | Pitcher WHIP | walks + hits | innings pitched | upstream MLB Stats season value; `pipeline.py:499-501`; `api/main.py:862` | baserunners/IP | season* pitcher | all | all | `None` if absent | prior replacement below 5 IP | DISPLAY |
| `pitcher_k_pct` | Pitcher K% | strikeouts | batters faced | `pipeline.py:502-504`; `api/main.py:863` | percentage points, 1 dp | season* pitcher | all | all | `None` if BF=0 | prior replacement below 5 IP | DISPLAY; raw pitcher K/BF separately feeds MAIN pitcher suppressor |
| `pitcher_bb_pct` | Pitcher BB% | walks | batters faced | `pipeline.py:505-507`; `api/main.py:864` | percentage points, 1 dp | season* pitcher | all | all | `None` if BF=0 | prior replacement below 5 IP | DISPLAY; raw pitcher BB/BF separately feeds MAIN pitcher suppressor |
| `pitcher_barrel_allowed` | Barrel% Allowed | Savant pitcher barrels | PA, source `brl_pa` | pitcher Statcast parser `clients/statcast.py:132-174,525-598`; pass-through `pipeline.py:508-512`; `api/main.py:865` | decimal fraction 0–1 (not percentage points) | SC blend | all batters | all | `None` if absent | Savant min=1; MAIN factor copy half-life 60 BF | DISPLAY alias; same raw source feeds MAIN pitcher contact factor; also TM vuln component |
| `pitcher_hh_allowed` | HH% Allowed | hard-hit BBE | BBE | pitcher Statcast `hard_hit_pct`; `pipeline.py:508-512`; `api/main.py:866` | decimal fraction 0–1 | SC blend | all batters | all | `None` if absent | Savant min=1; MAIN copy half-life 80 BF | DISPLAY alias; same raw source feeds MAIN pitcher contact factor |
| `pitcher_fb_allowed` | FB% Allowed | fly-ball BBE | classified BBE | pitcher batted-ball `fb_pct`; `pipeline.py:508-512`; `api/main.py:867` | decimal fraction 0–1 | SC blend | all batters | all | `None` if absent | Savant min=1; MAIN copy half-life 150 BF | DISPLAY alias; same raw source feeds MAIN pitcher contact factor |
| `pitcher_gb_allowed` | GB% Allowed | ground-ball BBE | classified BBE | pitcher batted-ball `gb_pct`; `pipeline.py:508-512`; `api/main.py:868` | decimal fraction 0–1 | SC blend | all batters | all | `None` if absent | Savant min=1 | DISPLAY |
| `pitcher_hr9` | Pitcher HR/9 | HR ×9 | parsed innings pitched | `pipeline.py:293-296,474`; `clients/mlb_stats.py:136-144`; `api/main.py:869` | HR/9, 2 dp | season* pitcher | all | all | **0.0** when IP <5, not null | 5 IP | confidence + display/TM; same raw HR/IP is part of MAIN pitcher factor |

## E. JIG, Arsenal Edge, TM, and role contracts

| Internal key | Display label | Numerator | Denominator | Source / computation | Unit / scale | Window | Hand | Pitch | Null behavior | Minimum sample | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `jigScore` | JIG SCORE | normalized contact base + HR/PA term, PA stabilization, arsenal/pitch-damage/pitch-mix signals | fixed normalization bands | exact `_jig_score` formula `api/main.py:596-701`; assigned `:907-922` | index 0–100+, uncapped | mixed season/current pitch data | batter side / pitcher hand | arsenal weighted | missing numeric inputs become 0; tactical exceptions fall back to 0 | PA stabilization `PA/(PA+100)`; pitch feeds have their own gates | JIG canonical score/order; no `model_prob`, no HVY |
| `jigTier` | JIG TIER | threshold class of `jigScore` | n/a | `_jig_tier` `api/main.py:706-715`; thresholds `config.py:281-293`; assignment `api/main.py:913-914` | categorical | slate | matchup | all | built score always classifies | none | OUTPUT from JIG; not a JIG input |
| `jigscore_projected` | Projected JIG Score | current `jigScore` when pitcher is identified | n/a | `api/main.py:915-918` | index | slate | matchup | arsenal | `None` without identified pitcher | pitcher required | DISPLAY projection |
| `arsenal_edge_score` | AEE Score | `Σ(usage × blended_exploit × confidence) ×3 × batter_shape` | fixed league baselines and clamps | `engine/arsenal_edge.py:97-203`; attached `api/main.py:934-959` | 0–10, 1 dp | pitch datasets/cache | effective batter side | per pitch, usage weighted | `None` on data gap | batter-vs-pitch PA ≥3; pitcher HR rate needs ≥5 PA; hard hit source needs ≥5 contacts | DISPLAY AEE; feeds display-only TM |
| `arsenal_edge_label` | AEE Label | bands of AEE score/confidence | n/a | `engine/arsenal_edge.py:40-65,198-203` | categorical | same | same | same | `DATA GAP` when unavailable | inherited | DISPLAY |
| `arsenal_edge_key_pitch` | Key Pitch | pitch with max weighted contribution | eligible pitch contributions | `engine/arsenal_edge.py:130-146,183,192-203` | pitch code | same | same | per pitch | `None` on gap/no positive contribution | batter-vs-pitch PA ≥3 | DISPLAY |
| `arsenal_edge_confidence` | AEE Confidence | `Σ(usage × pitch_confidence)` | eligible usage sum | `engine/arsenal_edge.py:180-181,195-203` | decimal 0–1, 2 dp | same | same | per pitch | `None` on gap | batter-vs-pitch PA ≥3 | DISPLAY; feeds TM |
| `arsenal_edge_sample_flag` | AEE Thin Sample | any eligible batter-vs-pitch PA <10 | n/a | `engine/arsenal_edge.py:198-203` | boolean | same | same | per pitch | false on data gap | flags 3–9 PA | DISPLAY |
| `true_matchup_score` | TM | `100×(.40×model_n + .30×AEE_n + .20×AEE_conf + .10×pitcher_vuln_n)` | fixed clamps | `_true_matchup_score` `api/main.py:566-593`; assignment `:963-978` | integer 0–100 | slate/game | matchup | arsenal aggregate | `None` only if `model_prob` is `None`; missing AEE=0, missing pitcher vuln defaults neutral 0.5 | none beyond components | DISPLAY composite only; never feeds MAIN/JIG/order |
| `tm_projected` | Projected TM | same TM formula with projected model probability | fixed clamps | `api/main.py:963-978` | integer 0–100 | slate/game | matchup | arsenal aggregate | `None` without projected model probability | pitcher/projected probability required | DISPLAY |
| `prime` | PRIME Role | all: barrel≥9, xSLG≥.500, HH≥45, EV≥90, tier APEX/ELITE | threshold conjunction | `roles.py:41-73`; config `config.py:390-402`; serialized `api/main.py:872` | boolean | slate | all | all | false if any required field null | all required | DISPLAY ROLE only |
| `explosive` | EXPLOSIVE Role | maxEV≥113 and barrel≥8.5 and (blast≥12 or pullair≥20) | threshold conjunction | `roles.py:75-86`; config `config.py:404-407`; `api/main.py:873` | boolean | slate | all | all | null sub-trait skipped; both null → false | required core + one sub-trait | DISPLAY ROLE only |
| `advantage` | ADVANTAGE Role | non-top MAIN tier and (xSLG≥.490 or barrel≥9) | threshold gate | `roles.py:88-95`; `config.py:409-412,421-422`; `api/main.py:874,919-921` | boolean | slate | all | all | false if traits null | one qualifying trait | DISPLAY/JIG-surfaced ROLE only |
| `wildcard` | WILDCARD Role | non-top MAIN tier and ≥1 of maxEV≥116, barrel≥12, xSLG≥.520, pullair≥30 | threshold count | `roles.py:97-109`; `config.py:414-422`; `api/main.py:875,919-921` | boolean | slate | all | all | null traits do not pass | one qualifying trait | DISPLAY/JIG-surfaced ROLE only |

## F. Identity, market, lineup, and game-context contracts

| Internal key | Display label | Numerator | Denominator | Source / computation | Unit / scale | Window | Hand | Pitch | Null behavior | Minimum sample | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `id <- player_id` | Player ID | MLBAM ID; fallback name slug | n/a | `api/main.py:775` | int/string | slate | all | all | slug fallback | none | identity |
| `name <- player_name` | Player | MLB full name | n/a | pipeline profile `pipeline.py:419-422`; `api/main.py:776` | string | slate | all | all | may be empty only if source is empty | none | DISPLAY |
| `teamAbbr <- team` | Team | schedule team abbreviation | n/a | `pipeline.py:419-421`; `api/main.py:777` | string | game | all | all | source-dependent | none | DISPLAY |
| `bats <- batter_side` | Bats | MLB bat-side code | n/a | player info `pipeline.py:244-247,449`; `api/main.py:778` | L/R/S | current | batter | all | empty if unavailable | none | MAIN park/platoon + JIG routing |
| `gameId` | Game ID | away-home slug; append game_pk only on doubleheader collision | n/a | `api/main.py:727-743,765-771,800` | string | game | all | all | fallback team tokens | none | identity |
| `game_pk` | MLB Game PK | schedule game primary key | n/a | pass-through `api/main.py:801-802` | integer | game | all | all | `None` if source missing | none | identity/display |
| `odds <- fanduel_american` | ODDS | FanDuel American price formatted with plus sign | n/a | odds match `pipeline.py:609-641`; serializer `api/main.py:761-763,803` | string American odds | current market pull | all | all | `None` when no FD price or zero | market availability | DISPLAY only; market never changes MAIN rank/tier |
| `fd_event_link` | FanDuel Event Link | direct URL | n/a | odds link attachment `pipeline.py:645-696`; `api/main.py:805` | URL/null | current market pull | all | all | `None` when unmapped | none | DISPLAY handoff |
| `fd_bet_link` | FanDuel Bet Link | outcome URL | n/a | same; `api/main.py:806` | URL/null | current market pull | all | all | usually `None` | none | DISPLAY handoff |
| `lineup_confirmed` | Lineup Confirmed | `lineup_spot is not None` | n/a | `pipeline.py:424-425`; `api/main.py:833` | boolean | game | all | all | false without spot | none | MAIN: false triggers 0.82 probability penalty (`pipeline.py:335-338`) |
| `lineup_spot` | Lineup Spot | hydrated lineup order position | n/a | schedule parse `clients/mlb_stats.py:270-277`; pipeline `:250`; serializer `api/main.py:834` | integer 1–9 | game | all | all | `None` before lineup | none | MAIN expected PA |
| `gameStartUtc <- game_time_utc` | Game Start | schedule timestamp | n/a | `api/main.py:870` | UTC ISO string | game | all | all | empty string fallback | none | DISPLAY; weather lookup context upstream |
| `gameStatus <- game_status` | Game Status | schedule status | n/a | `api/main.py:871` | string | game | all | all | `Scheduled` fallback | none | DISPLAY |

## Production payload cross-check

Checked `https://mlb-hr-api.fly.dev/api/slate` on 2026-07-21. Response: date `2026-07-21`, `stale=false`, 234 MAIN rows and 234 JIG rows. Sample row: Yordan Alvarez (`id=670541`, game `824165`).

| Check | Payload | Recalculation / result |
|---|---:|---|
| Percentage-point Statcast scale | `barrel=12.8`, `hh=53.4`, `fb=40.1`, `ld=26.7`, `pull=41.8` | Confirms batter contact percentages emit on 0–100 scale. |
| Decimal expected-stat scale | `xslg=.723`, `xwoba=.479` | Confirms expected stats remain decimal rates. |
| PullAir compound | `pullair=27.9` | `41.8 × (40.1 + 26.7) / 100 = 27.9`; exact match. |
| AIR frontend derivation | not present in payload | `40.1 + 26.7 = 66.8`; confirms derived-only contract. |
| CENTER residual | `center=32.5` | `100 − 41.8 − 25.7 = 32.5`; exact match. |
| ISO mismatch | `iso=.384`, `slg=.651`, `avg=.324`, `xslg=.723` | actual `SLG−AVG=.327`, while emitted `.384` implies `xBA=.339`; confirms emitted xISO. |
| HR/FB snapshot | `hr=33`, `hrfb=22.3` | The payload snapshot corresponds to `33/(33+115)=22.3%`. A later in-progress MLB Stats API read had 441 PA and 116 airOuts, producing 22.1%; the difference is expected live-game timing, not a formula difference. |
| Dead fields | `woba=null`, `whiff=null`, `swstr=null`, `pullbrl=null` | Confirms all four stubs are null in production. |
| Pitcher Statcast scale | `pitcher_barrel_allowed=.056`, `pitcher_hh_allowed=.439` | Confirms pitcher allowed rates emit as 0–1 fractions, unlike batter percentage-point aliases. |
| Tactical outputs | `jigScore=100.17`, `jigTier=APEX`, `AEE=4.8`, `TM=74` | Confirms JIG can exceed 100, AEE is 0–10, and TM is integer 0–100. |

## Scoring separation summary

- **MAIN inputs/sources:** season PA/HR; lineup spot/confirmation; batter side; pitcher identity/hand; H2H; raw Statcast barrel, EV, xSLG, hard-hit, sweet-spot, FB, and pull; pitcher contact data and season pitching counts. MAIN output is `model_prob`; `hrprob`, `tier`, and MAIN `model_tier_rank` are derived outputs.
- **JIG inputs:** season PA/HR; `xslg`, `xiso`, `barrel_pct`, `pull_air_pct`, `hard_hit`, `sweet_spot_pct`; pitcher arsenal and batter/pitcher pitch-type data. JIG ordering is `jigScore`, never MAIN tier or TM.
- **TM inputs:** `model_prob`, Arsenal Edge score/confidence, `pitcher_hr9`, and pitcher barrel allowed. TM is display-only and is never fed back.
- **Display/role only:** HR/FB, AVG/SLG/OBP/BABIP, xwOBA, LA, directional residuals, bat tracking, pitcher summary aliases, projections, role flags, and market/link/context fields. Some share upstream raw data with scoring, but the emitted aliases are not read back into MAIN/JIG.
- **Dead/no source:** `woba`, `whiff`, `swstr`, `pullbrl`.

## Audit boundary

This reference documents current reality. It does not ratify ambiguous labels, does not define future formulas, and does not authorize Phase 2 implementation. Protected systems touched: **no**.
