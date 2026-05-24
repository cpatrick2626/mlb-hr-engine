# Runtime Isolation & Boundary Architecture Doctrine v1
## MLB HR Engine v4 — Permanent Runtime Boundary Law & Execution Ownership Governance

**Document Status:** Architecture Governance Doctrine — Planning Only  
**Phase:** Division 09 — Step 5/8 Runtime Boundary Architecture  
**Owner:** Claude (Architecture Governance)  
**Date:** 2026-05-23  
**Runtime Systems:** FROZEN (no production changes from this document)  
**Preceding Doctrines:**
- `controlled_modularization_doctrine_v1.md` — architecture targets, protected zones, phase map
- `modularization_dependency_audit_doctrine_v1.md` — dependency classification, hidden contracts, audit workflow
- `extraction_execution_governance_doctrine_v1.md` — extraction lifecycle, rollback standards, validation gates
- `phase1_extraction_prioritization_doctrine_v1.md` — extraction sequencing, risk tiers, readiness scoring

---

## Table of Contents

1. [Purpose of Runtime Isolation](#1-purpose-of-runtime-isolation)
2. [Core Architectural Philosophy](#2-core-architectural-philosophy)
3. [Runtime Layer Hierarchy](#3-runtime-layer-hierarchy)
4. [Ownership Boundary Doctrine](#4-ownership-boundary-doctrine)
5. [Legal Dependency Directions](#5-legal-dependency-directions)
6. [State Isolation Doctrine](#6-state-isolation-doctrine)
7. [Tactical Isolation Doctrine](#7-tactical-isolation-doctrine)
8. [Shell Boundary Doctrine](#8-shell-boundary-doctrine)
9. [Cache Ownership Doctrine](#9-cache-ownership-doctrine)
10. [Runtime Communication Contracts](#10-runtime-communication-contracts)
11. [Validation Boundary Doctrine](#11-validation-boundary-doctrine)
12. [Forbidden Architectural Patterns](#12-forbidden-architectural-patterns)
13. [Future-State Runtime Vision](#13-future-state-runtime-vision)

**Appendices:**
- [A. Runtime Layer Diagram](#appendix-a-runtime-layer-diagram)
- [B. Dependency Direction Matrix](#appendix-b-dependency-direction-matrix)
- [C. Ownership Responsibility Matrix](#appendix-c-ownership-responsibility-matrix)
- [D. Forbidden Pattern Examples](#appendix-d-forbidden-pattern-examples)
- [E. Future Thin-Orchestrator Example](#appendix-e-future-thin-orchestrator-example)

---

## 1. Purpose of Runtime Isolation

### 1.1 Why Boundary Law Is Required

The prior doctrines in this series established *what* to extract, *when* to extract it, and *how* to execute extractions safely. This doctrine answers a different question: **what structural laws must govern extracted modules in perpetuity so that the system never devolves back into entanglement.**

Extraction without boundary law is an unstable equilibrium. Modules extracted today will be modified tomorrow. Without codified ownership rules, future modifications will re-introduce cross-layer coupling, rerender contamination, and state mutation outside authorized zones — the same defects that made app.py dangerous at 10,706 lines. The purpose of this doctrine is to make those defects structurally impossible, not merely unlikely.

Boundary law must be defined **before** extraction begins, because it determines:
- Which files may import which other files
- Which layers may write to session_state
- Which systems own cache lifetimes
- Which modules may call orchestration functions
- How tactical intelligence reaches the render layer without polluting it

Without these rules defined in advance, every extraction decision is an ad hoc judgment call that accumulates inconsistency across sessions.

### 1.2 Hidden Contamination Risks

Cross-layer contamination does not announce itself. It manifests as subtle degradation weeks after the contaminating change was introduced:

| Contamination Type | Trigger | Symptom |
|-------------------|---------|---------|
| Import contamination | Lower layer imports upper layer | Circular import error; or worse, silent circular scope at startup |
| State write contamination | Non-owner module writes session_state key | Key initialized twice; second init overwrites first, timing-dependent |
| Cache contamination | Extracted module re-decorates already-cached function | Two cache identities for same data; one stale, one fresh — race condition |
| Rerender contamination | Extracted module mutates state during render phase | Phantom rerenders on every page load; investigation atmosphere degrades |
| Orchestration contamination | Render module calls pipeline directly | Double pipeline execution; latency spike; data inconsistency |

All five contamination types have occurred in the current system (confirmed by Phase 3A stabilization history). All five must be made structurally illegal by this doctrine.

### 1.3 Orchestration Leakage Risks

Orchestration leakage is a specific contamination class: **logic that belongs in the orchestration layer appearing in rendering, tactical, or state modules.** Leakage mechanisms:

- Render functions calling `pipeline.run()` or `build_player_profiles()` directly
- Tactical scoring modules fetching their own fresh data (bypassing pipeline cache)
- State initialization modules invoking fetch clients
- Shell modules dispatching to Full Slate scoring chains

Leakage is insidious because it often *works* initially. The module gets its data, renders correctly, and passes visual inspection. But it has forked the execution graph: the same data may now be fetched twice, the cache may hold two different versions of the same date's picks, and the pipeline's ownership of execution sequencing is broken.

### 1.4 UI/Runtime Coupling Dangers

Streamlit's execution model couples UI rendering and Python logic in ways that are not present in traditional web frameworks. Every `st.session_state` write triggers a rerender. Every `st.write()`, `st.dataframe()`, or `st.metric()` call is both a display operation and a side effect on the Streamlit execution graph.

This means UI coupling is not merely a code quality concern — it is a **runtime safety concern**:

- A display function that writes session_state is a hidden state mutation
- A tactical scoring function that calls `st.spinner()` is a hidden render operation
- A data service that reads `st.session_state` for configuration is a hidden UI dependency

All three patterns are present in the current system. Boundary law must explicitly prohibit each one.

---

## 2. Core Architectural Philosophy

### 2.1 Deterministic Execution

**Law:** Given identical inputs (date, picks, session state at startup), the system must produce identical outputs on every execution path.

Non-determinism currently enters via:
- Different modules fetching data at different moments (stale/fresh race)
- State initialization order varying by navigation path
- Cache invalidation triggered by non-deterministic events (module move, function rename)

All future architectural decisions must be evaluated against this law. An extraction that introduces execution-path-dependent results is prohibited regardless of functional correctness.

### 2.2 Single Ownership

**Law:** Every runtime resource (session_state key, cache slot, data object, orchestration chain) has exactly one owner. No resource may have zero owners (orphan) or two owners (split control).

Ownership is not a file-level concept. A module "owns" a resource if it is the sole authorized writer to that resource. Readers may be multiple; writers must be singular.

| Resource Type | Owner Definition |
|--------------|-----------------|
| session_state key | The single module authorized to initialize and update that key |
| @st.cache_data slot | The single decorated function that creates and owns that cache entry |
| Pipeline output | The pipeline module that produces it; downstream modules are consumers only |
| Orchestration chain | The orchestrator that sequences it; no child module may re-enter the chain |
| Tactical score | The scoring module that computes it; display modules receive a copy only |

### 2.3 Downward-Only Dependency Flow

**Law:** Dependencies flow downward only. Upper layers may import lower layers. Lower layers must never import upper layers.

This produces a strict DAG (directed acyclic graph) — no cycles possible by construction. The layer hierarchy (Section 3) defines the ordering. Any import that flows upward violates this law regardless of functionality.

### 2.4 Orchestration Isolation

**Law:** Orchestration logic (data fetching, pipeline sequencing, scoring chain invocation) must never appear inside rendering, state, or utility modules.

The orchestrator is the entry point for all data work. Every module below it receives data already produced. No module below the orchestrator layer may initiate a new data operation.

### 2.5 Tactical Containment

**Law:** Tactical intelligence systems (Full Slate, JIG, MAIN, Performance, Strategy) are isolated execution domains. They may receive inputs from the orchestration layer and return outputs to the display layer. They must not invoke each other, write shared state, or access rendering functions.

### 2.6 Rollback-Safe Architecture

**Law:** Every module must be independently disableable without system collapse. If a module is toggled off or reverted to its prior location, all other modules must continue to function correctly.

This law prohibits tight coupling between modules — any inter-module dependency must be mediated by a contract (defined data shape, stable API), not by direct internal access.

---

## 3. Runtime Layer Hierarchy

### 3.1 Layer Definitions

Layers are ordered from highest (most authority) to lowest (most isolated). Each layer may only import from layers **below** it. Communication upward is prohibited.

```
LAYER 0 — SHELL
LAYER 1 — ORCHESTRATION
LAYER 2 — TACTICAL INTELLIGENCE
LAYER 3 — RENDERING
LAYER 4 — STATE
LAYER 5 — SERVICES
LAYER 6 — DATA
LAYER 7 — UTILITIES
LAYER 8 — VALIDATION
```

### 3.2 Layer Descriptions

**Layer 0 — Shell**  
The persistent runtime container. Owns navigation lifecycle, viewport structure, modal governance, and contextual rails. Never destroyed between page navigations. Imports from all layers. Does NOT initiate data work. Does NOT own tactical logic.

*Current files:* app.py (startup block), navigation_continuity.py, nav_state.py

**Layer 1 — Orchestration**  
The execution entry point for all data operations. Sequences pipeline execution, invokes scoring chains, manages pipeline cache, coordinates tactical module dispatch. Single entry point per execution path.

*Current files:* pipeline.py, app.py (orchestration sections — to be extracted)

**Layer 2 — Tactical Intelligence**  
Isolated scoring and classification domains. Each tactical system is a self-contained execution unit: receives structured input, returns structured output. Zero shared state between tactical modules. Zero Streamlit imports.

*Current files:* strategies/, engine/ modules, portfolio/ modules, filter_controls.py (scoring logic only)

**Layer 3 — Rendering**  
Pure display functions. Accepts pre-computed data objects. Emits Streamlit output. Does NOT compute scores. Does NOT mutate session_state. Does NOT fetch data. Each render function is stateless relative to the data it displays.

*Current files:* app.py (rendering sections — to be extracted), components/ modules

**Layer 4 — State**  
Session state governance. Owns initialization order, key registry, and state migration. Only layer authorized to write session_state (except controlled exceptions documented in Section 6). All other layers read session_state but do not write it.

*Current files:* investigation_state.py, nav_state.py (state sections)

**Layer 5 — Services**  
External interface adapters. Wraps API clients, file I/O, Google Sheets, CLV capture. Does NOT interpret results — passes raw data upward. Stateless per call (no session_state dependency).

*Current files:* clients/ directory, tracking/ modules

**Layer 6 — Data**  
Static reference data, park factors, configuration constants, manual odds fallback. Pure data — no computation. Never imports from Layers 0–5.

*Current files:* data/ directory, config.py, manual_odds.csv

**Layer 7 — Utilities**  
Pure functions with no external dependencies. String manipulation, math helpers, formatting, date utilities. Zero imports from Layers 0–6 (except Layer 6 config constants where needed).

*Current files:* engine/market.py, engine/ev.py, engine/sizing.py (pure math sections)

**Layer 8 — Validation**  
Runtime assertion and schema checking. Stateless. Called by any layer to verify data contract compliance at boundary crossings. Zero side effects.

*Current files:* tracking/data_integrity.py, backtest validation modules

### 3.3 Layer Authority Matrix

| Operation | L0 Shell | L1 Orch | L2 Tactical | L3 Render | L4 State | L5 Services | L6 Data | L7 Utils | L8 Valid |
|-----------|----------|---------|------------|----------|---------|-----------|--------|---------|---------|
| Init session_state | Trigger only | ✗ | ✗ | ✗ | ✓ Owner | ✗ | ✗ | ✗ | ✗ |
| Write session_state | ✗ | Controlled | ✗ | ✗ | ✓ Owner | ✗ | ✗ | ✗ | ✗ |
| Read session_state | ✓ | ✓ | Read-only | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Invoke pipeline | ✗ | ✓ Owner | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Invoke tactical | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Call API/fetch | ✗ | Via L5 | ✗ | ✗ | ✗ | ✓ Owner | ✗ | ✗ | ✗ |
| Emit st.* output | ✓ | ✗ | ✗ | ✓ Owner | ✗ | ✗ | ✗ | ✗ | ✗ |
| Own cache slots | ✗ | ✓ Owner | ✗ | ✗ | ✗ | Via L1 | ✗ | ✗ | ✗ |
| Navigation control | ✓ Owner | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Validate data shape | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ Owner |

---

## 4. Ownership Boundary Doctrine

### 4.1 Execution Ownership

**Execution** (who initiates data work and pipeline sequencing):  
Owner: **Layer 1 — Orchestration** (pipeline.py, future orchestrator module)

No module outside Layer 1 may initiate a data fetch, pipeline run, or scoring chain invocation. If a rendering module needs fresh picks, it must request them through the orchestration layer, not by calling services directly.

Enforcement: Any `import clients.*` or `import pipeline` statement appearing in Layers 2–8 is a boundary violation.

### 4.2 Rendering Ownership

**Rendering** (who calls `st.*` display functions):  
Owner: **Layer 3 — Rendering** (display modules, components/)

Layer 0 (Shell) also calls `st.*` for layout structure and navigation chrome. This is permitted because the shell owns viewport structure.

No module outside Layers 0 and 3 may call Streamlit display functions. Tactical modules (Layer 2) must not emit `st.write()`, `st.metric()`, `st.dataframe()`, or any other Streamlit output. They return data objects; rendering modules display them.

Enforcement: Any `import streamlit` statement in Layers 2, 4–8 is a boundary violation.

### 4.3 State Ownership

**Session State** (who initializes and updates `st.session_state` keys):  
Owner: **Layer 4 — State** (investigation_state.py, nav_state.py, future state_registry module)

All session_state keys must be registered in the state layer's key registry before use. No key may be created inline in a rendering or tactical module. Navigation-driven state updates (route changes) are processed by Layer 4 in response to Layer 0 navigation events — not by Layer 0 directly.

One controlled exception: Layer 1 (Orchestration) may write a small set of pipeline-output keys (defined in the state registry) to transfer execution results into the render path. These keys are explicitly registered and documented.

### 4.4 Tactical Intelligence Ownership

**Tactical scoring and classification** (Full Slate, JIG, MAIN, Performance, Strategy):  
Owner: **Layer 2 — Tactical Intelligence** (strategies/, engine/ computation modules)

Tactical modules own their scoring chains end-to-end. The orchestrator invokes them with structured input and receives structured output. Nothing else may invoke tactical modules — not rendering functions, not state modules, not the shell.

Tactical output is a data object (dict or dataclass). Rendering modules receive this object and display it. They do not re-invoke the tactical chain to refresh it.

### 4.5 Cache Ownership

**@st.cache_data slots**:  
Owner: **Layer 1 — Orchestration** (pipeline.py)

All cache-decorated functions live in the orchestration layer. No other module may define `@st.cache_data` or `@st.cache_resource` decorators. If an extracted module needs to cache computation, it must expose a pure function and the orchestration layer wraps it with caching.

Enforcement: Any `@st.cache_data` or `@st.cache_resource` decorator appearing outside pipeline.py (or its designated successor) is a boundary violation.

### 4.6 Validation Ownership

**Runtime data shape checking**:  
Owner: **Layer 8 — Validation** (data_integrity.py, validation utilities)

Any layer may *call* validation functions at boundary crossings. Only Layer 8 may *implement* validation logic. This prevents validation logic from fragmenting across layers.

---

## 5. Legal Dependency Directions

### 5.1 Allowed Imports by Layer

| Importing Layer | May Import From |
|----------------|----------------|
| L0 Shell | L1, L2 (output only), L3, L4, L5 (via L1), L6, L7, L8 |
| L1 Orchestration | L2, L4 (read), L5, L6, L7, L8 |
| L2 Tactical Intelligence | L6, L7, L8 only |
| L3 Rendering | L4 (read), L6, L7, L8 only |
| L4 State | L6, L7, L8 only |
| L5 Services | L6, L7, L8 only |
| L6 Data | L7, L8 only |
| L7 Utilities | L8 only (or nothing) |
| L8 Validation | Nothing (or L7 math-only) |

### 5.2 Forbidden Imports

The following import relationships are categorically forbidden regardless of apparent functionality:

| From | To | Reason |
|------|----|--------|
| L2 Tactical | L0 Shell | Tactical logic must not know UI exists |
| L2 Tactical | L1 Orchestration | Tactical cannot re-enter pipeline |
| L2 Tactical | L3 Rendering | Tactical must not emit display output |
| L2 Tactical | L4 State | Tactical must not write session_state |
| L2 Tactical | L5 Services | Tactical must not fetch data |
| L3 Rendering | L1 Orchestration | Render cannot invoke pipeline |
| L3 Rendering | L2 Tactical | Render cannot invoke scoring chains |
| L3 Rendering | L5 Services | Render cannot fetch data |
| L4 State | L0 Shell | State module must not import Streamlit shell |
| L4 State | L1 Orchestration | State cannot invoke pipeline |
| L5 Services | L0–L4 | Services are stateless adapters only |
| L6 Data | L0–L5 | Pure reference data, no runtime imports |
| L7 Utilities | L0–L6 | Pure functions, no framework imports |
| L8 Validation | L0–L6 | Stateless validators, no side effects |

### 5.3 Upward Dependency Prohibition

**No module may import a module in a higher layer.** This is the single most important import rule and covers all specific forbidden cases in Section 5.2 as special cases of the general law.

The practical test: if Module A imports Module B, and B is in a higher layer than A, the import is illegal and must be resolved by:
1. Moving the shared logic down to a layer both can import
2. Passing the needed value as a function argument (data contract) rather than importing
3. Inverting the dependency so B provides a callback that A invokes

### 5.4 Orchestration-Only Communication Paths

Certain communication paths are restricted to the orchestration layer to prevent leakage:

| Communication | Allowed Path | Forbidden Paths |
|--------------|-------------|----------------|
| Raw API data → picks | L5 → L1 → L2 | L5 → L2 (direct), L5 → L3 |
| Picks → display | L1 → L4 (write key) → L3 (read key) | L1 → L3 (direct), L2 → L3 (direct) |
| Scoring result → UI | L2 → L1 (return) → L4 (write) → L3 (read) | L2 → L3 (direct) |
| Navigation event → state | L0 → L4 | L0 → L1, L0 → L3 |

---

## 6. State Isolation Doctrine

### 6.1 Session State Ownership Zones

All `st.session_state` keys are partitioned into ownership zones. Each zone has exactly one owner.

| Zone | Key Prefix Convention | Owner | Legal Writers |
|------|--------------------|-------|---------------|
| Navigation | `nav_*`, `route_*`, `active_route` | L4 nav_state.py | L4 only |
| Investigation | `inv_*`, `investigation_*`, `active_workspace` | L4 investigation_state.py | L4 only |
| Pipeline Output | `picks_*`, `pipeline_*`, `slate_*` | L1 via L4 registry | L1 (controlled write) |
| Tactical State | `jig_*`, `main_*`, `fs_*`, `perf_*`, `strat_*` | L4 (tactical registry) | L1 on behalf of L2 |
| UI Ephemeral | `ui_*`, `modal_*`, `filter_*` | L0 Shell or L3 (documented exceptions) | L0 Shell only |
| System | `hydration_*`, `continuity_*`, `fingerprint_*` | L4 system registry | L4 only |

### 6.2 Legal State Writers

The complete set of legal state writers, by key zone:

- **Navigation keys:** `nav_state.py` (L4) only. Shell (L0) triggers navigation; L4 processes it.
- **Investigation keys:** `investigation_state.py` (L4) only. Tactical modules return updated investigation context to L1; L1 passes it to L4 for writing.
- **Pipeline output keys:** `pipeline.py` (L1) only, using keys registered in L4's key registry. Written once per execution cycle. Never written by L3 display functions.
- **Tactical state keys:** L1 orchestration on behalf of completed tactical modules. Never written by the tactical modules themselves.
- **UI ephemeral keys:** L0 Shell for navigation-driven UI state. L3 Rendering is forbidden from writing any session_state key — all UI-driven state flows through L0 or L4.

### 6.3 State Mutation Boundaries

**All session_state writes must occur before any `st.*` render call in the execution path.**

Streamlit's execution model evaluates top-to-bottom. State writes that occur after display calls produce rerenders on the *next* cycle, not the current one. This creates one-frame lag in UI updates and is the source of investigation atmosphere flicker.

Enforcement rule: In any function that both writes session_state and calls `st.*` display functions, the state writes must all precede the display calls. If this ordering cannot be maintained, the state write must be moved to a state-layer function called before the display function.

### 6.4 State Tracing Rules

When a new session_state key is introduced anywhere in the system, the following must be documented in the state registry:

```
KEY: [key_name]
ZONE: [navigation | investigation | pipeline_output | tactical | ui_ephemeral | system]
OWNER: [file:function]
INIT_VALUE: [initial value]
INIT_LOCATION: [file:line]
WRITERS: [list of authorized writer locations]
READERS: [all modules that read this key]
INVALIDATION: [conditions that reset this key]
```

No key may be created without a registry entry.

### 6.5 Forbidden State Coupling

The following state patterns are structurally forbidden:

- **Cross-zone coupling:** A tactical state key initialized by reading a navigation state key at init time. Zones are independent; initialization must not chain across zones.
- **Display-driven state:** A render function writing session_state in response to user interaction without routing the event through L0/L4. All user interaction events must be handled by the shell layer, not by display modules.
- **Implicit key creation:** `st.session_state.some_new_key = value` appearing anywhere outside the state layer. This creates an unregistered, unowned key.
- **Cross-module state reads without registry:** A module reading a session_state key that belongs to another module's zone without being listed in that key's reader registry.

---

## 7. Tactical Isolation Doctrine

### 7.1 Protected Tactical Systems

The following tactical systems are isolated execution domains. Each is treated as an opaque function: receives structured input, returns structured output, with zero side effects.

| System | Description | Input Contract | Output Contract |
|--------|-------------|---------------|----------------|
| Full Slate | Complete daily HR threat generation | Pipeline picks dict, date, config | Ranked threat list + escalation metadata |
| JIG | Jackpot Intelligence Grid — high-conviction picks | Filtered picks, barrel thresholds | JIG row list + confidence scores |
| MAIN | Main slate display picks | Filtered picks, EV/edge filters | MAIN row list + ranked composite |
| Performance | Historical P&L and CLV tracking | Settled pick CSV, date range | Performance metrics dict |
| Strategy | Bet sizing and portfolio optimization | Picks + constraints + bankroll | Optimized slate + sizing recommendations |

### 7.2 Tactical Isolation Rules

1. **No shared state between tactical systems.** Full Slate results must never be used as JIG inputs in a single execution cycle. Each system receives its data from the orchestration layer independently.

2. **No Streamlit imports inside tactical modules.** If a file in `strategies/` or `engine/` contains `import streamlit`, it is a boundary violation. Display adapters live in L3; tactical logic in L2.

3. **No tactical system may invoke another tactical system.** Full Slate does not call JIG scoring. MAIN does not invoke Strategy optimization. The orchestrator sequences their execution; they do not sequence each other.

4. **Tactical scoring chains are single-entry-point.** Each tactical system has one function that serves as its public interface. The orchestrator calls that function. No other entry point into the tactical system is permitted.

5. **Tactical output is immutable from the producing system's perspective.** Once a tactical module returns its output object, it has no further authority over that object. The orchestrator may modify, filter, or cache it.

### 7.3 Escalation System Containment

The escalation hierarchy (escalation tiers, threat levels, suppression indicators, archetype classification) is owned by the Full Slate tactical system. Escalation decisions are computed inside Full Slate and returned as part of its output contract.

The rendering layer reads escalation metadata from the output object and displays it. It must not re-compute escalation tiers, re-classify archetypes, or modify suppression state. Display of escalation is passive — reading and rendering a pre-computed result.

No module outside the Full Slate system may modify escalation tier assignment.

### 7.4 JIG/MAIN Dispatcher Governance

The JIG/MAIN dispatch logic (which view is currently active, which picks are shown in which system) is owned by the shell navigation layer (L0) and state layer (L4). The dispatcher reads session_state navigation keys and selects which tactical output to display.

This is the critical boundary: the dispatcher **selects** tactical output for display but does not **invoke** tactical scoring. If the required tactical output is not in session_state (cache miss or fresh session), the dispatcher signals the orchestration layer to run the needed tactical chain. It does not run the chain itself.

---

## 8. Shell Boundary Doctrine

### 8.1 Persistent Shell Ownership

The shell (Layer 0) is the persistent runtime container that survives across Streamlit rerenders and navigation events. It owns:

- Viewport layout structure (column configuration, sidebar organization)
- Navigation chrome (contextual rails, route indicators, breadcrumbs)
- Modal governance (which modal is open, modal z-index hierarchy)
- Hydration fingerprint guard (detects partial hydration; blocks display until complete)
- `navigation_continuity.py` startup logic (session initialization sequencing)

The shell is the only layer that exists before any data is loaded. It renders structural chrome before pipeline data is available.

### 8.2 Navigation Boundaries

Navigation events flow in one direction: user interaction → shell (L0) → state layer (L4) → state keys updated → downstream modules read new route.

The shell must not:
- Invoke the pipeline in response to navigation events (that is L1's job)
- Compute tactical scores to determine what navigation options are available
- Read pipeline output to construct navigation chrome (navigation is state-driven, not data-driven)
- Pass data objects between views via navigation events (use session_state pipeline output keys)

The shell triggers the orchestration layer when a navigation event requires fresh data (e.g., route change to a date not currently in cache). It does not execute the pipeline itself.

### 8.3 Contextual Rails Isolation

The contextual rails (the persistent right-side intelligence panel in current implementation) display pre-computed tactical metadata. This is a rendering operation (L3), not a shell operation. The rail is *mounted* by the shell within the viewport structure, but its content is rendered by L3 display functions reading pre-computed data from session_state.

The shell must not compute what to show in the rails. It must not read raw picks and decide escalation tier. It reads a pre-computed rail content object from session_state and passes it to the L3 rail renderer.

### 8.4 Viewport Isolation

Each viewport region (main content area, sidebar, contextual rails, modal overlay) is owned by one module. Multiple modules may contribute display elements within a region, but one module governs the region's layout contract.

| Viewport Region | Layout Owner | Content Producers |
|----------------|-------------|------------------|
| Main content | L0 Shell (layout) | L3 view-specific display modules |
| Sidebar | L0 Shell (layout) | L3 sidebar components |
| Contextual rails | L0 Shell (mount) | L3 rail renderer |
| Modal overlay | L0 Shell (z-index) | L3 modal components |

### 8.5 Modal Containment

Modals are display components (L3) mounted inside a shell-governed overlay region. The shell maintains the "is_modal_open" and "current_modal" state keys (via L4). Display modules may *request* a modal open by signaling through L4 state, but they must not render the modal overlay themselves.

The modal rendering sequence:
1. User interaction triggers modal request in L3 display module
2. L3 signals L4 state layer (modal_open=True, modal_target=X)
3. L0 shell detects modal state change and renders overlay region
4. L3 modal component renders content within the shell's overlay structure

This sequence ensures modals never cause double-render artifacts from competing overlay ownership.

---

## 9. Cache Ownership Doctrine

### 9.1 Cache Ownership Hierarchy

All `@st.cache_data` and `@st.cache_resource` decorators must reside in the orchestration layer (L1 — pipeline.py or its designated successor). This is a hard constraint, not a preference.

**Rationale:** Cache identity in Streamlit is determined by the decorated function's identity (module path + function name) and its arguments. When a function moves files, its cache identity changes — the warm cache is silently invalidated and the function re-executes. If cache decorators are scattered across multiple modules, any modularization activity will trigger unpredictable cache invalidations.

By concentrating all caches in L1, cache identity is stable across all modularization activity in Layers 2–8.

### 9.2 Cache Invalidation Authority

Only the orchestration layer (L1) may explicitly invalidate cached data (via `cache_function.clear()`). No other layer has invalidation authority.

If a lower-layer module detects a condition requiring cache refresh (e.g., data staleness check in a service module), it must signal this condition upward to L1 (via a return value or state flag), not perform the invalidation itself.

### 9.3 Extraction Constraints on Cache

When a function currently decorated with `@st.cache_data` in app.py is extracted to a lower-layer module:

1. The `@st.cache_data` decorator must be **removed** from the extracted function
2. The decorator must be **re-applied** in L1 to a wrapper function that calls the extracted function
3. The cache key (function arguments) must be identical to preserve cache continuity
4. Cache continuity testing is required before extraction is considered complete

This is not optional. Extracting a cached function without moving the decorator produces a silently uncached function — performance regression with no visible error.

### 9.4 Cache Visibility Boundaries

Cached objects must not be mutated by consuming modules. If a module receives a cached list of picks and modifies it (sorts, filters, appends), the modification must be to a **copy** of the cached object, not the cached object itself. Python's caching semantics do not protect against in-place mutation; mutation of a cached object propagates the mutation to all subsequent cache readers within the same Streamlit session.

Enforcement: All cached objects returned by pipeline.py must be treated as immutable. Consuming modules must call `copy()` or `dict(obj)` before modification.

---

## 10. Runtime Communication Contracts

### 10.1 Orchestration-to-Render Communication

The orchestration layer (L1) communicates results to the rendering layer (L3) exclusively through session_state keys registered in the L4 state registry.

**Prohibited:** L1 calling L3 rendering functions directly with data arguments.  
**Prohibited:** L3 importing L1 to pull pipeline results.  
**Required:** L1 writes results to registered session_state keys. L3 reads those keys.

This indirection is not bureaucracy — it is the only communication pattern that survives Streamlit's rerender model. Direct function calls between L1 and L3 produce data-coupling that breaks when rerenders are triggered mid-execution.

### 10.2 Render-to-State Restrictions

Rendering modules (L3) may read session_state. They must not write session_state.

One narrow documented exception: interactive widget state (e.g., `st.session_state.filter_slider_ev`) created by Streamlit widget calls is implicitly written by the Streamlit runtime, not by the display module. These keys must be registered in the UI Ephemeral zone of the state registry and must be treated as read-only by all non-shell modules.

If a rendering module needs to trigger a state change in response to user interaction, it must expose the interaction as a signal that L0 Shell reads and processes — not mutate session_state directly.

### 10.3 Tactical-to-Shell Restrictions

Tactical modules (L2) must not communicate with the shell (L0) in any direction.

Tactical modules do not know the shell exists. They receive data in, return data out. If tactical output needs to influence shell behavior (e.g., an escalation condition that changes navigation chrome), the communication path is:

```
L2 Tactical output → L1 Orchestration (reads output) → L4 State (writes shell-signal key) → L0 Shell (reads shell-signal key)
```

There is no direct path from L2 to L0.

### 10.4 Service Boundary Rules

Service modules (L5 — clients/, tracking/) are stateless adapters. They accept explicit function arguments and return data objects. They must not:

- Read session_state for configuration (receive config as arguments)
- Cache their own responses (caching is L1's responsibility)
- Write to session_state as a side effect
- Import from Layers 0–4

Service modules are pure I/O adapters. All intelligence, caching, and state management is the responsibility of higher layers.

---

## 11. Validation Boundary Doctrine

### 11.1 Layer-Specific Validation Responsibilities

Each layer performs validation appropriate to its position in the hierarchy:

| Layer | What It Validates | When |
|-------|------------------|------|
| L0 Shell | Navigation state completeness; hydration fingerprint | At startup; on navigation event |
| L1 Orchestration | Pipeline output schema; pick data completeness | After pipeline execution; before tactical dispatch |
| L2 Tactical | Input data contract compliance; output schema before return | At tactical entry point; before return |
| L3 Rendering | Display data shape (picks have required display fields) | Before first render call; graceful error display on failure |
| L4 State | Key registration compliance; zone ownership | On session_state write; on initialization |
| L5 Services | API response schema; fallback to CSV on failure | On every API response |
| L8 Validation | Shared validation schemas used by all layers | Called by any layer at boundary crossings |

### 11.2 Runtime Observation Ownership

Runtime observation (monitoring the live app for rerender counts, latency, blank panel detection) is the responsibility of the operator during the designated observation period after any extraction. This is not automated — it requires human observation of the tactical UX.

No code change may be considered complete until the operator has confirmed:
- Investigation atmosphere renders correctly on first load
- Navigation between routes does not trigger blank panels
- Modal open/close cycle does not cause phantom rerenders
- Escalation badges render with correct tier on page load

### 11.3 Rerender Monitoring Ownership

Rerender monitoring (counting Streamlit rerun cycles, detecting phantom rerenders from state mutation) is owned by the operator using browser developer tools and Streamlit's built-in profiling. No automated test can fully substitute for this observation because rerender contamination is timing-dependent and session-dependent.

The extraction governance doctrine (extraction_execution_governance_doctrine_v1.md) defines the specific runtime observation checklist. This doctrine adds the boundary rule: any module that introduces session_state writes must be individually tested for rerender contamination before the extraction is considered complete.

### 11.4 Rollback Authority Boundaries

Rollback authority is owned by the operator. No AI agent may execute a rollback without explicit operator authorization. The rollback procedure defined in the extraction governance doctrine specifies the sequence.

Boundary rule: The validation layer (L8) may *detect* conditions that trigger a rollback recommendation. It may not execute the rollback itself. Detection (automated) and execution (operator-authorized) are separated by design.

---

## 12. Forbidden Architectural Patterns

### 12.1 Render-Driven State Mutation

**Pattern:** A display function writes to session_state based on displayed data or user interaction.

```python
# FORBIDDEN
def render_picks_table(picks):
    st.dataframe(picks_df)
    st.session_state.last_rendered_pick_count = len(picks)  # state write in render function
```

**Why forbidden:** Triggers phantom rerender on next cycle. Creates ownership ambiguity — is this key owned by the rendering module or the state layer? Breaks the single-write-per-key rule if other modules also write this key.

**Correct pattern:** L1 writes pick count to a registered state key before L3 renders. L3 reads the key.

### 12.2 Cross-Layer Imports

**Pattern:** A lower-layer module imports from a higher-layer module.

```python
# FORBIDDEN — tactics importing from orchestration
# In strategies/full_slate.py:
from pipeline import run_pipeline
fresh_picks = run_pipeline(date)  # tactical re-entering orchestration
```

**Why forbidden:** Creates upward dependency. Tactical module now triggers pipeline execution — breaks orchestration isolation. Results in potential double-execution if orchestrator also runs pipeline.

**Correct pattern:** Orchestrator runs pipeline, passes results as argument to tactical module entry point.

### 12.3 Duplicated Orchestration

**Pattern:** Multiple modules each independently invoke the pipeline or scoring chains.

```python
# FORBIDDEN — two render paths each fetching picks
# In some_view.py:
picks = run_pipeline(date)  # duplicated pipeline call

# In another_view.py:
picks = run_pipeline(date)  # second duplicated call
```

**Why forbidden:** Two pipeline calls for the same date may return different results (API latency variance, odds update between calls). Cache key collisions. Double API rate-limit consumption.

**Correct pattern:** Pipeline runs once per execution cycle in L1. All views read from session_state pipeline output keys.

### 12.4 Shell-Controlled Tactical Scoring

**Pattern:** Navigation or shell logic reads raw picks and invokes scoring to determine display.

```python
# FORBIDDEN — shell invoking tactical scoring
# In navigation_continuity.py or app.py shell section:
if route == "full_slate":
    scored_picks = score_full_slate(picks)  # shell calling tactical
    st.session_state.fs_output = scored_picks
```

**Why forbidden:** Shell now owns tactical execution. Breaks tactical isolation. Shell must run before data is available — scoring in the shell creates sequencing dependency that breaks cold-start.

**Correct pattern:** L1 orchestration runs Full Slate when route is active. Shell reads pre-computed output from session_state.

### 12.5 Cache Ownership Duplication

**Pattern:** Two modules define `@st.cache_data` on the same function or two different functions that return the same data.

```python
# FORBIDDEN — cache defined in service layer
# In clients/mlb_stats.py:
@st.cache_data(ttl=3600)
def fetch_lineups(date):
    ...

# AND separately in pipeline.py:
@st.cache_data(ttl=3600)
def get_lineups(date):
    return fetch_lineups(date)  # two cache layers for same data
```

**Why forbidden:** Two cache entries for the same data. Cache invalidation of one does not invalidate the other. One stale, one fresh. Data inconsistency within a single session.

**Correct pattern:** Single `@st.cache_data` in L1 pipeline. Service layer function is uncached (called by pipeline's cached wrapper only).

### 12.6 Tactical UI State Side-Effects

**Pattern:** A tactical scoring function reads or writes session_state to store intermediate results or communicate with the display layer.

```python
# FORBIDDEN — tactical writing session_state
# In strategies/full_slate.py:
def score_picks(picks):
    results = compute_scores(picks)
    st.session_state.fs_escalation_counts = count_escalations(results)  # FORBIDDEN
    return results
```

**Why forbidden:** Tactical module now has a side effect outside its output contract. The session_state write couples the tactical module to the state layer. Rollback of the tactical module leaves a stale session_state key. Multiple calls to score_picks within one session will re-write the key, creating unpredictable state.

**Correct pattern:** Tactical module returns escalation counts as part of its output contract dict. L1 receives the dict, writes the relevant fields to registered state keys via L4.

---

## 13. Future-State Runtime Vision

### 13.1 Thin Orchestrator Architecture

The target runtime architecture reduces the orchestrator (currently pipeline.py + a large fraction of app.py) to a thin dispatch function:

1. Reads active route from session_state
2. Checks pipeline cache for current date's picks
3. If cache miss: invokes pipeline.run() → stores output in state
4. Reads route → dispatches to appropriate tactical module with cached picks
5. Tactical module returns output → L1 writes output to state
6. Returns control to shell → shell renders using pre-computed state

The orchestrator's code footprint in this target state is < 200 lines. All intelligence lives in tactical modules. All display lives in rendering modules. All state governance lives in the state layer.

### 13.2 Bounded Tactical Modules

Each tactical system (Full Slate, JIG, MAIN, Performance, Strategy) is a self-contained directory with a single public entry-point function. Internal complexity is bounded within the directory boundary.

Target structure:
```
tactical/
  full_slate/
    __init__.py          # public entry point only
    scorer.py            # escalation and composite scoring
    escalation.py        # tier classification
    threat_builder.py    # threat card data assembly
  jig/
    __init__.py
    filter.py
    ranker.py
  main/
    __init__.py
    filter.py
    ranker.py
```

No module outside `tactical/full_slate/` imports from inside it (except via `__init__.py`). This is the module boundary.

### 13.3 Isolated Services

Each service module (client) is a pure function adapter with no Streamlit imports, no session_state dependency, and no caching. Services are independently testable without launching Streamlit.

Target: All files in `clients/` pass `python -m pytest clients/test_*` without a running Streamlit app.

### 13.4 Stable Shell Architecture

The shell stabilizes at < 500 lines: startup sequence, viewport layout, navigation chrome, modal governance. All tactical display is delegated to rendering modules.

The shell is the last module to change in any modularization wave. It stabilizes only after all lower layers are extracted and validated.

### 13.5 Protected Execution Graph

The execution graph in target state is a DAG with no cycles:

```
User → Shell (L0)
Shell → Orchestrator (L1)
Orchestrator → Pipeline → Services (L5) → APIs
Orchestrator → Tactical Modules (L2) [parallel, isolated]
Orchestrator → State Layer (L4) [writes results]
State Layer → Rendering Modules (L3) [reads results]
Rendering Modules → Shell (L0) [display within viewport]
```

Every edge in this graph is downward or lateral (within a layer). No upward edges exist. No cycles exist. The graph is statically verifiable from import analysis alone.

---

## Appendix A: Runtime Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 0 — SHELL                                                │
│  navigation_continuity.py, nav_state.py (shell),               │
│  app.py (startup + layout only)                                 │
│  ● Owns: viewport, navigation chrome, modal z-index             │
│  ● Does NOT: invoke pipeline, write state, compute scores       │
└─────────────────────────┬───────────────────────────────────────┘
                          │ triggers (data needed)
┌─────────────────────────▼───────────────────────────────────────┐
│  LAYER 1 — ORCHESTRATION                                        │
│  pipeline.py, (future orchestrator.py)                          │
│  ● Owns: pipeline execution, cache slots, tactical dispatch      │
│  ● Does NOT: render st.*, modify nav state                       │
└──────────┬──────────────┬──────────────────────────────────────┘
           │ invokes      │ writes results to
┌──────────▼──────┐ ┌─────▼──────────────────────────────────────┐
│  LAYER 2        │ │  LAYER 4 — STATE                           │
│  TACTICAL       │ │  investigation_state.py, nav_state.py       │
│  INTELLIGENCE   │ │  ● Owns: all session_state keys             │
│  Full Slate     │ │  ● Does NOT: fetch data, invoke tactical     │
│  JIG / MAIN     │ └────────────────────┬───────────────────────┘
│  Performance    │                      │ state keys read by
│  Strategy       │ ┌────────────────────▼───────────────────────┐
│  ● Zero st.*   │ │  LAYER 3 — RENDERING                       │
│  ● Zero state  │ │  components/, display modules               │
│  writes         │ │  ● Owns: all st.* calls (except L0 chrome) │
└──────────┬──────┘ │  ● Does NOT: write state, invoke pipeline   │
           │ input  └────────────────────────────────────────────┘
┌──────────▼──────────────────────────────────────────────────────┐
│  LAYER 5 — SERVICES                                             │
│  clients/mlb_stats.py, clients/odds_api.py, tracking/*          │
│  ● Stateless adapters. No session_state. No caching.            │
└──────────┬──────────────────────────────────────────────────────┘
           │ raw reference only
┌──────────▼──────────────────────────────────────────────────────┐
│  LAYER 6 — DATA    │  LAYER 7 — UTILITIES  │  LAYER 8 — VALID  │
│  config.py         │  engine/market.py     │  data_integrity.py │
│  data/park_factors │  engine/ev.py         │  backtest valid    │
│  manual_odds.csv   │  engine/sizing.py     │  (pure assertions) │
└────────────────────┴───────────────────────┴────────────────────┘
```

---

## Appendix B: Dependency Direction Matrix

**Legend:** ✓ = Allowed, ✗ = Forbidden, C = Controlled (documented exception required)

| From ↓ / To → | L0 Shell | L1 Orch | L2 Tactical | L3 Render | L4 State | L5 Services | L6 Data | L7 Utils | L8 Valid |
|---------------|---------|--------|------------|----------|---------|-----------|--------|---------|---------|
| **L0 Shell** | — | ✓ | C* | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| **L1 Orch** | ✗ | — | ✓ | ✗ | C† | ✓ | ✓ | ✓ | ✓ |
| **L2 Tactical** | ✗ | ✗ | — | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| **L3 Render** | ✗ | ✗ | ✗ | — | Read‡ | ✗ | ✓ | ✓ | ✓ |
| **L4 State** | ✗ | ✗ | ✗ | ✗ | — | ✗ | ✓ | ✓ | ✓ |
| **L5 Services** | ✗ | ✗ | ✗ | ✗ | ✗ | — | ✓ | ✓ | ✓ |
| **L6 Data** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | — | ✓ | ✓ |
| **L7 Utils** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | — | ✓ |
| **L8 Valid** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | — |

*C\* Shell may receive L2 output only through L4 state keys — never by direct L2 import*  
*C† L1 writes to L4-registered state keys only — not arbitrary session_state writes*  
*‡ L3 reads session_state (L4-owned keys) only — never writes*

---

## Appendix C: Ownership Responsibility Matrix

| Resource | Owner | Legal Writers | Legal Readers | Invalidation Authority |
|----------|-------|--------------|--------------|----------------------|
| Navigation session_state keys | L4 nav_state.py | L4 only | L0, L1, L3 | L4 on route change |
| Investigation session_state keys | L4 investigation_state.py | L4 only | L0, L3 | L4 on workspace change |
| Pipeline output session_state keys | L1 pipeline.py (via L4 registry) | L1 controlled | L1, L2 (input), L3 | L1 on new date |
| Tactical output session_state keys | L1 (writes on behalf of L2) | L1 controlled | L0, L3 | L1 on new execution |
| UI ephemeral session_state keys | L0 Shell | L0 only | L3 (read-only) | L0 on navigation |
| @st.cache_data slots | L1 pipeline.py | L1 decorator only | L1 (returns to callers) | L1 explicit clear() |
| Viewport layout structure | L0 Shell | L0 only | — | L0 on rerender |
| Modal state | L4 (is_modal_open key) | L4 on signal from L0/L3 | L0, L3 | L4 on close event |
| Tactical scoring chain | L2 per-system | L2 (pure computation) | L1 (receives return value) | N/A (stateless) |
| API client state | L5 Services (stateless) | None (stateless per call) | L1 (via return value) | N/A |
| Hydration fingerprint | L4 system registry | L4 only | L0 (guard check) | L4 on reset |
| Rollback authority | Operator | Operator only | Operator | N/A |

---

## Appendix D: Forbidden Pattern Examples

### D.1 Render-Driven State Mutation

```python
# FORBIDDEN
def render_threat_cards(threats):
    for threat in threats:
        with st.expander(threat["name"]):
            st.metric("HR Prob", f"{threat['model_prob']:.1%}")
    # STATE WRITE IN RENDER FUNCTION — FORBIDDEN
    st.session_state.last_card_render_ts = datetime.now()
```

```python
# CORRECT
# L1 writes timestamp to state before dispatch to L3
# L3 renders without writing any state
def render_threat_cards(threats):
    for threat in threats:
        with st.expander(threat["name"]):
            st.metric("HR Prob", f"{threat['model_prob']:.1%}")
```

### D.2 Tactical Module with Streamlit Import

```python
# FORBIDDEN — strategies/full_slate.py
import streamlit as st

def score_picks(picks, date):
    with st.spinner("Scoring picks..."):  # FORBIDDEN st.* in tactical
        results = _compute_scores(picks)
    return results
```

```python
# CORRECT — no Streamlit in tactical module
def score_picks(picks, date):
    results = _compute_scores(picks)
    return results
# Spinner lives in L1 orchestrator or L3 render wrapper
```

### D.3 Service Layer Reading Session State

```python
# FORBIDDEN — clients/mlb_stats.py
import streamlit as st

def fetch_lineups(date):
    # Reading session_state from service layer — FORBIDDEN
    config_date = st.session_state.get("selected_date", date)
    return _api_call(config_date)
```

```python
# CORRECT — explicit argument, no session_state dependency
def fetch_lineups(date):
    return _api_call(date)
# Caller (L1) reads session_state and passes date as argument
```

### D.4 Upward Import from Tactical to Orchestration

```python
# FORBIDDEN — strategies/full_slate.py
from pipeline import run_pipeline, get_cached_picks

def score_with_fresh_data(date):
    picks = get_cached_picks(date)  # UPWARD IMPORT — FORBIDDEN
    return _score(picks)
```

```python
# CORRECT — orchestrator passes picks as argument
# In strategies/full_slate.py:
def score_picks(picks, date, config):  # receives picks from L1
    return _score(picks)
```

### D.5 Cache Decorator Outside Orchestration Layer

```python
# FORBIDDEN — clients/statcast.py (service layer)
import streamlit as st

@st.cache_data(ttl=3600)  # FORBIDDEN — cache in service layer
def fetch_barrel_rates(player_ids):
    return _statcast_api(player_ids)
```

```python
# CORRECT — service layer uncached; L1 wraps with cache
# In clients/statcast.py:
def fetch_barrel_rates(player_ids):  # no cache decorator
    return _statcast_api(player_ids)

# In pipeline.py (L1):
@st.cache_data(ttl=3600)  # cache owned by L1
def _cached_barrel_rates(player_ids_tuple):
    from clients.statcast import fetch_barrel_rates
    return fetch_barrel_rates(list(player_ids_tuple))
```

---

## Appendix E: Future Thin-Orchestrator Example

Target orchestrator structure (illustrative — not a production implementation):

```python
# future: orchestrator.py (L1) — target < 200 lines
# THIS IS PLANNING DOCUMENTATION — NOT PRODUCTION CODE

def run_for_route(route: str, date: str, state: StateRegistry) -> None:
    """
    Single entry point for all data work.
    Reads route. Checks cache. Fetches if needed. Dispatches tactical. Writes state.
    """
    # Step 1: Check pipeline cache
    picks = _get_cached_picks(date)
    if picks is None:
        picks = _execute_pipeline(date)   # L5 services → L6 config → L7 math
        _write_pipeline_state(picks, state)  # write to L4-registered keys

    # Step 2: Dispatch to tactical module for active route
    tactical_fn = ROUTE_TO_TACTICAL.get(route)
    if tactical_fn is None:
        return  # shell will render "no data" state

    tactical_output = tactical_fn(picks, date)  # L2 tactical — pure function

    # Step 3: Write tactical output to state (L4-registered keys)
    _write_tactical_state(route, tactical_output, state)

    # Step 4: Return. Shell reads state. Rendering modules display it.
    # Orchestrator does NOT render. Orchestrator does NOT import st.*

ROUTE_TO_TACTICAL = {
    "full_slate": full_slate.score_picks,
    "jig":        jig.score_picks,
    "main":       main_picks.score_picks,
    "performance": performance.compute_metrics,
    "strategy":   strategy.optimize,
}
```

This structure makes the orchestration layer a routing table plus a data-fetch gate. All intelligence is in tactical modules. All display is in rendering modules. The orchestrator is independently testable without Streamlit running.

---

*Document complete. Runtime isolation and boundary architecture doctrine v1 — Planning only. No production systems modified. Runtime systems remain frozen.*

*Preceding doctrine chain:*
- `controlled_modularization_doctrine_v1.md`
- `modularization_dependency_audit_doctrine_v1.md`
- `extraction_execution_governance_doctrine_v1.md`
- `phase1_extraction_prioritization_doctrine_v1.md`
- **`runtime_isolation_boundary_doctrine_v1.md` ← current**

*Next: Validation sequencing doctrine — defines gates, verification checkpoints, and observation protocols for each extraction phase.*
