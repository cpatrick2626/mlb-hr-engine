# Extraction Execution Governance Doctrine v1
## MLB HR Engine v4 — Controlled Modularization Execution & Rollback Standards

**Document Status:** Governance Doctrine — Planning Only  
**Phase:** Division 09 — Step 3/8 Extraction Governance  
**Owner:** Claude (Architecture Governance)  
**Date:** 2026-05-23  
**Runtime Systems:** FROZEN (no production changes from this document)  
**Preceding Doctrines:**
- `controlled_modularization_doctrine_v1.md` — architecture targets, protected zones, phase map
- `modularization_dependency_audit_doctrine_v1.md` — dependency classification, hidden contracts, audit workflow

---

## Table of Contents

1. [Purpose of Controlled Extraction](#1-purpose-of-controlled-extraction)
2. [Extraction Governance Philosophy](#2-extraction-governance-philosophy)
3. [Extraction Lifecycle](#3-extraction-lifecycle)
4. [Extraction Authorization Rules](#4-extraction-authorization-rules)
5. [Safe Extraction Standards](#5-safe-extraction-standards)
6. [High-Risk Extraction Standards](#6-high-risk-extraction-standards)
7. [Validation Gate Hierarchy](#7-validation-gate-hierarchy)
8. [Rollback Governance](#8-rollback-governance)
9. [Ownership Transfer Doctrine](#9-ownership-transfer-doctrine)
10. [Import Governance](#10-import-governance)
11. [Tactical UX Preservation During Extraction](#11-tactical-ux-preservation-during-extraction)
12. [Runtime Observation Doctrine](#12-runtime-observation-doctrine)
13. [Extraction Failure Scenarios](#13-extraction-failure-scenarios)

**Appendices:**
- [A. Extraction Readiness Checklist](#appendix-a-extraction-readiness-checklist)
- [B. Example SAFE Extraction Walkthrough](#appendix-b-example-safe-extraction-walkthrough)
- [C. Example FAILED Extraction Recovery](#appendix-c-example-failed-extraction-recovery)
- [D. Runtime Observation Checklist](#appendix-d-runtime-observation-checklist)
- [E. Operator Approval Template](#appendix-e-operator-approval-template)

---

## 1. Purpose of Controlled Extraction

### 1.1 Why Uncontrolled Modularization Fails

Modularization that proceeds without governance produces a specific class of defect distinct from ordinary bugs: **structural regression**. Structural regressions are caused not by logic errors but by the act of moving code itself — import resolution changes, shared-scope assumptions collapse, cache identity breaks, and state initialization order shifts. These failures share a common property: they are **invisible during extraction** and **catastrophic in production**.

The most dangerous property of uncontrolled extraction is that it appears to succeed. The Python interpreter does not error. The Streamlit app loads. The route renders. But somewhere in the dependency chain, a contract has been silently broken — a session_state key initialized one call too late, a cache invalidated because its owning function moved files, a render function now reading stale state because its caller no longer executes first. These defects surface hours or days after the extraction, in UI paths not exercised by the developer during testing, triggered by user interactions that cross the now-broken boundary.

### 1.2 Hidden Dependency Collapse Risks

The dependency audit doctrine identified five classes of hidden dependency that do not appear in `import` statements:

| Hidden Dependency Class | Collapse Mechanism | Discovery Method |
|------------------------|-------------------|-----------------|
| `st.session_state` key sharing | Extraction breaks initialization order; keys read before written | Full session_state key trace |
| `@st.cache_data` function identity | Moving decorated function changes cache key; warm cache invalidated | Cache identity analysis |
| Hydration callback data shape | Downstream renderers assume specific dict keys from pipeline output | Render-phase data flow trace |
| Route-synchronization timing | Route reads happen at app.py startup; extracted router reads one frame later | Startup sequence audit |
| Cross-file state mutation | Two files mutate the same session_state key with no import relationship | Session_state write-map |

Any extraction that touches a system with known hidden dependencies must complete a full hidden dependency audit before execution is authorized.

### 1.3 Rerender Contamination Risks

Streamlit's execution model means any `st.session_state` mutation anywhere in an execution path triggers a full app rerender. This creates a contamination vector: a module extracted with its own internal state mutations will inject rerenders into execution paths that previously did not generate rerenders.

**Rerender contamination is cumulative.** If three modules are extracted with unaudited state mutations, each adding one phantom rerender cycle, the app becomes noticeably slower and flicker-prone before the root cause is identified. The stabilization work that preceded this doctrine (Phase 3A) required significant effort to suppress existing rerender contamination. That work must not be reversed by extraction activity.

### 1.4 Tactical UX Degradation Risks

The cinematic investigation atmosphere — escalation hierarchy, threat card density, shell pacing, investigation state machine — is the operator's primary interface to the system's intelligence output. This UX is not a cosmetic layer. It encodes the system's analytical judgment through escalation tier, badge state, suppression indicator, and archetype classification. Degradation of this UX is operationally equivalent to degrading the model's output.

Extraction that breaks tactical rendering produces:
- Blank threat card panels (data arrives but rendering contract broken)
- Missing escalation badges (badge state computed but display path broken)
- Investigation atmosphere reset on navigation (state not preserved across extraction boundary)
- Shell pacing disruption (timing-sensitive render chains reordered)

These failures are not detectable by Python tests. They require human operator observation during runtime observation period.

---

## 2. Extraction Governance Philosophy

### 2.1 Principle 1: Deterministic Extraction

Every extraction must produce a deterministic outcome. Before extraction begins, the operator must be able to state exactly:
- Which lines move from which source to which destination
- Which imports are added and removed
- Which session_state keys are touched by the moved code
- Which cache decorators are relocated and how their identity changes
- What the rollback sequence is if extraction fails

If any of these cannot be stated in advance, extraction is not authorized to begin.

### 2.2 Principle 2: Bounded Ownership

Every module owns exactly one domain. The extraction must define, in writing, the domain boundary of the new module before code moves. Domain definitions must be consistent with the layer model defined in the controlled modularization doctrine (Layers 1–7).

A module that owns rendering must not own state. A module that owns state must not own data fetching. A module that owns calculations must not own route dispatch.

### 2.3 Principle 3: Single-Responsibility Migration

One extraction at a time. Parallel extractions operating on the same system create interlocking dependencies that make rollback impossible and blame attribution ambiguous. Each extraction must be:
- Scoped to a single domain
- Completed and validated before the next begins
- Committed independently with a reversible commit point

### 2.4 Principle 4: Rollback-First Doctrine

**Rollback is not a recovery option. Rollback is the primary plan.** Every extraction must have a rollback procedure written before extraction begins. The rollback procedure must be executable in under five minutes by following documented steps without requiring diagnosis. If no clean rollback procedure exists, extraction is not authorized.

This principle exists because extraction failures frequently corrupt state that makes forward recovery impossible without rollback. Attempting forward recovery on a broken extraction state risks layering new corruption on top of existing corruption.

### 2.5 Principle 5: Isolation-Before-Movement

The target module must exist and be validated in isolation before any code is removed from the source. The sequence is always:

1. Create target file with ownership declaration
2. Copy (not move) code into target
3. Add import in source pointing to target
4. Validate that source still works with import redirection
5. Remove original code from source only after validation passes
6. Validate again after removal

**Never remove before redirecting.** Removal-before-redirect is the most common cause of immediate extraction failures.

---

## 3. Extraction Lifecycle

Each extraction passes through nine lifecycle stages. No stage may be skipped. Skipping a stage is a governance violation, not a developer judgment call.

### Stage 1: AUDIT

**Purpose:** Establish ground truth about the extraction target.

Required outputs:
- Dependency classification (ISOLATED / LOW / MEDIUM / HIGH / CRITICAL / RUNTIME-GOVERNED)
- Complete list of callers in the codebase that reference the target code
- Complete list of session_state keys read or written by the target code
- Complete list of `@st.cache_data` decorators in the target code
- Complete list of hidden dependencies (state-sharing, data-shape contracts)
- Layer classification (which of Layers 1–7 does this code belong to?)
- Extraction risk score (derived from dependency audit doctrine scoring system)

**Blocked if:** Target is classified RUNTIME-GOVERNED (no extraction authorized at any phase).

### Stage 2: DEPENDENCY MAPPING

**Purpose:** Produce the complete dependency graph for the extraction target.

Required outputs:
- Import graph (what the target imports, what imports the target)
- Session_state key map (all keys read/written, when they are initialized, which other modules access the same keys)
- Data flow trace (what data structures pass through the target, their shape, their producers and consumers)
- Layer boundary analysis (does the target code cross layer boundaries? if so, resolution required before extraction)
- Hidden dependency resolution plan (for each hidden dependency, how is it preserved post-extraction?)

**Blocked if:** Any layer boundary violation cannot be resolved without modifying protected systems.

### Stage 3: RISK SCORING

**Purpose:** Produce a numeric extraction risk score and determine which standard applies.

Scoring dimensions (from dependency audit doctrine):
- Coupling classification: ISOLATED=0, LOW=1, MEDIUM=3, HIGH=7, CRITICAL=15, RUNTIME-GOVERNED=BLOCKED
- Session_state access points: 0 points per 0 keys; +3 per key
- Cache decorators: +5 per decorator
- Hidden dependencies: +4 per dependency
- Downstream callers: +1 per caller
- Tactical rendering dependency: +5 if in tactical/display chain
- Navigation dependency: +5 if in navigation chain

**Risk thresholds:**
- Score 0–5: SAFE extraction standard applies (Section 5)
- Score 6–15: HIGH-RISK extraction standard applies (Section 6)
- Score 16+: BLOCKED — requires operator escalation and phased decomposition before extraction

### Stage 4: ISOLATION VALIDATION

**Purpose:** Verify the target code can operate correctly in isolation before moving it.

Required steps:
1. Create the target module file with ownership declaration docstring
2. Copy target code into module (do not remove from source)
3. Add all required imports to target module
4. Import target module from source (redirect call sites to use import)
5. Run isolated import test: `python -c "from [target_module] import [function]"` — must succeed with zero errors
6. Confirm no circular imports introduced (run `python -c "import app"` — must succeed)
7. Confirm cache identity unchanged (if any `@st.cache_data` moved, document new cache key)

**Blocked if:** Isolated import test fails. Circular import detected. Cache identity change requires user session invalidation at inopportune time.

### Stage 5: EXTRACTION

**Purpose:** Execute the code movement.

Required steps (in order — do not reorder):
1. Create rollback snapshot: `git stash` or `git commit -m "pre-extraction checkpoint: [target]"`
2. Target file already exists from Stage 4 (do not re-create)
3. Remove original code from source file
4. Replace removed code with import redirect if callers exist outside the redirected call site
5. Verify all import paths resolve: `python -c "import app"` must succeed
6. Verify all redirected call sites use the new import path

**Forbidden during extraction:**
- Renaming functions or variables
- Refactoring logic
- Adding new parameters
- Changing return types
- Adding error handling not present in original
- Fixing bugs noticed during extraction

If any of the above are needed, stop extraction, note the issue, complete extraction as-is, then address in a separate commit.

### Stage 6: VALIDATION

**Purpose:** Confirm extraction did not break anything detectable by static analysis.

Required validation sequence (must all pass):
1. `python -c "import app"` — no ImportError, no circular import
2. `python -m py_compile app.py` — no syntax errors
3. `python -m py_compile [target_module].py` — no syntax errors
4. Import-only test of all known callers: `python -c "import [caller1]; import [caller2]"`
5. Type check if applicable (mypy or pyright — do not introduce new errors)
6. No new `DeprecationWarning` or `SyntaxWarning` on import

### Stage 7: RUNTIME OBSERVATION

**Purpose:** Confirm extraction did not break anything detectable only at runtime.

Required steps:
1. Start Streamlit app: `streamlit run app.py`
2. Navigate to every route that the extracted module's code could affect
3. Exercise every user interaction that touches the extracted domain
4. Observe for: blank panels, missing escalation badges, navigation loss, modal failures, rerender flicker
5. Observe session_state persistence: navigate away and return — confirm state survived
6. Observe cache behavior: reload the page — confirm cached data reloads correctly
7. Observe tactical rendering: confirm escalation tiers, threat card data, HVY modifier display correct

**Duration:** Minimum 10 minutes of active observation. Clock starts after app loads fully.

**Blocked if:** Any observation fails. Even cosmetic failures are blockers — they indicate a contract was broken.

### Stage 8: OPERATOR APPROVAL

**Purpose:** Human operator confirms extraction result matches expected behavior.

Operator must confirm:
- Tactical UX behavior unchanged
- Navigation continuity preserved
- Session state persistence intact
- No visible rerender flicker introduced
- All previously-working routes still work

**Operator approval is required before the extraction is committed.** Developer self-approval is not permitted for HIGH-RISK extractions.

### Stage 9: DEPLOYMENT READINESS

**Purpose:** Package the extraction for permanent inclusion.

Required steps:
1. Write a commit message documenting: what moved, from where to where, why, and the rollback procedure
2. Commit the extraction as a single atomic commit (source changes + target file in one commit)
3. Update `Docs/09_DECISIONS/layer_violations_register.md` if any violations were resolved
4. Update module classification registry in dependency audit doctrine (mark target as extracted)
5. Update `Docs/controlled_modularization_doctrine_v1.md` progress notes
6. Archive the Extraction Readiness Checklist (Appendix A) for this extraction

---

## 4. Extraction Authorization Rules

### 4.1 Who Can Authorize Extraction

| Extraction Type | Authorization Required |
|----------------|----------------------|
| SAFE (score 0–5) | Developer self-authorization after completing Stages 1–3 |
| HIGH-RISK (score 6–15) | Operator review of Stage 3 risk score + written approval before Stage 5 |
| Score 16+ | Operator escalation required; extraction must be decomposed into smaller units before any execution |
| RUNTIME-GOVERNED system | No extraction authorized at any phase; requires full architecture redesign session |

### 4.2 Required Audit Conditions

Extraction is authorized only when all of the following are true:
- Stage 1 audit is complete and documented
- Dependency classification is confirmed (not estimated)
- Risk score is calculated and recorded
- Rollback procedure is written in advance
- No protected runtime zone is in the extraction path
- No active stabilization work is in progress on the same system

### 4.3 Blocked-State Conditions

Extraction is unconditionally blocked when any of the following is true:
- Target system is classified RUNTIME-GOVERNED
- Target system is in the Absolute Protection Zone (Section 3.1 of controlled modularization doctrine)
- An active stabilization pass is in progress on the codebase (any branch with "stabilization" in name)
- A prior extraction on the same session is in rollback state
- The dependency audit audit identifies an unresolved layer boundary violation in the target
- The operator has not approved for HIGH-RISK extractions

### 4.4 Forbidden Extraction Triggers

The following conditions must never be used as justification for extraction:
- "The code is messy" — code quality is not an extraction trigger
- "It would be cleaner" — aesthetic improvement is not an extraction trigger
- "While I'm here" — opportunistic extraction is forbidden
- "It's obviously safe" — intuition is not an audit result
- "The tests pass" — tests do not cover runtime rendering contracts
- "It's small" — size is not correlated with extraction risk

---

## 5. Safe Extraction Standards

Applies to systems with risk score 0–5 (ISOLATED or LOW COUPLING, no session_state, no cache decorators, no tactical rendering dependencies).

### 5.1 Helper Extraction Standards

**Target profile:** Pure utility functions with no side effects, no session_state access, no external API calls, no `@st.cache_data`.

Examples: formatting helpers, math utilities, string manipulation, color constants, static lookup tables.

**Requirements:**
- Target module must be in the correct layer (Layer 4 calculations, or a dedicated `utils/` module)
- All callers updated to use new import path in same commit
- Import test required (Stage 6, steps 1–2)
- Runtime observation: 5 minutes minimum (abbreviated — Stage 7)
- Operator approval: not required for pure function helpers
- Commit: single atomic commit

**Forbidden during helper extraction:**
- Adding type annotations not present in original
- Adding docstrings not present in original
- Changing function signatures
- Adding logging

### 5.2 Static UI Extraction Standards

**Target profile:** Streamlit rendering functions that accept data as arguments, do not write session_state, do not use `@st.cache_data`, and do not depend on tactical scoring.

Examples: static metric cards, informational banners, static data tables, configuration display panels.

**Requirements:**
- Rendering function must accept all data as explicit arguments (no session_state reads inside function)
- Target module goes into `ui/` layer
- Ownership declaration docstring required
- Full import test required (Stage 6)
- Runtime observation: 10 minutes (full Stage 7)
- Operator approval: not required for display-only functions with zero state access
- Commit: single atomic commit

### 5.3 Visualization Extraction Standards

**Target profile:** Chart-generating functions (Plotly, Altair, matplotlib) that accept DataFrames or dicts and return figure objects.

**Requirements:**
- Function must accept data as argument, return figure — no side effects
- Target module goes into `ui/` layer
- Confirm figure objects are not cached with `@st.cache_data` (chart caching depends on data hash, not function identity — safe to move, but verify)
- Runtime observation: confirm chart renders correctly in all contexts where it previously appeared
- Operator approval: not required

### 5.4 Tactical Display Extraction Standards

**Target profile:** Tactical scoring display functions — escalation badge rendering, threat card display, archetype label rendering — that accept pre-computed scoring data as arguments.

**Important:** Even if a tactical display function has low coupling by import count, it carries elevated tactical UX risk. Apply the following additional requirements.

**Requirements:**
- Must confirm function reads no session_state directly
- Must confirm all scoring data is passed as argument (not read from shared scope)
- Target module goes into `tactical/` layer
- Ownership declaration docstring required
- Full import test required
- Runtime observation: 15 minutes — specifically exercise all escalation tier displays, all threat card configurations, all badge states
- Operator must confirm tactical rendering matches pre-extraction behavior
- Operator approval: REQUIRED even for low-coupling tactical display functions

---

## 6. High-Risk Extraction Standards

Applies to systems with risk score 6–15 (MEDIUM or HIGH COUPLING, session_state access, cache decorators, or tactical/navigation dependencies).

### 6.1 Session_State System Extraction

**Target profile:** Any module that reads or writes `st.session_state`.

**This is the highest day-to-day risk category.** Session_state access is the primary rerender injection vector. Moving code with session_state access changes the call-stack position of state mutations, which can alter initialization order, trigger rerenders in new execution paths, or break the rerender suppression guards installed during Phase 3A stabilization.

**Requirements:**
- Complete session_state key map for the target (all keys read, written, initialized, and their initialization order)
- Rerender graph analysis: map all execution paths that reach this code and confirm which ones currently generate rerenders
- Rerender delta analysis: after extraction, confirm no new rerenders are introduced in any path
- Must not modify rerender suppression guards (`if key not in st.session_state:` patterns)
- Target module goes into `state/` layer
- Operator approval: REQUIRED before Stage 5 and again after Stage 7
- Runtime observation: 20 minutes minimum — specifically monitor for rerender flicker, state loss on navigation, key collision errors
- Separate commit required for session_state extractions (do not bundle with any other change)

### 6.2 Routing System Extraction

**Target profile:** Any code involved in route selection, workspace assignment, or active route synchronization.

**Do not extract routing systems in Phase 1 or Phase 2.** Routing extraction is authorized only in Phase 5+ per the migration sequencing plan. This section documents what that extraction would require when the time comes.

**Requirements:**
- Complete route state key map (all session_state keys that encode route identity)
- Startup sequence audit (confirm routing logic executes at correct position in app.py startup)
- Navigation continuity impact assessment (confirm extracted router is called before `navigation_continuity.py` reads route state)
- Multi-route round-trip test: navigate through every route in sequence, confirm no route reads stale state
- Operator approval: REQUIRED before Stage 5
- Runtime observation: 30 minutes minimum — navigate all routes, reload app mid-session, confirm deep-link route restoration works
- No routing extraction without written sign-off from operator documenting expected routing behavior before and after

### 6.3 Cache Function Extraction

**Target profile:** Any function decorated with `@st.cache_data` or `@st.cache_resource`.

**Cache identity is tied to function identity in Python.** Moving a `@st.cache_data`-decorated function to a new module changes the cache key from `app.function_name` to `new_module.function_name`. This silently invalidates all warm caches for all connected user sessions.

**Requirements:**
- Document the current cache key (module path + function name)
- Document the new cache key after extraction
- Assess cache warm-up cost (how expensive is a cold load for this cache?)
- Plan the migration timing: schedule extraction when cache invalidation cost is acceptable (e.g., off-peak, or at start of new session)
- Confirm TTL behavior unchanged after extraction
- Operator approval: REQUIRED
- Runtime observation: verify cache warm-up completes correctly, verify cached data is correct shape after first population
- Post-extraction: monitor first 3 sessions for cold-load performance impact

### 6.4 Dispatcher Extraction

**Target profile:** Any code that selects which view to render based on session_state route.

**Dispatcher extraction is Phase 5+ only.** Dispatcher logic owns the routing decision tree; fragmentation of dispatcher logic creates split-brain routing where two code paths independently compute route, resulting in conflicting render decisions.

**Requirements:**
- All route states must be enumerated and documented before extraction
- Dispatcher must remain atomic (all route decisions in one place — never split across files)
- If dispatcher is extracted, it becomes the sole routing authority — no routing logic may remain in app.py
- Operator approval: REQUIRED before Stage 2 (before even dependency mapping begins)
- Post-extraction: verify every route renders correctly; verify route persistence across session reloads

### 6.5 Shell System Extraction

**Target profile:** App-level shell components — header, sidebar, navigation rail, workspace container.

**Requirements:**
- Shell components have implicit dependency on session_state key initialization order
- Startup sequence must be fully mapped before extraction
- Shell extraction must not separate the shell render from the state that drives it
- Navigation rail must remain synchronized with active route at all times after extraction
- Operator approval: REQUIRED
- Runtime observation: 20 minutes — navigate all routes through the extracted shell, confirm rail state matches rendered view

### 6.6 Tactical Orchestration Chain Extraction

**Target profile:** Any code that orchestrates multiple tactical systems in sequence — JIG intel pipeline, Full Slate escalation chain, investigation state machine transitions.

**These are the most dangerous extractions in the system.** Orchestration chains have timing dependencies: system A must complete before system B reads its output. Extraction that alters call order breaks the chain without generating any Python error.

**Requirements:**
- Full orchestration sequence must be documented before extraction: what calls what, in what order, with what data shape
- Extracted orchestrator must preserve call order exactly
- Each step in the chain must be independently validatable
- Operator approval: REQUIRED before Stage 2
- Runtime observation: 30 minutes minimum — exercise every path through the orchestration chain, confirm outputs match pre-extraction outputs
- Post-extraction: operator must review full tactical output against a pre-extraction baseline on the same date's data

---

## 7. Validation Gate Hierarchy

Validations are ordered. A failure at any gate halts progression to subsequent gates. Subsequent gates may not be reached by skipping a failed gate.

### Gate 1: Syntax Validation

```
python -m py_compile [target_module].py
python -m py_compile app.py
```

**Pass condition:** Zero errors, zero warnings.  
**Failure response:** Fix syntax error. Do not proceed to Gate 2.

### Gate 2: Import Validation

```
python -c "import app"
python -c "from [target_module] import [extracted_symbol]"
```

**Pass condition:** No ImportError, no ModuleNotFoundError, no circular import.  
**Failure response:** Resolve import issue. If circular import, re-evaluate extraction boundary. Do not proceed to Gate 3.

### Gate 3: Isolated Runtime Validation

```
python -c "from [target_module] import [symbol]; result = [symbol]([test_args])"
```

**Pass condition:** Function executes without raising any exception.  
**Failure response:** Fix runtime error. If root cause requires modifying protected systems, abort extraction and rollback.

### Gate 4: Rerender Observation

Start app. Navigate to any route that exercises the extracted code. Observe page for 60 seconds.

**Pass condition:** No visible rerender flicker. Page is stable after initial load.  
**Failure response:** Identify session_state mutation introduced by extraction. If mutation cannot be eliminated without modifying the original logic, rollback.

### Gate 5: Tactical Flow Verification

Navigate to Full Slate view. Exercise the following in sequence:
1. Click into investigation for any player
2. Observe escalation tier and badge rendering
3. Navigate to next player
4. Return to Full Slate — confirm state preserved
5. Confirm HVY modifier display correct

**Pass condition:** All above steps complete with correct output matching pre-extraction behavior.  
**Failure response:** Identify broken rendering contract. If fix requires modifying protected tactical systems, rollback.

### Gate 6: Navigation Continuity

Navigate through all primary routes in sequence:
1. Full Slate → JIG → Main → back to Full Slate
2. Reload page — confirm landing route is correct
3. Confirm active workspace and active route consistent after reload

**Pass condition:** All routes resolve correctly. Reload restores correct route. Workspace and route are in sync.  
**Failure response:** Navigation continuity break. Rollback unless fix is isolated to the extracted module with zero impact on navigation_continuity.py.

### Gate 7: State Persistence

Navigate to Full Slate. Set filters. Navigate away. Return to Full Slate.

**Pass condition:** Filters preserved. Investigation state preserved. Modal state preserved (no phantom modals).  
**Failure response:** Session_state key loss. Identify initialization order issue. Rollback.

### Gate 8: Operator Confirmation

Operator personally exercises Gates 4–7 and confirms all pass from user perspective.

**Pass condition:** Operator states: "Behavior matches pre-extraction baseline."  
**Failure response:** Operator identifies discrepancy. Return to Gate where discrepancy first manifests. Fix and restart from that gate.

---

## 8. Rollback Governance

### 8.1 Immediate Rollback Triggers

Rollback must be initiated immediately — without diagnosis, without attempted forward fix — when any of the following occurs:

| Trigger | Immediate Action |
|---------|-----------------|
| App fails to load after extraction | `git stash pop` or `git reset --hard [pre-extraction-commit]` |
| ImportError on `import app` | Rollback |
| Session_state KeyError in any rendered route | Rollback |
| Navigation route resolves to wrong view | Rollback |
| Rerender loop detected (app re-executes continuously) | Rollback |
| Blank tactical panel where content previously appeared | Rollback |
| Operator reports behavior differs from pre-extraction baseline | Rollback |
| Gate 1 or Gate 2 fails after code removal | Rollback |

**Do not attempt to diagnose before rolling back.** The extraction can be re-attempted after rollback with a better understanding of the failure. Diagnosing on a broken extraction state risks corrupting the state further.

### 8.2 Rollback Ladder

Rollback proceeds through the following sequence from least to most aggressive:

**Level 1 — Import Undo:**  
Restore the import redirect in the source file. Re-add the original code. Do not delete the target module (it may be needed for re-extraction).

**Level 2 — Git Stash Pop:**  
`git stash pop` — restores all files to pre-extraction state. Use when Level 1 is insufficient or extraction spanned multiple files.

**Level 3 — Git Reset to Pre-Extraction Checkpoint:**  
`git reset --hard [pre-extraction-commit]` — restores working tree to the state at the pre-extraction commit. Use when stash is corrupt or Level 2 fails.

**Level 4 — Session Restart:**  
Stop the Streamlit app completely. Clear Streamlit cache. Restart. Use after any Level 3 rollback to ensure no in-memory cache state persists from the failed extraction.

### 8.3 Rollback Ownership

Rollback execution is owned by the operator. The developer must not execute a Level 3 rollback without operator confirmation, as `git reset --hard` is a destructive operation that discards all uncommitted work.

### 8.4 Recovery Sequencing

After rollback completes:

1. Confirm app loads correctly and all gates pass (run Gate 1–3 minimum)
2. Document what failed: which gate, which specific error or observation, what the likely root cause is
3. Record failure in `Docs/09_DECISIONS/layer_violations_register.md`
4. Do not re-attempt extraction in the same session
5. Re-analyze the extraction with the new failure information — revise dependency map, risk score, and rollback procedure before scheduling re-extraction

### 8.5 Contaminated Extraction Response

A contaminated extraction is one where partial changes have been committed before failure is detected. This is the worst-case scenario.

**Prevention:** Never commit until all 8 gates pass. The pre-extraction checkpoint commit is the only commit until extraction is fully validated.

**If contamination occurs:**
1. Do not make additional commits to fix forward
2. Identify the contaminating commit
3. `git revert [contaminating-commit]` — creates a new commit that undoes the contamination
4. Verify revert restores correct behavior (run Gate 1–3)
5. Operator reviews the revert
6. Document the contamination in the decisions register

---

## 9. Ownership Transfer Doctrine

### 9.1 Moving Ownership Between Files/Modules

When code moves from source to target, ownership of that code's domain transfers completely. There must be no residual ownership in the source file.

Residual ownership takes two forms:
- **Code residue:** fragments of the extracted code remain in source (copy/paste error)
- **Authority residue:** source still imports and re-exports symbols from target, pretending to still own them

Both forms are forbidden. After extraction, the source either does not reference the domain, or references it only through a direct import with no re-export.

### 9.2 Preserving Authority Boundaries

Ownership transfer must not create ambiguity about which module has final authority over a domain. To prevent authority disputes:

- Target module must include ownership declaration docstring (domain, what it reads, what it writes, what it calls)
- Source module's removal of code must be accompanied by a comment-free import redirect (no `# moved to target_module` comments — these become stale)
- If the source previously owned the domain exclusively, it now owns nothing in that domain

### 9.3 Preventing Duplicate Ownership

**Duplicate ownership** — two modules both implementing logic for the same domain — is more dangerous than monolithic code. It creates two sources of truth that can diverge silently.

Prevent duplicate ownership by:
- Never leaving stub implementations in source after extraction
- Never creating wrapper functions in source that delegate to target (wrapper becomes a second implementation surface)
- Confirming via grep that no other module in the codebase independently implements the extracted domain

### 9.4 Deprecating Legacy Systems Safely

When a legacy system in app.py is superseded by an extracted module:

1. The extracted module must be fully operational and validated before legacy code is removed
2. Legacy code is removed in a separate commit from the extraction commit
3. Legacy removal must pass the same Gate 1–3 validation
4. No `# deprecated` comments left in place — comments are not authoritative removal

---

## 10. Import Governance

### 10.1 Allowed Dependency Directions

Imports must flow downward through the layer hierarchy. Lower layers never import from higher layers.

```
Layer 7 (RENDER)        → may import from: L6, L5, L4, L3, L2, L1
Layer 6 (ORCHESTRATION) → may import from: L5, L4, L3, L2, L1
Layer 5 (TACTICAL)      → may import from: L4, L2, L1
Layer 4 (CALCULATIONS)  → may import from: L1 only
Layer 3 (STATE)         → may import from: L2, L1
Layer 2 (DATA ACCESS)   → may import from: L1
Layer 1 (FETCH)         → may import from: stdlib and external packages only
```

`config.py` is a special case: any layer may import `config.py`. It is a constants module, not a layer participant.

### 10.2 Forbidden Import Patterns

| Pattern | Reason Forbidden |
|---------|-----------------|
| `ui/` module importing from `state/` and writing state | UI layer must be read-only |
| `engine/` module importing from `tracking/` | Calculation layer must not depend on persistence layer |
| `clients/` module importing from `engine/` | Fetch layer must not depend on calculation layer |
| `ui/` module importing from `clients/` directly | UI must receive data through pipeline, not fetch directly |
| `tactical/` module importing from `shell/` | Tactical layer must not depend on routing layer |
| Any module importing from `app.py` | app.py imports from modules; modules never import from app.py |
| Wildcard imports: `from module import *` | Wildcard imports hide dependency surface area |

### 10.3 Circular Import Prevention

Circular imports in Python cause `ImportError` at runtime, but they are frequently not detected until a specific import order is triggered by a specific execution path.

**Prevention rules:**
- Before adding any new import, run: `python -c "import app"` and confirm it still imports cleanly
- If a circular import is detected, do not fix it by adding `import` inside a function body (deferred import) — this hides the circular dependency without resolving it. Resolve by restructuring the dependency
- Run `pipdeptree --warn fail` or equivalent after any extraction that modifies import structure

### 10.4 UI/Engine Boundary Rules

The boundary between the rendering layer and the engine layer is the most important boundary in the system. Violations of this boundary are the primary cause of hidden dependencies between display logic and model logic.

**Enforced rules:**
- No `engine/` module may import any Streamlit function (`st.*`)
- No `ui/` module may call any `engine/` function directly — all engine output arrives pre-computed via pipeline
- No `tactical/` module may modify engine constants at runtime
- No `ui/` module may write to `engine/` module-level state

---

## 11. Tactical UX Preservation During Extraction

### 11.1 Escalation Hierarchy Preservation

The escalation hierarchy (TIER-1 THREAT → ELITE THREAT → MODERATE THREAT → SUPPRESSED) must render identically before and after any extraction that touches:
- Composite score calculation
- Badge state determination
- Threat card rendering
- Escalation signal propagation

**Preservation requirement:** After every extraction that could affect escalation rendering, run the full Full Slate view on a known date with known outputs. Confirm escalation tier assignments match the pre-extraction baseline.

### 11.2 Shell Pacing Preservation

The cinematic shell pacing — loading skeleton → progressive reveal → settled state — depends on render timing. Any extraction that changes when state becomes available or when rendering functions are called can disrupt pacing.

**Preservation requirement:** After extraction, load the app cold (cleared cache). Observe the loading sequence. Progressive reveal must complete in the same approximate sequence as pre-extraction.

### 11.3 Cinematic Density Preservation

Threat card density — the amount of intelligence displayed per card — must not decrease after extraction. Extraction of display functions must not accidentally omit any data field that was present in the source.

**Preservation requirement:** After extraction, compare the Full Slate threat card for any well-known player against a screenshot baseline. Confirm all data fields are present.

### 11.4 Investigation Flow Preservation

The investigation flow — entering player investigation, viewing detailed intel, navigating between players, returning to Full Slate — must complete without state loss after extraction.

**Preservation requirement:** After any extraction that touches investigation rendering or investigation_state.py references, complete a full investigation flow for at least two players and confirm state does not reset mid-investigation.

### 11.5 Player Navigation Continuity

Navigating between players within investigation must preserve:
- Previous player investigated
- Investigation depth (which intel category was open)
- Scroll position within investigation panel (if preserved pre-extraction)
- Return-to-slate destination

**Preservation requirement:** After extraction, exercise player navigation three times in sequence and confirm all preserved state remains intact.

---

## 12. Runtime Observation Doctrine

### 12.1 Post-Extraction Observation Period

Every extraction requires a minimum observation period during which the app runs under normal usage conditions before extraction is considered complete.

| Extraction Type | Observation Period |
|----------------|-------------------|
| SAFE (pure helper) | 5 minutes active observation |
| SAFE (static UI) | 10 minutes active observation |
| SAFE (tactical display) | 15 minutes active observation |
| HIGH-RISK (session_state) | 20 minutes active observation + first 3 sessions monitored |
| HIGH-RISK (routing) | 30 minutes active observation + first 5 sessions monitored |
| HIGH-RISK (cache function) | 20 minutes active + verify cache warm-up in 3 distinct sessions |
| HIGH-RISK (orchestration chain) | 30 minutes active + operator sign-off after each of first 3 sessions |

"Active observation" means a human operator is using the app, not that the app is running unattended.

### 12.2 Rerender Monitoring

During observation, monitor for rerender indicators:
- Page content flickers or resets unexpectedly
- Loading indicator reappears after initial load completes
- Values that should persist (filter selections, investigation state) reset unexpectedly
- The Streamlit "Running..." spinner appears when no user action was taken

**Rerender detection method:** In Streamlit, unexpected rerenders manifest as a brief flash or content reset. If any is detected, it must be traced to its source before the observation period concludes.

### 12.3 Cache Monitoring

After any extraction involving `@st.cache_data` functions:
- Confirm first load populates cache (response time higher than subsequent loads — expected)
- Confirm second load uses cache (response time significantly lower)
- Confirm cache is not continuously invalidated (load times do not remain high across all requests)
- Confirm cached data shape is correct (not a serialization artifact from cache key change)

### 12.4 Session_State Monitoring

After any extraction involving session_state access:
- Navigate to all primary routes and confirm session_state keys are initialized correctly at each
- Use the browser developer tools or Streamlit's `st.write(st.session_state)` (in a dev debug sidebar) to confirm key presence and type at each route
- Confirm no `KeyError` or `AttributeError` from unexpected missing keys

### 12.5 Navigation Persistence Monitoring

After any extraction that could affect navigation:
- Navigate to Full Slate, then JIG, then Main, then back to Full Slate
- Reload the page at each route — confirm reload restores the correct route
- Navigate deeply (into investigation) then reload — confirm deep route is correctly restored or gracefully degrades to parent route

---

## 13. Extraction Failure Scenarios

### 13.1 Partial Extraction Failure

**Definition:** Extraction began but was not completed — some code moved, some did not, leaving the system in a split-ownership state.

**Symptoms:**
- `ImportError: cannot import name 'X' from 'target_module'` (moved in source, not yet in target)
- `NameError: name 'X' is not defined` (removed from source, not yet in target)
- Double rendering (not removed from source, already in target, both executing)

**Response:**
1. Do not try to fix forward by moving more code
2. Assess which state is less broken (source-only or target-only)
3. Rollback to whichever is less broken
4. If source-only is recoverable: remove target file, restore source code (Level 1 rollback)
5. Verify recovery with Gate 1–2

### 13.2 Orphaned Imports

**Definition:** An import statement remains in a module pointing to a symbol that no longer exists at that path.

**Symptoms:**
- `ImportError: cannot import name 'X' from 'module'` at app startup
- Module loads but specific functionality silently fails (if import was conditional)

**Response:**
1. Identify the orphaned import (grep for the symbol across all files)
2. If the symbol now lives in the target module, update the import path
3. If the symbol was deleted, remove the import and trace all callers
4. Run Gate 1–2 after each fix

### 13.3 Rerender Loops

**Definition:** An extraction introduces a state mutation in a new execution path that triggers a Streamlit rerender, which re-executes the extraction path, which mutates state again, creating a continuous loop.

**Symptoms:**
- Streamlit "Running..." spinner never stops
- Page content continuously resets
- `st.session_state` values flip back and forth between two values

**Response:**
1. Immediate rollback (Level 2 or 3) — do not attempt to fix while the loop is active
2. After rollback, identify which session_state mutation was introduced by the extraction
3. The mutation must be guarded: `if 'key' not in st.session_state: st.session_state['key'] = value`
4. Verify the guard was present in the original code — if not, the extraction moved code that was safe in its original context (inside a conditional) to a new context (unconditional)

### 13.4 State Desync

**Definition:** Two systems that shared state via session_state are now in different files and one was updated without the other, causing key mismatch.

**Symptoms:**
- `KeyError` on session_state access in the extracted module
- A view renders with stale data that doesn't match what other views show
- Filter state applied in one route does not appear in another

**Response:**
1. Rollback (Level 1 if state is the only issue)
2. Map all session_state keys that the extracted module accessed
3. Confirm all those keys are initialized before the extracted module runs
4. If initialization order changed, either restore order or move initialization into the extracted module with explicit guard

### 13.5 Hidden Dependency Break

**Definition:** A dependency that was not expressed as a Python import existed between the extracted module and its original context, and that dependency is now missing.

**Symptoms:**
- Rendering function displays correct structure but wrong values (data shape contract broken)
- Tactical display shows no escalation badges (badge state dict missing a key the display expected)
- Investigation view loads but shows empty player data (hydration callback data shape changed)

**Response:**
1. Rollback
2. Re-audit the extraction target: specifically trace every data access that was inside the extracted function
3. For each data access, identify whether the data was in scope via local variable, function argument, or session_state at the point of origin
4. If via local variable (closure over outer scope): the extraction broke the closure — the dependency must be made explicit as a function argument before re-extraction

### 13.6 Rollback Sequencing for All Scenarios

Regardless of failure scenario:

1. Level 1 rollback first (least destructive)
2. Verify Gate 1–3 after Level 1
3. If not recovered, Level 2 rollback
4. Verify Gate 1–3 after Level 2
5. If not recovered, Level 3 rollback (operator confirmation required)
6. Verify Gate 1–3 after Level 3
7. Level 4: session restart
8. Document failure in decisions register
9. Do not re-attempt extraction without revised dependency map

---

## Appendix A: Extraction Readiness Checklist

Complete this checklist for every extraction. Archive it with the extraction commit.

```
EXTRACTION READINESS CHECKLIST
================================
Extraction Target: [module/function name]
Source File: [app.py or other source]
Target File: [target module path]
Date: [YYYY-MM-DD]
Operator: [name]

STAGE 1 — AUDIT
[ ] Dependency classification confirmed: [ISOLATED / LOW / MEDIUM / HIGH / CRITICAL / RUNTIME-GOVERNED]
[ ] Risk score calculated: [score]
[ ] Standard applies: [SAFE / HIGH-RISK / BLOCKED]
[ ] Complete caller list documented
[ ] Complete session_state key list documented (or: confirmed zero session_state access)
[ ] Cache decorator inventory: [count, or zero]
[ ] Hidden dependencies identified: [list, or none]
[ ] Layer classification confirmed: [Layer 1–7]

STAGE 2 — DEPENDENCY MAPPING
[ ] Import graph documented
[ ] Session_state key map documented (or: not applicable)
[ ] Data flow trace documented
[ ] Layer boundary analysis complete
[ ] Hidden dependency resolution plan documented (or: not applicable)

STAGE 3 — RISK SCORING
[ ] Numeric risk score: [score]
[ ] Extraction standard confirmed: [SAFE / HIGH-RISK]
[ ] Operator approval obtained (HIGH-RISK only): [yes / N/A]

STAGE 4 — ISOLATION VALIDATION
[ ] Target file created with ownership declaration docstring
[ ] Code copied into target (not moved)
[ ] Import redirect added in source
[ ] python -c "from [target] import [symbol]" — PASSED
[ ] python -c "import app" — PASSED (no circular import)
[ ] Cache identity change documented (or: no cache decorators)

STAGE 5 — EXTRACTION
[ ] Pre-extraction checkpoint commit created: [commit hash]
[ ] Rollback procedure written: [Level 1 steps documented]
[ ] Code removed from source
[ ] All import redirects updated
[ ] python -c "import app" — PASSED after removal

STAGE 6 — VALIDATION
[ ] Gate 1 — Syntax: PASSED
[ ] Gate 2 — Import: PASSED
[ ] Gate 3 — Isolated runtime: PASSED
[ ] Gate 4 — Rerender observation: PASSED (or: not applicable for pure helpers)
[ ] Gate 5 — Tactical flow: PASSED (or: not applicable for non-tactical extractions)
[ ] Gate 6 — Navigation continuity: PASSED (or: not applicable)
[ ] Gate 7 — State persistence: PASSED (or: not applicable)
[ ] Gate 8 — Operator confirmation: PASSED

STAGE 7 — RUNTIME OBSERVATION
[ ] Observation duration: [minutes]
[ ] Rerender flicker observed: [yes — BLOCKED / no — continue]
[ ] Cache behavior correct: [yes / not applicable]
[ ] Session_state keys intact: [yes / not applicable]
[ ] Navigation persistence intact: [yes / not applicable]

STAGE 8 — OPERATOR APPROVAL
[ ] Operator confirms: behavior matches pre-extraction baseline
[ ] Operator name: [name]
[ ] Approval timestamp: [YYYY-MM-DD HH:MM]

STAGE 9 — DEPLOYMENT READINESS
[ ] Extraction commit created (single atomic commit)
[ ] Commit message includes: what moved, from where, to where, rollback procedure
[ ] Layer violations register updated (or: no violations resolved)
[ ] Module classification registry updated
[ ] This checklist archived with commit
```

---

## Appendix B: Example SAFE Extraction Walkthrough

**Target:** A formatting helper function `_format_ev_pct(ev)` that formats EV percentage strings for display. Currently in `app.py` at line 4,231.

**Stage 1 Audit:**
- Classification: ISOLATED
- Callers: 3 (all in app.py rendering functions)
- Session_state: zero access
- Cache decorators: none
- Hidden dependencies: none
- Layer: 4 (pure calculation/formatting)
- Risk score: 0

**Stage 2 Dependency Mapping:**
- Import graph: imports `config.py` for threshold constant only
- No session_state keys
- Input: float, output: formatted string
- Layer: no boundary violations

**Stage 3 Risk Scoring:**
- Score: 0 (ISOLATED, no state, no cache, no hidden deps)
- Standard: SAFE helper extraction

**Stage 4 Isolation Validation:**
- Created `ui/formatters.py` with ownership docstring
- Copied `_format_ev_pct` into `ui/formatters.py`
- Added `from ui.formatters import _format_ev_pct` to app.py temporarily alongside original
- `python -c "from ui.formatters import _format_ev_pct"` — passed
- `python -c "import app"` — passed

**Stage 5 Extraction:**
- Pre-extraction checkpoint: `git commit -m "pre-extraction checkpoint: _format_ev_pct"`
- Removed original `_format_ev_pct` from app.py
- Updated 3 call sites to use import from `ui.formatters`
- `python -c "import app"` — passed

**Stage 6 Validation:**
- Gate 1 (syntax): passed
- Gate 2 (import): passed
- Gate 3 (isolated runtime): `python -c "from ui.formatters import _format_ev_pct; print(_format_ev_pct(0.053))"` → `+5.3%` — passed
- Gates 4–7: abbreviated for pure helper (no state, no routing, no tactical display)
- Gate 8: operator confirms formatting still correct in Full Slate view

**Stage 9:**
- Single atomic commit: `feat(ui): extract _format_ev_pct to ui/formatters.py`
- Commit includes rollback procedure: "revert by reverting this commit and re-adding function to app.py at original location"

---

## Appendix C: Example FAILED Extraction Recovery

**Target:** A session_state initialization block for investigation state. Classified HIGH COUPLING. Risk score 12.

**What went wrong:**
The extraction moved `_init_investigation_state()` to `state/investigation.py`. The function included the line:
```python
st.session_state["investigation_player"] = None
```
This line was previously inside an `if "investigation_player" not in st.session_state:` guard in app.py. After extraction, the guard was not preserved. The extracted function ran unconditionally on every rerender, resetting investigation state.

**Symptom observed:**
Investigation view reset to empty every time a widget was interacted with anywhere in the app (because any widget interaction triggers a Streamlit rerender, which now unconditionally resets investigation state).

**Gate failure point:**
Gate 7 (state persistence) — investigation state reset on return to Full Slate.

**Response executed:**

1. Attempted Level 1 rollback: re-added `_init_investigation_state()` to app.py inline. Removed import from `state/investigation.py`. Confirmed Gate 1–2 pass.

2. Verified Gate 7 pass after Level 1 rollback — state preservation restored.

3. Documented failure: "Moved guarded initialization to unguarded execution context. Fix: preserve `if key not in st.session_state:` guard in extracted function or assert precondition at function entry."

4. Updated extraction plan: added "guard preservation audit" as explicit step in Stage 5 for all session_state extractions.

5. Did not re-attempt extraction in same session.

**Revised extraction plan:**
The function now reads:
```python
def init_investigation_state():
    if "investigation_player" not in st.session_state:
        st.session_state["investigation_player"] = None
```
This guard must be present in the extracted version. Stage 5 step added: "Confirm all session_state initializations in extracted code are guarded with `if key not in st.session_state:`."

---

## Appendix D: Runtime Observation Checklist

Complete during Stage 7 runtime observation for every extraction.

```
RUNTIME OBSERVATION CHECKLIST
================================
Extraction Target: [module/function name]
Observation Start: [HH:MM]
Observation End: [HH:MM]
Observer: [name]

RERENDER MONITORING
[ ] Page stable after initial load (no spontaneous rerender)
[ ] Interacting with sidebar widgets does not trigger unexpected content reset
[ ] Navigating between routes does not produce flicker
[ ] No "Running..." spinner appeared without user action

TACTICAL RENDERING
[ ] Full Slate view renders complete threat cards (no blank panels)
[ ] Escalation tiers displayed correctly (spot-check 3 players)
[ ] HVY modifier display present for qualifying picks
[ ] Escalation badges render at correct tier
[ ] Suppression indicators render for suppressed picks

NAVIGATION CONTINUITY
[ ] Full Slate → JIG: route resolves correctly
[ ] JIG → Main: route resolves correctly
[ ] Main → Full Slate: route resolves correctly
[ ] Page reload: restores correct route
[ ] Active workspace consistent with active route after reload

STATE PERSISTENCE
[ ] Filter state preserved across navigation
[ ] Investigation state preserved after navigating to another route and returning
[ ] Modal state: no phantom modals on navigation return
[ ] Shortlist state preserved across navigation

CACHE BEHAVIOR (if applicable)
[ ] First load: cache populates (higher latency — expected)
[ ] Subsequent load: cache hit (lower latency)
[ ] Cached data shape correct (no serialization artifacts)

OBSERVATIONS LOG
[Time] [Observation]
[Time] [Observation]

RESULT: [ ] PASS — proceed to Stage 8    [ ] FAIL — rollback initiated
```

---

## Appendix E: Operator Approval Template

Use this template to record operator approval for HIGH-RISK extractions (required at Stage 8).

```
OPERATOR EXTRACTION APPROVAL
================================
Extraction Target: [module/function name]
Date: [YYYY-MM-DD]
Time: [HH:MM]
Operator: [name]

PRE-EXTRACTION BASELINE
Operator confirms the following behavior was observed BEFORE extraction:
[ ] Full Slate renders correctly with complete escalation hierarchy
[ ] Investigation flow works end-to-end
[ ] Navigation routes resolve correctly
[ ] State persists across navigation

POST-EXTRACTION VERIFICATION
Operator confirms the following behavior is observed AFTER extraction:
[ ] Full Slate renders identically to pre-extraction baseline
[ ] Investigation flow works end-to-end (no state reset)
[ ] Navigation routes resolve correctly
[ ] State persists across navigation
[ ] No new rerender flicker observed
[ ] Tactical output for [test player] matches pre-extraction output

APPROVAL DECISION
[ ] APPROVED — extraction is consistent with pre-extraction baseline
[ ] CONDITIONAL APPROVAL — minor discrepancy noted (document below); approved to proceed
[ ] REJECTED — discrepancy observed (document below); rollback required

Notes / Discrepancies:
[Free text]

Operator Signature: [name]
Timestamp: [YYYY-MM-DD HH:MM]
```

---

*End of Extraction Execution Governance Doctrine v1*  
*Owner: Claude — Architecture Governance*  
*Next Phase: Division 09 Step 4 — Extraction Candidate Prioritization & Phase 1 Staging Plan*
