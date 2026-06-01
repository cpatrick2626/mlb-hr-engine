# Modularization Dependency Audit Doctrine v1

**Document Class:** Architecture Governance  
**Phase:** Controlled Modularization — Phase 0 Audit  
**Status:** ACTIVE — Pre-Extraction Planning Only  
**Owner:** Claude (Architecture Governance)  
**Last Updated:** 2026-05-23  
**Preceding Doctrine:** `controlled_modularization_doctrine_v1.md`

---

## Governance Statement

No extraction of production modules is authorized until every system targeted for extraction has passed the full audit workflow defined in Section 10. This doctrine defines how that audit is performed, what evidence it must produce, and which systems are permanently forbidden from unilateral extraction.

All decisions in this doctrine supersede developer intuition. If a system feels "obviously safe to move," it must still complete the audit. Surprise coupling is the most common cause of modularization-induced regression.

---

## 1. Purpose of Dependency Auditing

### 1.1 Why Modularization Without Mapping Is Dangerous

Modularization without prior dependency mapping produces a class of defects that are difficult to detect and expensive to recover from:

**Silent contract breakage.** When a caller imports a module's output via shared state rather than a direct import, changes to the output structure break callers without generating import errors. The system appears to run but renders garbage or crashes at a UI path not covered by smoke testing.

**Rerender cascade injection.** Streamlit rerenders the entire app on any `st.session_state` mutation. A module extracted with its own internal state mutations will trigger cascading rerenders unless the full rerender graph is mapped and accounted for in the extraction design.

**Cache identity loss.** `@st.cache_data` keyed by function identity. When a decorated function is moved to a new module path, its cache key changes, invalidating all warm caches and forcing cold load paths on every user session until the TTL expires.

**Circular import introduction.** Extraction frequently creates circular imports in Python when a "utility" module is moved to a layer that already imports from the module's original location. Python's import system raises `ImportError` at runtime, not at write time.

**Tactical coupling fragmentation.** UI rendering logic for the HVY modifier, JIG intel, and tactical threat card depends on pick data structures being available in a specific shape at a specific render phase. Splitting these systems without mapping their data dependencies produces blank UI panels or incorrect renders without any Python exception.

### 1.2 The Hidden Dependency Problem

**Definition:** A hidden dependency is a dependency that is not expressed via a Python `import` statement but that still couples two systems.

Known hidden dependencies in this codebase:

| Caller | Dependency | Mechanism | Line |
|--------|-----------|-----------|------|
| `app.py` | `pipeline.py` output structure | `st.session_state["data"]` populated by hydration callback | ~1654 |
| `app.py` | `filter_controls.py` | Shared session_state keys (no import required) | Multiple |
| `app.py` | `nav_state.py` | Shared session_state navigation keys | ~667 |
| `app.py` | `navigation_continuity.py` | Route restoration reads state at startup | ~689 |
| `output/ranker.py` | `tracking/adaptive_weights.py` | Weights injected via pipeline, not direct import | pipeline.py |

Hidden dependencies **cannot be detected by reading `import` statements alone.** They require tracing `st.session_state` key access patterns and data structure field references.

---

## 2. Dependency Classification System

Every module in the system is assigned exactly one classification. Classifications are mutually exclusive and ordered by extraction complexity.

### Classification Definitions

**ISOLATED**  
No shared state. No session_state access. No cross-module imports beyond `config.py` and stdlib. Self-contained pure functions. Can be extracted or moved without audit.

Examples: `portfolio/metrics.py`, `engine/market.py`, `engine/ev.py`

---

**LOW COUPLING**  
Imports `config.py` and one or two peer modules. No session_state access. No `@st.cache_data`. Output is a primitive type or simple dict. Safe to extract with lightweight audit (import graph check only).

Examples: `engine/sizing.py`, `engine/vig.py`, `data/park_factors.py`, `clients/weather.py`

---

**MEDIUM COUPLING**  
Imports 3–6 peer modules. May import from `engine/` and `clients/` layers. No session_state access. No cache decorators. Output consumed by pipeline. Requires full import graph audit before extraction.

Examples: `clients/statcast.py`, `clients/odds_api.py`, `engine/filters.py`, `output/parlay.py`, `backtest/runner.py`

---

**HIGH COUPLING**  
Imports 7+ peer modules OR is imported by 7+ modules. May produce structured output consumed by multiple downstream callers. Requires import graph audit + downstream caller audit + rollback plan.

Examples: `pipeline.py`, `engine/probability.py`, `output/ranker.py`, `tracking/pick_tracker.py`, `tracking/adaptive_weights.py`

---

**CRITICAL SHARED STATE**  
Accesses or mutates `st.session_state`. Any extraction of this module risks rerender cascade or key collision. Requires full session_state audit, rerender graph analysis, and operator review before any extraction is attempted.

Examples: `filter_controls.py`, `nav_state.py`, `navigation_continuity.py`, `investigation_state.py`, `components/sub_room_rail.py`

---

**RUNTIME-GOVERNED**  
Cannot be extracted under any circumstances without full runtime architecture redesign approved at governance level. Extraction would require simultaneous changes to routing, session_state schema, cache identity, and hydration logic.

Examples: `app.py` (orchestration layer), `api/main.py` (API entrypoint), `api/cache.py` (cloud pick cache)

---

### Module Classification Registry

| Module | Classification | Rationale |
|--------|---------------|-----------|
| `config.py` | RUNTIME-GOVERNED | 44+ importers; hub of entire system |
| `app.py` | RUNTIME-GOVERNED | Orchestration + session_state owner |
| `pipeline.py` | HIGH COUPLING | 8 callers; hidden dependency from app.py |
| `engine/probability.py` | HIGH COUPLING | Core model; imported by pipeline, backtest, portfolio |
| `engine/calibration.py` | HIGH COUPLING | Platt params; called by pipeline after probability |
| `engine/filters.py` | MEDIUM COUPLING | 7-rule filter; consumed by pipeline and ranker |
| `engine/ev.py` | LOW COUPLING | Pure math; 2 callers |
| `engine/market.py` | LOW COUPLING | Odds conversion; 3 callers |
| `engine/sizing.py` | LOW COUPLING | Kelly math; 2 callers |
| `engine/vig.py` | LOW COUPLING | Dynamic vig; 2 callers |
| `engine/trust.py` | LOW COUPLING | Trust scoring; 2 callers |
| `output/ranker.py` | HIGH COUPLING | Adaptive weights integration; consumed by pipeline + app |
| `output/parlay.py` | MEDIUM COUPLING | 3 callers (pipeline, main, app indirect) |
| `output/display.py` | LOW COUPLING | CLI table formatter; 1 caller |
| `clients/mlb_stats.py` | MEDIUM COUPLING | Core data source; pipeline + probability |
| `clients/statcast.py` | MEDIUM COUPLING | Barrel/exit velo; pipeline + probability |
| `clients/odds_api.py` | MEDIUM COUPLING | Odds fetch; pipeline + main |
| `clients/weather.py` | LOW COUPLING | Weather factors; 2 callers |
| `clients/pitch_mix.py` | LOW COUPLING | Display-only signal; 2 callers |
| `clients/arsenal.py` | LOW COUPLING | Arsenal data; 2 callers |
| `clients/pull_air.py` | MEDIUM COUPLING | Uses pipeline data; 3 callers |
| `clients/session_utils.py` | CRITICAL SHARED STATE | Session management |
| `data/park_factors.py` | LOW COUPLING | Static data; 3 callers |
| `tracking/pick_tracker.py` | HIGH COUPLING | 38-field schema; 6+ callers |
| `tracking/clv.py` | MEDIUM COUPLING | CLV log; 4 callers |
| `tracking/pnl.py` | MEDIUM COUPLING | P&L; 3 callers |
| `tracking/adaptive_weights.py` | HIGH COUPLING | Injected into pipeline + ranker |
| `tracking/drift_monitor.py` | LOW COUPLING | Analytics only; 2 callers |
| `tracking/line_snapshots.py` | LOW COUPLING | Append-only CSV; 2 callers |
| `tracking/data_integrity.py` | LOW COUPLING | Validation only; 2 callers |
| `tracking/auto_learn.py` | MEDIUM COUPLING | Weight learning; 3 callers |
| `tracking/sheets.py` | LOW COUPLING | GSheets sync; 1 caller |
| `tracking/notify.py` | LOW COUPLING | Notifications; 1 caller |
| `tracking/line_movement.py` | LOW COUPLING | Movement tracking; 1 caller |
| `tracking/strategy_log.py` | LOW COUPLING | Strategy logging; 1 caller |
| `portfolio/optimizer.py` | MEDIUM COUPLING | Greedy optimizer; 3 callers |
| `portfolio/correlation.py` | LOW COUPLING | Correlation math; 2 callers |
| `portfolio/exposure.py` | LOW COUPLING | HHI profiling; 2 callers |
| `portfolio/sizing.py` | LOW COUPLING | 9 strategies; 2 callers |
| `portfolio/metrics.py` | ISOLATED | Pure math; no external deps |
| `backtest/runner.py` | MEDIUM COUPLING | Historical scorer; 4 callers |
| `backtest/calibration.py` | LOW COUPLING | Platt fitting; 2 callers |
| `backtest/outcomes.py` | LOW COUPLING | Result aggregation; 2 callers |
| `backtest/feature_importance.py` | LOW COUPLING | Signal analysis; 1 caller |
| `strategies/arbitrage.py` | LOW COUPLING | Cross-book arb; 1 caller |
| `strategies/hedge.py` | LOW COUPLING | Hedge sizing; 1 caller |
| `strategies/stacks.py` | LOW COUPLING | Lineup stacking; 1 caller |
| `strategies/staking.py` | LOW COUPLING | Bankroll allocation; 1 caller |
| `strategies/correlation.py` | LOW COUPLING | Corr-aware limits; 1 caller |
| `strategies/value_decay.py` | LOW COUPLING | Line decay; 1 caller |
| `filter_controls.py` | CRITICAL SHARED STATE | Filter UI state; session_state owner |
| `nav_state.py` | CRITICAL SHARED STATE | Navigation persistence; session_state owner |
| `navigation_continuity.py` | CRITICAL SHARED STATE | Route restoration; startup state reader |
| `investigation_state.py` | CRITICAL SHARED STATE | Modal/investigation state; session_state owner |
| `components/sub_room_rail.py` | CRITICAL SHARED STATE | Sidebar nav; renders + reads state |
| `api/main.py` | RUNTIME-GOVERNED | API entrypoint |
| `api/cache.py` | RUNTIME-GOVERNED | Cloud pick cache |
| `api/auth.py` | HIGH COUPLING | Beta gates; 3 callers |
| `api/cron.py` | MEDIUM COUPLING | Cron trigger; 2 callers |

---

## 3. Extraction Readiness Scoring

### 3.1 Scoring Factors

Each factor is scored 0–3. Total score determines readiness tier.

| Factor | 0 (Low Risk) | 1 (Moderate) | 2 (High Risk) | 3 (Critical) |
|--------|-------------|-------------|--------------|-------------|
| **session_state access** | None | Reads only | Reads + writes | Writes during render |
| **Cache ownership** | No decorators | TTL-cached, single site | Multi-site cached | Cache identity tied to routing |
| **Routing access** | None | Reads route | Writes route | Owns route system |
| **Rerender sensitivity** | None | Triggers on explicit action | Triggers on data load | Triggers on every render |
| **Import density** | 0–2 importers | 3–5 importers | 6–10 importers | 11+ importers |
| **Tactical coupling** | None | Display signal | Scoring input | Ranking/filter gate |

### 3.2 Readiness Tiers

| Score | Tier | Extraction Status |
|-------|------|-----------------|
| 0–3 | **SAFE** | Extract freely after import graph check |
| 4–7 | **CAUTION** | Full audit required; rollback plan required |
| 8–12 | **DANGEROUS** | Operator review required; phased extraction only |
| 13–18 | **FORBIDDEN** | No extraction without full architecture redesign |

### 3.3 Module Readiness Scores

| Module | SS | Cache | Route | Rerender | Import | Tactical | **Total** | **Tier** |
|--------|----|-------|-------|----------|--------|---------|-----------|---------|
| `portfolio/metrics.py` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | SAFE |
| `engine/market.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `engine/ev.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `data/park_factors.py` | 0 | 0 | 0 | 0 | 1 | 1 | **2** | SAFE |
| `engine/sizing.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `clients/weather.py` | 0 | 0 | 0 | 0 | 1 | 1 | **2** | SAFE |
| `tracking/drift_monitor.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `portfolio/correlation.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `portfolio/exposure.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `backtest/calibration.py` | 0 | 0 | 0 | 0 | 1 | 0 | **1** | SAFE |
| `engine/filters.py` | 0 | 0 | 0 | 0 | 2 | 2 | **4** | CAUTION |
| `clients/statcast.py` | 0 | 0 | 0 | 0 | 2 | 2 | **4** | CAUTION |
| `backtest/runner.py` | 0 | 0 | 0 | 0 | 2 | 1 | **3** | SAFE |
| `output/ranker.py` | 0 | 0 | 0 | 1 | 2 | 3 | **6** | CAUTION |
| `tracking/pick_tracker.py` | 0 | 0 | 0 | 0 | 2 | 1 | **3** | SAFE |
| `tracking/adaptive_weights.py` | 0 | 0 | 0 | 1 | 2 | 2 | **5** | CAUTION |
| `engine/probability.py` | 0 | 0 | 0 | 0 | 3 | 3 | **6** | CAUTION |
| `pipeline.py` | 1 | 1 | 0 | 2 | 3 | 2 | **9** | DANGEROUS |
| `filter_controls.py` | 3 | 0 | 1 | 2 | 1 | 1 | **8** | DANGEROUS |
| `nav_state.py` | 3 | 0 | 2 | 2 | 1 | 0 | **8** | DANGEROUS |
| `navigation_continuity.py` | 3 | 0 | 3 | 2 | 1 | 0 | **9** | DANGEROUS |
| `components/sub_room_rail.py` | 2 | 0 | 3 | 2 | 1 | 1 | **9** | DANGEROUS |
| `app.py` | 3 | 3 | 3 | 3 | 3 | 3 | **18** | FORBIDDEN |
| `config.py` | 0 | 0 | 0 | 0 | 3 | 3 | **6**\* | FORBIDDEN |
| `api/main.py` | 2 | 2 | 2 | 1 | 2 | 1 | **10** | DANGEROUS |

\* `config.py` score of 6 understates its true risk. As the system-wide constant hub (44+ importers), any extraction or split of `config.py` produces immediate cascading breakage. Manually classified FORBIDDEN regardless of score.

---

## 4. app.py Ownership Mapping Doctrine

`app.py` owns seven distinct functional layers. These layers are co-located in a single file by design (Streamlit architectural requirement). Future modularization may extract individual layers as import-safe components, but only after session_state and cache audits are complete for each layer.

### Layer Definitions

**Orchestration Layer** (lines ~1–200, ~1620–1730)  
Owns the Streamlit page configuration, session_state initialization, hydration lifecycle, and date picker. Single point of entry. Controls when `pipeline.load_game_data()` is called and how results are stored in session_state. Nothing may call `pipeline.load_game_data()` except through this layer.

**Routing Layer** (lines ~655–735)  
Owns `active_route` and `_PENDING_WORKSPACE_ROUTE_KEY`. All workspace navigation passes through this layer. No other module may write these keys. Route restoration (from modal payloads) executes here at startup.

**State Layer** (lines ~300–600)  
Initializes all session_state keys with safe defaults. Defines the session_state schema. All 50+ keys have their canonical default values set here. Must execute before any UI rendering begins.

**Data Layer** (lines ~1620–1730)  
Hydration callback. Receives pipeline output dict and stores it in `session_state["data"]`. Manages `cache_key`, `data_loaded_at`, and `hydration_fingerprint`. No business logic — pure data handoff.

**Rendering Layer** (lines ~1730–end, per-tab)  
Consumes session_state picks and renders workspace UI. Calls sub-components. Manages tab routing. Each workspace tab is a distinct render path. Rendering layer must not mutate session_state except via explicit widget callbacks.

**Tactical Layer** (HVY modifier, JIG, Threat Card sections)  
Renders the high-density tactical UI surfaces. Depends on ranker output structure. Depends on pick_by_tab groupings. Owns compact mode state, pitch_mix_expanded flags, and tactical filter fingerprints. Sensitive to pick structure changes.

**Helper Layer** (utility functions within app.py)  
Pure functions used by rendering and tactical layers. No session_state access. Candidates for future extraction once session_state audit confirms no hidden state dependencies.

---

## 5. session_state Audit Standards

### 5.1 State Ownership Requirements

Every session_state key must have exactly one owner. Ownership means: only the owning system may set the key's default value and only the owning system may initiate writes to that key. Other systems may read but not write.

Before any extraction, the auditor must produce:

- **Key inventory:** Full list of all `st.session_state` key names accessed in the module being extracted.
- **Write site map:** Every line where each key is assigned (`st.session_state[k] = ...`).
- **Read site map:** Every line where each key is read (`x = st.session_state[k]` or `st.session_state.get(k, ...)`).
- **Owner identification:** For each key, which module is the canonical owner (initializer + primary writer).

### 5.2 State Mutation Tracing Requirements

Mutations that occur during a render cycle (outside of a widget callback) must be flagged. These mutations trigger rerenders. The auditor must document:

- The trigger condition (what causes the mutation)
- The downstream effect (what rerenders as a result)
- Whether a guard (fingerprint, flag, or equality check) prevents cascade

### 5.3 Hidden Coupling Detection

Hidden coupling via session_state occurs when:

1. Module A writes `st.session_state["key"]`
2. Module B reads `st.session_state["key"]`
3. Neither module imports the other

This coupling is invisible to import analysis. Detect by:
- Full-text search for each session_state key across all Python files
- Verifying every reader has a documented dependency on the writer

### 5.4 Shared Key Collision Prevention

Before extraction, verify that the module's session_state keys do not collide with keys owned by other modules. Key naming collisions produce subtle state corruption bugs. Document key namespacing conventions:

- Navigation keys: `active_route`, `_PENDING_WORKSPACE_ROUTE_KEY`
- Filter keys: `min_ev`, `min_edge`, `min_confidence`, `cutoff_utc_hour`
- Modal keys: `selected_player_modal`, `show_modal`, `modal_source_tab`, `modal_source_section`
- Cache keys: `data`, `cache_key`, `data_loaded_at`, `hydration_fingerprint`
- Tactical keys: `tac_filter_fp`, `tac_ranked`, `tcc_compact_mode`
- Bet slip keys: `fd_slip`, `fd_slip_sources`, `clear_slip_confirm`
- Table keys: `table_col_preset_{scope}`, `table_visible_cols_{scope}`

---

## 6. Cache Governance Audit

### 6.1 Cache Ownership Tracing

Seven `@st.cache_data` decorators exist in `app.py`. Before any extraction involving a cached function:

1. Identify the function's full qualified path (used as cache key)
2. Identify all callers
3. Identify the TTL and whether TTL expiry is acceptable in the extraction context
4. Document what triggers invalidation beyond TTL

### 6.2 Cache Invalidation Dependencies

Some cached functions in `app.py` implicitly depend on `st.session_state` values passed as arguments (used as cache-key parameters). Moving the function changes its `__qualname__`, which changes the cache key, which forces a cold load on all user sessions. This is not always harmful but must be a documented decision, not an accident.

### 6.3 Function Identity Risks

`@st.cache_data` uses the function's module path + name as part of its cache key. Renaming a module or moving a function to a new module invalidates all cached results for that function. This is a one-time cost per deployment but can produce user-visible spinners on first load after extraction. Document this as expected behavior in the extraction rollout plan.

### 6.4 Extraction Hazards for Cached Functions

Do not extract a cached function if:
- It reads from `st.session_state` inside its body (violates cache purity)
- It calls another cached function (double-caching produces unpredictable TTL behavior)
- Its output is consumed by the routing layer or state initialization layer

---

## 7. Render-Chain Analysis

### 7.1 Rerender-Sensitive Regions

Streamlit rerenders the entire app on any `st.session_state` mutation. The following regions in `app.py` are rerender-sensitive because they write to session_state during the render cycle:

| Region | Line Range | State Written | Guard Present |
|--------|-----------|--------------|--------------|
| Route restoration | ~667–689 | `active_route`, `_PENDING_WORKSPACE_ROUTE_KEY` | Equality check before write |
| Route change handler | ~715–734 | `active_route` | Button callback (safe) |
| Hydration callback | ~1654–1704 | `data`, `cache_key`, `data_loaded_at`, `hydration_fingerprint` | `hydration_fingerprint` equality check |
| Pitcher map update | ~1670–1690 | `pitcher_map_at_load`, `pitcher_changes` | Timestamp comparison |
| Filter gate state | ~1122–1134 | Filter values | Widget callback (safe) |
| Tactical filter FP | ~tac_filter_fp | `tac_filter_fp`, `tac_ranked` | Fingerprint equality check |

### 7.2 Expensive UI Chains

These render paths are computationally expensive. Any extraction that disrupts their data supply will cause visible slowness or blank panels:

- **Elite Prospects tab:** Loads ranked picks from `session_state["data"]["picks_by_tab"]["elite"]`. If picks_by_tab structure changes, this tab renders blank with no error.
- **JIG (Pitcher Intel Grid):** Loads pitcher data from `session_state["data"]`. Requires `pitcher_map_at_load` to be populated. Renders empty table if pitcher data is missing.
- **Tactical HR Threat Card:** Reads `tac_ranked` (recomputed on filter change via `tac_filter_fp`). If `tac_ranked` is missing from session_state, entire card fails to render.
- **HVY Modifier panel:** Reads `pitch_mix` data from per-pick `hvy_modifier` field. If pick structure changes to omit this field, HVY panel renders "N/A" for all picks.

### 7.3 Spinner and Load Dependencies

Three spinner blocks in the hydration flow:

1. `"Loading picks from cache..."` — fires when `hydration_fingerprint` mismatch detected; calls `pipeline.load_game_data()`
2. `"Recalculating pitcher matchups..."` — fires when pitcher_map staleness detected
3. `"Rebuilding pick cache..."` — fires on full pipeline re-run (manual or date change)

Any extraction touching the hydration callback must preserve these spinner semantics.

### 7.4 Chained Component Dependencies

```
pipeline.load_game_data()
  → session_state["data"]
    → picks_by_tab["elite"] → Elite tab renderer
    → picks_by_tab["all"] → Full slate renderer
    → picks_by_tab["parlays"] → Parlay renderer
    → all_picks → Tactical threat card (tac_ranked)
    → all_picks → Portfolio optimizer input
    → all_picks → Bet slip (fd_slip)
    → games → JIG pitcher intel
    → metadata → Run stats display
```

Any structural change to the pipeline output dict propagates silently through all branches above. This is the primary modularization risk in the system.

---

## 8. Tactical UX Dependency Preservation

### 8.1 Preserved Systems

The following tactical UX systems must remain fully functional after any modularization. They are not candidates for simplification or structural change.

**Shell Pacing**  
The deploy tray and queue panel (`_shell_deploy_tray_open`, `_shell_queue_open`) provide the primary workspace control surface. Their expand/collapse state must persist across rerenders.

**Escalation Hierarchy**  
Picks are displayed in ranked tiers (S/A/B/C confidence). The escalation hierarchy must be preserved: picks that score below a tier threshold must not appear in that tier's rendering surface. Any extraction of ranking logic must maintain tier output compatibility.

**Cinematic Density**  
The tactical card and JIG panel render at high information density. Column ordering, compact mode, and section expansion state are deliberate UX design decisions. Modularization of rendering helpers must not alter default column order or visible column sets.

**Tactical Flow Continuity**  
The player investigation flow (click pick → modal → investigation → backlink to source tab) passes source tab and section information via session_state. The full chain:
```
table row click → selected_player_modal + show_modal + modal_source_tab + modal_source_section
  → modal renders → "back" → route restored to modal_source_tab
```
Any extraction touching modal state or routing must preserve this chain.

### 8.2 Coupling Preservation Rules

- Do not extract HVY modifier rendering from the tab renderer that calls it. The HVY modifier reads pick-level fields inline; extracting it to a separate module requires passing the full pick dict as argument, which is acceptable, but the calling convention must be documented.
- Do not merge the JIG's compact/detail mode toggle with any other display mode. JIG has its own session_state key (`jig_port_mode_sel`) that must remain independent.
- Do not remove the `tcc_compact_mode` guard that prevents the tactical card from rerendering when compact mode has not changed (`_tcc_compact_prev`).

---

## 9. Import Dependency Doctrine

### 9.1 Circular Import Prevention

Python resolves circular imports at module load time, not at call time. The following import layer order must be strictly maintained. Lower-numbered layers may only import from layers with equal or lower numbers.

```
Layer 0: stdlib, third-party (pandas, numpy, streamlit, requests)
Layer 1: config.py (constants only — no imports from this repo)
Layer 2: data/ (park_factors — imports config)
Layer 3: engine/ (imports config, data)
Layer 4: clients/ (imports config, data, engine)
Layer 5: output/ (imports config, engine)
Layer 6: tracking/ (imports config, engine, output)
Layer 7: portfolio/ (imports config, engine, tracking)
Layer 8: backtest/ (imports config, engine, tracking, portfolio)
Layer 9: pipeline.py (imports all layers 1–8)
Layer 10: main.py, api/ (imports pipeline + tracking)
Layer 11: app.py (imports config + routing helpers; receives pipeline output via session_state)
```

Any proposed extraction that would require a layer to import from a higher layer number must be rejected or restructured.

### 9.2 Service Boundary Rules

- `engine/` modules must not import from `clients/`. Clients fetch data; engine processes it. Pipeline is the integration point.
- `clients/` modules must not import from `output/`. Output is for display; clients are for data access.
- `tracking/` modules must not import from `portfolio/`. Portfolio consumes tracking; not the reverse.
- `app.py` must not import `pipeline.py` directly. Pipeline output enters app via session_state through the hydration callback.

### 9.3 UI vs Engine Separation

No `import streamlit` statement is permitted outside of: `app.py`, `components/`, `filter_controls.py`, `nav_state.py`, `navigation_continuity.py`, `investigation_state.py`, `strategies_ui.py`, `api/main.py`.

Engine, client, tracking, and portfolio modules must be Streamlit-agnostic. If a module currently imports streamlit for any reason other than those files listed above, that is a violation that must be resolved before extraction.

---

## 10. Extraction Readiness Workflow

This is the mandatory step-by-step audit process that must be completed and documented before any module is extracted into a new location.

### Step 1 — Identify Candidate Module

- Record module path, file size, and classification tier
- State the reason extraction is desired (testability, separation of concerns, deployment split)
- Record extraction readiness score from Section 3

If score is FORBIDDEN: stop. Escalate to governance.  
If score is DANGEROUS: escalate to operator review before proceeding.

### Step 2 — Map All Import Dependencies

- List every module that imports the candidate (importers)
- List every module the candidate imports (dependencies)
- Verify no importers are in a lower layer than the candidate (layer violation check)
- Verify no circular import would be introduced by the move

Deliverable: dependency table (module → imports → imported-by)

### Step 3 — Map session_state Accesses

- Full-text search for `st.session_state` in the candidate file
- Document every key read and every key written
- Identify the owner of each key accessed
- Verify no key write occurs during the render cycle without a guard

Deliverable: session_state key table (key → read/write → owner → guard)

### Step 4 — Map Cache Decorators

- List all `@st.cache_data` or `@st.cache_resource` decorators in the candidate
- Document TTL, callers, and cache key implications of the move
- Confirm no cached function reads session_state internally

Deliverable: cache decorator table (function → TTL → callers → post-move key change)

### Step 5 — Identify Rerender Exposure

- Identify whether the candidate writes session_state during render (not in callback)
- If yes: document the guard that prevents cascade
- Confirm extraction would not remove or bypass that guard

Deliverable: rerender exposure statement (none / guarded / unguarded — unguarded blocks extraction)

### Step 6 — Identify Rollback Path

- Document how to revert the extraction if it causes regression
- Confirm the revert requires only: restoring the file to its original path and updating import references
- If revert requires session_state schema migration or cache invalidation: flag as high-risk rollback

Deliverable: rollback plan (file restore + import list + any migration steps)

### Step 7 — Validate Isolation

- Run existing test suite (if any)
- Manually verify the primary render path that depends on the candidate
- Confirm pick output structure is unchanged (run `python main.py --date [recent]` and diff output)

Deliverable: isolation validation report (tests passed / UI paths verified / output unchanged)

### Step 8 — Operator Checkpoint

- Present all deliverables from Steps 1–7 to the owning operator
- Receive explicit written approval before committing the extraction
- Record approval in the extraction decision log

---

## 11. Protected Systems Registry Expansion

The following systems are added to the protected systems registry established in `controlled_modularization_doctrine_v1.md`. These additions reflect the dependency audit findings.

| System | Owner | Reason | Min Extraction Phase | Validation Required |
|--------|-------|--------|---------------------|-------------------|
| `app.py` — Orchestration Layer | Claude + Operator | FORBIDDEN tier; Streamlit entrypoint | Never without redesign | N/A |
| `app.py` — Routing Layer | Claude | Owns active_route; session_state singleton | Phase 5+ | Full session audit |
| `app.py` — Hydration Callback | Claude | Hidden pipeline dependency; fingerprint guard | Phase 4+ | Pipeline contract doc |
| `pipeline.py` output structure | Claude | Implicit contract with 8 callers | Phase 3+ | TypedDict definition first |
| `config.py` constant hub | Claude | 44+ importers; system-wide coupling | Never split without staged migration | Layer-by-layer constant extraction |
| `filter_controls.py` | Operator | CRITICAL SHARED STATE; filter key owner | Phase 3+ | Full session_state audit |
| `nav_state.py` | Operator | CRITICAL SHARED STATE; navigation key owner | Phase 4+ | Route restoration test |
| `navigation_continuity.py` | Operator | CRITICAL SHARED STATE; startup state reader | Phase 4+ | Route restoration test |
| `investigation_state.py` | Operator | Modal state owner; investigation flow | Phase 3+ | Modal flow end-to-end test |
| `tracking/adaptive_weights.py` | Claude | Injected into pipeline + ranker; weight integrity | Phase 2+ | Backtest output delta check |
| `output/ranker.py` | Claude | Tactical tier escalation owner | Phase 2+ | Tier distribution diff |
| JIG compact/detail mode | Operator | `jig_port_mode_sel`; independent of other display modes | Phase 3+ | JIG render test |
| Tactical threat card compact guard | Operator | `_tcc_compact_prev`; prevents rerender cascade | Phase 3+ | Rerender trace |
| Player investigation chain | Operator | 4-key session_state chain; backlink routing | Phase 4+ | Full modal flow test |

---

## 12. Audit Deliverables Standard

Every extraction audit must produce exactly these artifacts before extraction is approved:

### 12.1 Dependency Map

Format: markdown table with columns — Module | Imports | Imported By | Layer | Classification

Scope: candidate module + all first-degree neighbors.

### 12.2 Extraction Report

Sections:
1. Candidate module and readiness score
2. Import dependency findings
3. session_state audit findings
4. Cache audit findings
5. Rerender exposure findings
6. Identified risks (enumerated, severity-tagged)
7. Recommended extraction approach
8. Operator approval record

### 12.3 Rollback Plan

Format: numbered step-by-step procedure. Must be executable by any team member without prior context. Maximum 10 steps.

### 12.4 Risk Summary

Format: table with columns — Risk | Severity (LOW/MED/HIGH/CRITICAL) | Mitigation | Owner

Maximum 10 rows. If more than 10 distinct risks are identified, escalate to DANGEROUS or FORBIDDEN tier.

### 12.5 Operator Checkpoints

Define explicit pause points where operator review is required before proceeding:
- After Step 1 if score is DANGEROUS
- After Step 2 if circular import risk detected
- After Step 4 if cache identity change confirmed
- After Step 5 if unguarded rerender mutation found
- Before Step 8 always

---

## 13. Future Audit Automation Vision

This section documents future tooling that does not yet exist. It informs tooling investment priorities but does not authorize any current work.

### 13.1 Dependency Graph Generation

A static analysis script (`analyze_imports.py`) could parse all Python files in the repo, extract import statements, and generate a directed dependency graph (DOT format or JSON). This graph would make Section 2's classification registry auto-maintainable. Priority: medium.

### 13.2 Rerender Tracing

A runtime instrumentation layer could log every `st.session_state` write during a Streamlit session, tag it with the calling function and line, and report which writes triggered rerenders (via Streamlit's script runner). This would replace the manual rerender exposure analysis in Step 5. Priority: high (most labor-intensive manual step).

### 13.3 State Mutation Logging

`tracking/data_integrity.py` could be extended with a session_state audit mode: log all key writes during a session and produce a key ownership report. Would detect hidden coupling violations automatically. Priority: medium.

### 13.4 Extraction Readiness Scoring Automation

The six scoring factors in Section 3.1 could be computed from static analysis (import density, cache decorator count, session_state access count) and runtime analysis (rerender trigger frequency). A script accepting a module path as input would return the readiness score and tier. Priority: low (manual scoring is sufficient at current extraction cadence).

---

## Appendix A — Extraction Risk Matrix

| Risk | Trigger Condition | Severity | Detection Method | Mitigation |
|------|-----------------|----------|-----------------|-----------|
| Silent pipeline contract break | pipeline output dict key removed/renamed | CRITICAL | app.py KeyError at runtime on specific tab | TypedDict definition; integration smoke test |
| Cache identity loss | Decorated function moved to new module | HIGH | Cold load on all user sessions after deploy | Document as expected; deploy off-peak |
| Circular import | Layer violation (higher layer imports lower after move) | HIGH | `ImportError` at startup | Layer diagram review before move |
| Rerender cascade | Unguarded session_state write during render | HIGH | Infinite rerender loop; Streamlit timeout | Fingerprint guard required |
| session_state key collision | Two modules write same key with different semantics | HIGH | Intermittent state corruption | Key ownership registry; namespacing |
| Tactical rendering blank | picks_by_tab structure change | MED | UI panel renders empty; no error | Output structure diff before/after |
| HVY modifier N/A | `hvy_modifier` field missing from pick dict | MED | All HVY cells show "N/A" | Pick structure regression test |
| Modal backlink broken | `modal_source_tab` key missing | MED | "Back" button navigates to wrong tab | Modal flow end-to-end test |
| Adaptive weights drift | `tracking/adaptive_weights.py` isolation changes | MED | Ranker composite scores shift silently | Backtest output delta check |
| Import layer violation | New module imports from higher-numbered layer | LOW | No immediate error; maintainability risk | Layer diagram review |

---

## Appendix B — Example Dependency Audit Template

```markdown
## Dependency Audit: [module/path.py]

**Date:** YYYY-MM-DD  
**Auditor:** [Name]  
**Extraction Readiness Score:** [0–18]  
**Tier:** [SAFE / CAUTION / DANGEROUS / FORBIDDEN]

### Imports (this module imports)
| Module | Layer | Purpose |
|--------|-------|---------|
| config | 1 | Constants |
| ... | ... | ... |

### Importers (this module is imported by)
| Module | Layer | How Used |
|--------|-------|---------|
| pipeline | 9 | Calls function X |
| ... | ... | ... |

### session_state Keys
| Key | Access Type | Owner | Guard |
|-----|------------|-------|-------|
| N/A | — | — | — |

### Cache Decorators
| Function | TTL | Callers | Post-Move Key Change |
|---------|-----|---------|---------------------|
| N/A | — | — | — |

### Rerender Exposure
[None / Guarded (describe guard) / Unguarded (blocks extraction)]

### Identified Risks
| Risk | Severity | Mitigation |
|------|---------|-----------|
| ... | ... | ... |

### Rollback Plan
1. Restore [module] to [original path]
2. Revert import in [callers]
3. Verify with `python main.py`

### Operator Approval
- [ ] Approved by: [Name] on [Date]
```

---

## Appendix C — Example Protected System Mapping

```markdown
## Protected System: pipeline.py Output Contract

**Owner:** Claude (Architecture Governance)  
**Classification:** HIGH COUPLING  
**Extraction Readiness:** DANGEROUS (score: 9)  
**Min Extraction Phase:** Phase 3+

### Output Structure (current)
```python
{
    "games": list[dict],          # schedule + lineups
    "all_picks": list[dict],      # fully-modeled picks
    "picks_by_tab": {
        "elite": list[dict],
        "all": list[dict],
        "parlays": list[dict],
        # ... tab-name keys
    },
    "metadata": dict              # run stats
}
```

### Callers and Access Patterns
| Caller | Keys Accessed | Risk if Key Removed |
|--------|-------------|-------------------|
| app.py (hydration) | all | Full UI failure |
| app.py (Elite tab) | picks_by_tab["elite"] | Tab renders blank |
| app.py (JIG) | games, picks | Pitcher intel fails |
| app.py (tactical) | all_picks | Threat card fails |
| main.py | all | CLI output fails |
| api/cache.py | all | API returns 500 |

### Protection Rule
No field may be removed from this output structure without:
1. Updating all callers listed above
2. Verifying each render path
3. Operator approval
```

---

## Appendix D — Example Safe Extraction Walkthrough

**Module:** `portfolio/metrics.py`  
**Score:** 0 (SAFE)  
**Reason for extraction:** Move to standalone `analytics/` package for cross-project reuse

**Step 1 — Candidate**  
- Score: 0, Tier: SAFE, no governance escalation required

**Step 2 — Import Dependencies**  
- Imports: stdlib only (`math`, `statistics`)
- Imported by: `portfolio/optimizer.py`, `portfolio/sizing.py`, `analyze_portfolio.py`
- No layer violation: all callers are layer 7+; metrics.py has no layer-specific imports

**Step 3 — session_state**  
- Zero session_state accesses found. No audit required.

**Step 4 — Cache Decorators**  
- Zero cache decorators found. No audit required.

**Step 5 — Rerender Exposure**  
- None. Pure functions only.

**Step 6 — Rollback Plan**  
1. Move file back to `portfolio/metrics.py`
2. Update import in `portfolio/optimizer.py`: `from portfolio.metrics import ...`
3. Update import in `portfolio/sizing.py`: `from portfolio.metrics import ...`
4. Update import in `analyze_portfolio.py`
5. Run `python main.py` to verify

**Step 7 — Isolation Validation**  
- `python -m pytest tests/` (if tests cover portfolio)
- Run `python analyze_portfolio.py` and confirm output unchanged

**Step 8 — Operator Checkpoint**  
- Score 0 modules: operator notification recommended but approval not required
- Document in extraction log

**Result:** Extraction approved. Proceed.

---

## Validation Summary

**Doctrine Alignment Checks:**

- [x] No production code modified
- [x] No runtime systems touched
- [x] app.py structure unchanged
- [x] routing systems unchanged
- [x] session_state architecture unchanged
- [x] cache systems unchanged
- [x] No import rewrites introduced
- [x] tactical scoring systems unchanged
- [x] live rendering behavior unchanged
- [x] All protected runtime zones remain protected
- [x] Consistent with `controlled_modularization_doctrine_v1.md` sequencing
- [x] Migration sequencing respects runtime safety

**Highest-Risk Dependency Zones Identified:**

1. `app.py` ↔ `pipeline.py` hidden dependency via `session_state["data"]`
2. `config.py` as 44-importer hub — any split cascades system-wide
3. Hydration callback (lines ~1654–1704) — rerender guard must not be disturbed
4. Tactical UI render chain — silent structural break risk if pick dict changes
5. `navigation_continuity.py` — startup state reader; disruption causes route loss on reload

**Safest Extraction Candidates (SAFE tier, score 0–3):**

1. `portfolio/metrics.py` — score 0, pure math
2. `engine/market.py` — score 1, odds conversion
3. `engine/ev.py` — score 1, EV math
4. `engine/sizing.py` — score 1, Kelly math
5. `portfolio/correlation.py` — score 1, correlation math
6. `tracking/drift_monitor.py` — score 1, analytics only
7. `backtest/calibration.py` — score 1, Platt fitting
8. `data/park_factors.py` — score 2, static data
9. `clients/weather.py` — score 2, weather factors

**New Protected Systems Identified (added to registry):**

- `pipeline.py` output structure (implicit contract with 8 callers)
- `config.py` constant hub (44+ importers, FORBIDDEN classification)
- `tracking/adaptive_weights.py` (weight integrity gate for ranker)
- Player investigation 4-key session_state chain

**Extraction Readiness Framework:**

Scoring is defined in Section 3. Six factors (session_state, cache, routing, rerender, import density, tactical coupling), each 0–3. Tiers: SAFE (0–3), CAUTION (4–7), DANGEROUS (8–12), FORBIDDEN (13–18). Mandatory 8-step audit workflow defined in Section 10. All extractions require Step 8 operator checkpoint regardless of score.

---

*End of Doctrine v1 — modularization_dependency_audit_doctrine_v1.md*
