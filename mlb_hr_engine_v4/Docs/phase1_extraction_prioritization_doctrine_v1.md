# Phase 1 Extraction Prioritization Doctrine v1
## MLB HR Engine v4 — Staged Modularization Execution Roadmap

**Document Status:** Governance Doctrine — Planning Only  
**Phase:** Division 09 — Step 4/8 Phase 1 Extraction Prioritization  
**Owner:** Claude (Architecture Governance)  
**Date:** 2026-05-23  
**Runtime Systems:** FROZEN — no production changes from this document  
**Preceding Doctrines:**
- `controlled_modularization_doctrine_v1.md` — architecture targets, protected zones, phase map
- `modularization_dependency_audit_doctrine_v1.md` — dependency classification, hidden contracts, audit workflow
- `extraction_execution_governance_doctrine_v1.md` — extraction lifecycle, rollback standards, validation gates

---

## Table of Contents

1. [Purpose of Phase 1 Extraction](#1-purpose-of-phase-1-extraction)
2. [Phase 1 Governance Rules](#2-phase-1-governance-rules)
3. [Extraction Prioritization Framework](#3-extraction-prioritization-framework)
4. [Approved Phase 1 Extraction Categories](#4-approved-phase-1-extraction-categories)
5. [Forbidden Phase 1 Categories](#5-forbidden-phase-1-categories)
6. [Extraction Grouping Doctrine](#6-extraction-grouping-doctrine)
7. [Validation Cadence Doctrine](#7-validation-cadence-doctrine)
8. [Rollback Trigger Matrix](#8-rollback-trigger-matrix)
9. [Tactical UX Protection During Phase 1](#9-tactical-ux-protection-during-phase-1)
10. [Extraction Freeze Conditions](#10-extraction-freeze-conditions)
11. [Recommended Exact Phase 1 Candidates](#11-recommended-exact-phase-1-candidates)
12. [Phase 1 Completion Criteria](#12-phase-1-completion-criteria)
13. [Phase 2 Readiness Requirements](#13-phase-2-readiness-requirements)

**Appendices:**
- [A. Ranked Extraction Candidate Table](#appendix-a-ranked-extraction-candidate-table)
- [B. Example Micro-Extraction Workflow](#appendix-b-example-micro-extraction-workflow)
- [C. Example Rollback Scenario](#appendix-c-example-rollback-scenario)
- [D. Phase 1 Validation Checklist](#appendix-d-phase-1-validation-checklist)
- [E. Phase 2 Gate Approval Checklist](#appendix-e-phase-2-gate-approval-checklist)

---

## 1. Purpose of Phase 1 Extraction

### 1.1 Why Phase 1 Must Be Ultra-Low-Risk

Phase 1 is not a performance initiative. It is a trust-building exercise. The system must demonstrate, on live production code, that modularization can be executed without introducing rerender contamination, import coupling failures, state desynchronization, or tactical display degradation.

This goal requires that Phase 1 candidates share four properties:

1. **Zero session_state contact.** If a function does not read or write `st.session_state`, it cannot introduce rerender contamination when extracted.
2. **Zero cache decorator ownership.** `@st.cache_data` functions change cache key identity when moved. Phase 1 candidates must own no cache decorators.
3. **Zero Streamlit API calls.** Functions that call `st.markdown()`, `st.button()`, `st.write()`, or any Streamlit widget cannot be safely extracted without auditing their full rerender graph first.
4. **Zero import circularity risk.** Phase 1 targets pure-Python functions that import only stdlib or `config.py`. They introduce no new dependency edges that could create circular imports.

These constraints are not conservative in the sense of being overly cautious. They are precise. They define the exact class of code that can be moved without risk of structural regression. Any relaxation of these constraints moves the extraction into Phase 2 or Phase 3 scope, with the corresponding audit requirements.

### 1.2 Why Confidence-Building Matters

The stabilization work of Phase 3A required sustained effort to suppress rerender amplification, fix modal persistence failures, correct JIG sort type safety, and restore navigation continuity. That work must not be reversed.

The engineering team's confidence in modularization safety must be earned incrementally:

- First extraction: proves the new module structure works
- First import in app.py: proves import path is clean
- First runtime observation window: proves no phantom rerenders were introduced
- First rollback drill (if needed): proves the rollback path is reliable

Each of these milestones builds the operator's confidence in the modularization process itself. Without this confidence, every subsequent extraction carries unnecessary psychological risk, which leads to slower execution and more conservative rollback decisions.

Phase 1 is designed to produce several guaranteed wins before the system is asked to handle genuinely complex extractions.

### 1.3 Why Extraction Pacing Must Stay Slow

The most dangerous failure mode in modularization is the "phantom success." Code moves cleanly. Python imports succeed. The app loads. No exception is raised. But three hours later, during a specific navigation sequence, the investigation atmosphere resets unexpectedly because a helper function that was extracted now initializes one call-stack frame too late.

Slow pacing exists to detect phantom successes before they accumulate. Each extraction must be followed by a runtime observation window before the next extraction begins. If two extractions are executed back-to-back without observation windows, and a defect is introduced by the second extraction, the operator cannot determine which extraction caused the defect.

**Rule:** One extraction group per session. One runtime observation window per extraction group. No exceptions.

---

## 2. Phase 1 Governance Rules

### 2.1 Hard Prohibition: Runtime-Governed Systems

Phase 1 extraction authorization is permanently denied for any code that:

- Reads or writes `st.session_state` in any form
- Owns or references `@st.cache_data` or `@st.fragment` decorators
- Calls any Streamlit API (`st.markdown`, `st.button`, `st.metric`, `st.spinner`, etc.)
- Participates in route synchronization logic
- Reads from or writes to navigation state keys
- Contains hydration callback logic
- Participates in the startup context build (`_build_startup_context`)

These systems are governed by runtime execution order. Moving them changes the order in which they execute relative to Streamlit's rerun cycle. That change is not detectable by syntax checking or import analysis.

### 2.2 Hard Prohibition: State Extraction

No `st.session_state` key initialization, read, or write may be moved in Phase 1. Session state in Streamlit is order-dependent. The moment a key is read before it is written — even by one Streamlit execution frame — the system can silently return the wrong value or raise a `KeyError` at a UI path that is not exercised during smoke testing.

### 2.3 Hard Prohibition: Routing Extraction

The active workspace router, route dispatcher, route coercion logic, and navigation continuity system are permanently out of Phase 1 scope. These systems are the most fragile in the entire codebase: they depend on execution order, session_state initialization order, and Streamlit's fragment execution model. Any extraction that alters the call order of routing logic can produce navigation corruption that only manifests under specific interaction sequences.

### 2.4 Hard Prohibition: Cache Extraction

`@st.cache_data` functions must not be moved. Cache identity in Streamlit is tied to function identity (module path + function name). Moving a cached function to a new module path invalidates the warm cache for all active user sessions at the moment of deployment. This causes a cold-load storm: every user gets a full pipeline re-execution simultaneously. In development this is invisible. In production it causes latency spikes and potential API rate-limit exhaustion.

### 2.5 Hard Prohibition: Orchestration Extraction

Tactical orchestration chains — the sequences that build shell context, run hydration callbacks, fire side effects, and gate lazy route loading — must not be touched in Phase 1. These are timing-sensitive execution graphs where moving any node changes the observable behavior of the system, even if the individual functions are logically pure.

---

## 3. Extraction Prioritization Framework

### 3.1 Priority Scoring Dimensions

Each candidate is scored on six dimensions (1–5 scale, 5 = safest):

| Dimension | Weight | Definition |
|-----------|--------|-----------|
| Dependency isolation | 25% | No imports beyond stdlib and config.py |
| Rerender immunity | 25% | Zero session_state contact, zero Streamlit API calls |
| Rollback simplicity | 20% | Rollback = revert one file, fix one import |
| Import simplicity | 15% | New module adds one import line to app.py |
| Tactical isolation | 10% | Not on any tactical rendering path |
| State independence | 5% | Does not read or modify any mutable shared state |

### 3.2 Priority Score Calculation

```
priority_score = (dep_isolation × 0.25)
              + (rerender_immunity × 0.25)
              + (rollback_simplicity × 0.20)
              + (import_simplicity × 0.15)
              + (tactical_isolation × 0.10)
              + (state_independence × 0.05)
```

Candidates scoring ≥ 4.5 are Phase 1 approved.  
Candidates scoring 3.5–4.4 are Phase 2 candidates.  
Candidates scoring < 3.5 are Phase 3+ candidates.

### 3.3 Tiebreaker Rules

When two candidates score equally:

1. Prefer the candidate with fewer lines (smaller blast radius if rollback is needed)
2. Prefer the candidate that is called by fewer callers in app.py (fewer import references to update)
3. Prefer the candidate whose name is already module-appropriate (begins with a category noun, not `_render_` or `_shell_`)

---

## 4. Approved Phase 1 Extraction Categories

### 4.1 Pure Primitive Formatters

Functions that accept a scalar input and return a scalar output with no imports beyond stdlib. These are the safest possible extraction targets. They have zero observable side effects and their rollback is trivial.

**Criteria:**
- Input: primitive type (str, int, float, None)
- Output: primitive type (str)
- No imports except stdlib
- No session_state
- No Streamlit API

**Examples in app.py:**
- `_fmt_american(odds)` — formats American odds to string
- `_pf(val, default)` — coerces to float with fallback
- `_badge(val, thr, fmt)` — formats a threshold badge string
- `_iso_now_local()` — formats current time to ISO string
- `_deg_to_compass(deg)` — converts wind degrees to compass label
- `_stable_key_token(*parts)` — hashes parts to stable string
- `_fanduel_url(player_name)` — builds FanDuel URL string

### 4.2 Static Constants and Data Maps

Module-level constants that contain no executable logic, no runtime dependencies, and no mutable state. These are strings, tuples, sets, or dicts of primitive values. They can be moved to a constants module with a single `from ui.constants import X` import.

**Criteria:**
- Assignment statement only — no function call on the right-hand side
- No imports required to evaluate
- No reference to session_state or runtime state
- No `@st.cache_data` or `@st.fragment`

**Examples in app.py:**
- `_DARK_GREEN`, `_GREEN`, `_RED`, `_DARK_RED` — CSS color strings (line 1726)
- `_HEAT_COLS` — set of column names (line 1841)
- `_HEAT_NEUTRAL`, `_HEAT_BASE` — CSS strings (line 1847)
- `_DEPLOYMENT_TIER_ORDER` — pure tuple of tier names (line 2308)
- `_DEPLOYMENT_TIER_META` — pure dict of tier metadata (line 2317)
- `_LIFECYCLE_ORDER` — pure tuple of lifecycle states (line 2326)
- `_MAIN_TCC_SECTION_LABELS` — pure dict of section labels (line 1881)
- `_MAIN_TCC_SECTION_KEYS` — pure dict of section → keys mapping (line 1871)
- `_MAIN_TCC_SECTION_ORDER` — pure tuple derived from labels dict (line 1891)
- `_BATTERS_TABLE_ALL_COLUMNS` — pure tuple of column names (line 1892)
- `_BATTERS_TABLE_PRESETS` — pure dict of preset → columns (line 1897)
- `_BATTERS_TABLE_TOOLTIP_META` — pure dict of column metadata (line 1915)

### 4.3 Pure CSS / Color Classification Functions

Functions that accept scalar inputs and return CSS style strings or color hex codes. These functions are self-contained threshold maps. They depend only on color constants (Category 4.2) and perform no state access.

**Criteria:**
- Input: column name + numeric value
- Output: CSS string or color hex code
- Depends only on color constants (can be extracted together with those constants)
- Zero session_state, zero Streamlit API

**Examples in app.py:**
- `_stat_css(col, val)` — returns CSS style string for stat cell (line 1731)
- `_stat_badge(col, val)` — returns emoji-prefixed string (line 1831)
- `_edge_col(edge)` — returns CSS color for edge% (line 2296)
- `_pct_band(value, elite, strong, dangerous)` — returns band label (line 2022)

**Extraction dependency:** `_stat_css` and `_stat_badge` depend on color constants. Extract color constants first, then CSS functions in the same group.

### 4.4 Pure Label / Rating Functions

Functions that accept player stat scalars and return formatted label strings with emoji or rating designations. These contain threshold logic but no state access.

**Criteria:**
- Input: numeric scalars (ev_pct, edge_pct, etc.)
- Output: string label with optional emoji prefix
- No imports
- No session_state, no Streamlit API

**Examples in app.py:**
- `_pick_rating(ev_pct, edge_pct, model_prob, confidence)` — returns rating string (line 1561)
- `_pitcher_label(name, pitcher_factor, platoon_factor)` — returns colored pitcher name (line 1577)
- `_spot_label(spot, platoon_factor)` — returns colored lineup spot string (line 1595)

### 4.5 Pure Weather Display Helpers

Functions that accept a player dict and compute weather display strings from its values. These read player dict fields only — no session_state, no Streamlit rendering.

**Criteria:**
- Input: player dict
- Output: string (weather summary or HTML badge)
- Depends only on `_deg_to_compass` (Category 4.1 primitive)
- No session_state, no Streamlit API

**Examples in app.py:**
- `_weather_summary(player)` — returns compact weather string (line 2604)
- `_weather_badge(player)` — returns HTML badge string (line 2628)
- `_hr_env_score(player)` — returns (score, color, label) tuple (line 2641)

---

## 5. Forbidden Phase 1 Categories

### 5.1 Session State Systems — PERMANENTLY FORBIDDEN FROM PHASE 1

Any function that reads or writes `st.session_state` in any form. These functions are order-dependent within Streamlit's rerun cycle and cannot be safely moved without a full session_state key trace and execution order audit.

**Specific forbidden functions:**
- `_build_startup_context()` — initializes startup state (line 26)
- `_runtime_diag()` — reads `_RUNTIME_DIAG_KEY` from session_state (line 168)
- `_mark_runtime_rerun()` — writes to session_state (line 199)
- `_update_runtime_route_diag()` — writes route diagnostics to session_state (line 204)
- `_ensure_navigation_continuity_state()` — initializes navigation keys (line 213)
- `_record_hydration_state()` — writes hydration fingerprint to session_state (line 344)
- `_run_hydration_side_effects_once()` — reads/writes side effect fingerprint (line 355)
- `_clear_runtime_refresh_state()` — deletes session_state keys (line 413)
- `_snapshot_runtime_context()` — reads session_state (line 645)
- `_push_runtime_context()` — writes to session_state stack (line 664)
- `_restore_runtime_context()` — pops from session_state stack (line 670)
- `_request_workspace_route()` — writes pending workspace route (line 710)
- `_coerce_shell_route()` — reads and normalizes route from session_state (line 625)
- `get_data()` — primary data hydration with session_state writes (line 1642)

### 5.2 Cached Functions — PERMANENTLY FORBIDDEN FROM PHASE 1

Any function decorated with `@st.cache_data` or `@st.fragment`. Moving these changes cache key identity and invalidates warm caches.

**Specific forbidden functions:**
- `_auto_refresh_ticker()` — `@st.fragment(run_every=60)` decorator (line 1611)
- `_load_pipeline_cached()` — `@st.cache_data` decorated (line 1629)
- `_cached_pitcher_map()` — `@st.cache_data` decorated (line 1636)

### 5.3 Routing and Navigation Systems — PERMANENTLY FORBIDDEN FROM PHASE 1

Any function that participates in route determination, navigation state management, or workspace activation.

**Specific forbidden functions:**
- `_ensure_navigation_continuity_state()` (line 213)
- `_coerce_shell_route()` (line 625)
- `_request_workspace_route()` (line 710)
- `_jump_to_investigation_target()` (line 720) — writes to session_state, triggers rerun
- `_build_runtime_shell_context()` (line 822) — reads route + trust state from session_state

### 5.4 Shell Rendering Functions — PERMANENTLY FORBIDDEN FROM PHASE 1

Any function that calls Streamlit rendering APIs. These functions are entangled with Streamlit's widget rendering lifecycle and cannot be safely moved without a full render-path audit.

**Specific forbidden functions:**
- `_render_command_strip()` (line 856)
- `_render_sidebar_shell_zones()` (line 915)
- `_render_live_feed_shell()` (line 999)
- `_render_queue_shell()` (line 1018)
- `_render_deployment_tray()` (line 1044)
- `_render_navigation_breadcrumbs()` (line 217)
- `_render_interruption_indicators()` (line 236)
- `_render_recovery_prompt_shell()` (line 251)
- `_render_runtime_diagnostics()` (line 468)
- `_render_batters_table_html()` (line 2163) — contains session_state reads and Streamlit calls
- `_render_tcc_section_header()` (line 2008) — contains Streamlit calls
- `_show_player_modal()` (line 3181) — full Streamlit modal with session_state
- `_render_deployment_cards()` (line 2485) — Streamlit rendering with session_state

### 5.5 Tactical Orchestration Systems — PERMANENTLY FORBIDDEN FROM PHASE 1

Any function that participates in hydration, pipeline execution, or tactical data orchestration.

**Specific forbidden functions:**
- `_build_hydration_fingerprint()` (line 316) — produces cache fingerprint for hydration guard
- `_record_hydration_state()` (line 344)
- `_run_hydration_side_effects_once()` (line 355)
- `_build_status_urgency_bundle()` (line 1139) — complex status cache with timing logic
- `_ensure_pitch_mix_contexts()` (line 568) — async pitch mix loading with session_state

### 5.6 Complex Display Functions With Hidden Dependencies — FORBIDDEN FROM PHASE 1

Functions that appear to be "display helpers" but read session_state or call Streamlit APIs internally.

**Specific forbidden functions:**
- `_batters_table_apply_preset()` (line 1955) — writes to `session_state`
- `_batters_table_visible_columns()` (line 1960) — reads from `session_state`
- `_set_all_tcc_sections()` (line 1997) — writes to `session_state`
- `_reset_tcc_visibility_state()` (line 2002) — writes to `session_state`
- `_tcc_section_visible()` (line 1990) — reads `session_state`
- `_tcc_section_active_count()` (line 1971) — reads `session_state`
- `_consume_batters_table_player_query()` (line 2268) — reads/writes `session_state`
- `_session_fp_value()` (line 547) — reads `session_state` via fingerprint system

### 5.7 Startup and Import Systems — PERMANENTLY FORBIDDEN FROM PHASE 1

- `_build_startup_context()` (line 26) — handles import-time module loading
- `_format_startup_import_error()` (line 61) — formats startup exceptions
- `_STARTUP_CONTEXT` (line 76) — top-level startup state; moving changes module initialization order

---

## 6. Extraction Grouping Doctrine

### 6.1 Micro-Extractions

**Definition:** Single function or 1–3 closely related constants moved in one operation.

**Rules:**
- One micro-extraction per Claude session
- Full validation window before next micro-extraction
- Candidate must score ≥ 4.8 on priority scoring framework
- Rollback must be achievable in under 60 seconds (single file revert + one import deletion)

**Approved micro-extraction pattern:**
```
Phase: Select single function
Action: Move to target module
Action: Add single import line to app.py
Verify: App loads, no import errors
Verify: Runtime observation window (30+ minutes)
Decision: Proceed or rollback
```

### 6.2 Grouped Extractions

**Definition:** Multiple Phase 1 candidates moved together when they share a mutual dependency (e.g., color constants + CSS functions that reference those constants).

**Rules:**
- Maximum 3 functions per grouped extraction
- All functions in group must score ≥ 4.5
- All functions in group must share the same target module
- The dependency must be internal to the group (functions only depend on each other)
- Grouped extraction still counts as one extraction per session

**Approved grouping pattern:**
```
Group: Color constants + _stat_css + _stat_badge
Reason: _stat_css depends on color constants; _stat_badge depends on _stat_css
Target: ui/stat_colors.py
Single import line: from ui.stat_colors import _stat_css, _stat_badge, _DARK_GREEN, ...
```

**Forbidden groupings:**
- Mixing a pure function with any session_state-adjacent function
- Grouping functions from different target modules
- Grouping more than 3 functions regardless of score

### 6.3 Sequential-Only Extractions

Certain extractions must be done in strict order because later candidates depend on earlier ones. These dependencies must be extracted in parent-first order. A dependent function cannot be extracted before its dependency is in place.

**Dependency chains requiring sequential extraction:**

| Step | Extract | Because |
|------|---------|---------|
| 1 | Color constants | `_stat_css` references these |
| 2 | `_stat_css` | `_stat_badge` calls `_stat_css` |
| 3 | `_stat_badge` | depends on `_stat_css` |
| — | — | — |
| 1 | `_deg_to_compass` | `_weather_summary` calls this |
| 2 | `_weather_summary` | `_weather_badge` calls this |
| 3 | `_weather_badge` | depends on `_weather_summary` |

These sequences may be collapsed into grouped extractions (all three in one operation) if they all target the same module file.

### 6.4 Forbidden Grouped Migrations

The following combinations are explicitly forbidden, regardless of individual candidate scores:

| Forbidden Group | Reason |
|----------------|--------|
| Any Phase 1 candidate + any session_state function | State contamination risk |
| Any Phase 1 candidate + any `@st.cache_data` function | Cache invalidation risk |
| Any Phase 1 candidate + any Streamlit rendering function | Rerender graph coupling |
| Two sequential-dependency candidates in wrong order | Import resolution failure |
| Any Phase 1 candidate + startup logic | Module initialization order risk |
| More than 3 functions regardless of score | Blast radius exceeds rollback speed |

---

## 7. Validation Cadence Doctrine

### 7.1 Validation After Every Extraction

No exceptions. Every extraction — regardless of size — must be followed by the complete validation sequence before the next extraction begins.

**Mandatory validation sequence:**
1. Python import test (`python -c "import app"`) — confirms no circular imports, no NameError
2. Streamlit cold start (`streamlit run app.py`) — confirms app loads without exception
3. Route navigation test — navigate to MAIN, JIG, INVESTIGATION views manually
4. Modal open/close test — open at least one player modal, close it, confirm state clears
5. Batter table render test — confirm table loads with heatmap coloring intact
6. Shell badge render test — confirm shell badges render with correct tier colors
7. 30-minute runtime observation window — observe for phantom rerenders, missing elements

### 7.2 Rerender Observation Frequency

During the 30-minute runtime observation window:

- At 5 minutes: confirm no console rerender loop warnings
- At 15 minutes: navigate between routes, confirm no route reset
- At 30 minutes: confirm investigation atmosphere persists across navigation

If any observation fails at any checkpoint, execute rollback immediately. Do not attempt to diagnose while in production.

### 7.3 Runtime Observation Intervals

| Extraction Risk Level | Observation Window | Navigation Tests Required |
|----------------------|-------------------|--------------------------|
| Score 4.8–5.0 (ultra-safe) | 30 minutes | MAIN + one route |
| Score 4.5–4.7 (safe) | 45 minutes | MAIN + all primary routes |
| Score 4.0–4.4 (Phase 2 border) | Do not extract in Phase 1 | — |

### 7.4 Rollback Trigger Thresholds

If any of the following are observed at any point during the observation window, trigger immediate rollback without waiting for the window to complete:

- Any console rerender loop (same component re-executing more than 3× per second)
- Any Streamlit `KeyError` in session_state
- Any import error after app reload
- Any blank render where content previously appeared
- Any shell badge showing wrong tier color
- Any route that fails to load when previously working
- Any modal that fails to clear on close

---

## 8. Rollback Trigger Matrix

### 8.1 Immediate Rollback Triggers (No Diagnosis First)

Execute rollback immediately upon observation. Do not attempt to fix inline.

| Symptom | Mechanism | Rollback Action |
|---------|-----------|----------------|
| Rerender loop | Extracted function introduced session_state write on import path | Revert target module; restore original app.py import block |
| `KeyError` in session_state | Initialization order changed by extraction | Revert target module; restore original app.py |
| `ImportError` or `ModuleNotFoundError` | Circular import introduced or import path wrong | Revert target module; restore original import line in app.py |
| Blank tactical card panel | Render contract broken by extraction | Revert and escalate to Phase 2 audit before re-attempting |
| Navigation route reset on page interaction | Route synchronization timing broken | Immediate revert; flag as forbidden Phase 1 candidate |
| Missing shell badges | Badge HTML generation path broken | Revert target module; restore original function |
| Modal fails to persist | session_state fingerprint broken | Immediate revert; escalate to full hidden dependency audit |
| App fails to start (exception at import time) | Module initialization order disrupted | Immediate revert; investigate startup_context coupling |

### 8.2 Delayed Rollback Triggers (Diagnose Then Decide)

These symptoms may indicate extraction issues but could have other causes. Diagnose before rolling back.

| Symptom | Diagnose Before Rollback | Max Diagnosis Time |
|---------|--------------------------|--------------------|
| Slower page load | Could be unrelated API latency; check pipeline timing | 15 minutes |
| Slightly different badge color | Could be data-driven; check player data for that route | 10 minutes |
| Console deprecation warning | Could be pre-existing; check git blame | 5 minutes |

If diagnosis does not identify the cause within the time limit, treat as immediate rollback trigger.

### 8.3 False Positive Protection

The following conditions are NOT rollback triggers:
- Streamlit version warnings not related to the extracted code
- Slow API response from The Odds API or MLB Stats API
- Pipeline data unavailability (no games today)
- Console output from `@st.cache_data` cache miss on cold start (expected)

---

## 9. Tactical UX Protection During Phase 1

### 9.1 Shell Consistency Requirements

The tactical shell — command strip, trust badge, source badges, degraded badges — must render identically after every Phase 1 extraction. Shell rendering functions are not extraction targets, but their dependencies (color constants, badge HTML helpers) may be.

After any extraction that touches badge-related constants or helpers:
- Manually verify all badge tier colors: FULL, DEGRADED, PARTIAL, LIVE
- Verify `_shell_token_palette()` returns correct colors for each state
- Verify `_shell_badge_html()` renders without visual regression

### 9.2 Investigation Flow Protection

The investigation atmosphere — escalation tier display, threat card density, suppression indicators, archetype classification — must be verified after any extraction that touches label, CSS, or rating functions.

After extracting `_pick_rating`, `_pitcher_label`, `_spot_label`, or any stat CSS function:
- Manually load the INVESTIGATION route with a live pick slate
- Confirm threat card escalation labels are correct
- Confirm CSS heatmap coloring applies to stat columns
- Confirm pitcher vulnerability labels display correctly

### 9.3 Escalation Readability Protection

The operator's ability to read escalation hierarchy must not be degraded. After any extraction:
- Confirm "🌟 ONCE IN A LIFETIME", "🔥 STRONG EDGE", "✅ SOLID PLAY", "📊 MARGINAL" labels render correctly
- Confirm deployment tier badges ("Core Deployment", "High Conviction", etc.) display with correct colors

### 9.4 Visual Pacing Protection

Phase 1 extractions touch display helpers but not rendering orchestrators. As a result, visual pacing (the order in which panels appear during a page load) should not be affected. If pacing appears to change after an extraction, treat it as a delayed rollback trigger and diagnose.

### 9.5 Command Hierarchy Integrity

No Phase 1 extraction may touch the command strip rendering, route label generation, or workspace route resolution. These define the operator's primary navigation interface. Any regression in command hierarchy display is an immediate rollback trigger.

---

## 10. Extraction Freeze Conditions

### 10.1 Active Freeze Triggers

Modularization is immediately frozen when any of the following conditions are observed:

| Condition | Freeze Duration | Lift Condition |
|-----------|----------------|----------------|
| Rollback was executed in the previous session | Until cause is identified and documented | Operator reviews cause, confirms doctrine was followed, approves resumption |
| Runtime contamination observed (rerender loop) | Indefinite | Full rerender graph audit of extracted module; confirmed clean |
| Import contamination observed (circular import) | Until resolved | Import graph fully mapped and clean |
| Tactical UX degradation (blank cards, missing badges) | Indefinite | Full hidden dependency audit of affected rendering path |
| State desynchronization (wrong state in any view) | Indefinite | Full session_state key trace for affected keys |
| Operator has not completed validation window | Until window complete | 30–45 minute observation window completes with clean result |
| Two or more extractions in the same session | Automatic | Wait for next session |

### 10.2 Stabilization Override Conditions

If the production system exhibits ANY of the following, modularization is suspended entirely until the system returns to stable baseline:

- Active rerender amplification causing visible UI flicker
- Navigation route inconsistency observed across sessions
- JIG or tactical card data failing to hydrate correctly
- Modal state corruption (modal opens in wrong state or fails to clear)
- Any `st.session_state` KeyError in production

Stabilization work takes priority over modularization work. The system's operational integrity is more important than its structural cleanliness.

### 10.3 Runtime Contamination Conditions

If an extraction causes runtime contamination that is not immediately resolved by rollback (e.g., the contamination persists due to cached state), the modularization process is suspended pending:

1. A full Streamlit session reset (clear cache + restart)
2. Operator confirmation that baseline behavior is restored
3. Documentation of the contamination mechanism
4. Update to this doctrine's forbidden categories if the contamination reveals a previously unknown hidden dependency

### 10.4 Operator Freeze Authority

The operator may freeze modularization at any time, for any reason, without justification. An operator freeze is not overridable by any architectural governance. Resume only when the operator explicitly lifts the freeze.

---

## 11. Recommended Exact Phase 1 Candidates

### 11.1 Ranked Candidate Table

See Appendix A for full ranked candidate table with dependency and rollback details.

### 11.2 Top 5 Recommended First Extractions

Listed in recommended extraction order:

**Extraction 1 — Pure Primitive Group → `ui/formatters.py`**

Move together (grouped extraction, all share target module, no inter-dependency conflicts):
- `_fmt_american(odds)` (line 1719) — zero deps, 4 lines
- `_pf(val, default)` (line 87) — zero deps, 2 lines
- `_deg_to_compass(deg)` (line 2597) — zero deps, 3 lines

Risk: NONE. These are the three safest candidates in the entire file. Zero session_state, zero imports, zero Streamlit API, pure scalar → scalar functions.

Target file: `mlb_hr_engine_v4/ui/formatters.py`  
Import line in app.py: `from ui.formatters import _fmt_american, _pf, _deg_to_compass`  
Rollback: Delete `ui/formatters.py`, restore 3 function definitions to app.py, delete import line.

---

**Extraction 2 — Weather Display Group → `ui/weather_display.py`**

Prerequisite: Extraction 1 complete and validated (depends on `_deg_to_compass`).

Move together:
- `_weather_summary(player)` (line 2604)
- `_weather_badge(player)` (line 2628)
- `_hr_env_score(player)` (line 2641)

These depend only on `_deg_to_compass` (in `ui/formatters.py` after Extraction 1). Read player dict only. No session_state.

Target file: `mlb_hr_engine_v4/ui/weather_display.py`  
Import line in app.py: `from ui.weather_display import _weather_summary, _weather_badge, _hr_env_score`  
`weather_display.py` imports: `from ui.formatters import _deg_to_compass`

---

**Extraction 3 — Stat Color System → `ui/stat_colors.py`**

Prerequisite: Extraction 1 validated (no dependency on Extraction 2).

Move together:
- Color constants: `_DARK_GREEN`, `_GREEN`, `_RED`, `_DARK_RED` (line 1726)
- `_HEAT_COLS` set (line 1841)
- `_HEAT_NEUTRAL`, `_HEAT_BASE` strings (line 1847)
- `_stat_css(col, val)` (line 1731)
- `_stat_badge(col, val)` (line 1831)
- `_edge_col(edge)` (line 2296)

These form a self-contained system. `_stat_css` depends on the color constants. `_stat_badge` depends on `_stat_css`. `_edge_col` is independent. All can co-locate in `ui/stat_colors.py`.

Target file: `mlb_hr_engine_v4/ui/stat_colors.py`  
Import line in app.py: `from ui.stat_colors import _stat_css, _stat_badge, _edge_col, _HEAT_COLS, _HEAT_NEUTRAL, _HEAT_BASE`

Note: Color constants used only by `_stat_css` and `_stat_badge`. After move, app.py no longer references `_DARK_GREEN` etc. directly. Confirm no other callers before moving.

---

**Extraction 4 — Pick Rating and Label Helpers → `ui/pick_labels.py`**

Prerequisite: Extraction 3 validated.

Move together:
- `_pick_rating(ev_pct, edge_pct, model_prob, confidence)` (line 1561)
- `_pitcher_label(name, pitcher_factor, platoon_factor)` (line 1577)
- `_spot_label(spot, platoon_factor)` (line 1595)

Zero deps on extracted modules. Zero session_state. These are pure threshold → string functions.

Target file: `mlb_hr_engine_v4/ui/pick_labels.py`  
Import line in app.py: `from ui.pick_labels import _pick_rating, _pitcher_label, _spot_label`

---

**Extraction 5 — Deployment Constants → `ui/deployment_constants.py`**

Prerequisite: All prior extractions validated.

Move together:
- `_DEPLOYMENT_TIER_ORDER` (line 2308)
- `_DEPLOYMENT_TIER_META` (line 2317)
- `_LIFECYCLE_ORDER` (line 2326)

Pure data constants. No function deps. Can co-locate with TCC section constants.

Target file: `mlb_hr_engine_v4/ui/deployment_constants.py`  
Import line in app.py: `from ui.deployment_constants import _DEPLOYMENT_TIER_ORDER, _DEPLOYMENT_TIER_META, _LIFECYCLE_ORDER`

---

### 11.3 Phase 1 Deferred Candidates (Require Further Audit)

The following candidates appear safe but require additional audit before extraction:

| Candidate | Concern | Required Audit |
|-----------|---------|---------------|
| `_apply_heatmap(df)` (line 1851) | Calls pandas Styler — imports `pd`; verify no hidden Streamlit coupling | Confirm no widget state reference in Styler callbacks |
| `_batters_table_tooltip_meta` dict (line 1915) | References column name strings that must match widget keys | Verify no session_state key overlap |
| `_BATTERS_TABLE_PRESETS` (line 1897) | Referenced by `_batters_table_apply_preset` which writes session_state | Confirm constants can be moved independently of the function |
| `_MAIN_TCC_SECTION_LABELS/KEYS/ORDER` (lines 1871–1891) | Referenced by `_tcc_section_active_count` which reads session_state | Confirm constants can be moved independently of the function |
| `_pick_rating` (line 1561) | Called from inside card HTML builders that may have hidden state deps | Trace all callers for session_state contact |

These candidates are approved for Phase 1 only after the specified audit is complete and documents a clean result.

---

## 12. Phase 1 Completion Criteria

### 12.1 Quantitative Completion Requirements

Phase 1 is complete when ALL of the following are satisfied:

- Minimum 5 extraction groups completed and validated
- All 5 top-ranked extractions (Section 11.2) completed
- No rollback has been required in the last 3 extraction sessions
- Runtime observation windows for all completed extractions were clean

### 12.2 Required Runtime Stability Window

Before Phase 1 is declared complete:
- 7 consecutive days without a Phase 1-related defect in any production session
- All primary routes (MAIN, JIG, INVESTIGATION, DEPLOYMENT) tested after all Phase 1 extractions
- All shell badge states verified correct after all Phase 1 extractions
- All tactical card render paths verified correct after all Phase 1 extractions

### 12.3 Validation Pass Requirements

All of the following must pass for each extraction that is part of Phase 1 completion:
- Python import test: PASS
- Streamlit cold start: PASS
- Route navigation (all 4 primary routes): PASS
- Modal lifecycle: PASS
- Heatmap coloring: PASS
- Shell badge rendering: PASS
- 30+ minute clean observation window: PASS

### 12.4 Operator Approval Requirements

Phase 1 cannot be declared complete without explicit operator approval. Operator must confirm:
1. All validation checklists (Appendix D) completed for each extraction
2. No active freeze conditions in place
3. 7-day stability window observed
4. Phase 2 gate checklist (Appendix E) reviewed and prerequisites understood

---

## 13. Phase 2 Readiness Requirements

### 13.1 What Must Be Proven Before Phase 2

Phase 2 extractions involve code with more complex dependencies: functions that read player data structures, functions with 2–5 internal dependencies, functions that sit closer to the rendering boundary. Before Phase 2 begins, the following must be demonstrated:

1. **Extraction process discipline confirmed.** At least 5 Phase 1 extractions completed without requiring a rollback.
2. **Module import structure clean.** The `ui/` module directory established by Phase 1 imports correctly with no circular dependency warnings.
3. **Rollback path verified.** At least one rollback drill completed successfully (intentional rollback during a test extraction), demonstrating the rollback mechanism is reliable.
4. **Runtime observation protocol internalized.** Operator has completed at least 3 observation windows without shortcuts.

### 13.2 State Governance Prerequisites for Phase 2

Before Phase 2 extractions can touch any function that is within 2 call-stack levels of session_state:
- A complete `st.session_state` key map must exist (all keys, all writers, all readers, initialization order)
- The key map must be validated against actual runtime behavior (not inferred from code reading alone)
- Any key that is written by more than one location must be flagged as a Cross-Write Key and excluded from Phase 2 scope

### 13.3 Runtime Trust Requirements for Phase 2

The system must have demonstrated, through Phase 1, that:
- Modularization does not introduce phantom rerenders when pure functions are moved
- Import structure changes do not affect Streamlit's widget key resolution
- The observation window protocol is sufficient to catch defects before they accumulate

Phase 2 authorization requires explicit operator sign-off on all three points.

### 13.4 Phase 2 Scope Preview (NOT Authorized Yet)

The following categories are the likely Phase 2 scope, listed here for planning awareness only. **No Phase 2 extraction is authorized until Phase 1 completion criteria (Section 12) are satisfied.**

- `_card_html()` and card HTML builder functions (with hidden deps audit first)
- `_intelligence_card_html()` and `_elite_card_html()` (large HTML builders, complex deps)
- `_combo_html()` parlay card builder
- `_deployment_tier()` and `_deployment_lifecycle()` (read player dict, no session_state — audit needed)
- `_player_photo_html()` (reads MLB photo URL — audit URL builder deps)

Each of these will require a full hidden dependency audit and callers trace before Phase 2 extraction is authorized.

---

## Appendix A. Ranked Extraction Candidate Table

| Rank | Candidate | Lines | Target Module | Dep Isolation | Rerender Immunity | Rollback Simplicity | Priority Score | Phase |
|------|-----------|-------|--------------|--------------|-------------------|--------------------|--------------|----|
| 1 | `_fmt_american(odds)` | 1719 | `ui/formatters.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 2 | `_pf(val, default)` | 87 | `ui/formatters.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 3 | `_deg_to_compass(deg)` | 2597 | `ui/formatters.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 4 | `_DARK_GREEN/_GREEN/_RED/_DARK_RED` | 1726 | `ui/stat_colors.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 5 | `_DEPLOYMENT_TIER_ORDER` | 2308 | `ui/deployment_constants.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 6 | `_DEPLOYMENT_TIER_META` | 2317 | `ui/deployment_constants.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 7 | `_LIFECYCLE_ORDER` | 2326 | `ui/deployment_constants.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 8 | `_HEAT_COLS` | 1841 | `ui/stat_colors.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 9 | `_HEAT_NEUTRAL/_HEAT_BASE` | 1847 | `ui/stat_colors.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 10 | `_edge_col(edge)` | 2296 | `ui/stat_colors.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 11 | `_pick_rating(...)` | 1561 | `ui/pick_labels.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 12 | `_pitcher_label(...)` | 1577 | `ui/pick_labels.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 13 | `_spot_label(...)` | 1595 | `ui/pick_labels.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 14 | `_stat_css(col, val)` | 1731 | `ui/stat_colors.py` | 5 | 5 | 5 | **4.90** | Phase 1 (after color constants) |
| 15 | `_stat_badge(col, val)` | 1831 | `ui/stat_colors.py` | 5 | 5 | 5 | **4.90** | Phase 1 (after _stat_css) |
| 16 | `_weather_summary(player)` | 2604 | `ui/weather_display.py` | 4 | 5 | 5 | **4.70** | Phase 1 (after _deg_to_compass) |
| 17 | `_weather_badge(player)` | 2628 | `ui/weather_display.py` | 4 | 5 | 5 | **4.70** | Phase 1 (after _weather_summary) |
| 18 | `_hr_env_score(player)` | 2641 | `ui/weather_display.py` | 5 | 5 | 5 | **4.85** | Phase 1 |
| 19 | `_pct_band(...)` | 2022 | `ui/pick_labels.py` | 5 | 5 | 5 | **4.95** | Phase 1 |
| 20 | `_fanduel_url(player_name)` | 2590 | `ui/formatters.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 21 | `_iso_now_local()` | 298 | `ui/formatters.py` | 5 | 5 | 5 | **5.00** | Phase 1 |
| 22 | `_apply_heatmap(df)` | 1851 | `ui/stat_colors.py` | 4 | 4 | 4 | **4.15** | Phase 1 (after audit) |
| 23 | `_MAIN_TCC_SECTION_LABELS/KEYS/ORDER` | 1871 | `ui/tcc_constants.py` | 5 | 5 | 4 | **4.70** | Phase 1 (after caller audit) |
| 24 | `_BATTERS_TABLE_ALL_COLUMNS/_PRESETS` | 1892 | `ui/table_constants.py` | 5 | 5 | 4 | **4.70** | Phase 1 (after caller audit) |
| 25 | `_deployment_tier(player)` | 2337 | `ui/deployment_logic.py` | 4 | 5 | 4 | **4.40** | Phase 2 |
| 26 | `_deployment_lifecycle(player)` | 2358 | `ui/deployment_logic.py` | 4 | 5 | 4 | **4.40** | Phase 2 |
| 27 | `_player_photo_html(...)` | 2529 | `ui/player_display.py` | 3 | 5 | 4 | **4.10** | Phase 2 (after URL audit) |
| 28 | `_pitch_attack_tags(ctx, player)` | 2653 | `ui/pitch_display.py` | 3 | 5 | 3 | **3.85** | Phase 2 |
| 29 | `_intelligence_card_html(...)` | 2703 | `ui/card_builders.py` | 2 | 4 | 3 | **3.10** | Phase 3 |
| 30 | `_elite_card_html(...)` | 2943 | `ui/card_builders.py` | 2 | 4 | 3 | **3.10** | Phase 3 |

---

## Appendix B. Example Micro-Extraction Workflow

**Extraction: `_fmt_american(odds)` → `ui/formatters.py`**

**Step 1: Pre-Extraction Audit**
```bash
grep -n "_fmt_american" app.py
```
Confirm all callers are in app.py. Confirm no callers in other modules.

**Step 2: Create Target Module**
```python
# ui/formatters.py
def _fmt_american(odds) -> str:
    if odds is None:
        return "--"
    return f"+{odds}" if int(odds) > 0 else str(odds)
```
Ensure `ui/__init__.py` exists (empty file).

**Step 3: Update app.py**

Add import at top of app.py import block:
```python
from ui.formatters import _fmt_american
```
Remove the function definition from app.py (lines 1719–1722).

**Step 4: Immediate Validation**
```bash
python -c "from ui.formatters import _fmt_american; print(_fmt_american(+150))"
# Expected: +150
python -c "import app"
# Expected: no errors
streamlit run app.py
# Expected: app loads on http://localhost:8501
```

**Step 5: Runtime Observation**
- Navigate to MAIN route → confirm odds display correct
- Open player modal → confirm odds display in modal
- Navigate to JIG route → confirm odds display in JIG table
- Wait 30 minutes → confirm no rerender anomalies

**Step 6: Commit or Rollback Decision**
- CLEAN: proceed with documentation of successful extraction
- ANOMALY: rollback immediately (delete `ui/formatters.py`, restore function to app.py, delete import line)

---

## Appendix C. Example Rollback Scenario

**Scenario: `_stat_css` extracted; blank heatmap coloring observed during observation window**

**What happened:**
After extracting `_stat_css` to `ui/stat_colors.py`, the batter table renders without background colors. The `_apply_heatmap` function in app.py still references `_HEAT_COLS` which was also moved but not properly re-imported.

**Rollback sequence:**

1. Delete `ui/stat_colors.py`
2. Restore original function definitions to app.py at original line numbers
3. Remove import line from app.py: `from ui.stat_colors import ...`
4. Restart Streamlit: `streamlit run app.py`
5. Verify heatmap coloring restored: navigate to batter table, confirm colors appear
6. Document: "Extraction of `_stat_css` revealed that `_apply_heatmap` has a hidden dependency on `_HEAT_COLS` that was not included in the import line."
7. Update extraction plan: `_stat_css`, `_stat_badge`, `_edge_col`, `_HEAT_COLS`, and `_apply_heatmap` must move together as a complete group.

**Root cause:** `_HEAT_COLS` was listed as a separate extraction candidate, but `_apply_heatmap` (remaining in app.py) reads `_HEAT_COLS` directly. The constants and the function using them are tightly coupled. The corrected plan groups all of them together.

---

## Appendix D. Phase 1 Validation Checklist

Complete this checklist for every Phase 1 extraction before proceeding to the next.

**Extraction:** `_______________________`  
**Target Module:** `_______________________`  
**Date/Session:** `_______________________`

**Pre-Extraction:**
- [ ] Candidate confirmed in Approved Phase 1 Categories (Section 4)
- [ ] Candidate priority score ≥ 4.5
- [ ] All callers in app.py identified via `grep -n "function_name" app.py`
- [ ] Confirmed no callers in other modules
- [ ] Confirmed no session_state access in function body
- [ ] Confirmed no Streamlit API calls in function body
- [ ] Target module file does not yet exist (new module) OR target module previously validated

**Post-Extraction:**
- [ ] `python -c "import app"` — PASS / FAIL
- [ ] `streamlit run app.py` — PASS / FAIL (no exceptions)
- [ ] MAIN route loads correctly — PASS / FAIL
- [ ] JIG route loads correctly — PASS / FAIL
- [ ] INVESTIGATION route loads correctly — PASS / FAIL
- [ ] Player modal opens and closes cleanly — PASS / FAIL
- [ ] Batter table renders with heatmap colors — PASS / FAIL
- [ ] Shell badges render with correct tier colors — PASS / FAIL
- [ ] Pick rating labels display correctly — PASS / FAIL

**Observation Window (minimum 30 minutes):**
- [ ] 5-minute check: no rerender loop warnings in console — CLEAN / ANOMALY
- [ ] 15-minute check: route navigation produces no route reset — CLEAN / ANOMALY
- [ ] 30-minute check: investigation atmosphere persists across navigation — CLEAN / ANOMALY

**Decision:**
- [ ] PROCEED to next extraction
- [ ] ROLLBACK — reason: `_______________________`

---

## Appendix E. Phase 2 Gate Approval Checklist

Complete before authorizing any Phase 2 extraction.

**Phase 1 Completion Gate:**
- [ ] Minimum 5 extraction groups completed — COUNT: ___
- [ ] All 5 top-ranked extractions (Section 11.2) completed
- [ ] No rollback required in last 3 extraction sessions
- [ ] 7-day stability window with zero Phase 1-related defects
- [ ] All primary routes tested after all Phase 1 extractions — PASS
- [ ] All shell badge states verified after all Phase 1 extractions — PASS
- [ ] All tactical card render paths verified after all Phase 1 extractions — PASS

**State Governance Prerequisites:**
- [ ] Complete `st.session_state` key map exists (all keys, writers, readers, initialization order)
- [ ] Key map validated against actual runtime behavior (not inferred from code reading)
- [ ] All Cross-Write Keys flagged and excluded from Phase 2 scope

**Rollback Verification:**
- [ ] At least one rollback drill completed successfully
- [ ] Rollback time measured and confirmed < 60 seconds for Phase 1 targets
- [ ] Rollback path documented and operator can execute without Claude assistance

**Process Internalization:**
- [ ] Operator has completed minimum 3 observation windows without shortcuts
- [ ] Extraction pacing rule (one extraction group per session) has been followed consistently
- [ ] No extraction freeze conditions currently active

**Operator Sign-Off:**
- [ ] Modularization does not introduce phantom rerenders when pure functions moved — CONFIRMED
- [ ] Import structure changes do not affect Streamlit widget key resolution — CONFIRMED
- [ ] Observation window protocol is sufficient to catch defects before accumulation — CONFIRMED

**Authorization:** `_______________________ [Date]`

---

*Document end. Phase 1 Extraction Prioritization Doctrine v1. All runtime systems remain frozen. No production extraction authorized from this document.*
