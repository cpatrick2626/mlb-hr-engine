# Phase 4 Modularization Synthesis Doctrine v1.0
## MLB HR ENGINE — Controlled Modularization Governance (All 13 Deliverables)
### Status: ARCHITECTURE PLANNING | Phase 4 Entry Point | No Production Changes

---

## AUTHORITY NOTE

This document is the **Phase 4 entry point** for modularization governance.
It synthesizes all 8 Room 09 docs and adds Phase 4-specific deliverables.

**Precedence:** Inherits from `master_modularization_governance_framework_v1.md` (Rank 1 Authority).
**Conflicts:** Master doc governs. This doc governs where master doc is silent.
**Execution gate:** Operator must explicitly state "Ready to begin Phase 1 extraction." No extraction begins without this.

---

## DELIVERABLE 1: PROTECTED MONOLITH DOCTRINE

### What a Protected Monolith Is

A Protected Monolith is a large, well-integrated single file that:
- Contains multiple systems with shared runtime context
- Is NOT fragmented because the cost of wrong extraction exceeds the cost of size
- Has known coupling that is governed rather than ignored
- Is stabilized, tested, and trusted in production

MLB HR ENGINE `app.py` (10,706 lines) qualifies as a Protected Tactical Monolith.

### Why MLB HR ENGINE Currently Qualifies

| Qualifier | Evidence |
|-----------|----------|
| Shared session_state | All tabs share single init block — extraction creates split-ownership risk |
| Shared cache contracts | `@st.cache_data` boundaries cross conceptual module lines |
| Navigation continuity | Route sync is timing-dependent — extraction breaks sequencing |
| Hydration fingerprint guard | Startup order is non-commutative — order matters, fragmentation breaks it |
| Tactical render chains | MAIN/JIG/Full Slate render sequences are entangled by design |

### Stabilization-First Philosophy

**Doctrine:** A working monolith is preferable to a broken module.
Modularization is an optimization. Runtime trust is a hard-won asset.
When they conflict, runtime trust wins. Always.

### Safe-Growth Doctrine

Monolith growth is acceptable when:
- New systems follow the protected ownership zone boundaries
- New state keys are added inside the approved init block
- New render logic follows the established render sequence
- No new cross-layer imports are introduced

### Protected-Runtime Philosophy

The monolith is protected because **we have earned trust in it**.
Extraction earns new trust, slowly, one module at a time.
No extraction earns trust by assertion — only by validation.

### Acceptable Monolith Behavior

- File size growth from new tactical systems (acceptable)
- Internal refactoring of pure helpers within app.py (acceptable with observation)
- New modal systems following `spec_modal_governance_v1.md` (acceptable)

### Dangerous Growth Patterns

- Adding new `st.session_state` init blocks outside the main init section
- Adding new `@st.cache_data` decorators inside tab render functions
- Cross-tab state writes from inside tab render functions
- Import of engine modules from inside render closures

### Stabilization Triggers (Halt Extraction, Return to Monolith Management)

- Any render regression in MAIN, JIG, or Full Slate tabs
- Any session_state KeyError
- Any calibration drift alert (|bias|>3pp at n≥50)
- Any Full Slate orchestration failure
- Operator-declared freeze

### Extraction Prerequisites

Before any extraction begins:
1. All 5 tabs render without error on cold start (≥3 consecutive)
2. Full Slate orchestration passes consistently
3. Git branch isolated from main
4. Rollback procedure demonstrated (dry run)
5. Operator explicit authorization given

---

## DELIVERABLE 2: RUNTIME OWNERSHIP ZONE DOCTRINE

### Protected Ownership Zones

| Zone | Location | Owner | Coupling Sensitivity | Extraction Risk |
|------|----------|-------|---------------------|-----------------|
| Shell layer | `app.py` (startup/dispatch) | Claude (frozen) | CRITICAL | ABSOLUTE FREEZE |
| Routing layer | `app.py` (`active_workspace`, `active_route`) | Claude (frozen) | CRITICAL | ABSOLUTE FREEZE |
| Session state init | `app.py` (init block) | Claude (frozen) | CRITICAL | ABSOLUTE FREEZE |
| Hydration / fingerprint | `app.py` (startup sequence) | Claude (frozen) | CRITICAL | ABSOLUTE FREEZE |
| Cache ownership | `pipeline.py` / `app.py` | Claude (frozen) | HIGH | OPERATOR APPROVAL |
| Pipeline contract | `pipeline.py` | Claude (frozen) | CRITICAL | ABSOLUTE FREEZE |
| Full Slate orchestration | `app.py` (Full Slate chain) | Claude (frozen) | HIGH | OPERATOR APPROVAL |
| Escalation hierarchy | `app.py` (escalation chain) | Claude (frozen) | HIGH | OPERATOR APPROVAL |
| MAIN tab render sequence | `app.py` | Claude (frozen) | HIGH | OPERATOR APPROVAL |
| JIG tab render sequence | `app.py` | Claude (frozen) | HIGH | OPERATOR APPROVAL |
| TCC shell render | `app.py` | Claude (frozen) | HIGH | OPERATOR APPROVAL |
| Tactical display helpers | `app.py` (formatting fns) | Claude | LOW | Phase 1 safe |
| Color / badge constants | `app.py` (mappings) | Claude | LOW | Phase 1 safe |
| Metric calculation helpers | `app.py` (pure math) | Claude | LOW | Phase 1 safe |
| Config hub | `config.py` | Operator (absolute) | CRITICAL | NEVER |

### Ownership Boundaries: What Each Zone May Do

**Shell Layer:** Reads session_state. Writes session_state (startup only). Calls tab renderers. Dispatches routing. No data fetch.

**Routing Layer:** Reads `active_workspace`. Writes `active_workspace` and `active_route`. No render calls. No data fetch.

**Tactical Display Helpers (extractable):** Accept data as arguments. Return display strings / formatted values. No session_state access. No imports above Layer 1.

---

## DELIVERABLE 3: EXTRACTION HIERARCHY DOCTRINE

### Risk Tier Classification

#### LOW RISK — Phase 1 (Pure Functions, Zero Runtime Risk)

| Target | Why Safe | Observation Window |
|--------|----------|-------------------|
| Formatting utilities (ANSI, number format, % display) | No state, no imports upward, pure output | 1 session |
| Color / badge mapping constants | Declarative dict, no runtime dependency | 1 session |
| Metric calculation helpers (Sharpe, Kelly, EV math) | Pure math, no session_state | 1 session |
| Display string builders (odds → string, prob → label) | No cache, no session dependency | 1 session |
| Icon / emoji maps | Pure constant, no runtime dependency | 1 session |
| Tooltip text definitions | Pure string constants | 1 session |
| Visual token definitions (colors, gradients, thresholds) | No render call, no state | 1 session |

#### MEDIUM RISK — Phase 2 (State-Adjacent, Read-Only Access)

| Target | Why Medium | Observation Window |
|--------|-----------|-------------------|
| Stateless filter functions | Read config only, return filtered data | 2 sessions |
| Stateless ranker helpers | Read picks, return ranked picks | 2 sessions |
| Display table builders | Accept data in, return display artifact | 2 sessions |

Phase 2 does not begin until Phase 1 is stable for ≥2 sessions AND operator approves.

#### HIGH RISK — Phase 3 (Orchestration Layer, Post-Phase-2 Stabilization Only)

| Target | Why High | Observation Window |
|--------|---------|-------------------|
| Tab content renderers | Thin wrappers calling Phase 1/2 modules | 3 sessions |
| Sidebar component modules | Isolated sidebar logic | 3 sessions |
| Card render components | Threat card, suppression card modules | 3 sessions |

Phase 3 does not begin until Phase 2 is stable for ≥3 sessions AND operator approves.

#### NEVER EXTRACT — Absolute Freeze

- `active_workspace` ownership and mutation logic
- `active_route` synchronization logic
- `st.session_state` initialization blocks
- Hydration fingerprint guard logic
- `@st.cache_data` ownership contracts
- Shell render sequence
- Pipeline output schema
- Full Slate orchestrator chain
- Escalation hierarchy chain

### Extraction Pacing Rules

- One extraction per session. No parallel extractions.
- One module per extraction step. No bundled multi-module extractions.
- No extraction while runtime incident is open.
- No extraction during Full Slate active deployment window.

---

## DELIVERABLE 4: RENDER ISOLATION DOCTRINE

### Tactical Surface Isolation

Each tactical surface (MAIN, JIG, Full Slate, Strategy, Performance) must render without knowledge of other surfaces' internal state.

**Rule:** Tab render functions receive data as arguments. They do not query session_state for other tabs' state. They do not trigger state mutations in other tabs.

### Render-Boundary Governance

```
LEGAL render boundary:
  pipeline_data → tab_renderer(data) → display artifact

ILLEGAL render boundary:
  tab_renderer() → st.session_state["other_tab_key"] → display artifact
  tab_renderer() → pipeline.run() → display artifact
  tab_renderer() → st.cache_data.clear() → display artifact
```

### Rerender Containment Rules

- No `st.session_state` write during render phase (only during init phase)
- No `@st.cache_data.clear()` inside tab render function
- No `st.experimental_rerun()` inside render loop
- No pipeline fetch inside tab render function

### Interaction Isolation

User interactions (button clicks, selectbox changes) must:
1. Write to session_state ONLY — no direct render calls
2. Let Streamlit's natural rerender handle the display update
3. Not trigger cross-tab state mutations

### Table Isolation

Each table render function (Batters Table, JIG table, Full Slate table):
- Receives its data as a function argument
- Maintains its own sort/filter state in scoped session_state keys
- Does not read or write other tables' session_state keys

### Shell Isolation

Shell dispatch sequence is the ONLY entry point for tab render calls.
No tab render function calls another tab render function directly.

### Safe Render Zones

- Pure formatting helpers: always safe to call from any render context
- Color/badge mapping: always safe
- Metric calculations: always safe
- Display string builders: always safe

### Dangerous Rerender Patterns

| Pattern | Risk | Rule |
|---------|------|------|
| Writing session_state during render | Full-app rerender loop | FORBIDDEN |
| Pipeline call inside tab render | Double execution, latency spike | FORBIDDEN |
| Cross-tab session_state read (mutable) | Timing-dependent state corruption | FORBIDDEN |
| `st.cache_data.clear()` inside render | Cache eviction on every page load | FORBIDDEN |
| Import of app.py from extracted module | Circular import, startup crash | FORBIDDEN |

---

## DELIVERABLE 5: DEPENDENCY GOVERNANCE DOCTRINE

### Layer Hierarchy (Strict Dependency Directionality)

```
Layer 0: config.py              ← no imports from any layer above
Layer 1: Pure helpers           ← import Layer 0 only
Layer 2: Data clients           ← import Layer 0-1 only
Layer 3: Engine modules         ← import Layer 0-2 only
Layer 4: Pipeline               ← import Layer 0-3 only
Layer 5: Tab renderers          ← import Layer 0-4 only
Layer 6: Shell / app.py         ← import Layer 0-5 only
```

**No upward imports.** Layer N cannot import Layer N+1 or higher.

### Hidden Coupling Detection

Run before every extraction step:
```bash
python -c "import ast, sys; ..."   # dependency graph check
python -c "import app"             # circular import check
```

Identify hidden contracts:
- Functions in app.py that access session_state inline (not via argument)
- Functions that call `pipeline.py` directly from render context
- Functions that assume cache warming from a prior function

### Cross-System Contamination Prevention

**Approved dependency flows:**

```
config.py → engine/* → pipeline.py → app.py tabs
clients/* → pipeline.py → app.py tabs
tracking/* → app.py (display only, no mutation)
portfolio/* → app.py (display only, no mutation)
```

**Forbidden dependency flows:**

```
engine/* → app.py       (upward import)
pipeline.py → app.py    (upward import)
extracted helper → app.py (upward import)
tracking/* → pipeline.py (lateral same-layer import, not governed)
```

### Circular Dependency Prevention

Any extracted module must satisfy:
```
python -c "import <extracted_module>"
```
Without triggering any import of app.py, pipeline.py, or Streamlit.
If import chain reaches Streamlit: module is NOT safe to extract.

### Ownership Hierarchy

| Layer | Allowed Imports | Forbidden Imports |
|-------|----------------|-------------------|
| config.py | None | Everything |
| Pure helpers | config.py | All layers above |
| Clients | config.py, helpers | Pipeline, app.py |
| Engine | config.py, helpers, clients | Pipeline, app.py |
| Pipeline | All below | app.py |
| Tab renderers | All below | Other tab renderers |
| app.py shell | All | Nothing forbidden (top of hierarchy) |

---

## DELIVERABLE 6: TACTICAL SURFACE SEPARATION DOCTRINE

### Tactical Surfaces and Their Isolation Contracts

#### Tactical Command Center (TCC) / MAIN Tab

- Owns: Batter threat card display, escalation badge rendering, batters table sort/filter
- Receives: `pipeline_data` from shell dispatch
- Writes: Only scoped session_state keys (`main_sort_col`, `main_filter_*`)
- Must not read: JIG, Full Slate, Strategy, Performance session_state keys

#### Full Slate Tab

- Owns: Parent orchestrator chain, escalation hierarchy, slate risk governance
- Receives: `pipeline_data`, date context from shell
- Writes: Only scoped session_state keys (`full_slate_*`)
- Must not call: pipeline.run() directly (data arrives pre-fetched)
- Must not read: MAIN or JIG session_state keys

#### Batters Table Surface

- Owns: Column sort state, filter state, pagination state
- Receives: ranked pick list as argument
- Writes: `batters_sort_col`, `batters_sort_dir`, `batters_filter_*`
- Must not write: Any other surface's state

#### Player Card Systems

- Owns: Card modal open/close state, selected player state
- Receives: single player row as argument
- Writes: `player_card_open`, `player_card_target`
- Must not access: pipeline data directly

#### Deployment Systems

- Owns: Deployment queue state, deployment confirmation state
- Receives: slip list, bankroll context from shell
- Writes: `deployment_queue`, `deployment_status`
- Must not read: MAIN tab ranking state directly

#### Trust-State Systems

- Owns: Data integrity flags, calibration status, pipeline health indicators
- Source of truth: `engine/trust.py`, `tracking/data_integrity.py`
- App.py display layer reads trust state, never writes it
- Trust state mutations happen in trust/integrity modules only

### Coordination Without Contamination

Surfaces may share data only via:
1. Shell dispatch passing `pipeline_data` as argument
2. Scoped session_state keys with explicit ownership (one surface writes, others read-only)
3. Shared config constants (config.py, read-only for all)

Surfaces may NOT share data via:
- Direct import of each other's render functions
- Mutating shared session_state keys from render phase
- Calling pipeline or clients directly from surface render function

---

## DELIVERABLE 7: STABILIZATION-FIRST MODULARIZATION DOCTRINE

### When NOT to Modularize

Do NOT begin extraction when:
- Any render regression is active in any tab
- Full Slate orchestration is unstable
- An active calibration drift alert exists (|bias|>3pp at n≥50)
- An operator-declared freeze is in effect
- A production incident is open
- Stabilization work is in progress (stabilization owns the runway)

### Stabilization Prerequisites

Before ANY extraction step:
1. All 5 tabs render without error on cold start (≥3 consecutive passes)
2. Full Slate run produces output matching pre-extraction baseline
3. Git state is clean (all prior work committed)
4. Branch is isolated from main
5. Calibration bias within threshold
6. No active operator freeze

### Extraction Readiness Criteria

For Phase 1 (LOW RISK targets):
- All stabilization prerequisites met
- Target function is pure (no session_state, no cache, no Streamlit calls)
- Target function has no hidden upward dependency
- Rollback procedure demonstrated on dry run
- Operator explicit authorization given

For Phase 2 (MEDIUM RISK targets):
- Phase 1 complete AND stable for ≥2 production sessions
- Phase 1 operator sign-off received
- Target function read-only (receives data as arg, no state writes)
- Additional operator per-step approval required

For Phase 3 (HIGH RISK targets):
- Phase 2 complete AND stable for ≥3 production sessions
- Phase 2 operator sign-off received
- Per-step operator approval required
- Full regression test baseline captured before each step

### Rollback Requirements

Every extraction step must have:
- `git diff` confirming exact changes before commit
- Single-revert path (one file reverts, no cascading changes)
- Import restoration path documented before extraction begins

### Validation Sequencing

After every extraction step, in order:
1. `python -c "import app"` — no circular import error
2. Cold-start launch — no Streamlit startup error
3. Navigate all 5 tabs — no render error, no empty tab
4. Trigger Full Slate run — output matches pre-extraction baseline
5. Operator visual inspection sign-off

All 5 must pass. No skipping. No "close enough."

### Hard Rule

> **No modularization proceeds unless:**
> - Runtime stability confirmed (all 5 tabs clean)
> - Validation passes exist (L1-L5)
> - Rollback path exists and is tested
> - Ownership is clear (one owner, no ambiguity)
> - Operator has explicitly authorized

---

## DELIVERABLE 8: VALIDATION DOCTRINE

### Modularization Validation Checklist

#### Rerender Stability

- [ ] Cold start produces no Streamlit error (≥3 consecutive)
- [ ] No phantom rerenders observed on MAIN tab after extraction
- [ ] No phantom rerenders on JIG tab after extraction
- [ ] Session state inspector shows no unexpected key additions or removals

#### Ownership Isolation

- [ ] Extracted module contains zero `st.session_state` references
- [ ] Extracted module contains zero `@st.cache_data` decorators
- [ ] Extracted module receives all data as function arguments
- [ ] `import <extracted_module>` does not trigger Streamlit import

#### Dependency Integrity

- [ ] `python -c "import app"` passes with no circular import
- [ ] Layer hierarchy audit: extracted module imports only Layer 0 (config.py)
- [ ] No new upward imports introduced in any existing module

#### Tactical Continuity

- [ ] MAIN tab batter threat cards render correctly
- [ ] Escalation badges render with correct tier colors
- [ ] Batters table sort and filter state preserved across navigation
- [ ] JIG composite scores unchanged (same inputs → same outputs)

#### Escalation Preservation

- [ ] Full Slate escalation hierarchy renders all tiers correctly
- [ ] Escalation badge colors match pre-extraction baseline
- [ ] Escalation jump logic unchanged (verified by Full Slate run)

#### Shell Continuity

- [ ] Shell startup sequence completes without error
- [ ] Active workspace dispatch routes correctly to all 5 tabs
- [ ] Navigation continuity: returning to tab restores prior state

#### Trust-State Continuity

- [ ] Data integrity flags display correctly
- [ ] Calibration status indicators unchanged
- [ ] Pipeline health indicators unchanged

#### Deployment Continuity

- [ ] Deployment queue state persists across tab navigation
- [ ] Deployment confirmation flow completes without error

### Validation Authority Hierarchy

| Level | Validator | Authority | Pass Criteria |
|-------|-----------|-----------|---------------|
| L1 | Import check | `python -c "import app"` | No ImportError, no circular import |
| L2 | Cold start | Full app launch | No Streamlit error on startup |
| L3 | Tab navigation | Navigate all 5 tabs | No render error, no empty tab |
| L4 | Full Slate run | Trigger Full Slate | Output matches pre-extraction baseline |
| L5 | Operator sign-off | Visual inspection | Operator confirms behavioral parity |

---

## DELIVERABLE 9: CODEX IMPLEMENTATION BOUNDARIES

### What Codex MAY Execute Independently

| Action | Scope |
|--------|-------|
| Phase 1 extraction implementations | Explicitly scoped by operator |
| Test creation for extracted pure modules | Unit tests only, no Streamlit dependency |
| Import verification scripts | Dependency graph analysis |
| Formatting helper extraction | Phase 1 targets only |
| Constant / mapping extraction | Phase 1 targets only |

### What Codex REQUIRES Operator Approval For

| Action | Gate |
|--------|------|
| Phase 2 extraction steps | Per-step operator approval |
| Phase 3 extraction steps | Per-step operator approval |
| Any change to session_state access pattern | Operator approval |
| Any change to cache behavior | Operator approval |

### Protected Runtime Zones — Codex MUST NOT Touch

| Zone | Location | Protection |
|------|----------|-----------|
| Shell orchestration | `app.py` startup/dispatch | ABSOLUTE |
| Pipeline contract | `pipeline.py` | ABSOLUTE |
| Config hub | `config.py` | ABSOLUTE |
| Session state init | `app.py` init block | ABSOLUTE |
| Cache ownership | `pipeline.py` / `app.py` | ABSOLUTE |
| Navigation continuity | `app.py` routing logic | ABSOLUTE |
| Hydration guard | `app.py` startup | ABSOLUTE |
| Trust-state orchestration | `engine/trust.py` + app.py display | ABSOLUTE |
| Deployment lifecycle | Deployment chain in `app.py` | ABSOLUTE |
| Full Slate orchestrator chain | `app.py` Full Slate section | ABSOLUTE |
| Escalation hierarchy chain | `app.py` escalation section | ABSOLUTE |

### Extraction Escalation Rules for Codex

If during Phase 1 extraction Codex discovers:
- Target function accesses session_state → STOP. Report to Claude. Do not extract.
- Target function imports pipeline → STOP. Report to Claude. Do not extract.
- Target function calls Streamlit directly → STOP. Report to Claude. Do not extract.
- Extraction creates circular import → ROLLBACK immediately. Report to Claude.

Codex does not self-authorize scope expansion. If the target turns out to be higher-risk than Phase 1 criteria, Codex halts and escalates.

---

## DELIVERABLE 10: RUNTIME CONTAMINATION RISKS

### Contamination Catalog

#### C1 — Import Contamination

**Mechanism:** Extracted module imports from a layer above it (e.g., helper imports app.py).
**Trigger:** Extraction moves function to Layer 1 but function calls remain in Layer 5+ scope.
**Symptom:** `ImportError: circular import` or silent scope-level circular reference at startup.
**Detection:** `python -c "import <module>"` fails with ImportError.
**Prevention:** Verify no upward imports before extraction commit.
**Containment:** Revert extracted module immediately. Restore original import.

#### C2 — State Write Contamination

**Mechanism:** Extracted module writes `st.session_state` directly instead of receiving state as argument.
**Trigger:** Original function accessed session_state inline; extraction preserved the pattern.
**Symptom:** Session state key initialized twice; second init overwrites first; timing-dependent bugs.
**Detection:** Grep extracted module for `st.session_state` write operations.
**Prevention:** All extracted modules must be pure (data-in, data-out). State writes stay in app.py.
**Containment:** Revert extracted module. Refactor to pass state as argument before re-extracting.

#### C3 — Cache Contamination

**Mechanism:** Extracted module introduces new `@st.cache_data` decorator on previously uncached function.
**Trigger:** Developer adds caching to extracted module "for performance."
**Symptom:** Two cache identities for same data; race condition between stale and fresh; unpredictable cache hit behavior.
**Detection:** Grep all extracted modules for `@st.cache_data`.
**Prevention:** No extracted module may introduce new `@st.cache_data`. Cache ownership stays in pipeline.py / app.py.
**Containment:** Remove decorator from extracted module. Revert if cache behavior is already corrupted.

#### C4 — Rerender Contamination

**Mechanism:** Extracted module mutates session_state during render phase.
**Trigger:** State update logic was embedded inside display function; extraction preserved the pattern.
**Symptom:** Phantom rerenders on every page load; investigation atmosphere degraded; app feels "jittery."
**Detection:** Observe cold start — if page re-renders immediately after first render, state mutation during render is likely.
**Prevention:** Display functions must not write session_state. Mutations belong in callback handlers only.
**Containment:** Separate mutation logic from display logic. Revert if rerender storm is active.

#### C5 — Orchestration Contamination

**Mechanism:** Extracted render module calls pipeline.run() or build_player_profiles() directly.
**Trigger:** Original display function had an embedded data-fetch for convenience.
**Symptom:** Double pipeline execution; latency spike; data inconsistency between tabs (each tab has slightly different data).
**Detection:** Observe pipeline execution count — if > 1 per page load, orchestration contamination is likely.
**Prevention:** Tab render functions receive pre-fetched data as arguments. No data fetch inside render.
**Containment:** Remove pipeline call from extracted module. Pass data as argument from shell dispatch.

#### C6 — Ownership Ambiguity

**Mechanism:** Extracted module is partially owned by two systems (e.g., Claude and Codex both modify it).
**Trigger:** Extraction boundary was drawn at wrong level — function contained both pure logic and orchestration logic.
**Symptom:** Conflicting changes to same module; inconsistent validation passes.
**Prevention:** Every extracted module has one declared owner. If unclear, don't extract until ownership is clear.
**Containment:** Operator decides ownership. Document explicitly. One owner, no exceptions.

#### C7 — Rerender Storms

**Mechanism:** Cascading rerenders triggered by state write in render phase or multiple `st.experimental_rerun()` calls.
**Trigger:** Extracted module writes state → triggers rerender → state write again → infinite loop.
**Symptom:** Browser hangs; Streamlit shows repeated "running" indicator; app becomes unusable.
**Prevention:** No state writes in render phase. No `st.experimental_rerun()` in render functions.
**Containment:** Kill Streamlit process. Revert last extraction. Investigate state mutation pattern.

#### C8 — Extraction Drift

**Mechanism:** Extracted module accumulates new logic over time that violates its original boundary contract.
**Trigger:** Convenience additions to "nearby" extracted module instead of proper placement.
**Symptom:** Module grows beyond its declared scope; imports expand; originally-low-risk module becomes medium-risk.
**Prevention:** Each extracted module has a declared scope boundary. Changes that exceed scope require operator review.
**Detection:** Periodic import graph audit; module line count monitoring.

#### C9 — Validation Blindness

**Mechanism:** Extraction appears validated but cached state masks the regression.
**Trigger:** Warm Streamlit reload uses cached session state; errors only appear on cold start.
**Symptom:** Local validation passes; first user session after deploy fails.
**Prevention:** Always cold-start test (kill Streamlit, restart, fresh browser session).
**Detection:** Run `python -c "import app"` then launch fresh — not warm reload.

#### C10 — Duplicate State Systems

**Mechanism:** Extracted module initializes its own session_state keys that duplicate existing app.py keys.
**Trigger:** Module was extracted without full audit of its session_state access.
**Symptom:** State appears inconsistent; different parts of app see different values for same concept.
**Prevention:** Full session_state key audit before extraction. No new keys in extracted modules.
**Containment:** Merge duplicate keys. Revert extraction. Re-extract with explicit argument passing.

### Contamination Prevention Rules Summary

1. No upward imports (Layer N cannot import Layer N+1)
2. No `st.session_state` writes in extracted modules
3. No `@st.cache_data` in extracted modules
4. No pipeline calls in extracted render functions
5. No `st.experimental_rerun()` in render functions
6. Always cold-start test before declaring extraction valid
7. One owner per module, documented before extraction begins
8. Scope boundaries declared before extraction begins

### Containment Rules

- First response to any contamination: **rollback the extraction step immediately**
- Do not attempt in-place fix during contamination event — restore first, diagnose second
- Document exact failure before rollback to preserve investigation context
- Operator notified for P0/P1 events; post-hoc notification for P2/P3

---

## DELIVERABLE 11: UX ANTI-PATTERNS

### Anti-Pattern 1 — Modular Sprawl Without Discoverability

**Pattern:** Extracting components into many small files with no clear organization scheme.
**Risk:** Developer cannot find where a behavior lives. "Where is the escalation badge color defined?" → search across 40 files.
**Rule:** Every extracted module goes into a declared directory with a declared purpose. No orphan files.
**Approved structure:**
```
helpers/          → Pure formatting, calculation, display string utilities
components/       → Card render components, table helpers
tabs/             → Tab content renderers (Phase 3 only)
```

### Anti-Pattern 2 — Extraction for Extraction's Sake

**Pattern:** Moving code to a separate file without reducing coupling or improving testability.
**Risk:** Complexity increases (now need to track two files) without benefit.
**Rule:** Only extract when: (a) the function is reused in 2+ places, OR (b) the function is a pure utility testable in isolation, OR (c) operator explicitly requests it.

### Anti-Pattern 3 — Premature Phase 3 Extraction

**Pattern:** Extracting tab renderers before Phase 1 and Phase 2 are stable.
**Risk:** Tab renderers are stateful — extracting them before low-risk helpers creates entangled extraction dependencies.
**Rule:** Phase 3 does not begin until Phase 2 is stable for ≥3 sessions AND operator approves.

### Anti-Pattern 4 — Skinny-File Theater

**Pattern:** Extracting a 5-line helper to its own file to make app.py "look modular."
**Risk:** Import overhead. No real decoupling. Cognitive overhead of tracking micro-files.
**Rule:** Minimum extraction target: functions that appear in ≥2 contexts OR functions >30 lines that are purely utility.

### Anti-Pattern 5 — Extraction During Active Feature Work

**Pattern:** Extracting a module while simultaneously adding features to it.
**Risk:** Extraction and feature changes are entangled — cannot isolate which change caused regression.
**Rule:** No feature work during extraction steps. Extraction is a behavior-preserving operation only.

### Anti-Pattern 6 — State-Passing Avoidance

**Pattern:** Extracted module accesses `st.session_state` directly because "passing it as an argument is verbose."
**Risk:** C2 contamination (see Deliverable 10). Module is no longer extractable or testable.
**Rule:** Verbosity is acceptable. State access from extracted modules is not.

### Anti-Pattern 7 — Validation Skipping Under Time Pressure

**Pattern:** Skipping L3 (tab navigation) or L4 (Full Slate run) validation because "the change was small."
**Risk:** Small changes in shared-scope files have outsized impact. Skipped validation = unknown state.
**Rule:** All 5 validation levels required for every extraction step. No exceptions.

### Anti-Pattern 8 — Rewrite Culture Creep

**Pattern:** "While I'm extracting this, I should also improve/clean/refactor the surrounding code."
**Risk:** Scope creep. Behavioral change. Regression risk. Blame ambiguity when regression is found.
**Rule:** Extraction is behavior-preserving ONLY. Adjacent code improvements require a separate, explicitly authorized session.

### Anti-Pattern 9 — Ownership Drift

**Pattern:** Claude extracts a module, Codex modifies it, operator assumes Claude still owns it.
**Risk:** Conflicting modifications. Inconsistent validation expectations.
**Rule:** Ownership is declared before extraction. Owner changes require operator authorization.

### Anti-Pattern 10 — Framework Migration Panic

**Pattern:** "While we're modularizing, should we switch from Streamlit to Next.js?"
**Risk:** Scope explosion. All current stabilization work is lost. Timeline becomes unbounded.
**Rule:** Framework migration is not on the modularization roadmap. Modularization improves the current architecture — it does not replace it.

---

## DELIVERABLE 12: RECOVERY / ROLLBACK DOCTRINE

### Rollback Trigger Matrix

| Severity | Trigger | Rollback Speed | Approval Required |
|----------|---------|---------------|-------------------|
| P0 | Protected system regression | Immediate | None — Claude executes immediately |
| P1 | Tab render failure (any tab) | Immediate | None — Claude executes immediately |
| P1 | `st.session_state` KeyError | Immediate | None — Claude executes immediately |
| P1 | Pipeline schema mismatch | Immediate | None — Claude executes immediately |
| P1 | Escalation hierarchy failure | Immediate | None — Claude executes immediately |
| P2 | Intermittent render issue | Next session | Operator notification |
| P3 | Non-critical display regression | Scheduled | Operator approval |
| Discretionary | Operator declares | Immediate | N/A (operator initiated) |

### Rollback Procedure

**Step 1 — Document the failure (before touching anything):**
```
Failure: [exact error message or observed behavior]
Extraction step: [Phase X, Step Y, target module]
Timestamp: [when observed]
Validation level that failed: [L1/L2/L3/L4/L5]
```

**Step 2 — Execute rollback:**
```bash
git revert <extraction-commit>
# OR
git checkout HEAD~1 -- <extracted_module_path>
git checkout HEAD~1 -- app.py  # restore original import
```

**Step 3 — Verify rollback:**
- Cold start → no error
- All 5 tabs render → no regression
- Full Slate run → matches pre-extraction baseline

**Step 4 — Notify operator:**
- Share failure documentation
- Share rollback confirmation
- Await operator decision: resume, redesign, or freeze

**Rule:** Do not attempt to fix in-place during rollback. Restore first. Diagnose second.

### Recovery Doctrine

After a rollback, before re-attempting extraction:
1. Root-cause the failure (why did extraction cause regression?)
2. Redesign the extraction boundary (was the target actually Phase 1 safe?)
3. Re-run pre-extraction checklist (Section 11.1 of master doc)
4. Operator approval required before re-attempting same target
5. ≥2 consecutive clean cold-start passes before re-attempting

### Rollback Authority Chain

| Actor | Can Initiate | Approval Needed |
|-------|-------------|-----------------|
| Claude | P0/P1 rollback | None — execute immediately |
| Claude | P2/P3 rollback | Operator notification (post-hoc) |
| Claude | Rollback of rollback (re-extract) | Operator approval required |
| Codex | Any rollback | Claude oversight + operator notification |
| Operator | Any rollback | N/A — operator authority is absolute |

### Total Extraction Freeze

Operator may declare Total Extraction Freeze at any time.

Effect:
- All extraction activity halts immediately
- No new extraction steps begin
- In-progress extraction reverts
- Freeze lifts only with explicit operator statement

Cannot be overridden by Claude or Codex.

---

## DELIVERABLE 13: FINAL MODULARIZATION HIERARCHY SUMMARY

### Authoritative Governance Pyramid

```
                    ┌─────────────────────────────────────┐
                    │  master_modularization_              │  ← Rank 1: ABSOLUTE AUTHORITY
                    │  governance_framework_v1.md          │     Resolves all conflicts
                    └────────────────┬────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ production_       │  │ runtime_         │  │ validation_      │  ← Rank 2-4
   │ extraction_       │  │ isolation_       │  │ runtime_         │     Gate + Law
   │ readiness_v1.md   │  │ boundary_v1.md   │  │ verification_v1  │     + Authority
   └──────────────────┘  └──────────────────┘  └──────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ extraction_       │  │ phase1_          │  │ modularization_  │  ← Rank 5-7
   │ execution_        │  │ extraction_      │  │ dependency_      │     Execution
   │ governance_v1.md  │  │ prioritization_  │  │ audit_v1.md      │     + Ordering
   └──────────────────┘  └──────────────────┘  └──────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────┐
                    │  controlled_modularization_          │  ← Rank 8: Foundation
                    │  doctrine_v1.md                      │     All docs inherit from this
                    └─────────────────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────┐
                    │  phase4_modularization_              │  ← Phase 4 Entry Point
                    │  synthesis_doctrine_v1.md (THIS)     │     13-deliverable synthesis
                    └─────────────────────────────────────┘
```

### Extraction Phase Summary

| Phase | Targets | Risk | Observation | Operator Gate |
|-------|---------|------|-------------|---------------|
| 1 | Formatting, constants, pure math | LOW | 1 session/step | Phase start only |
| 2 | Stateless filters, rankers, table builders | MEDIUM | 2 sessions/step | Per-step approval |
| 3 | Tab renderers, sidebar, card components | HIGH | 3 sessions/step | Per-step approval |
| NEVER | Routing, session_state, cache, shell, pipeline contract | ABSOLUTE | N/A | Never lift without operator |

### Protected Systems Summary

All systems marked ABSOLUTE in Deliverable 2 (Ownership Zones) are frozen.
No extraction. No rewrite. No import change. No structural modification.
Lift authority: Operator only, written authorization.

### Go/No-Go Gate Summary

```
GO (ALL must be true):
  ✓ All 5 tabs render clean (≥3 consecutive cold starts)
  ✓ No active runtime regression
  ✓ Rollback demonstrated on dry run
  ✓ Branch isolated from main
  ✓ Calibration bias within threshold (|bias|<3pp at n≥50)
  ✓ Operator explicit authorization: "Ready to begin Phase 1 extraction."

NO-GO (ANY blocks):
  ✗ Any open runtime incident
  ✗ Active operator freeze
  ✗ Calibration alert active
  ✗ Full Slate orchestration unstable
  ✗ Branch not isolated
  ✗ Operator authorization not given
```

### Contamination Prevention Summary

10 contamination risks identified (C1-C10). Prevention requires:
- No upward imports
- No session_state writes in extracted modules
- No cache decorators in extracted modules
- No pipeline calls in render functions
- Always cold-start validation
- One declared owner per module

### UX Discipline Summary

10 UX anti-patterns identified (AP1-AP10). Core rule:
**Extraction is behavior-preserving only.**
No rewrite culture. No framework panic. No scope creep.
Surgical, sequential, stabilization-first.

---

## DOCUMENT METADATA

```
Document:     phase4_modularization_synthesis_doctrine_v1.md
Status:       COMPLETE — Phase 4 Planning Governance
Phase:        Phase 4, Step 01/12
Owner:        Claude (governance); Operator (authority)
Created:      2026-05-23
Inherits:     master_modularization_governance_framework_v1.md (Rank 1)
Adds:         UX anti-patterns (AP1-AP10), Contamination catalog (C1-C10), Phase 4 entry framing
Supersedes:   Nothing — supplements existing 8 Room 09 docs
Review:       Required before Phase 1 extraction begins
```

---

*Phase 4 governance synthesis complete. All 13 deliverables covered.*
*No production changes. No files moved. No code modified.*
*Next: Operator explicit authorization to begin Phase 1 extraction.*
