# MLB HR Engine v4 — Comprehensive Pre-Implementation Audit
## AUDIT-001 · 2026-05-25

**Branch:** `stabilization-rerender-pass`
**Auditor:** Claude Code (read-only mode)
**Engine version under audit:** `mlb_hr_engine_v4`
**Scope:** Working tree state + per-surface feasibility for 5 design-locked surfaces + master implementation plan

---

## Executive Summary

| Domain | Finding |
|---|---|
| Working tree | 2 modified runtime files (`app.py`, `pipeline.py`) contain in-flight Full Slate table work — uncommitted but coherent. `.claude/skills/` deletion is an intentional skills cleanup. Untracked files are validation artifacts + screenshots + an audit doc. |
| Doctrine compliance | Modified `pipeline.py` introduces a `matchup_quality` tier function. Verified MAIN-only (no JIG/HVY logic) per doctrine. |
| Surface feasibility | All 5 design-locked surfaces are implementable. None are blocked. 2 are LOW-risk (Pitch Mix Analysis, Batter Card — modal architecture already exists). 3 are MEDIUM (Full Slate Matrix, MAIN Command Center, JIG Builder). |
| Critical dependency | Full Slate Matrix is on the critical path. Pitch Mix and Batter Card modals are children of it. Both Command Center and JIG Builder share filter and table infrastructure. |
| Recommended starting point | Land or revert the in-flight Full Slate table work first (it touches the critical-path surface). Then implement in this order: Full Slate Matrix → Batter Card → Pitch Mix Analysis → MAIN Command Center → JIG Builder. |
| Total effort estimate | ~10 audit/execution packet pairs, ~12-16 focused implementation sessions. |

**Operator decision pending:** disposition of the in-flight working-tree changes (commit / revert / partial commit). All forward implementation work assumes this is resolved first.

---

## PART 1 — Working Tree State

### 1.1 Modified files

#### `mlb_hr_engine_v4/app.py`  ·  +254 / -167 (≈421 lines touched)

**What changed (plain English):**
1. **Margin tightening** in shell scaffold renderers — `_render_navigation_breadcrumbs`, `_render_recovery_prompt_shell`, `_render_command_strip`, `_render_live_feed_shell` — bottom margin reduced from `12px`/`10px` to `6-8px`. Pure visual density change.
2. **New shell component `_render_deployment_readiness_strip`** (line ~1048, ~33 lines). Shows EMPTY/ARMED state pill in upper tactical shell based on `st.session_state["fd_slip"]` length. Read-only on session_state.
3. **Intelligence card stat-pill restyling** in `_intelligence_card_html` (~line 2900) — minor padding adjustments (`min-width:0`, `white-space:nowrap`, `text-overflow:ellipsis`), font-size 13→12px for MDL/EV/EDGE, identical color tokens. No data path change.
4. **NEW heatmap helpers** (line 4493 onward): `_heatmap_color_for_metric`, `_format_for_table`, `_mq_color`. Pure pure-Python utility functions that take values and league averages and return colors/formatted strings.
5. **`_render_full_slate_all_players` rewritten** (lines ~4961-5040) — replaces the previous flex-row tactical card layout with a 20-column HTML `<table>`. New columns include `PA`, `AVG`, `SLG`, `BABIP`, `GB%`, `HH%`, `LD%`, `BRL%`, `EV`, `LA°`, `PULL%`, `CTR%`, `OPP HR/9`, `xwOBA`, `HR/PA`. Includes inline heatmap colors for `BRL%` and `OPP HR/9` cells.
6. **Lens tabs simplified** in `tab_picks` (~line 6700) — removes 3 lens views (`power_profile`, `matchup_edge`, `deployment_edge`) and keeps only `full_slate` and `portfolio`. Adds guard that coerces unknown lens keys back to `full_slate`.
7. **JIG tab stat pill restyling** (~line 7732) — same kind of padding/font tweaks as item 3, applied to the JIG side of intelligence cards.
8. **Banner wrapper** (~line 10703) — wraps `st.image(banner)` in a 60px-max-height div to clip overflow.
9. **Calls `_render_deployment_readiness_strip(_shell_ctx)`** from the main shell render path (line 10729).

**Risk class:** MEDIUM
**Closed surfaces touched:**
- Routing — NO (active_route logic unchanged)
- session_state — READ-ONLY for new `_render_deployment_readiness_strip` (reads `fd_slip`)
- Cache — NO
- Streamlit UI scaffolding — YES (shell margins + banner wrapper). Per `PHASE3_REFINEMENT_DOCTRINE.md`, these are CLOSED surfaces.
- Modals — NO

**Recommendation:** **Needs review.** The Full Slate table redesign (item 5) is substantial and aligns with `DESIGN_FULL_SLATE_MATRIX.md` (the new table delivers columns 4-18 of the spec). However, two concerns:
- (a) Item 6 removes 3 lens views without a corresponding doctrine update. If those views were operational tools the operator was relying on, this is a behavior change rather than a refinement.
- (b) Items 1, 8, and parts of 2 touch shell scaffolding — `PHASE3_REFINEMENT_DOCTRINE.md` flags those as CLOSED surfaces requiring explicit authorization.

If operator authorized these in a prior session, this is safe to land. If not, a granular commit splitting "Full Slate table" from "shell margin tweaks" from "lens removal" would respect doctrine boundaries.

#### `mlb_hr_engine_v4/pipeline.py`  ·  +89 / +0 (additive only)

**What changed (plain English):**
1. **NEW function `_matchup_quality_tier`** (line 27-79). Pure function: takes `model_prob`, `barrel_pct`, `exit_velo`, `pitcher_hr9`, `park_factor` and returns one of `{ELITE, STRONG, AVG, WEAK, DANGER}`. Logic is deterministic and MAIN-side only (explicit docstring comment: "No JIG/HVY logic").
2. **`_build_player_profile` additions** — appends 5 new fields to the per-player dict that gets returned to the rest of the pipeline:
   - `batting_avg` (season hits / season at-bats)
   - `babip` (standard formula)
   - `xwoba` (raw passthrough from Statcast)
   - `center_pct` (derived as `1.0 - pull_pct - oppo_pct`, clamped to 0)
   - `matchup_quality` (result of `_matchup_quality_tier`)

**Risk class:** LOW
**Closed surfaces touched:** NO.

**Doctrine check (DOCTRINE_RANKING_RULE.md):**
- Does `_matchup_quality_tier` take market data as input? — NO ✓
- Does it reference EV/Edge/odds? — NO ✓
- Is it computed from model output only? — YES ✓
- Does it modify `model_prob`? — NO (`model_prob` is computed before the tier is assigned) ✓

Compliant with doctrine. This is exactly the kind of helper the design specs assume exists.

**Recommendation:** **Safe to commit.** This is foundational data infrastructure required by the Full Slate Matrix design spec (Matchup quality column #3) and the JIG Builder target table (Matchup Quality column).

#### `.claude/settings.local.json`  ·  +6 / -0

Adds permission allow-list entries: `git restore *`, `git add *`, `git commit *`, `awk '{print $1}'`, a specific `git diff --stat CLAUDE.md` invocation, and `bash`. The `bash` entry is broad (effectively allows arbitrary bash entry into the shell).

**Risk class:** LOW (tooling permissions only, no runtime code)
**Recommendation:** **Operator decision.** The blanket `Bash(bash)` permission widens shell access; if intentional, leave it; if reflexive, narrow it.

### 1.2 Deleted `.claude/skills/` files

22 deleted files across 7 skill directories (`caveman`, `cavecrew`, `caveman-commit`, `caveman-compress`, `caveman-help`, `caveman-review`, `caveman-stats`).

**Pattern:** Whole-skill removal — each deleted skill removes both its `README.md` / `SKILL.md` pair (plus the compression skill's full `scripts/` tree). This looks like an intentional cleanup of an old skills cohort, not partial deletion or accidental loss.

**Recommendation:** **Safe to commit as a batched skills cleanup commit.** Unrelated to runtime code; can be committed independently of the v4 changes.

### 1.3 Untracked files

| Path | Category | Recommendation |
|---|---|---|
| `FIX4_VALIDATION_REPORT.md` | Audit/validation doc (matches the `FIX*_VALIDATION_REPORT.md` pattern referenced in `CLAUDE.md` § 12) | Leave alone or commit as frozen artifact alongside others in repo root |
| `validate_app.py`, `validate_app_simple.py`, `validate_fix1.py` | Ad-hoc validation scripts | If still in active use → add to `mlb_hr_engine_v4/scripts/analysis/` and commit; if one-shot → delete or gitignore |
| `validation_results.json` | Validation output | gitignore (output artifact) |
| `vault_architecture_audit.md` | Folder snapshot (matches `CLAUDE.md` § 12 reference) | Commit or gitignore depending on whether it's expected to stay frozen |
| `draw_flag_duo/` | Unknown — directory not inspected per read-only mandate | Operator should triage |
| `mlb_hr_engine_v4/screenshot_01_default_load.png`, `..._05_scrolled.png`, `..._06_full_page.png` | Test/debug screenshots | gitignore PNGs at this path, OR move to a deliberate `_debug/` dir |
| `mlb_hr_engine_v4/screenshots/`, `screenshots2/`, `screenshots3/` | Screenshot collections | gitignore — these will accumulate noise; add `mlb_hr_engine_v4/screenshot*` and `mlb_hr_engine_v4/screenshots*/` to `.gitignore` |

**Pattern observation:** screenshots, validation scripts, and validation JSON are the kind of dev-time artifacts that should be `.gitignore`d project-wide.

---

## PART 2 — Per-Surface Implementation Feasibility

For each of the 5 design-locked surfaces, this section captures: where it would render, what data it needs, what config thresholds it touches, what new code is required, risk class, closed surfaces touched, and external dependencies.

---

### 2.1 Full Slate Matrix

**Spec:** `mlb_hr_engine_v4/_design/DESIGN_FULL_SLATE_MATRIX.md` (177 lines)
**Risk per spec:** MEDIUM
**Status:** Partial implementation already in working tree (see Part 1 item 5 above).

#### Where it renders

- `mlb_hr_engine_v4/app.py` function `_render_full_slate_all_players` (~line 4547-5040)
- Invoked from `tab_picks` when active lens is `full_slate` (~line 6770)
- Active when `active_route == "MAIN"` and a MAIN sub-room of "Full Slate" is selected

#### Data needs vs current pipeline output

| Spec column | Pipeline field today | Status |
|---|---|---|
| Tier icon (model tier) | `model_prob` | ✓ available |
| Player | `player_name`, `team` | ✓ available |
| Matchup quality | `matchup_quality` | ✓ NEW — in-flight in `pipeline.py` diff |
| PA | `season_pa` | ✓ available |
| AVG | `batting_avg` | ✓ NEW — in-flight in `pipeline.py` diff |
| SLG | `actual_slg` | ✓ available |
| BABIP | `babip` | ✓ NEW — in-flight in `pipeline.py` diff |
| GB% | `gb_pct` | ✓ available |
| HH% | `hard_hit` | ✓ available |
| LD% | `ld_pct` | ✓ available |
| Barrel% | `barrel_pct` | ✓ available |
| EV | `exit_velo` | ✓ available |
| LA degrees | `avg_launch_angle` | ✓ available |
| Pull% | `pull_pct` | ✓ available |
| Cent% | `center_pct` | ✓ NEW — in-flight in `pipeline.py` diff |
| Opp HR/9 | `pitcher_hr9` | ✓ available |
| xwOBA | `xwoba` | ✓ NEW — in-flight in `pipeline.py` diff |
| HR/PA | derived (`season_hr / season_pa`) | ✓ derivable inline |
| FanDuel (display-only) | `best_american` + url builder | ✓ via `_fanduel_url()` |

**All data needs satisfied** assuming the in-flight `pipeline.py` changes land.

#### Config thresholds consumed

Tier thresholds for the 5 visual tiers (Critical / Dangerous / Strong / Active / Quiet) per spec § Tier system. Currently the in-flight `_matchup_quality_tier` uses ad-hoc thresholds (0.15, 0.10, 0.05, 2.2 HR/9) hard-coded in `pipeline.py`. Spec says: "Exact thresholds live in config.py and are the single source of truth."

**Implementation gap:** Either move the 5 numeric tier thresholds into `config.py` (new constants like `MQ_ELITE_PROB`, `MQ_STRONG_PROB`, etc.) and reference them from `pipeline.py`, OR document why they live where they live. Doctrine ("config.py is single source of truth for thresholds") says they should live in config.

Heatmap percentile cutoffs per metric also belong in config (per spec § Color heatmap). Currently the inline `BRL%` and `OPP HR/9` thresholds in the new table renderer are hard-coded values (0.08, 0.05 / 1.8, 2.2). Same recommendation.

#### New code estimate

- Header section per game (park, time, weather pill, env tier badge): ~80 lines, additive to `_render_full_slate_all_players`
- Game-view vs Player-view toggle (spec § View modes): ~40 lines + session_state key (`fs_view_mode`)
- 5-tier icon column with click → opens FanDuel: ~30 lines (extends current row HTML)
- Heatmap classification helper (already partially exists as `_heatmap_color_for_metric` and `_mq_color` in the diff): another ~80 lines to wire per-metric percentile lookups
- Tooltip layer (every column header + every cell): ~120 lines (Streamlit's `help=` doesn't apply to raw HTML tables — needs `<span title="...">` overlays or shift to a Streamlit `st.dataframe` with custom Styler)
- Drag-to-reorder columns (spec § Drag-to-reorder, HIGH risk per spec): ~150 lines + session_state ownership for column order. Cannot be done with raw HTML markdown — requires either `streamlit.components.v1` for a custom component, or a Streamlit-native widget approach. **DEFER to v2.**

**Estimated new code for v1 (no drag-reorder, no per-cell tooltips):** ~250 lines additive to current diff.

#### Risk class

**MEDIUM** for v1 (drop drag-reorder, drop hover tooltips on every cell). Aligns with spec.
**HIGH** if drag-to-reorder columns is in scope (touches session_state ownership which is closed per `PHASE3_REFINEMENT_DOCTRINE.md`).

#### Closed surfaces touched

- Routing — NO
- session_state — only if drag-reorder is included (then YES, HIGH risk)
- Cache — NO (heatmap calc is per-render, no caching required for 50-300 rows)
- Modals — only via outbound links (Batter Card, Pitch Mix) — depends on those surfaces existing

#### External dependencies

None beyond current imports. The existing renderer uses only Streamlit + Python stdlib + html escaping.

#### Specific blockers

1. **In-flight diff resolution** — the current `_render_full_slate_all_players` rewrite needs to land or revert before further iteration.
2. **Tier thresholds need to move to `config.py`** per doctrine (operator authorization needed since `config.py` is single-source-of-truth and currently doesn't have these constants).
3. **Game header section is not yet implemented** — current renderer just outputs the table; the spec requires per-game park/time/weather/env header above each table.

#### Effort estimate

**2 packets** (1 audit + 1 execution) for v1 (table + game headers + view toggle, no drag-reorder, no per-cell tooltips). Drag-reorder is a separate future packet.

---

### 2.2 Pitch Mix Analysis modal

**Spec:** `mlb_hr_engine_v4/_design/DESIGN_PITCH_MIX_ANALYSIS.md` (141 lines)
**Risk per spec:** MEDIUM
**Status:** Substantial existing implementation as `_render_pitch_mix_expander` (~line 3916, ~528 lines). Modal infrastructure (`@st.dialog`) already exists.

#### Where it renders

Current: rendered as a `st.expander` inside player detail surfaces.
Target per spec: rendered as a modal overlay opened from Full Slate Matrix row → matchup quality pie click.

#### Data needs vs current pipeline output

The existing implementation already pulls:
- `pitch_mix.arsenal` (pitcher arsenal with usage %, velo, k%, whiff%)
- `pitch_mix.hand_splits` (per-pitch handedness splits)
- `pitch_mix.h2h` (batter vs this pitcher historical)
- `pitch_mix.batter_rows` (per-pitch batter stats: xwOBA, barrel%, whiff%)
- `hvy_modifier` (display-only JIG signal)
- `pitcher_arsenal`, `pitcher_hand`, `batter_side`

All data needs from the spec are already available.

#### Config thresholds consumed

- `ARSENAL_LEAGUE_AVG_WHIFF` (24.5%) — used in current implementation
- `ARSENAL_RV_SCALE` (40.0)
- HVY display threshold (not yet a constant in `config.py` per the read — would need to be added if spec § Section 4 confidence threshold is enforced)

#### New code estimate

The bulk of the work is **adapting the existing `_render_pitch_mix_expander` body to render inside a `@st.dialog` instead of `st.expander`**:

- New modal wrapper function `_show_pitch_mix_modal(player, ctx)` decorated with `@st.dialog("📊 Pitch Mix Analysis", width="large")`: ~30 lines
- HVY display panel with the explicit "display only · does NOT modify MAIN" badge: ~25 lines (spec § Section 4 — explicit doctrine requirement)
- Pitcher arsenal donut chart (currently the existing impl shows a table; spec wants a donut): ~80 lines — likely uses `plotly` or `altair`. **External dependency check needed.**
- Final tactical verdict bar with DEPLOY/WATCHLIST/HOLD/SCRATCH (not in current expander): ~50 lines
- "Open Batter Card" cross-modal navigation button: ~20 lines (depends on Batter Card modal existing)
- Modal-trigger from Full Slate Matrix row click: ~30 lines (mirrors `_open_player_modal` pattern at line 3447)

**Total new code:** ~235 lines (mostly composition, since most of the data lookup logic already exists).

#### Risk class

**MEDIUM**. The verdicts:
- Modal architecture exists (`@st.dialog` already used at line 3218 for player details)
- Cross-modal navigation (Pitch Mix → Batter Card) is HIGH per spec, because Streamlit dialogs cannot be open simultaneously — switching means closing one + opening another via session_state. Manageable but touches modal state ownership.
- HVY display-only enforcement is doctrine-bound — adding the explicit visible badge is a tractable UI change.

#### Closed surfaces touched

- Modals — YES (closed surface per `CLAUDE.md`). Per spec § Implementation risks: "Modal rendering (modal architecture is a closed surface)".
- session_state — YES, for modal state (`show_modal`, `selected_player_modal`)
- Routing — NO

**Operator authorization required** because this touches modal architecture.

#### External dependencies

Possible new lib for donut chart:
- **plotly** — not currently imported
- **altair** — partial Streamlit support but currently not imported
- Alternative: pure HTML/CSS conic-gradient donut — no new deps, more code (~100 lines for chart + tooltips). **Recommended path** to avoid adding a dependency.

#### Specific blockers

1. **Cross-modal navigation pattern** must be approved by operator (touches modal state ownership)
2. **Donut chart approach** — pick: plotly add OR pure CSS conic-gradient
3. **Click-handler from Full Slate row** — needs a Streamlit-button-keyed cell pattern (HTML markdown links can't trigger Python callbacks)

#### Effort estimate

**2 packets** (1 audit, 1 execution) — most data wiring already exists; the work is layout, the doctrine badge, and modal wiring.

---

### 2.3 Batter Card modal

**Spec:** `mlb_hr_engine_v4/_design/DESIGN_BATTER_CARD.md` (177 lines)
**Risk per spec:** MEDIUM (HIGH if layout persistence added)
**Status:** Existing `_show_player_modal` (line 3218) provides a player detail dialog but does not match the 12-module grid layout in the spec.

#### Where it renders

Target: modal overlay opened from Full Slate Matrix row → player name click.
Existing entry point: `_open_player_modal()` at line 3447 (mature pattern, called from 17+ sites in `app.py`).

#### Data needs vs current pipeline output

All 12 modules consume fields that are already in the pipeline output:

| Module | Fields |
|---|---|
| HR Threat | `model_prob`, threat-tier mapping |
| HR Projection | `model_prob`, trend (needs `model_prob_trend` — possibly new) |
| Statcast Metrics (16-tile sub-grid) | `barrel_pct`, `exit_velo`, `avg_launch_angle`, `sweet_spot_pct`, `pull_air_pct`, `xslg`, `iso`, `xwoba` and others — all available |
| xSLG Splits | `xslg_vs_rhp`, `xslg_vs_lhp` (may need to verify) |
| Pull Power | `pull_pct`, `center_pct` (new in diff), `oppo_pct` |
| Pitch Type Destruction | `pitch_mix.batter_rows` (JIG-flagged) |
| Barrel Quality | requires barrel breakdown (perfect/solid/total) — may need pipeline enhancement |
| Contact Quality | requires squared-up % — may need pipeline enhancement (Statcast `squared_up_rate`) |
| Plate Discipline | `z_swing_pct`, `bb_rate`, `zone_contact_pct` — verify availability |
| HR Environment tonight | `park_factor`, `weather_factor`, `temp_f`, `wind_mph`, `humidity`, `air_density` |
| Power vs RHP/LHP last 20 games | Recent split data — may need pipeline enhancement (recent N-game splits) |
| Up Next opposing pitcher | `pitcher_name`, `pitcher_hr9`, `pitcher_barrel_pct_allowed`, `pitcher_xwoba_allowed` — verify |

**Gap analysis:** Several modules ("Barrel Quality", "Contact Quality", "Power vs RHP/LHP last 20", "Up Next pitcher quick stats") may need new pipeline fields. A subordinate audit on `pipeline.py` line-by-line is warranted before commencing implementation.

#### Config thresholds consumed

- 5-tier mapping for HR Threat module (same as Full Slate Matrix tier thresholds → reinforces the need to move tier cutoffs to `config.py`)
- HR Environment tier classifier (0-10 score) — likely needs new constants

#### New code estimate

- Module renderer functions (12 modules @ ~40-80 lines each): ~720 lines
- Identity strip (fixed top): ~60 lines
- System status footer (fixed bottom): ~60 lines
- Modal wrapper `_show_batter_card_modal(player)` with `@st.dialog`: ~30 lines
- Trigger wiring from Full Slate Matrix row click: ~30 lines
- Drag-to-reorder modules (v1 may defer): ~150 lines if included
- "Up Next pitcher card click → Pitch Mix modal" cross-modal nav: ~40 lines (depends on Pitch Mix modal landing first)

**Total new code (without drag-reorder):** ~950 lines. With drag-reorder: ~1100 lines.

#### Risk class

**MEDIUM** for v1 without drag-reorder. **HIGH** if drag-reorder included (touches session_state ownership).

#### Closed surfaces touched

- Modals — YES
- session_state — only if drag-reorder enabled
- Routing — NO

#### External dependencies

- Trend chart (Module 11: Power vs RHP/LHP last 20 games, 20-bar chart) — could be done with `st.bar_chart`, `st.altair_chart`, or pure HTML bars. Pure HTML is simplest.
- Otherwise no new deps.

#### Specific blockers

1. **12 modules is a large surface area** — would benefit from splitting into 2-3 implementation packets (e.g., "modules 1-4", "modules 5-8", "modules 9-12") to keep diffs reviewable
2. **Pipeline fields gap** — confirm Module 7 (Barrel Quality breakdown), Module 8 (Contact Quality / squared-up), and Module 11 (Power vs RHP/LHP recent 20G) data is in pipeline today
3. **Cross-modal navigation** to Pitch Mix modal depends on Pitch Mix modal landing first

#### Effort estimate

**3 packets** (1 audit, 2 execution sessions) for v1 without drag-reorder. Drag-reorder is a deferred separate packet.

---

### 2.4 MAIN Command Center

**Spec:** `mlb_hr_engine_v4/_design/DESIGN_MAIN_COMMAND_CENTER.md` (191 lines)
**Risk per spec:** MEDIUM (HIGH for preset persistence)
**Status:** Substantial existing infrastructure — `filter_controls.py` with `MAIN_PRESETS`, `JIG_PRESETS`, `render_filter_control`, `render_preset_bar` (198 lines). Tactical sections currently rendered in `tab_picks` (`MAIN`) and `tab_jig` (`JIG`).

#### Where it renders

Current location: filters are spread across `tab_picks` and `tab_jig` ad-hoc.
Target per spec: dedicated MAIN Command Center surface, sub-room of MAIN, also serves as TCC pull-out overlay.

The existing `_MAIN_TCC_SECTION_KEYS` / `_MAIN_TCC_SECTION_LABELS` / `_MAIN_TCC_SECTION_ORDER` (lines 1909-1929) already define section keys for collapsible TCC sections — partial scaffolding for what the spec describes.

#### Data needs

Filter scope. No new pipeline fields needed. Filter values feed into `_apply_ui_filters` (line 3626) and `_apply_tactical_filters` (line 3673), which already exist.

#### Config thresholds consumed

All filter defaults map to `config.py` constants:
- `MIN_QUAL_PROB` (0.08)
- `MIN_EV_PCT` (3.0)
- `MIN_EDGE_PCT` (2.0)
- `MIN_PA_THRESHOLD` (3.3)
- `MAX_PARK_PENALTY` (0.87)
- `MAX_WEATHER_PENALTY` (0.88)
- `MAX_PITCHER_SUPPRESSOR` (0.75)
- League averages (`LEAGUE_AVG_*`) for relative threshold pills

The spec § Filter input types maps clearly to the existing `render_filter_control` interface.

#### New code estimate

- 9 section card components: ~9 × 60 = ~540 lines
- Filter section render layout (auto-fit grid with `minmax(360px, 1fr)`): ~60 lines
- Top brand bar with status strip: ~80 lines
- Preset bar (Save/Load/Reset/active count) — partially exists, needs UI extension: ~80 lines
- Bottom visibility toolbar (Hide / Link Tier / Compact / Expanded / Presets / Save Density): ~120 lines
- Footer status indicators: ~50 lines
- Drag-to-reorder sections (HIGH per spec): ~180 lines — **defer to v2**
- Drag-to-reorder filters within sections + cross-section (HIGH): ~250 lines — **defer to v2**
- Preset Save/Load persistence (HIGH): ~80 lines (touches session_state)

**Total for v1 (no drag, no preset save persistence):** ~930 lines, additive.
**Total for v2 (with drag + preset save):** ~1440 lines.

#### Risk class

**MEDIUM** for v1 (static layout, existing filter primitives).
**HIGH** for drag-reorder and preset persistence.

#### Closed surfaces touched

- Routing — partially YES (MAIN Command Center is a sub-room of MAIN; routing scaffold exists via `_MAIN_SUB_ROOM_MAP`)
- session_state — only for v2 features (preset persistence, hide-sections persistence, drag-reorder)
- Cache — NO
- Modals — NO

#### External dependencies

None — all primitives already in `filter_controls.py`.

#### Specific blockers

1. **Spec § Section 6 includes 2 JIG-domain filters** (Contact Shape Score, Arsenal Matchup Score). Per spec: "Both tooltips explicitly note 'Display only · does NOT modify MAIN'". Implementation must explicitly badge these as JIG-domain even on the MAIN surface.
2. **Drag-reorder is significant complexity** — recommend explicit operator decision to ship v1 without it.
3. **"Link Tier Mode"** (visibility toolbar button) is described as cross-surface link to Full Slate Matrix tier scope — requires both surfaces to exist and a shared session_state contract. HIGH risk per spec.

#### Effort estimate

**3 packets** (1 audit, 2 execution) for v1 (static 9-section layout, no drag, no preset save).

---

### 2.5 JIG Builder All-In-One

**Spec:** `mlb_hr_engine_v4/_design/DESIGN_JIG_BUILDER.md` (191 lines)
**Risk per spec:** MEDIUM (HIGH for JIG grade computation and preset persistence)
**Status:** Existing `tab_jig` (line 7547) has sub-room scaffolding (`_JIG_SUB_ROOM_MAP` with "JIG Builder" key). Filter primitives shared with MAIN via `filter_controls.JIG_PRESETS`.

#### Where it renders

Sub-room `command_center` inside JIG room. Current code already routes `"JIG Builder"` → `"command_center"` (line 8074).

#### Data needs

The Zone 2 target table needs:
- All MAIN fields (model probability, Statcast)
- JIG fields: `arsenal_score`, `hvy_modifier`, `contact_shape_score`, JIG grade (NEW)
- The columns specified are largely overlapping with Full Slate Matrix (good — table renderer can be shared).

**Critical new field: JIG GRADE.** Spec § JIG GRADE column says it's derived from:
- Model HR probability (MAIN signal, weighted in)
- JIG arsenal exploit signal
- HVY pitch-mix signal
- Recency / momentum factors
- Environment + matchup composite

Per spec: "JIG grade computation is HIGH risk for implementation because it requires a JIG scoring formula that must NOT blend into MAIN model probability. The formula lives in JIG-domain code; output is JIG-domain only."

This means a new file/module like `engine/jig_grade.py` is justified, with explicit input/output contracts. The grade is a derived display column on JIG surfaces only; it must never affect MAIN ranking or be added to a MAIN-side dict.

#### Config thresholds consumed

All MAIN filter thresholds plus new JIG GRADE cutoffs (e.g., A+ = composite ≥ X, A = ≥ Y …). These must be new `config.py` constants: `JIG_GRADE_APLUS_CUTOFF`, etc.

#### New code estimate

- Zone 1 (filter command, 9 sections — JIG version): mirrors MAIN Command Center, ~830 lines (most logic shared via `filter_controls.py` primitives, but separate render). Could be ~50% smaller if Zone 1 uses a shared `_render_command_panel(side="JIG")` factory.
- Zone 2 (player target table): mirrors Full Slate Matrix table — could share `_render_command_table()` factory with Full Slate. ~150 additional lines on top of existing table renderer for the JIG-specific columns (Rank with click-to-FanDuel, GRADE pill).
- JIG GRADE module — new file `engine/jig_grade.py`: ~120 lines with composite formula, weights stored in `config.py`. Includes explicit docstring forbidding use on MAIN surfaces.
- Workflow zone labels banner: ~30 lines
- Cross-surface modal triggers (Pitch Mix, Batter Card): ~40 lines
- Drag-reorder + preset persistence: deferred to v2 (~430 lines combined)

**Total for v1 (static layout, JIG GRADE included, no drag, no preset save):** ~1170 lines, much of it duplication-with-MAIN-Command-Center.

#### Risk class

**HIGH** specifically for JIG GRADE composition. The composite must:
1. Read MAIN model probability (allowed — read access)
2. Read JIG arsenal exploit / HVY signal / recency factors
3. Combine into a grade
4. Output only on JIG surfaces
5. NEVER be passed back to MAIN ranking
6. Be reviewable by AGENTS.md's verification questions for MAIN/JIG separation

Failure mode if done wrong: composite leaks into a shared dict that MAIN surfaces consume, contaminating MAIN tier display with JIG signal. Code reviewer must verify this.

**MEDIUM** for Zone 1 (filter command — shared logic).
**MEDIUM** for Zone 2 (target table — shared with Full Slate).

#### Closed surfaces touched

- Routing — YES (sub-room routing for JIG Builder already exists, just needs new sub-room renderer)
- session_state — partial (Zone 1 filter values map to existing `tac_*` keys)
- Modals — YES (cross-surface triggers depend on Pitch Mix + Batter Card modals)
- Cache — NO

#### External dependencies

None.

#### Specific blockers

1. **JIG GRADE formula must be authored from scratch and reviewed for MAIN/JIG separation**. Operator authorization to define the composite weights is required (probably stored as `JIG_GRADE_WEIGHTS` dict in `config.py`).
2. **All MAIN Command Center work must come first** if the two filter command panels are to share a `_render_command_panel(side=)` factory. Otherwise the JIG Builder duplicates the MAIN logic.
3. **Pitch Mix + Batter Card modals must be implemented first** for cross-surface navigation to work.

#### Effort estimate

**3 packets** (1 audit, 2 execution sessions) for v1.

---

## PART 3 — Master Implementation Plan

### 3.1 Dependency order

```
                    [In-flight changes resolved (operator decision)]
                                       |
                                       v
              ┌─────────────────────────────────────────────┐
              │   Full Slate Matrix (the critical-path surface)   │
              │   — establishes table renderer + tier system │
              │   — adds tier thresholds to config.py        │
              └─────────────┬───────────────────────┬───────┘
                            |                       |
                            v                       v
              ┌─────────────────────┐   ┌─────────────────────┐
              │   Batter Card        │   │   Pitch Mix Analysis │
              │   (modal child)      │   │   (modal child)      │
              └─────────┬───────────┘   └────────┬─────────────┘
                        │                        │
                        └────────────┬───────────┘
                                     |
                              (cross-modal nav becomes possible)
                                     |
                                     v
              ┌──────────────────────────────────────────┐
              │   MAIN Command Center                      │
              │   (filter command panel, sub-room of MAIN)│
              └──────────────────────┬───────────────────┘
                                     |
                              (shared filter factory primitives)
                                     |
                                     v
              ┌──────────────────────────────────────────┐
              │   JIG Builder All-In-One                  │
              │   (Zone 1 shares with Command Center;    │
              │    Zone 2 shares with Full Slate Matrix; │
              │    new JIG GRADE module)                 │
              └──────────────────────────────────────────┘
```

**Surfaces that can be done in parallel:** Batter Card and Pitch Mix Analysis (after Full Slate lands) — they share no code.
**Surfaces that gate everything else:** Full Slate Matrix establishes the table renderer + tier system.
**Surface that depends on all others:** JIG Builder needs Pitch Mix + Batter Card for cross-modal nav, and benefits from MAIN Command Center for the filter command pattern.

### 3.2 Phased rollout (recommended sequence)

**PHASE 0 — Resolve working tree** (immediate)
- Operator decision on in-flight `app.py` + `pipeline.py` changes
- Skills cleanup commit
- Decide on screenshots / validation artifacts (gitignore vs commit)
- **Risk:** N/A (operator decision, not a code change)
- **Estimated session count:** 1 review session
- **Blocks:** ALL forward work

**PHASE 1 — Full Slate Matrix completion** (foundational)
- Audit packet: AUDIT-002
- Execution packet: EXEC-002
- Scope: complete the table per spec § Layout (game headers + view toggle + tier icon column + heatmap layer); move tier thresholds to `config.py`
- **Risk:** MEDIUM (no drag-reorder in v1)
- **Estimated session count:** 2 sessions
- **Blocks:** Batter Card (needs trigger), Pitch Mix (needs trigger), JIG Builder Zone 2 (shares table renderer)
- **Operator authorization gate:** confirm tier threshold values to add to `config.py`

**PHASE 2 — Batter Card modal v1** (child surface)
- Audit packet: AUDIT-003
- Execution packets: EXEC-003a (modules 1-6), EXEC-003b (modules 7-12 + identity strip + footer)
- Scope: 12-module grid, no drag-reorder, no layout persistence
- **Risk:** MEDIUM (touches modal architecture — closed surface, operator authorization required)
- **Estimated session count:** 3 sessions
- **Blocks:** JIG Builder cross-modal nav to Batter Card
- **Operator authorization gate:** modal architecture change (Streamlit `@st.dialog`); confirm Module 7/8/11 pipeline field availability via subordinate `pipeline.py` audit

**PHASE 3 — Pitch Mix Analysis modal v1** (sibling child surface, can parallel Phase 2)
- Audit packet: AUDIT-004
- Execution packet: EXEC-004
- Scope: convert existing `_render_pitch_mix_expander` into a `@st.dialog`, add explicit HVY display-only badge per doctrine, add tactical verdict bar, add donut chart (pure CSS conic-gradient — no new deps)
- **Risk:** MEDIUM (touches modal architecture)
- **Estimated session count:** 2 sessions
- **Blocks:** JIG Builder cross-modal nav to Pitch Mix
- **Operator authorization gate:** modal architecture change; donut chart approach (recommend CSS, not plotly)

**PHASE 4 — MAIN Command Center v1** (filter panel surface)
- Audit packet: AUDIT-005
- Execution packets: EXEC-005a (sections 1-5), EXEC-005b (sections 6-9 + toolbar + footer)
- Scope: static 9-section grid layout; no drag-reorder, no preset save persistence
- **Risk:** MEDIUM
- **Estimated session count:** 3 sessions
- **Blocks:** None hard-block; JIG Builder Zone 1 can benefit from shared factory
- **Operator authorization gate:** confirm section 6 JIG-domain filter labeling treatment

**PHASE 5 — JIG Builder All-In-One v1** (composite surface)
- Audit packet: AUDIT-006 (includes a dedicated JIG GRADE doctrine-compliance audit)
- Execution packets: EXEC-006a (JIG GRADE module + tests), EXEC-006b (Zone 1 filter command), EXEC-006c (Zone 2 target table + workflow banner)
- **Risk:** HIGH (specifically for JIG GRADE composition — doctrine-sensitive)
- **Estimated session count:** 4 sessions
- **Blocks:** None remaining
- **Operator authorization gate:** JIG GRADE composite formula (input fields, weights, output gating); explicit code-review pass on MAIN/JIG separation per AGENTS.md verification questions

**PHASE 6 (deferred future) — v2 enhancements**
- Drag-to-reorder columns (Full Slate Matrix)
- Drag-to-reorder modules (Batter Card)
- Drag-to-reorder sections + filters (MAIN Command Center + JIG Builder)
- Preset Save/Load persistence
- "Link Tier Mode" cross-surface link
- Per-cell tooltips (every Full Slate cell)
- **Risk:** HIGH (session_state ownership across all surfaces — closed per `PHASE3_REFINEMENT_DOCTRINE.md`)
- **Estimated session count:** ~5-8 sessions (split across surfaces)

### 3.3 Total effort estimate

| Item | Count |
|---|---|
| Audit packets (one per phase) | 5 |
| Execution packets (some phases have multiple) | 10 |
| Total focused-work sessions (Phases 1-5) | ~14 |
| Deferred v2 sessions (Phase 6) | ~5-8 |
| **Grand total** | **~19-22 sessions** |

If operator runs 1 session per day, **Phases 1-5 complete in ~3 weeks**. v2 enhancements (drag-reorder + persistence) add another ~1-2 weeks.

### 3.4 Risks and unknowns

**Questions that can only be answered during implementation:**

1. **Tier threshold values for `config.py`** — the spec says "exact thresholds live in config.py" but does not specify what they should be. Operator must define them (likely from historical model output distribution analysis via `scripts/analysis/analyze_calibration.py`).

2. **Module 7/8/11 pipeline field availability** (Batter Card) — Barrel Quality breakdown, Contact Quality squared-up rate, and Power vs RHP/LHP last 20G recent splits may or may not currently flow through `pipeline.py`. A subordinate audit before Phase 2 is needed.

3. **JIG GRADE composite weights** — spec gives the inputs but not the weights. Operator-defined.

4. **Click-handler patterns for HTML table rows** — Streamlit markdown tables can't trigger Python callbacks. Two options: (a) use Streamlit columns with `st.button` per row (verbose, may rerender slowly for 300 rows), or (b) use `streamlit.components.v1` for a custom component. This may force the table renderer to change shape from raw HTML markdown.

5. **`@st.dialog` simultaneous-modal limitation** — Streamlit doesn't allow two dialogs open at once. Cross-modal navigation (e.g., Batter Card → Pitch Mix) must close the first dialog and open the second on the next rerun. This is a known Streamlit constraint, not a blocker, but the UX needs to be tested.

**What might invalidate this plan:**

- If the in-flight working-tree changes are reverted instead of landed, Phase 1 starts from a different baseline and gains scope.
- If operator authorizes a Next.js migration of any of these surfaces (per CLAUDE.md § 10), Phases 4-5 reshape significantly.
- If the JIG GRADE doctrine compliance review surfaces a contamination risk, Phase 5 may need a re-design.

### 3.5 Recommended next surface to start with and why

**Full Slate Matrix completion (Phase 1).**

Reasons:
1. It is the critical-path surface — every other surface either renders on it (modals), routes from it (Batter Card, Pitch Mix), or shares its table renderer (JIG Builder Zone 2).
2. The in-flight working-tree changes have already started this work — finishing it (rather than reverting) preserves a substantial amount of completed work.
3. It establishes the tier-threshold-in-`config.py` discipline that all other surfaces will reference.
4. It is the lowest-risk MEDIUM in the plan (no closed surfaces if v1 drops drag-reorder).
5. Operator can validate the SCAN → QUALIFY → DEPLOY workflow against a real surface immediately and provide feedback that informs subsequent phases.

---

## Recommendation for Operator

### Immediate (Phase 0)

1. **Decide disposition of in-flight changes:**
   - `pipeline.py` (+89 lines, additive, doctrine-compliant) — recommend **commit as-is** (Phase 1 needs these fields anyway). One small change: extract the 5 tier-threshold numerics from `_matchup_quality_tier` to new `config.py` constants in the same commit.
   - `app.py` (+254/-167) — recommend **review and selective commit**:
     - Shell margin tweaks (items 1, 8) — separate small commit or skip if not authorized
     - `_render_deployment_readiness_strip` (item 2) — small commit; verify operator wanted this
     - Intelligence card stat-pill restyling (items 3, 7) — small commit
     - Full Slate table rewrite (items 4, 5) — commit as the foundation for Phase 1
     - Lens removal (item 6) — separate commit; confirm operator wanted the 3 lenses gone (`power_profile`, `matchup_edge`, `deployment_edge`)
   - `.claude/skills/` deletions — separate cleanup commit
   - Screenshots and validation artifacts — gitignore + delete from working tree

2. **Decide on `.claude/settings.local.json`** — the new `Bash(bash)` allow is broad; narrow it if reflexive.

3. **Confirm tier threshold values** for `MQ_ELITE_PROB`, `MQ_STRONG_PROB`, `MQ_WEAK_PROB`, `MQ_DANGER_HR9` to add to `config.py`.

### Phase 1 kickoff

Once Phase 0 is resolved, queue **AUDIT-002 + EXEC-002 for Full Slate Matrix completion**. Scope: per-game headers, view toggle (game vs player), tier icon column, heatmap percentile classification per metric, no drag-reorder.

### Long-running considerations

- Drag-to-reorder is a v2 theme across 4 surfaces. Decide now if it's in scope at all for this stabilization branch, or if it lives on a separate feature branch.
- JIG GRADE is the highest-risk doctrine surface in the plan. Schedule a dedicated design review session before EXEC-006a.
- Frontend Next.js (`mlb_hr_engine_v4/frontend/`) is currently dormant per CLAUDE.md § 10. None of the 5 surfaces in this audit touch it. If at any point the operator decides to migrate one of these surfaces to Next.js, the plan reshapes — re-audit at that decision point.

---

## Appendices

### Appendix A — Doctrine cross-checks summary

| Surface | MAIN/JIG separation | Market-display-only | Tier from config | No fabricated data |
|---|---|---|---|---|
| Full Slate Matrix | ✓ (MAIN; HVY excluded) | ✓ (FanDuel column display-only) | ✗ thresholds need to move to config.py | ✓ (`--` for missing data per spec) |
| Pitch Mix Analysis | ✓ (HVY badged display-only) | ✓ (FanDuel button only) | N/A | ✓ |
| Batter Card | ✓ (Pitch Type Destruction badged JIG) | ✓ (FanDuel button only) | depends on Full Slate config moves | ✓ |
| MAIN Command Center | ✓ (Sec 6 JIG filters badged) | ✓ (no market filters) | ✓ uses existing config constants | ✓ |
| JIG Builder | △ (JIG GRADE is doctrine-sensitive — needs review) | ✓ (display-only) | ✗ JIG GRADE cutoffs need to go to config.py | ✓ |

### Appendix B — Closed surfaces touched per phase (cumulative)

| Phase | Routing | session_state | Cache | Modals | Streamlit shell |
|---|---|---|---|---|---|
| 0 | — | — | — | — | already-touched (in-flight diff) |
| 1 (Full Slate v1) | — | — | — | — | minor (Full Slate renderer is inside existing tab) |
| 2 (Batter Card v1) | — | minor (`show_modal` etc) | — | YES (closed) | — |
| 3 (Pitch Mix v1) | — | minor (`show_modal` etc) | — | YES (closed) | — |
| 4 (Command Center v1) | minor (sub-room routing exists) | — | — | — | — |
| 5 (JIG Builder v1) | minor (sub-room routing exists) | minor (filter scope) | — | YES (cross-modal triggers) | — |
| 6 (v2 enhancements) | YES | YES (preset persistence + drag state) | — | YES | — |

Phases 1-5 stay within MEDIUM risk envelope per `PHASE3_REFINEMENT_DOCTRINE.md` if drag-reorder + preset persistence are deferred to Phase 6.

### Appendix C — Files that will be touched in this implementation arc

- `mlb_hr_engine_v4/app.py` (all phases — primary surface file)
- `mlb_hr_engine_v4/pipeline.py` (Phases 1, 2 — additive field expansions)
- `mlb_hr_engine_v4/config.py` (Phases 1, 5 — tier threshold + JIG GRADE constants)
- `mlb_hr_engine_v4/filter_controls.py` (Phase 4, 5 — minor preset extensions)
- `mlb_hr_engine_v4/engine/jig_grade.py` (Phase 5 — NEW file)
- `mlb_hr_engine_v4/_design/*.md` (read-only references; not modified)
- `CLAUDE.md`, `AGENTS.md`, `MASTER_TCC_DOCTRINE.md` (read-only references; not modified)

No frontend (`mlb_hr_engine_v4/frontend/`) changes in scope.
No API (`mlb_hr_engine_v4/api/`) changes in scope.
No backtest (`mlb_hr_engine_v4/backtest/`) changes in scope.

---

*End of AUDIT-001 report.*
