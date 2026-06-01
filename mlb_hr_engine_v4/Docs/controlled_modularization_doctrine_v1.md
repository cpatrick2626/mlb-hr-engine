# Controlled Modularization Doctrine v1
## MLB HR Engine v4 — Architecture Planning & Migration Governance

**Document Status:** Architecture Planning Only  
**Phase:** Division 09 — Controlled Modularization Planning  
**Owner:** Claude  
**Date:** 2026-05-23  
**Runtime Systems:** FROZEN (no production changes from this document)

---

## Table of Contents

1. [Why Modularization Is Required](#1-why-modularization-is-required)
2. [Core Modularization Philosophy](#2-core-modularization-philosophy)
3. [Protected Runtime Zones](#3-protected-runtime-zones)
4. [Recommended Architecture Hierarchy](#4-recommended-architecture-hierarchy)
5. [Execution Layer Doctrine](#5-execution-layer-doctrine)
6. [Migration Sequencing Plan](#6-migration-sequencing-plan)
7. [Low-Risk Early Candidates](#7-low-risk-early-candidates)
8. [High-Risk Systems](#8-high-risk-systems)
9. [Runtime Safety Doctrine](#9-runtime-safety-doctrine)
10. [Tactical UX Preservation Rules](#10-tactical-ux-preservation-rules)
11. [Validation Doctrine](#11-validation-doctrine)
12. [Rollback & Recovery](#12-rollback--recovery)
13. [Future-State Vision](#13-future-state-vision)

---

## 1. Why Modularization Is Required

### 1.1 Current Risk Profile

**app.py is 10,706 lines.** That is 27% of the entire v4 codebase (~39,000 lines) concentrated in a single file that owns:
- All Streamlit rendering
- Session state initialization
- Route dispatch
- Cache ownership
- Tactical scoring display
- Navigation persistence
- JIG/Main orchestration
- Portfolio optimization display
- Modal governance
- Multiple independent UI systems with no enforced boundaries

This concentration creates cascading failure risk: any change to app.py touches every system simultaneously.

### 1.2 Monolith Dangers

| Risk | Mechanism | Current Exposure |
|------|-----------|-----------------|
| Rerender amplification | State change in one section triggers full app rerender | HIGH — all session_state in shared scope |
| Import coupling | Circular or implicit dependencies hidden inside large file | ACTIVE — multiple systems share app.py scope |
| Ownership ambiguity | No clear module owns any given behavior | HIGH — 10k+ lines, no section isolation |
| Cognitive overload | No human can reason about 10k lines of entangled state | CONFIRMED — ongoing stabilization required |
| Test isolation impossibility | Cannot unit-test sections without loading entire app | HIGH |
| Change blast radius | Bug in display helper can corrupt routing | ACTIVE |

### 1.3 Scaling Limitations

- New tactical systems cannot be added without inserting into app.py, increasing entanglement
- React/Next.js frontend (frontend/) will diverge further from Streamlit without a shared contract layer
- Portfolio system, CLV intelligence, and deployment tracking are already separate modules — but their display lives in app.py, creating an ownership split
- Session 26 operational infrastructure (drift_monitor, data_integrity) is fully modular in tracking/ — but app.py display wrappers are not

### 1.4 Runtime Contamination Risks

Without modularization, the following contamination vectors remain active:

- **Rerender contamination:** A session_state write inside any function in app.py can cascade rerenders across unrelated views
- **Cache ownership confusion:** Multiple `@st.cache_data` decorators scattered through app.py create unpredictable cache invalidation behavior
- **Session fragmentation:** session_state keys defined inline at different call-stack depths can collide or be initialized out of order
- **Navigation corruption:** Route synchronization logic interleaved with display logic creates timing-dependent failures

---

## 2. Core Modularization Philosophy

### 2.1 Deterministic Architecture

Every module must have deterministic, observable behavior:
- Pure functions have no side effects
- Rendering functions accept state as arguments, never read session_state directly
- State mutations happen only in explicitly designated state modules
- Imports never cause side effects on load

### 2.2 Bounded Ownership

Each module owns exactly one domain. No module owns two domains. No domain is owned by two modules.

```
engine/       → probability math only
clients/      → external data fetch only
tracking/     → persistence and logging only
ui/           → rendering only (no state writes)
state/        → session_state lifecycle only
shell/        → routing and navigation only
tactical/     → tactical scoring display only
```

Ownership violations must be treated as bugs, not design decisions.

### 2.3 Isolated Execution Domains

Three execution domains must never directly call each other:

| Domain | What It Does | May Call |
|--------|-------------|----------|
| **Data** | Fetch, compute, transform | Nothing above data layer |
| **State** | Manage session_state lifecycle | Data layer only |
| **Render** | Display to Streamlit UI | State layer (read-only), Data layer |

Rendering functions must never write state. State modules must never render. Data modules must never read state.

### 2.4 Tactical Continuity Preservation

The cinematic tactical UX — escalation hierarchy, investigation atmosphere, threat card density, command flow — must survive modularization unchanged. Modularization is a structural change, not a UX change. If the operator cannot distinguish pre- and post-modularization behavior, the migration succeeded.

---

## 3. Protected Runtime Zones

The following systems must not be touched during modularization without explicit session-level authorization. Any extraction that requires modifying these systems is forbidden until late-phase migration with full validation.

### 3.1 Absolute Protection Zone

| System | File | Why Protected |
|--------|------|--------------|
| Active workspace ownership | app.py (dispatcher block) | Owns Main/JIG routing; any change risks null-route catastrophe |
| Active route synchronization | navigation_continuity.py | Stabilization-sensitive; owns cross-render persistence |
| Session state initialization | app.py (startup block) | Order-dependent; wrong init order = blank app |
| Cache ownership | app.py (@st.cache_data functions) | Streamlit cache tied to function identity; moving = cache bust |
| JIG/Main dispatcher logic | app.py (dispatch section) | Central routing arbiter; fragmentation = split-brain routing |
| Navigation persistence | nav_state.py + navigation_continuity.py | Multi-file coordination; extraction risks desync |

### 3.2 Stabilization-Sensitive Systems

These systems recently underwent stabilization work. Extraction requires prior art review of the stabilization commits.

- Rerender suppression guards (any `st.session_state` reads with `if key not in` guards)
- Modal persistence system
- Sort-state type safety (JIG sort)
- Investigation state machine (investigation_state.py)

### 3.3 Ownership Requirements

Any module that is extracted must immediately declare ownership via a module-level docstring:

```python
"""
Module: ui/threat_cards.py
Owns: HR threat card rendering
Reads: player data dicts (no session_state)
Writes: nothing
Calls: None above this layer
"""
```

---

## 4. Recommended Architecture Hierarchy

### 4.1 Target Directory Structure

```
mlb_hr_engine_v4/
├── app.py                    ← thin orchestrator only (~300 lines target)
├── pipeline.py               ← already clean (622 lines) — DO NOT TOUCH
├── config.py                 ← already clean (240 lines) — DO NOT TOUCH
├── main.py                   ← already clean (138 lines) — DO NOT TOUCH
│
├── shell/                    ← routing, navigation, workspace management
│   ├── router.py             ← route dispatch (extracted from app.py)
│   ├── workspace.py          ← active_workspace ownership
│   └── navigation.py         ← merge nav_state.py + navigation_continuity.py (far future)
│
├── state/                    ← session_state lifecycle management
│   ├── init.py               ← startup state initialization
│   ├── investigation.py      ← investigation_state.py (already exists, move reference)
│   └── filters.py            ← filter state (filter_controls.py already exists)
│
├── ui/                       ← pure rendering, no state writes
│   ├── threat_cards.py       ← HR threat card rendering
│   ├── full_slate.py         ← Full Slate view
│   ├── pitcher_suppression.py← pitcher suppression panel
│   ├── deployment.py         ← deployment tracking UI
│   ├── portfolio_ui.py       ← portfolio display
│   ├── clv_ui.py             ← CLV intelligence display
│   ├── parlay_ui.py          ← parlay builder display
│   └── modals.py             ← modal governance
│
├── tactical/                 ← tactical scoring, escalation, badges
│   ├── badges.py             ← escalation badge rendering
│   ├── archetypes.py         ← archetype scoring display
│   ├── hvy_display.py        ← HVY pitch mix display
│   └── scoring.py            ← composite score display helpers
│
├── engine/                   ← ALREADY CLEAN — no changes
├── clients/                  ← ALREADY CLEAN — no changes
├── tracking/                 ← ALREADY CLEAN — no changes
├── portfolio/                ← ALREADY CLEAN — no changes
├── strategies/               ← ALREADY CLEAN — no changes
├── output/                   ← ALREADY CLEAN — no changes
├── backtest/                 ← ALREADY CLEAN — no changes
├── data/                     ← ALREADY CLEAN — no changes
└── api/                      ← ALREADY CLEAN — no changes
```

### 4.2 Already-Extracted Root Modules (Good Patterns to Build On)

These files represent correct extraction precedents:

| File | Lines | Status |
|------|-------|--------|
| `navigation_continuity.py` | 485 | Correctly isolated — routing concern |
| `investigation_state.py` | 271 | Correctly isolated — state concern |
| `strategies_ui.py` | 1,054 | Correctly isolated — UI concern |
| `filter_controls.py` | 198 | Correctly isolated — UI/state concern |
| `nav_state.py` | 112 | Correctly isolated — state concern |

These demonstrate the extraction pattern works. app.py should eventually become as clean as these.

---

## 5. Execution Layer Doctrine

### 5.1 Layer Definitions

Seven execution layers. Each layer may only call layers below it. Never above.

```
Layer 7: RENDER        — Streamlit widgets, visual output
Layer 6: ORCHESTRATION — app.py dispatch, route selection
Layer 5: TACTICAL      — escalation scoring, badge logic
Layer 4: CALCULATIONS  — EV%, edge%, composite score
Layer 3: STATE         — session_state reads/writes
Layer 2: DATA ACCESS   — pipeline.py, cache reads
Layer 1: FETCH         — clients/, external APIs
```

### 5.2 Layer Rules

**Render (L7):**
- Accept data as arguments only
- Never write session_state
- Never call engine/ functions directly
- Never import pipeline.py

**Orchestration (L6):**
- Sole owner of routing decisions
- Coordinates layer calls in correct order
- Never renders directly — delegates to L7

**Tactical (L5):**
- Consumes calculated outputs (dicts, DataFrames)
- Produces badge states, escalation signals
- No I/O, no state writes

**Calculations (L4):**
- Pure math — same input = same output always
- engine/ modules already satisfy this
- New calculation code must go into engine/ or tactical/, never app.py

**State (L3):**
- Only layer permitted to read/write session_state
- Initializes all keys in defined order
- Never triggers side effects on read

**Data Access (L2):**
- Reads pipeline outputs
- Owns cache decorators
- Never called from L7 directly

**Fetch (L1):**
- HTTP calls, file reads
- Must be async-safe
- No state dependencies

### 5.3 Layer Violation Register

During migration, track any discovered layer violations in `Docs/09_DECISIONS/layer_violations_register.md`. Each violation must be resolved before the violating module is extracted.

---

## 6. Migration Sequencing Plan

### 6.1 Sequencing Principles

1. Extract pure functions before stateful functions
2. Extract display-only code before state-coupled code
3. Extract leaf nodes before root nodes
4. Extract systems with zero app.py cross-references before entangled systems
5. Never extract routing, dispatch, or cache ownership until Phases 5+

### 6.2 Phase Map

```
Phase 0: Audit (current)
Phase 1: Pure helper extraction
Phase 2: Tactical display extraction
Phase 3: UI section extraction (stateless views)
Phase 4: State module formalization
Phase 5: Shell extraction (routing/workspace)
Phase 6: app.py reduction to thin orchestrator
Phase 7: Cross-engine contract stabilization
```

### 6.3 Phase Detail

**Phase 0 — Audit (CURRENT PHASE)**
- Map all functions in app.py with session_state reads/writes
- Map all `@st.cache_data` ownership
- Identify all cross-section references within app.py
- Deliverable: `Docs/09_DECISIONS/app_py_audit_v1.md`
- Forbidden: any production changes
- Duration: 1 session

**Phase 1 — Pure Helper Extraction**
- Target: constants, formatting functions, label dicts, tooltip text
- Safety: zero session_state, zero imports of st
- Destination: `ui/helpers.py`, `tactical/labels.py`
- Validation: run app.py before/after, visual diff must be zero
- Risk: LOW

**Phase 2 — Tactical Display Extraction**
- Target: badge rendering, escalation tier display, archetype labels
- Safety: stateless rendering functions that accept dicts
- Destination: `tactical/badges.py`, `tactical/archetypes.py`
- Validation: Full Slate + JIG view must be visually identical
- Risk: LOW-MEDIUM (must verify no hidden state reads)

**Phase 3 — UI Section Extraction (Stateless Views)**
- Target: standalone view sections that can receive data as arguments
- Examples: threat cards, parlay display, pitcher suppression card
- Destination: `ui/threat_cards.py`, `ui/parlay_ui.py`, `ui/pitcher_suppression.py`
- Validation: each view exercised independently
- Risk: MEDIUM (depends on Phase 0 audit confirming stateless nature)
- Prerequisite: Phase 0 audit complete

**Phase 4 — State Module Formalization**
- Target: formalize state initialization into `state/init.py`
- Validate that existing state/ modules (investigation_state.py, nav_state.py) are coherent
- Do NOT move navigation_continuity.py yet — stabilization-sensitive
- Risk: MEDIUM-HIGH
- Prerequisite: Phases 1–3 complete and stable for 2+ sessions

**Phase 5 — Shell Extraction**
- Target: routing dispatch, workspace ownership
- Destination: `shell/router.py`, `shell/workspace.py`
- Risk: HIGH — this is the most dangerous extraction
- Prerequisite: Phase 4 complete, full regression test
- Requires: explicit session-level authorization

**Phase 6 — app.py Reduction**
- Target: app.py becomes ~300 line thin orchestrator
- Calls shell/, state/, ui/ in defined order
- Owns only startup bootstrap and top-level dispatch delegation
- Risk: HIGH but contained if prior phases clean
- Prerequisite: Phases 1–5 complete and stable

**Phase 7 — Cross-Engine Contract Stabilization**
- Target: define stable API contract between Streamlit and React frontends
- Align app.py orchestration with frontend/ requirements
- Out of scope for current planning horizon

### 6.4 Forbidden Early Extractions

These must NOT be extracted in Phases 1–3 under any circumstances:

- `session_state` initialization blocks
- `@st.cache_data` decorated functions
- Route dispatch logic (`if route == "..."` blocks)
- `active_workspace` setter/getter code
- Navigation persistence callbacks
- JIG/Main selection logic
- Any function touching `st.session_state["active_route"]`

---

## 7. Low-Risk Early Candidates

These are safe for Phase 1 extraction. All confirmed pure (no session_state, no `st.*` calls, no side effects on import).

### 7.1 Tier A: Zero-Risk Extractions

| Candidate | Description | Target Destination |
|-----------|-------------|-------------------|
| Column label dicts | Display name mappings for DataFrame columns | `ui/labels.py` |
| Color/badge constants | Escalation tier colors, badge text | `tactical/constants.py` |
| Tooltip text dicts | Hover text for UI elements | `ui/tooltips.py` |
| Number formatting helpers | `format_pct()`, `format_odds()`, `format_ev()` | `ui/formatters.py` |
| American odds display logic | +150 / -120 formatting rules | `ui/formatters.py` |
| Static archetype label maps | e.g., `BARREL_TIER_LABELS` dict | `tactical/labels.py` |

### 7.2 Tier B: Low-Risk Extractions (verify stateless first)

| Candidate | Description | Target Destination |
|-----------|-------------|-------------------|
| Threat card rendering | Accepts player dict, returns st.container | `ui/threat_cards.py` |
| Escalation badge renderer | Accepts tier int, returns colored badge | `tactical/badges.py` |
| Pitcher suppression card | Accepts pitcher dict, renders card | `ui/pitcher_suppression.py` |
| HVY signal display | Accepts pitch_mix dict, renders modifier | `tactical/hvy_display.py` |
| Visualization wrappers | `plotly` chart builders that accept DataFrames | `ui/charts.py` |

### 7.3 Already-Extractable (existing separate files — candidates for folder reorganization only)

- `strategies_ui.py` → `ui/strategies_ui.py` (rename-only, no code change)
- `filter_controls.py` → `ui/filter_controls.py` (rename-only, no code change)

**Note:** Renaming files that are imported by app.py requires updating imports in app.py. Only do this in a dedicated single-file rename session, not bundled with other changes.

---

## 8. High-Risk Systems

These systems require extreme caution. Any extraction attempt without the full Phase 0 audit and Phase 4 prerequisites is forbidden.

### 8.1 Critical Risk (Phases 5+)

| System | Risk | Why |
|--------|------|-----|
| `active_workspace` ownership | CRITICAL | Owns Main/JIG routing; wrong extraction = split-brain dispatch |
| Route synchronization | CRITICAL | Timing-dependent; extraction can cause ghost-route rerenders |
| Session state initialization | CRITICAL | Order-dependent initialization; wrong order = blank or corrupted app |
| Cache ownership (`@st.cache_data`) | CRITICAL | Function identity determines cache key; moving function = full cache bust |
| Navigation persistence | HIGH | Multi-file coordination; extraction risks desync across navigation_continuity.py + nav_state.py |

### 8.2 High Risk (Phase 4 only, with prerequisites)

| System | Risk | Why |
|--------|------|-----|
| Investigation state machine | HIGH | State machine logic; incorrect extraction creates orphaned state |
| Modal governance | HIGH | Modal open/close tied to session_state keys; extraction creates hidden coupling |
| JIG dispatcher | HIGH | Coordinates JIG sub-views; any split risks view-ordering bugs |
| Full Slate orchestrator | HIGH | Parent orchestrator for all battlefield view logic |
| Filter state management | MEDIUM-HIGH | filter_controls.py exists but may have hidden app.py coupling |

### 8.3 Warning Patterns

During Phase 0 audit, flag any function in app.py that:
- Reads `st.session_state` inside a rendering function
- Writes `st.session_state` as a side effect of display
- Uses `@st.cache_data` with arguments that reference session state
- Calls `st.experimental_rerun()` or `st.rerun()`
- Has a closure over session state variables

Each flagged function must be resolved to a safe execution layer before extraction.

---

## 9. Runtime Safety Doctrine

### 9.1 Duplicate Import Prevention

Every extracted module must:
1. Have a unique, descriptive import path
2. Never be importable under two names
3. Never shadow an existing module name

Check before creating any new file:
```powershell
# Verify no naming conflict
Get-ChildItem -Recurse -Filter "*.py" | Where-Object { $_.Name -eq "target_name.py" }
```

### 9.2 Circular Reference Prevention

Allowed import directions (unidirectional only):

```
app.py → shell/ → state/ → engine/ → data/
app.py → ui/    → tactical/ → engine/
ui/    → state/ (read-only access)
```

Never allowed:
```
engine/ → ui/
state/  → shell/
clients/ → engine/
tactical/ → state/ (state writes)
```

Before any extraction: draw the import graph. If any cycle exists, resolve at the data layer — extract shared types to a `types.py` or `contracts.py` that neither side imports from.

### 9.3 Rerender Amplification Prevention

Streamlit rerenders the entire app on any `st.session_state` write. Rules:
- Never write session_state inside a function called from a loop
- Never write session_state in a rendering function
- Never call `st.rerun()` except at the top-level orchestrator
- Use `st.session_state.get(key, default)` for reads that should not fail on first load

### 9.4 State Fragmentation Prevention

All session_state keys must be:
1. Defined in one place (the state init module)
2. Named with a consistent prefix pattern (e.g., `ui_`, `nav_`, `inv_`, `filter_`)
3. Initialized before first use, never inline

During Phase 0 audit: produce a complete session_state key inventory. This is the authoritative reference for Phase 4.

### 9.5 Hidden Side Effect Detection

Before marking any function as "safe to extract," verify:
- No print/logging statements with global side effects
- No module-level code that executes on import
- No `__init__` that mutates external state
- No import of `app.py` from within extracted modules (circular)

---

## 10. Tactical UX Preservation Rules

### 10.1 Shell Hierarchy Must Be Preserved

The tactical shell hierarchy — global nav → workspace → section → card → detail — must survive modularization intact. Modularization is a code-organization change. The operator must see identical UX before and after.

Hierarchy ownership after modularization:
```
Global nav        → shell/router.py
Workspace         → shell/workspace.py
Section dispatch  → ui/{section}.py
Card rendering    → ui/threat_cards.py, tactical/badges.py
Detail expansion  → ui/modals.py
```

### 10.2 Escalation Pacing Must Be Preserved

The escalation system — threat tier color, badge density, investigation atmosphere — is UX logic, not data logic. It must remain in `tactical/` modules, never in `engine/` or `state/`. Escalation is a display concern.

### 10.3 Cinematic Density Must Be Preserved

Card density, information hierarchy, and visual weight of tactical elements must not change as a side effect of modularization. Test the Full Slate view and JIG view visually after every Phase 2+ extraction.

### 10.4 Workflow Continuity

Investigation flow — scan → identify → investigate → deploy — must work identically after any extraction. If a single workflow step breaks, roll back the extraction.

### 10.5 Command Flow Preservation

Any operator command (filter change, sort, tab switch, investigation trigger) must produce identical behavior before and after extraction. Behavioral regression testing is required for Phase 3+.

---

## 11. Validation Doctrine

### 11.1 Extraction Validation Sequence

For every extracted module, in order:

1. **Static check:** `python -c "import module_path"` — confirms no import errors
2. **Null render check:** If rendering function, call with minimal mock data, confirm no crash
3. **app.py smoke test:** `streamlit run app.py` — confirm startup without errors
4. **View smoke test:** Navigate to every view that calls the extracted module — confirm visual identity
5. **Regression check:** Run any available test suite in `tests/`
6. **State check:** Confirm no unexpected session_state keys added or removed

### 11.2 Rollback Requirements

Before any extraction:
- Confirm git status is clean (all previous work committed)
- Create a named branch: `modular/phase-N-{module-name}`
- Extraction is a single atomic commit: move + update imports = one commit
- If validation fails at any step, `git checkout .` to revert

### 11.3 Test Requirements

Phase 1: Visual inspection only (pure helpers have no UX impact)  
Phase 2: Visual inspection + Full Slate smoke test  
Phase 3: Full view regression on all extracted views  
Phase 4: Full app regression + session_state key inventory diff  
Phase 5+: Requires dedicated test session with operator walkthrough

### 11.4 Operator Checkpoints

Required human sign-off before proceeding to next phase:
- After Phase 1: Confirm app behavior unchanged
- After Phase 3: Confirm Full Slate + JIG identical to pre-modularization
- After Phase 4: Confirm investigation flow works end-to-end
- After Phase 5: Confirm routing behavior identical across all navigation paths

---

## 12. Rollback & Recovery

### 12.1 Per-Extraction Rollback

```powershell
# Revert a single extraction
git checkout -- app.py
git checkout -- ui/threat_cards.py  # delete the new file
```

If committed:
```powershell
# Revert last commit (extraction), keep working directory clean
git revert HEAD --no-edit
```

### 12.2 Phase-Level Rollback

If an entire phase needs reversion:
```powershell
# Find the commit hash before phase started
git log --oneline

# Reset to that commit (preserves work in stash first)
git stash
git reset --hard {pre-phase-commit-hash}
```

**Warning:** Hard reset discards all changes since that commit. Confirm stash is valid before proceeding.

### 12.3 Recovery From Failed Extraction

If app.py stops rendering after an extraction:

1. Check `streamlit run app.py` error message — identify the import path that broke
2. Check if the extracted function had hidden session_state access (run Phase 0 audit on it)
3. Inline the function back into app.py temporarily
4. Add it to the Forbidden Extraction Registry in `Docs/09_DECISIONS/layer_violations_register.md`
5. Do NOT attempt re-extraction until root cause is resolved

### 12.4 Session State Corruption Recovery

If session_state becomes corrupted after extraction:
1. Clear browser local storage for the Streamlit app
2. Restart streamlit: `streamlit run app.py --server.port 8502` (fresh port)
3. If corruption persists, the extraction introduced a state ordering bug — roll back

---

## 13. Future-State Vision

### 13.1 Target Architecture

The final target state for MLB HR Engine v4:

```
app.py (~300 lines)
│  Startup bootstrap only
│  Delegates to shell/ for routing
│  Delegates to state/ for initialization
│  Delegates to ui/ for all rendering
│
├── shell/         ← routing, navigation, workspace
├── state/         ← all session_state lifecycle
├── ui/            ← all Streamlit rendering (pure)
├── tactical/      ← escalation, badges, scoring display
│
├── engine/        ← probability math (already clean)
├── clients/       ← data fetching (already clean)
├── tracking/      ← persistence layer (already clean)
├── portfolio/     ← portfolio optimization (already clean)
├── strategies/    ← betting strategies (already clean)
├── pipeline.py    ← shared pipeline (already clean)
└── config.py      ← constants (already clean)
```

### 13.2 app.py Target Profile

Post-modularization app.py should:
- Own only startup bootstrap logic
- Call `state.init()` exactly once on startup
- Call `shell.router.dispatch(route)` to delegate view rendering
- Be ~200-400 lines
- Contain zero rendering logic
- Contain zero business logic

### 13.3 Streamlit / React Convergence

Long-term: `ui/` modules in Python mirror `frontend/` component hierarchy in React. The `api/` module (FastAPI, already 360 lines) becomes the stable contract between both frontends. This enables:
- Python Streamlit for operator workflow (proven, fast to iterate)
- React for public-facing or embedded views
- Shared contract via `api/main.py` endpoints

### 13.4 Operational Maturity Milestones

| Milestone | Condition |
|-----------|-----------|
| Phase 1 complete | app.py < 10,000 lines |
| Phase 2 complete | app.py < 9,000 lines |
| Phase 3 complete | app.py < 7,000 lines |
| Phase 4 complete | app.py < 5,000 lines |
| Phase 5 complete | app.py < 2,000 lines |
| Phase 6 complete | app.py < 400 lines |

Each milestone requires operator validation before proceeding. No phase is time-boxed — stability over speed.

### 13.5 What Success Looks Like

An operator using the fully modularized platform:
- Sees zero UX difference from pre-modularization
- Benefits from faster startup (isolated cache domains)
- Benefits from clearer error messages (traceable to bounded modules)
- Benefits from new features that can be added without touching app.py

A developer working on the modularized platform:
- Can modify `ui/threat_cards.py` without risk to routing
- Can modify `tactical/badges.py` without risk to state
- Can add a new view by creating `ui/new_view.py` and adding one line to `shell/router.py`
- Can test any UI function in isolation

---

## Appendix A: Protected Systems Registry (Initial)

| System | Location | Protection Level | Extraction Phase |
|--------|----------|-----------------|-----------------|
| active_workspace dispatch | app.py | CRITICAL | Phase 5 minimum |
| active_route synchronization | navigation_continuity.py | CRITICAL | Phase 5 minimum |
| session_state init | app.py startup block | CRITICAL | Phase 4 |
| @st.cache_data functions | app.py | CRITICAL | Phase 5 |
| JIG dispatcher | app.py | HIGH | Phase 5 |
| Main dispatcher | app.py | HIGH | Phase 5 |
| investigation state machine | investigation_state.py | HIGH | Phase 4 |
| modal open/close keys | app.py | HIGH | Phase 4 |
| navigation persistence callbacks | navigation_continuity.py | HIGH | Phase 5 |
| filter state coupling | filter_controls.py + app.py | MEDIUM | Phase 3 |

---

## Appendix B: Phase 0 Audit Checklist

Complete before any extraction begins:

- [ ] Count all `st.session_state` reads in app.py
- [ ] Count all `st.session_state` writes in app.py
- [ ] Map all `@st.cache_data` function names and their call sites
- [ ] List all functions in app.py that call `st.rerun()`
- [ ] List all functions in app.py with zero session_state and zero `st.*` calls (extraction candidates)
- [ ] Count all unique session_state key names used in app.py
- [ ] Identify all import dependencies of app.py (what does it import?)
- [ ] Identify all files that import from app.py (what imports it?)
- [ ] Map cross-reference graph: which functions call which other functions in app.py
- [ ] Produce `Docs/09_DECISIONS/app_py_audit_v1.md` with above findings

---

*Document end. No production systems were modified in the creation of this document.*
