# Validation Runtime Verification Doctrine v1
## MLB HR Engine v4 — Runtime Verification Sequencing, Rerender Observation & Stabilization Governance

**Document Status:** Architecture Governance Doctrine — Planning Only  
**Phase:** Division 09 — Step 6/8 Validation Sequencing & Runtime Verification  
**Owner:** Claude (Architecture Governance)  
**Date:** 2026-05-23  
**Runtime Systems:** FROZEN (no production changes from this document)  
**Preceding Doctrines:**
- `controlled_modularization_doctrine_v1.md` — architecture targets, protected zones, phase map
- `modularization_dependency_audit_doctrine_v1.md` — dependency classification, hidden contracts, audit workflow
- `extraction_execution_governance_doctrine_v1.md` — extraction lifecycle, rollback standards, validation gates
- `phase1_extraction_prioritization_doctrine_v1.md` — extraction sequencing, risk tiers, readiness scoring
- `runtime_isolation_boundary_doctrine_v1.md` — ownership boundaries, legal dependency directions, boundary law

---

## Table of Contents

1. [Purpose of Runtime Verification](#1-purpose-of-runtime-verification)
2. [Validation Philosophy](#2-validation-philosophy)
3. [Validation Hierarchy](#3-validation-hierarchy)
4. [Extraction Validation Lifecycle](#4-extraction-validation-lifecycle)
5. [Rerender Observation Doctrine](#5-rerender-observation-doctrine)
6. [Runtime Observation Windows](#6-runtime-observation-windows)
7. [Tactical UX Verification](#7-tactical-ux-verification)
8. [Validation Escalation Matrix](#8-validation-escalation-matrix)
9. [Rollback Timing Doctrine](#9-rollback-timing-doctrine)
10. [Operator Verification Doctrine](#10-operator-verification-doctrine)
11. [Protected Runtime Validation Rules](#11-protected-runtime-validation-rules)
12. [False Success Prevention Doctrine](#12-false-success-prevention-doctrine)
13. [Future Validation Vision](#13-future-validation-vision)

**Appendices:**
- [A. Runtime Verification Checklist](#appendix-a-runtime-verification-checklist)
- [B. Rerender Warning Signatures](#appendix-b-rerender-warning-signatures)
- [C. Delayed Failure Examples](#appendix-c-delayed-failure-examples)
- [D. Rollback Escalation Matrix](#appendix-d-rollback-escalation-matrix)
- [E. Operator Runtime Approval Template](#appendix-e-operator-runtime-approval-template)

---

## 1. Purpose of Runtime Verification

### 1.1 Why Modularization Failures Are Often Delayed

Modularization failures do not arrive at the moment of extraction. They arrive later — sometimes minutes, sometimes sessions — triggered by runtime paths that were not exercised during the extraction itself. This delay is not accidental. It is structural.

The Python interpreter verifies import resolution at startup. Streamlit verifies widget rendering on first page load. But neither mechanism verifies:
- Session state key initialization *order* across rerender cycles
- Cache ownership continuity after module relocation
- Route synchronization timing when dispatcher logic moves files
- Hydration fingerprint consistency across cold-start vs warm-start sequences
- Tactical render sequencing when shell orchestration boundaries shift

All of these failure modes share one property: **they pass initial validation and fail later**. A system that treats "it launched" as validation will accumulate silent corruption across multiple extractions until the combined instability produces a catastrophic failure with no clear single cause.

Runtime verification exists to detect these delayed failures *before* they compound.

### 1.2 Why Rerender Corruption Hides Initially

Streamlit's execution model re-executes the entire app script on each user interaction. This means that a rerender defect introduced by an extraction may not trigger until:
- A user interacts with a widget that was not tested post-extraction
- A session_state key is read on the second render cycle that was previously initialized only on the first
- A hydration callback produces a different data shape on re-execution than on cold load
- A cached function is invalidated by identity change and recomputes on the third render, not the first

The first render cycle after extraction is always the most favorable. The extraction author exercised it manually. Subsequent cycles, across different navigation paths and session ages, are where corruption surfaces.

**Corollary:** Single-pass post-extraction testing is structurally insufficient. Runtime verification must span multiple render cycles, multiple navigation paths, and multiple session-state entry conditions.

### 1.3 Why Runtime Verification Must Outlive Extraction Itself

Extraction completes in minutes. Runtime verification must continue for hours. This is not conservatism — it is the minimum window required to observe delayed failure modes.

The observation window is not elapsed wall-clock time. It is the number of *distinct runtime paths* exercised across distinct session conditions. Minimum threshold: at minimum 3 full navigation cycles covering all protected runtime zones, observed with no anomalies, before an extraction is considered stable.

### 1.4 Why "It Launched Successfully" Is Not Validation

Successful launch confirms exactly one thing: Python import resolution succeeded and Streamlit's initial render loop completed without raising an unhandled exception. It confirms nothing about:
- State persistence across rerenders
- Cache coherence across sessions
- Tactical UX continuity across navigation paths
- Shell synchronization correctness
- Modal containment integrity
- Escalation pacing preservation
- Player investigation flow continuity

"It launched" is Gate 0 in an 8-gate hierarchy. Treating it as final validation is the single most common cause of false-positive successful extractions.

---

## 2. Validation Philosophy

### 2.1 Core Laws

**Law 1 — Rollback-First Verification**  
Before any extraction executes, a rollback path must be verified operational. Rollback must be testable in under 60 seconds. If rollback cannot be confirmed ready, extraction is blocked until rollback readiness is restored.

**Law 2 — Staged Validation**  
No validation stage may be skipped to reach a later stage. Each stage produces a binary pass/fail gate. A failed gate halts progression. All subsequent stages are suspended until the failed gate is resolved or rollback is executed.

**Law 3 — Deterministic Observation**  
Validation observations must be deterministic: same action, same navigation path, same session state entry, same expected output. Non-deterministic observations ("it looked fine") are not valid gate clearances. All gate clearances require specific, described observations.

**Law 4 — Operator-Confirmed Runtime Trust**  
No automated validation system may grant final runtime trust. Human operator confirmation is required at minimum for:
- Gate 4 (rerender observation)
- Gate 7 (state persistence)
- Gate 8 (operator runtime approval)

Automation may assist observation but may not substitute for human confirmation of runtime trust.

**Law 5 — Runtime-Over-Speed**  
Extraction velocity is subordinate to runtime stability. If operator scheduling pressure conflicts with observation window requirements, observation windows take precedence. No extraction may declare completion before its observation window has elapsed.

**Law 6 — Stabilization-Before-Expansion**  
No new extraction may begin while any prior extraction remains in its observation window. Concurrent extractions create entangled failure attribution: when a defect surfaces, it is impossible to determine which extraction caused it. Stabilization of the prior extraction must be confirmed before the next begins.

### 2.2 Anti-Patterns This Philosophy Prohibits

| Anti-Pattern | Why Prohibited |
|---|---|
| "Quick smoke test" post-extraction | Does not exercise multi-cycle render paths |
| Parallel extraction of two modules | Prevents failure attribution |
| Skipping observation window due to time pressure | Observation windows are minimum required, not optional |
| Treating Python import success as validation | Import success is Gate 0 only |
| Deferring rollback prep until after extraction | Rollback must be verified ready before extraction begins |
| "It worked last time" inference | Each extraction creates new hidden dependency risk |

---

## 3. Validation Hierarchy

### 3.1 Eight-Gate Hierarchy (Permanent)

Validation proceeds through eight gates in strict sequence. No gate may be bypassed.

```
GATE 0 — Syntax Validation
  ├─ Python syntax check: py -m py_compile <extracted_file>
  ├─ Import resolution: py -c "import <module>"
  ├─ No circular import detection
  └─ PASS/FAIL: any syntax or import error = FAIL → rollback required

GATE 1 — Import Validation
  ├─ All new imports resolve without side effects
  ├─ No session_state writes occur at module import time
  ├─ No @st.cache_data decorators on relocated functions
  │   without cache identity verification
  └─ PASS/FAIL: side-effect import = WARNING; session_state write at import = FAIL

GATE 2 — Isolated Runtime Validation
  ├─ Extracted module testable in isolation (py -m pytest or direct call)
  ├─ Module does not require full app.py execution chain to instantiate
  ├─ Module's exported interface matches all caller expectations
  └─ PASS/FAIL: cannot test in isolation = WARNING; interface mismatch = FAIL

GATE 3 — Full App Cold-Start Validation
  ├─ App launches without error on cold start
  ├─ Default route renders without exception
  ├─ No Streamlit warnings in startup output
  └─ PASS/FAIL: exception on cold start = FAIL → rollback required

GATE 4 — Rerender Observation (minimum 3 cycles)
  ├─ Trigger rerenders via 3 distinct widget interactions
  ├─ Observe: no unintended widget state reset
  ├─ Observe: no hydration loop indicators
  ├─ Observe: no session_state key errors
  └─ PASS/FAIL: any rerender anomaly = WARNING; state reset = FAIL

GATE 5 — Tactical Flow Verification
  ├─ Player card navigation tested end-to-end
  ├─ Full Slate render verified intact
  ├─ Tactical command rhythm verified responsive
  ├─ Escalation pacing verified consistent
  └─ PASS/FAIL: any UX degradation = WARNING; escalation failure = FAIL

GATE 6 — Navigation Continuity Verification
  ├─ All registered routes resolve without error
  ├─ active_workspace handoff verified across route transitions
  ├─ Back-navigation does not corrupt active_route
  ├─ Deep-link navigation from cold state works
  └─ PASS/FAIL: route resolution failure = FAIL; state corruption = FAIL

GATE 7 — State Persistence Verification
  ├─ session_state keys survive cross-page navigation
  ├─ Modal state does not leak across route boundaries
  ├─ Cache coherence across warm/cold session conditions
  ├─ Hydration fingerprint stable across 3 reloads
  └─ PASS/FAIL: state loss = FAIL; cache incoherence = FAIL

GATE 8 — Operator Runtime Approval
  ├─ Human operator reviews Gates 0-7 pass records
  ├─ Human operator executes tactical flow walkthrough
  ├─ Human operator confirms no visual regressions
  ├─ Operator issues signed runtime trust confirmation
  └─ PASS/FAIL: operator not satisfied = FAIL → extended observation or rollback
```

### 3.2 Gate Ownership

| Gate | Owner | Who May Clear |
|---|---|---|
| 0 — Syntax | Automated | Automated pass is sufficient |
| 1 — Import | Automated + Claude review | Claude review required |
| 2 — Isolated Runtime | Claude | Claude must verify isolation |
| 3 — Cold Start | Automated + Operator observation | Operator must observe launch |
| 4 — Rerender | Operator | Human observation required |
| 5 — Tactical Flow | Operator | Human walkthrough required |
| 6 — Navigation | Operator + Claude | Both must confirm |
| 7 — State Persistence | Operator | Human verification required |
| 8 — Runtime Approval | Operator (final authority) | Operator only |

---

## 4. Extraction Validation Lifecycle

### 4.1 Pre-Extraction Validation (Before Any Code Moves)

Pre-extraction validation confirms the system is in a known-good baseline state before extraction begins. A contaminated baseline makes post-extraction comparison impossible.

**Pre-Extraction Checklist:**
1. All prior extraction observation windows fully closed and signed off
2. Rollback snapshot created and rollback path tested (dry-run restore confirmed)
3. Known-good baseline app launch confirmed (Gates 0–3 passing before extraction)
4. Session_state key inventory captured for all keys touched by targeted extraction
5. Cache identity fingerprint captured for all `@st.cache_data` functions in scope
6. All hidden dependencies in targeted module documented and contractually preserved

**Pre-Extraction Blocking Conditions (extraction may not begin if any true):**
- Any prior extraction in observation window
- Rollback path not confirmed operational
- Known unstable rerender condition present
- Any Gate 4–8 anomaly from prior session not resolved

### 4.2 Active Extraction Validation (During Extraction Execution)

During active extraction, continuous validation monitors for defects introduced by the extraction itself.

**Active Extraction Rules:**
- Syntax validation runs after every file creation
- Import validation runs after every `__init__.py` modification
- No extraction step proceeds past syntax error without explicit operator override
- Extraction is atomic: if mid-extraction syntax failure occurs, full rollback is required (partial extraction is not a valid state)

### 4.3 Immediate Post-Extraction Validation (Gates 0–3)

Upon extraction completion, before any observation window begins, Gates 0–3 must pass.

Gates 0–3 are the minimum bar for declaring extraction "syntactically complete." They do not declare extraction "validated." A system at Gate 3 is in a **provisionally launched** state, not a validated state.

**Provisionally Launched ≠ Validated.** This distinction must be maintained in all extraction status reporting.

### 4.4 Runtime Observation Window

After Gates 0–3 pass, the extraction enters its observation window. During the observation window:
- No new extractions may begin
- No production configuration changes may be made
- All system interactions are observations, not modifications
- Gates 4–8 are completed progressively across the observation window duration

### 4.5 Delayed Validation Checks (Gates 4–7)

Delayed validation checks are structured observations completed across multiple sessions, not a single sitting. They are "delayed" because they require distinct session conditions to produce valid signal:
- A cold-start observation (fresh session, no warm cache)
- A warm-start observation (returning session, populated session_state)
- A cross-navigation observation (entering from a different route than the default)

All three session conditions must be exercised before Gate 7 can be cleared.

### 4.6 Stabilization Sign-Off (Gate 8 + Closure)

Stabilization sign-off is the formal closure of an extraction's validation lifecycle. It requires:
1. All 8 gates cleared with no unresolved anomalies
2. Operator runtime approval (Gate 8) issued in writing
3. Observation window formally closed
4. Extraction logged as STABLE in extraction registry
5. Next extraction authorized to begin

---

## 5. Rerender Observation Doctrine

### 5.1 Rerender Monitoring Procedures

Rerender monitoring requires triggering Streamlit's rerun mechanism through real user interactions and observing all system responses, not just visible UI output.

**Trigger sequence for each rerender observation cycle:**
1. Interact with a stateful widget (selectbox, button, slider)
2. Observe: no `st.session_state` key errors in Streamlit console
3. Observe: page renders to completion without spinner loop
4. Observe: all previously visible components remain visible
5. Observe: widget values persist (do not reset to defaults)
6. Interact with a second widget in a different panel
7. Repeat observations 2–5
8. Navigate to a second route and return
9. Observe: first route restores correctly

Minimum three full cycles before Gate 4 clearance.

### 5.2 Rerender Warning Signatures

The following observable patterns indicate rerender instability. Each pattern is described by its observable symptom and its likely structural cause.

| Warning Signature | Observable Symptom | Likely Cause | Severity |
|---|---|---|---|
| **Widget State Wipe** | Selectbox or text input resets to default on interaction | session_state initialization moved outside protected scope | CRITICAL |
| **Spinner Loop** | Loading spinner appears and never resolves | Hydration callback executing in rerender cycle; causes infinite rerun | CRITICAL |
| **Phantom Rerender** | Page content flickers without user interaction | Component triggers st.rerun() outside user event | WARNING |
| **Stale Data Display** | Data table shows outdated values after cache invalidation | Cache identity broken by module relocation; stale cache served | WARNING |
| **Component Duplication** | UI element appears twice on same render | Render function called from two locations post-extraction | WARNING |
| **Silent State Drop** | Navigation clears active session values with no error | session_state key written in relocated function before initialization | CRITICAL |
| **Route Desync** | URL changes but content does not update | Route dispatcher lost synchronization with active_workspace | CRITICAL |
| **Modal Bleed** | Modal content persists after close interaction | Modal state key initialized in wrong scope post-extraction | WARNING |

### 5.3 Rerender Amplification Indicators

Amplification indicators are early signals that a rerender defect is worsening across cycles rather than remaining stable.

**Amplification pattern:** A WARNING observed on cycle 1 that escalates to a different WARNING on cycle 2 and a CRITICAL on cycle 3 is an amplifying defect. Amplifying defects require immediate rollback — they will not self-stabilize.

**Amplification signatures:**
- Increasing render latency across successive cycles
- Progressive loss of session_state keys (1 key missing cycle 1, 3 keys missing cycle 3)
- Narrowing set of functional navigation paths across cycles
- Any CRITICAL warning on any cycle (no wait required — rollback immediately)

### 5.4 Hydration-Loop Detection

A hydration loop is a degenerate state in which Streamlit's rerun mechanism triggers itself continuously, producing an infinite execution cycle. Hydration loops are caused by:
- `st.rerun()` called in a module-level code path executed on every render
- A session_state write that triggers a widget state change that triggers a rerun
- A hydration callback that modifies session_state on every execution (not just on new data)

**Detection indicators:**
- Streamlit console shows continuous "Script execution completed" entries without user interaction
- Browser tab CPU usage elevated continuously after first page load
- Page content flickers at a regular interval
- Application becomes unresponsive to user input

**Response:** Hydration loop is an immediate EMERGENCY escalation. Stop the Streamlit server. Rollback. Do not attempt diagnosis on a running hydration loop.

### 5.5 Hidden State Reset Indicators

Hidden state resets occur when session_state values are silently overwritten during rerender without user interaction or visible error. They are "hidden" because the application continues to function — just with incorrect state.

**Detection procedure:**
1. Set a specific session_state value through a user interaction (e.g., select a player)
2. Trigger 3 unrelated widget interactions on other panels
3. Return to the first panel and verify the player selection persists
4. Navigate to a different route
5. Return and verify the player selection is still present

If the selection is lost at any point, a hidden state reset is present.

---

## 6. Runtime Observation Windows

### 6.1 Mandatory Observation Durations

Observation windows are defined by number of validated runtime paths observed without anomaly, not by elapsed wall-clock time. Wall-clock minimums are enforced only as floors.

| Extraction Risk Tier | Minimum Observation Paths | Minimum Wall-Clock Floor | Gates Required |
|---|---|---|---|
| SAFE (Tier 1) | 5 distinct paths | 30 minutes | Gates 0–5 |
| MODERATE (Tier 2) | 8 distinct paths | 2 hours | Gates 0–7 |
| HIGH (Tier 3) | 12 distinct paths | 8 hours (spans sessions) | Gates 0–8 |
| CRITICAL (Tier 4) | Not approved for extraction | — | Blocked |

"Distinct runtime path" means: a unique combination of entry route, session state age, and interaction sequence. The same interaction repeated in the same session is not a new distinct path.

### 6.2 High-Risk vs Low-Risk Extraction Timing

Extraction risk tier determines both the observation window length and the scheduling constraints on when extraction may begin.

**Tier 1 (SAFE) scheduling:**
- May begin any time
- Observation window completes within same session
- Gate 8 optional (Operator approval recommended but not required)

**Tier 2 (MODERATE) scheduling:**
- Requires operator presence during Gates 3–6
- Observation window should not be started at end of work session (requires continuity)
- Gate 8 required

**Tier 3 (HIGH) scheduling:**
- Requires pre-scheduled observation blocks spanning multiple sessions
- Operator must be available for both initial validation and next-session follow-up validation
- Extended observation: observations must be repeated in a fresh session after overnight gap
- Gate 8 required with written sign-off
- No other extractions may be queued while HIGH-tier extraction is in observation

### 6.3 Cooldown Periods

After any extraction failure that required rollback, a cooldown period is mandatory before attempting re-extraction.

| Failure Severity | Cooldown Period | Cooldown Requirements |
|---|---|---|
| Gate 0-1 failure (syntax/import) | 15 minutes | Re-verify hidden dependency analysis |
| Gate 2-3 failure (isolated/cold start) | 1 hour | Full dependency re-audit for target module |
| Gate 4-5 failure (rerender/tactical) | 4 hours | Full runtime path re-analysis, rollback root cause documented |
| Gate 6-7 failure (navigation/state) | 24 hours | Full protected runtime system audit, session_state key map re-verified |
| Hydration loop or EMERGENCY | 48 hours | Full stabilization doctrine review before any extraction resumes |

Cooldown periods are floors. If root cause analysis requires more time, extraction does not resume until root cause is confirmed resolved.

### 6.4 Freeze Periods

A freeze period is a temporary halt on all extraction activity. Freeze conditions are distinct from cooldown conditions: freeze applies to all extractions, not just the one that failed.

**Freeze conditions:**
- Any EMERGENCY escalation (system-wide freeze until EMERGENCY is resolved)
- Two or more HIGH-severity failures within 72 hours (indicates systemic instability)
- Any unresolved rerender anomaly present in production runtime
- Operator declares system not in known-good baseline state

**Freeze duration:** Operator determines. Freeze lifts when operator confirms system restored to known-good baseline via Gates 0–3.

### 6.5 Delayed-Failure Observation Windows

For all HIGH and MODERATE tier extractions, an additional delayed-failure observation pass must be completed in a new session, separate from the initial validation session. The delayed-failure pass tests:
- Warm-start behavior (returning session with populated session_state)
- Whether overnight server restarts affect cache coherence
- Whether extraction is stable when app is loaded from a bookmarked deep-link route
- Whether state persists correctly when application is loaded by a different operator

The delayed-failure pass must be scheduled and completed as a formal step. It may not be deferred indefinitely.

---

## 7. Tactical UX Verification

### 7.1 Escalation Pacing

Escalation pacing governs how quickly tactical threat indicators, bet sizing recommendations, and confidence scores are surfaced to the operator. Modularization that relocates output or render logic must demonstrate that escalation pacing is unchanged.

**Verification procedure:**
1. Load app with today's picks available
2. Observe Full Slate load time (baseline: comparable to pre-extraction timing)
3. Observe HR threat card render sequence (high-probability picks should appear without delay)
4. Trigger a player investigation from a threat card
5. Observe: investigation panel opens without delay, data complete
6. Close investigation, return to Full Slate
7. Verify Full Slate position and selection state preserved

Escalation pacing failure: any step that is visibly slower, requires additional user interaction, or produces incomplete data.

### 7.2 Shell Continuity

Shell continuity verifies that the navigation shell (workspace router, sidebar controls, route indicators) remains coherent across all extracted module boundaries.

**Verification procedure:**
1. Navigate to each registered route from the shell
2. Verify shell controls remain visible and functional on each route
3. Trigger route transition via shell navigation (not browser back)
4. Verify active route indicator updates correctly
5. Verify workspace context persists in shell across route transitions

Shell continuity failure: shell controls absent on any route, route indicator does not update, workspace context lost after navigation.

### 7.3 Contextual Rails

Contextual rails are the persistent UI elements that anchor operator context across sessions: player context banners, active game indicators, date selectors, bankroll status. These must not flicker, reset, or produce stale data after extraction.

**Verification:** After each route navigation, verify all contextual rail values are current and match the values set in the prior session or prior navigation step.

### 7.4 Player Investigation Flow

Player investigation flow encompasses the complete operator workflow from Full Slate → player card selection → investigation panel → stat detail view → return. This flow must be verified end-to-end post-extraction.

**Critical checkpoints:**
- Player card click opens correct player's panel (not a default or stale selection)
- All stat fields populated (no empty/None displays)
- Pitch mix modifier displayed correctly
- Back navigation returns to Full Slate with same scroll position and selection state
- Investigation panel does not leave orphaned session_state keys after close

### 7.5 Full Slate Readability

Full Slate is the primary operational view. Any degradation in Full Slate readability is a CRITICAL UX regression regardless of the extraction that caused it.

**Readability verification checklist:**
- All columns present and correctly labeled
- Sorting controls functional
- Filter controls functional
- Color coding for probability tiers preserved
- No truncated player names or stat values
- No horizontal scroll introduced by column width changes
- Row count matches expected pick count for the date

### 7.6 Tactical Command Rhythm

Tactical command rhythm is the operator's ability to move through picks, investigate players, log bets, and navigate reports without disruption. It is measured subjectively by the operator during Gate 5 and Gate 8 verification.

Operator should be able to complete a complete Full Slate review session (select best picks, investigate top 5, log bets) in the same time and with the same cognitive load as before extraction. If the operator reports feeling "slowed down" or "interrupted" by the UI, this is a WARNING requiring investigation before Gate 5 clearance.

### 7.7 Modal Continuity

Modals (bet logging dialogs, confirmation prompts, detail overlays) must open, retain state across widget interactions, and close without side effects.

**Verification procedure:**
1. Open a modal dialog (e.g., bet log entry)
2. Partially fill in fields
3. Interact with a widget outside the modal
4. Verify modal remains open with partial state preserved
5. Complete and submit the modal
6. Verify no session_state artifacts remain from the modal after close

Modal continuity failure: modal closes unexpectedly on external widget interaction; modal state cleared on rerender; modal submission creates duplicate records.

---

## 8. Validation Escalation Matrix

### 8.1 Severity Levels Defined

**INFO** — Observable anomaly that does not immediately impact function or stability. Requires logging and monitoring. No extraction pause required.

**WARNING** — Observable degradation in one or more validation dimensions. Extraction observation window extended. New extractions blocked until WARNING resolved. Operator notified.

**CRITICAL** — Functional failure in a protected runtime zone or validation gate failure. Extraction immediately suspended. Rollback evaluation required within 15 minutes. Operator action required.

**EMERGENCY** — Hydration loop, cascading state corruption, or multi-zone failure. Streamlit server stopped. Immediate rollback. All extraction activity frozen pending stabilization review.

### 8.2 Escalation Matrix

| Condition | Severity | Rollback Required | Extraction Suspended | Freeze | Authority |
|---|---|---|---|---|---|
| Syntax error in extracted file | CRITICAL | Yes | Yes | No | Claude (immediate) |
| Import side effect detected | WARNING | No | Yes | No | Claude reviews |
| Cold start exception | CRITICAL | Yes | Yes | No | Operator required |
| Single rerender widget flicker | WARNING | No | Yes (observation extended) | No | Operator monitors |
| Widget state wipe | CRITICAL | Yes | Yes | No | Rollback within 15min |
| Spinner/hydration loop | EMERGENCY | Yes | Yes (all) | Yes | Immediate server stop |
| Route desync | CRITICAL | Yes | Yes | No | Rollback within 15min |
| Silent state drop | CRITICAL | Yes | Yes | No | Rollback within 15min |
| Escalation pacing degraded | WARNING | No | Yes | No | Operator investigates |
| Full Slate column missing | CRITICAL | Yes | Yes | No | Rollback within 15min |
| Modal state leak | WARNING | No | Yes | No | Operator monitors |
| Two CRITICALs in 24h | CRITICAL+ | Evaluate | Yes (all) | Possible | Operator decides |
| Cache incoherence confirmed | CRITICAL | Yes | Yes | No | Rollback within 15min |
| Session_state key error | CRITICAL | Yes | Yes | No | Rollback within 15min |
| Navigation desync | CRITICAL | Yes | Yes | No | Rollback within 15min |

### 8.3 Rollback Authority

Rollback authority defines who may authorize rollback at each escalation level.

| Severity | Who May Authorize Rollback |
|---|---|
| INFO | Not applicable (no rollback) |
| WARNING | Claude recommends; Operator confirms |
| CRITICAL | Either Claude or Operator may initiate |
| EMERGENCY | Automatic — server stop is immediate, no authorization required |

No authorization process should delay a rollback when a CRITICAL or EMERGENCY condition is confirmed. The cost of rolling back a correct extraction is low. The cost of allowing a CRITICAL condition to persist is high.

### 8.4 Runtime Freeze Conditions

A runtime freeze suspends all extraction activity across all modules. Freeze is declared by either Claude or Operator.

**Conditions that trigger freeze:**
- Any EMERGENCY escalation
- Any CRITICAL in a Protected Runtime Zone (session_state, cache, routing, shell, modal, startup)
- Operator loses confidence in system stability
- Two or more unresolved WARNINGs simultaneously present
- Any confirmation of data corruption in pick_tracker.csv or CLV tracking

**Freeze procedures:**
1. Declare freeze verbally and in writing
2. Document all active observation windows and their current gate status
3. Stop any in-progress extraction immediately (rollback if extraction was active)
4. Complete a full Gates 0–3 validation to confirm baseline
5. Investigate all active WARNINGs and CRITICALs
6. Document root causes
7. Operator signs off on freeze lift when system is confirmed stable

---

## 9. Rollback Timing Doctrine

### 9.1 Immediate Rollback Triggers

These conditions require rollback without diagnostic investigation. The defect severity and rollback speed benefit outweigh the diagnostic delay cost.

**Immediate rollback required (no wait, no investigation first):**
- Hydration loop confirmed (spinner loop present)
- session_state key errors raised in Streamlit console
- Route desync (URL changes, content does not)
- Active data corruption (pick_tracker.csv or CLV log contents changed unexpectedly)
- Full Slate fails to render (blank or error state)
- Any EMERGENCY escalation

**Immediate rollback procedure:**
1. Stop user interaction with the application immediately
2. Execute rollback (git restore or backup restore — pre-prepared)
3. Confirm rollback success via Gate 0–3 rapid check
4. Confirm system is stable (no anomalies on cold start)
5. Document triggering condition and rollback time
6. Begin root cause analysis (after rollback confirmed, not before)

**Critical rule: rollback before diagnosis.** For immediate triggers, diagnosis on a contaminated runtime state is unreliable. Rollback first. Diagnose on the clean pre-extraction state by reproducing the conditions that revealed the defect.

### 9.2 Delayed Rollback Triggers

These conditions allow a brief investigation window before rollback decision, but rollback must be evaluated and decided within 15 minutes.

**Delayed rollback evaluation required:**
- Single-widget flicker (investigate whether it reproduces on second attempt)
- WARNING escalation (attempt to identify scope before rolling back)
- Unexpected console warning (evaluate whether warning indicates structural problem)
- UX degradation without state error (attempt to isolate cause)

**15-minute evaluation rule:** If investigation has not identified a clear, fixable root cause within 15 minutes, rollback is required. A defect that cannot be diagnosed in 15 minutes is too complex to resolve surgically during an active extraction.

### 9.3 Rollback-Before-Diagnosis Rule

This rule defines a fundamental priority ordering for CRITICAL and EMERGENCY conditions:

**Rollback first. Diagnose second. Always.**

The temptation to diagnose before rolling back is driven by the belief that rollback loses diagnostic information. This belief is incorrect for the following reasons:
1. A running contaminated system produces unreliable diagnostic signals
2. The pre-extraction state is preserved in git and backup — diagnostic comparison is better done against a clean baseline
3. Time spent diagnosing on a corrupted runtime is time during which the corruption may be worsening
4. Operators under cognitive load during active failures make poor diagnostic decisions

The only exception: INFO-level anomalies where diagnostic investigation is safe and rollback is not indicated.

### 9.4 Contaminated Runtime Protocol

A contaminated runtime is a system in which a failed extraction has partially modified state in ways that cannot be fully rolled back by file restoration alone. This occurs when:
- A failed extraction wrote to session_state in a way that persists in browser local storage
- A cache was invalidated during extraction and produced corrupted cached values
- pick_tracker.csv or CLV tracking files were modified during extraction

**Contaminated runtime indicators:**
- Rollback completes (files restored) but anomalies persist
- session_state errors occur in a rolled-back system
- Previously stable routes fail after rollback

**Contaminated runtime response:**
1. Hard browser refresh (clears browser local storage session state)
2. Streamlit server full restart (clears in-memory cache)
3. If CSV contamination suspected: restore from most recent backup
4. Re-run Gates 0–3 from cold start
5. Document contamination event in extraction log
6. Extend cooldown period to "contaminated runtime" tier (additional 24 hours minimum)

### 9.5 Stabilization Restoration Sequencing

After rollback, stabilization restoration follows a defined sequence. The sequence may not be reordered.

```
Step 1: Confirm rollback file state (git status shows clean)
Step 2: Hard restart Streamlit server (not hot-reload)
Step 3: Cold-start app in clean browser session (incognito)
Step 4: Gates 0-3 rapid verification
Step 5: Gate 4 rerender check (3 cycles, observe for anomalies)
Step 6: Operator confirms system looks stable
Step 7: Document: rollback complete, system stable as of [timestamp]
Step 8: Begin cooldown period (no extraction until cooldown elapsed)
Step 9: Root cause analysis begins (in separate document/session)
Step 10: Extraction re-authorization (requires root cause documented + cooldown elapsed)
```

---

## 10. Operator Verification Doctrine

### 10.1 Human Verification Responsibilities

Human operator verification cannot be delegated to automated systems for the following gates:

**Gate 4 (Rerender Observation):** Automated tools can detect console errors. They cannot detect visual flicker, subtle render delay, or cognitive friction in the UI. Human observation is required.

**Gate 5 (Tactical Flow):** Operator must walk through the complete pick-review workflow. "Looks correct" is not sufficient — operator must actually use the system as they would in production.

**Gate 6 (Navigation Continuity):** Operator navigates all routes and confirms shell, contextual rails, and active workspace behave as expected. No scripted click test substitutes for this.

**Gate 7 (State Persistence):** Operator must close and re-open the app, navigating back to a previously configured state, and confirm all values persist. Session simulator tools do not reproduce this.

**Gate 8 (Runtime Approval):** Final approval is a deliberate, considered human judgment. It must be explicit. Absence of reported issues is not approval. Operator must issue affirmative approval statement.

### 10.2 Visual Verification Requirements

Visual verification is a structured, step-by-step walk through the application UI that the operator conducts as part of Gate 5 and Gate 8. Visual verification is distinct from feature testing — it observes the application as a whole system, not individual features.

**Visual verification scope:**
- Full Slate renders with expected columns, color coding, and data completeness
- All sidebar elements present, labeled correctly, and functional
- All route-specific content panels render without blank sections
- No unexpected blank whitespace, missing widgets, or layout shifts compared to pre-extraction baseline
- All icons, labels, and formatting match pre-extraction baseline
- Loading state (if applicable) transitions correctly to loaded state
- Error states (no picks, no data) render gracefully

### 10.3 Tactical-Flow Confirmation

Tactical-flow confirmation is the operator's verification that the application's core operational workflow remains efficient and complete. It is performed as a scripted walkthrough:

```
TACTICAL FLOW WALKTHROUGH SCRIPT

1. Load app from cold start
2. Verify Full Slate loads with today's picks
3. Sort picks by model probability (descending)
4. Click top-ranked player card
5. Verify investigation panel opens with correct player
6. Review all stat fields — confirm no blanks
7. Review HVY pitch mix modifier — confirm displayed
8. Close investigation panel
9. Verify Full Slate position preserved
10. Click Filter by barrel tier ≥ 8%
11. Verify filter applies and row count changes
12. Clear filter
13. Click Log Bet for top pick
14. Enter bet amount
15. Verify bet log entry visible in tracking tab
16. Navigate to Reports route
17. Verify report renders
18. Navigate back to Full Slate
19. Verify Full Slate state preserved
20. Operator signs off: "Tactical flow confirmed [timestamp]"
```

### 10.4 Navigation Continuity Checks

Navigation continuity checks confirm that all application routes remain navigable and produce coherent content post-extraction.

**Check procedure:**
1. Start from Full Slate (home route)
2. Navigate to each route in the registered route list
3. On each route, confirm: content renders, shell visible, route indicator correct
4. After visiting all routes, return to Full Slate
5. Confirm Full Slate renders correctly (no stale state from route visits)
6. Test browser back button from each route (confirm it does not crash the app)

### 10.5 Runtime Trust Confirmation

Runtime trust is the operator's formal declaration that the system is in a known-good state following extraction validation. It must be explicit and time-stamped.

**Runtime trust is granted when:**
- All 8 gates passed with no unresolved anomalies
- Tactical flow walkthrough completed without issues
- Navigation continuity confirmed
- Operator has personally verified Full Slate, investigation flow, and modal behavior
- No outstanding WARNINGs or CRITICALs in the observation log

**Runtime trust is conditional when:**
- All gates passed but one or more INFO anomalies logged
- Observation window minimum paths reached but wall-clock minimum not yet elapsed
- Operator has concerns but no specific failures identified

Conditional trust requires a follow-up verification session before trust is elevated to full confirmation.

---

## 11. Protected Runtime Validation Rules

The following systems have special validation rules that supplement the standard 8-gate hierarchy. These rules exist because these systems are structurally more fragile or more dangerous in failure than ordinary modules.

### 11.1 session_state System Rules

Session_state is the most critical shared state system in the application. Any extraction that touches session_state initialization, reads, or writes requires:

- **Pre-extraction:** Complete session_state key inventory across all files that read or write affected keys
- **Active extraction:** No session_state logic may move unless all writers and readers of that key are moved together (or updated atomically)
- **Post-extraction Gate 1:** Static analysis must confirm no session_state writes occur at module import time
- **Post-extraction Gate 7:** Session persistence test must specifically verify all relocated keys
- **Special rule:** If extraction causes any new session_state key to be initialized in a different order relative to any other key, full hidden dependency analysis is required before Gates 4–7 may proceed

### 11.2 Cache System Rules

`@st.cache_data` and `@st.cache_resource` decorators create implicit coupling between function identity (file path + function name) and cache key. Moving a decorated function always invalidates its cache.

- **Pre-extraction:** Cache identity fingerprint recorded for all decorated functions in scope
- **Active extraction:** If decorated function must move, cache invalidation is accepted and documented
- **Post-extraction:** System must be tested in both cold-cache and warm-cache states
- **Special rule:** If cache invalidation would cause a significant performance regression (data re-fetch from external API), extraction of decorated functions must be scheduled during low-activity periods

### 11.3 Route Dispatcher Rules

The route dispatcher determines which module renders for each route value. Extraction that touches the dispatcher, route registration, or route resolution logic is HIGH risk regardless of extraction scope.

- **Pre-extraction:** Full route map documented (route key → render function → module)
- **Active extraction:** Route dispatch logic may not be split across files (dispatcher must be atomic)
- **Post-extraction Gate 6:** All routes must be tested, not just the routes affected by extraction
- **Special rule:** active_workspace handoff must be verified across every route transition, not just the routes directly modified by extraction

### 11.4 Shell System Rules

The shell (navigation controls, sidebar, workspace router) provides visual and functional continuity across all routes. It is the operator's primary control surface.

- **Shell extraction is HIGH risk minimum, regardless of apparent scope**
- Pre-extraction baseline must include shell screenshot or detailed visual description
- Post-extraction Gate 5 shell continuity verification is mandatory regardless of extraction tier
- **Special rule:** Shell render function may not be extracted into a module that also contains route-specific content — this creates hidden circular dependency risk

### 11.5 Modal System Rules

Modals represent transient user state (partially filled forms, confirmation dialogs) that exists between rerenders. Modal state corruption is common when session_state scope changes during extraction.

- **Pre-extraction:** All session_state keys used by any modal must be inventoried
- **Post-extraction Gate 7:** Modal open/fill/close cycle must be tested explicitly
- **Special rule:** Modal state keys must remain in the same initialization scope post-extraction as pre-extraction. Moving modal state initialization from app.py to a modal module is permitted only if the module is imported before any route render function executes.

### 11.6 Startup System Rules

Startup systems include: navigation_continuity initialization, session_state default value setup, pipeline pre-caching, and any code that executes before the first route dispatch.

- **Startup sequence extraction is the highest risk category**
- Any extraction touching startup systems requires written pre-authorization from operator
- Observation window for startup extractions is minimum 12 distinct paths spanning 2 sessions
- **Special rule:** Startup sequence execution order must be documented before and after extraction, and the two documents must be compared explicitly during Gate 3 validation

---

## 12. False Success Prevention Doctrine

### 12.1 Documented Delayed Corruption Examples

These examples document the class of failure that runtime verification is designed to prevent. Each example represents a real failure pattern in Streamlit modularization projects.

**Example 1 — The One-Session Wonder**  
Extraction of a player stat lookup module succeeds on all Gates 0–4. The first three operator sessions run without issue. On session 4, the operator selects a player not in the warm-start cache (a batter who was not active in the prior 3 sessions). The stat lookup module attempts to read a session_state key that was initialized in app.py before the module moved — but the new initialization order in the extracted version initializes it one rerun cycle too late. Result: player stats display as empty. Root cause not immediately apparent because it only triggers for players not in cache.

**Prevention:** Gate 7 state persistence test must specifically exercise the cold-cache, first-time-selection path for at least 3 players.

**Example 2 — The Happy Launch**  
Extraction of the ranker module succeeds on Gates 0–3. Full Slate loads. The operator declares success. Two days later, the operator notices that sort order is inconsistent — picks are not sorted by composite score as expected. Root cause: the ranker module was extracted correctly, but a second code path in app.py also modifies pick order (pre-extraction defensive sort). Post-extraction, both sort paths now interact in the wrong order. The bug does not appear on light datasets (< 15 picks) but triggers consistently with large slates (> 25 picks).

**Prevention:** Gate 5 tactical flow verification must test with a full slate (≥ 20 picks), not minimal test data.

**Example 3 — The Warm Cache Illusion**  
Extraction of the pipeline module succeeds. The operator validates during the same session as extraction, while the Streamlit server cache is still warm from the pre-extraction run. All data renders correctly. The following morning, with a cold cache, the app recomputes the pipeline — but the extracted pipeline module now reads a different set of configuration parameters due to a subtle import order change. Yesterday's correct results were from cache. Today's cold-computed results are wrong.

**Prevention:** Gate 7 requires explicit cold-start testing in a new session after overnight gap for MODERATE and HIGH tier extractions.

**Example 4 — The Invisible Rerender**  
Extraction of a utility formatting module succeeds on all gates. No anomalies observed. Three sessions later, the operator notices that HR probability values are displaying with inconsistent decimal precision across different views. Root cause: the formatting function was extracted but a second caller was not updated to use the extracted version — it continues calling the now-deleted original location through a stale local reference. No error raised because Python's late-binding allows the stale reference to resolve at runtime using the still-registered function object. The formatting inconsistency is only visible when both callers render on the same page.

**Prevention:** Gate 1 import validation must confirm all callers of extracted functions updated to use new import path. Static import graph analysis required.

### 12.2 Hidden Rerender Corruption Examples

**Pattern A — The Delayed Widget Reset**  
A widget produces a user-visible reset (selectbox returns to default) not on the user's interaction but on the *next* unrelated user interaction. The operator does not connect the cause and effect. After three sessions of frustration, the operator attributes it to "Streamlit being weird." Root cause: session_state key for the selectbox is initialized in the wrong phase of execution post-extraction.

**Pattern B — The Invisible State Loss**  
A session_state value that drives a conditional render path is silently set to None during a rerender caused by an unrelated interaction. The conditional content disappears without error. Because no error is raised, the operator assumes the content was intentionally hidden by some interaction they do not remember. The state loss is only detected during a structured Gate 7 verification.

### 12.3 False-Stable Startup States

A false-stable startup state is when the application appears fully functional on startup but contains latent defects that only activate after specific user interaction sequences.

**Indicators of false-stable startup:**
- App launches and initial route renders correctly
- Default player selection (if auto-selected) renders correctly
- But: the app has never been tested with no default data present
- And: the app has never been tested after the operator interacts with a non-default flow

False-stable startup states almost always involve session_state initialization that succeeds with default values but fails when a non-default user selection overwrites those values and a subsequent rerender attempts to read a key that was only initialized for the default path.

### 12.4 Silent Tactical Degradation Patterns

Silent tactical degradation is a reduction in UX quality that does not produce errors but reduces operator efficiency. It is detectable only through operator-observed timing and workflow friction.

**Common silent degradation patterns:**
- Escalation display speed reduced (operator adapts to slower response without noticing the cause)
- Sort order inconsistency in low-stakes scenarios (operator manually re-sorts, accepts it as normal)
- Occasional filter failure that clears when re-applied (operator applies filter twice as habit)
- Investigation panel load latency increase (operator attributes to network, not to extraction)

All of these patterns reduce ROI-impacting operator efficiency. Gate 5 tactical flow verification must be sensitive enough to detect latency increases > 1 second and any interaction that requires two attempts.

### 12.5 State Persistence Illusions

A state persistence illusion occurs when a session_state value appears to persist across navigation but is actually being re-initialized with the same default value, masking the fact that the user's selection was lost.

**Example:** The operator selects "2026-05-23" as the active date and navigates to the Reports route. The date appears correctly in the Reports route header — but this is because the Reports route re-initializes the date from `datetime.today()`, not from the session_state key the operator set. If the operator had selected a different date (e.g., "2026-05-20"), the Reports route would silently display "2026-05-23" regardless.

**Detection:** State persistence tests must always use a non-default value. If you test with the same value that initialization would produce, you cannot distinguish persistence from re-initialization.

---

## 13. Future Validation Vision

### 13.1 Automated Rerender Tracing

Future validation infrastructure should include an automated rerender trace that records every session_state read and write across a full render cycle and compares it against the pre-extraction baseline. Any new read/write pair, or any change in read/write order, is flagged for human review.

Implementation direction: Streamlit's `st.session_state` object can be wrapped in a tracing proxy that logs all accesses. The trace output can be compared diff-style against a baseline captured before extraction.

Expected benefit: Automatic detection of Pattern A and Pattern B hidden rerender corruption without requiring manual observation.

### 13.2 Dependency Graph Validation

Post-extraction dependency graph validation would verify that the actual import graph of the extracted system matches the intended graph from the dependency audit doctrine. Any new edge in the graph (A imports B when it wasn't supposed to) or missing edge (A no longer imports B but needed to) would be flagged.

Implementation direction: `importlib` and Python's `modulefinder` can reconstruct the actual import graph at runtime. Compare against the documented "legal import direction" matrix from `runtime_isolation_boundary_doctrine_v1.md`.

### 13.3 Extraction Simulation

Before executing a real extraction, an extraction simulator would:
1. Create a temporary copy of the app.py segment being extracted
2. Run it as an isolated module
3. Execute all gate-0 through gate-3 checks against the simulated extraction
4. Report any failures that would occur in the real extraction

This allows pre-detection of import errors, side-effect imports, and isolated runtime failures before any production code is touched.

### 13.4 Runtime Trust Scoring

Runtime trust scoring would produce a 0–100 score for each extraction's validation status based on:
- Number of distinct runtime paths observed (40 points)
- Gate pass/fail history (30 points)
- Observation window elapsed vs minimum required (20 points)
- Operator sign-off completed (10 points)

A trust score < 70 would block subsequent extractions. A trust score ≥ 90 would be the threshold for full production release.

### 13.5 Modular Validation Dashboards

A future validation dashboard within the Streamlit app would display the current validation status of all extracted modules, including:
- Gate status per module
- Observation window progress
- Active WARNINGs and CRITICALs
- Rollback readiness indicator
- Last operator confirmation timestamp

This provides continuous operational visibility into modularization health, not just point-in-time extraction validation.

---

## Appendix A: Runtime Verification Checklist

```
PRE-EXTRACTION
[ ] All prior extractions: observation windows closed
[ ] Rollback snapshot created and restore tested
[ ] System in known-good baseline (Gates 0-3 passing before extraction begins)
[ ] session_state key inventory captured for target extraction scope
[ ] Cache identity fingerprint captured for all @st.cache_data in scope
[ ] Hidden dependency analysis complete and documented
[ ] Operator present or scheduled for Gates 3-8

IMMEDIATE POST-EXTRACTION (Gates 0-3)
[ ] Gate 0: py -m py_compile passes on all new/modified files
[ ] Gate 0: py -c "import <module>" passes without side effects
[ ] Gate 1: No session_state writes at import time
[ ] Gate 1: All new imports resolve cleanly
[ ] Gate 2: Extracted module testable in isolation
[ ] Gate 2: Exported interface matches all caller expectations
[ ] Gate 3: App cold-start launches without exception
[ ] Gate 3: Default route renders without Streamlit warnings

OBSERVATION WINDOW (Gates 4-7)
[ ] Gate 4: 3 rerender cycles, no anomalies
[ ] Gate 4: Widget state persists across rerenders
[ ] Gate 4: No hydration loop indicators
[ ] Gate 5: Full tactical flow walkthrough completed
[ ] Gate 5: Full Slate renders correctly with full dataset
[ ] Gate 5: Player investigation flow complete
[ ] Gate 5: Modal open/fill/close cycle verified
[ ] Gate 6: All routes resolve without error
[ ] Gate 6: active_workspace persists across route transitions
[ ] Gate 6: Back navigation does not corrupt state
[ ] Gate 7: State persistence tested with non-default values
[ ] Gate 7: Cold-start session verification (new browser session)
[ ] Gate 7: Hydration fingerprint stable across 3 reloads

STABILIZATION SIGN-OFF (Gate 8)
[ ] Operator reviews Gates 0-7 pass records
[ ] Operator executes tactical flow walkthrough independently
[ ] Operator confirms no visual regressions
[ ] Operator issues runtime trust confirmation (signed, timestamped)
[ ] Extraction logged as STABLE in extraction registry
[ ] Observation window formally closed
[ ] Next extraction authorized
```

---

## Appendix B: Rerender Warning Signatures

```
CRITICAL SIGNATURES (rollback required if confirmed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WIDGET_STATE_WIPE
  Observable: Selectbox, text input, or multiselect resets to default
              value after an unrelated widget interaction
  Cause: session_state key initialized in wrong execution phase
  Test: Set widget to non-default value; interact with unrelated widget;
        verify value preserved
  Response: Immediate rollback

SPINNER_LOOP (HYDRATION LOOP)
  Observable: Loading spinner appears and does not resolve;
              continuous "Script execution completed" in console
  Cause: st.rerun() in code path executed on every render cycle
  Test: Load app; observe console for > 30 seconds without interaction
  Response: EMERGENCY — stop server immediately

ROUTE_DESYNC
  Observable: URL updates on navigation click but page content
              does not change; active route indicator incorrect
  Cause: Route dispatcher lost sync with active_workspace
  Test: Click each route in navigation shell; verify content updates
  Response: Immediate rollback

SILENT_STATE_DROP
  Observable: Operator-set value (player selection, date, filter)
              disappears without user action
  Cause: session_state key overwritten by relocated initialization code
  Test: Set a value; trigger 5 unrelated rerenders; verify value remains
  Response: Immediate rollback

SESSION_STATE_KEY_ERROR
  Observable: Streamlit console shows KeyError or AttributeError on
              st.session_state access
  Cause: Key read before initialization in new execution order
  Response: Immediate rollback

WARNING SIGNATURES (observation extended; investigate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHANTOM_RERENDER
  Observable: Page content flickers without user interaction
  Cause: Component calls st.rerun() outside user event handler
  Response: Extend observation; identify trigger path; if persists > 3 min: rollback

STALE_DATA_DISPLAY
  Observable: Data shows old values after interaction that should refresh
  Cause: Cache identity broken; stale warm cache served
  Response: Force cache clear; re-test; if persists: rollback

COMPONENT_DUPLICATION
  Observable: UI element (button, selector, table) appears twice
  Cause: Render function called from two locations post-extraction
  Response: Trace all callers of render function; if found: fix; if unclear: rollback

MODAL_BLEED
  Observable: Modal content visible after close; or prior modal data
              appears in new modal opening
  Cause: Modal session_state key not cleared on close
  Response: Verify modal close handler; if unresolved in 15 min: rollback

ESCALATION_LAG
  Observable: Tactical commands (sort, filter, investigate) take > 1s longer than baseline
  Cause: Extracted module adds import overhead or redundant computation
  Response: Profile extraction; if cause unclear: rollback
```

---

## Appendix C: Delayed Failure Examples

```
EXAMPLE 1: ONE-SESSION WONDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extraction: Player stat lookup module
Initial status: Passes Gates 0-4, 3 clean sessions
Failure trigger: Session 4, first-time selection of player not in warm cache
Symptom: Stat fields display as empty/None
Root cause: session_state key initialized one rerun cycle too late
           Only affects players not in warm Streamlit cache
Prevention: Gate 7 must test at least 3 players on cold cache
           (not previously loaded in session)

EXAMPLE 2: HAPPY LAUNCH
━━━━━━━━━━━━━━━━━━━━━━━
Extraction: Ranker module
Initial status: Passes Gates 0-3, operator declares success
Failure trigger: Session 3, slate with > 25 picks
Symptom: Sort order inconsistent; picks not ranked by composite score
Root cause: Pre-extraction defensive sort in app.py interacts with
           extracted ranker sort in wrong order on large datasets
Prevention: Gate 5 must test with full production-size slate
           (> 20 picks); never test with minimal data only

EXAMPLE 3: WARM CACHE ILLUSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extraction: Pipeline module
Initial status: Passes all gates in same session as extraction (warm cache)
Failure trigger: Morning after extraction, cold-cache compute
Symptom: Pick data incorrect; different from expected
Root cause: Extracted pipeline reads config parameters in different order;
           warm cache served correct results from pre-extraction compute
Prevention: Gate 7 requires cold-start testing in NEW session
           after overnight server restart for MODERATE+ tier extractions

EXAMPLE 4: INVISIBLE RERENDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extraction: Utility formatting module
Initial status: Passes all gates; no anomalies in initial observation
Failure trigger: Multiple render paths on same page view
Symptom: HR probability values display with inconsistent decimal precision
Root cause: Second caller not updated to new import path;
           stale reference resolves at runtime via late-binding
Prevention: Gate 1 must verify ALL callers of extracted functions
           updated to new import path; static import graph required

EXAMPLE 5: STATE PERSISTENCE ILLUSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extraction: Date selector module
Initial status: Passes Gate 7 with today's date (default value)
Failure trigger: Operator selects historical date (2026-05-20)
Symptom: Reports route shows today's date regardless of selection
Root cause: Reports route re-initializes date from datetime.today()
           not from session_state; selection was never actually persisted
Prevention: Gate 7 state persistence tests MUST use non-default
           values; test with a value different from initialization default
```

---

## Appendix D: Rollback Escalation Matrix

```
SEVERITY    CONDITION                           ROLLBACK?  TIMING      AUTHORITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMERGENCY   Hydration loop confirmed            YES        Immediate   Automatic
EMERGENCY   Multi-zone state corruption         YES        Immediate   Automatic
CRITICAL    session_state KeyError              YES        < 5 min     Claude/Operator
CRITICAL    Route desync confirmed              YES        < 5 min     Claude/Operator
CRITICAL    Widget state wipe confirmed         YES        < 15 min    Claude/Operator
CRITICAL    Cold start exception                YES        < 15 min    Claude/Operator
CRITICAL    Full Slate fails to render          YES        < 5 min     Claude/Operator
CRITICAL    Data file corruption confirmed      YES        < 5 min     Operator
CRITICAL    Syntax error in extracted file      YES        Immediate   Automated
WARNING     Single widget flicker               EVALUATE   15 min eval Claude recommends
WARNING     Phantom rerender                    EVALUATE   15 min eval Claude recommends
WARNING     Stale data display                  EVALUATE   15 min eval Claude recommends
WARNING     Component duplication               EVALUATE   15 min eval Claude recommends
WARNING     Escalation lag confirmed            EVALUATE   15 min eval Claude recommends
INFO        Console deprecation warning         NO         Monitor     Log only
INFO        Minor visual inconsistency          NO         Monitor     Log only

ROLLBACK PROCEDURE TIMING REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Immediate: Stop interaction now; restore files; restart server; verify Gates 0-3
< 5 min: Stop interaction; investigate for max 5 min; if unclear → rollback
< 15 min: Attempt diagnosis; if root cause not identified in 15 min → rollback
15 min eval: Attempt diagnosis; rollback if not resolved in 15 min

POST-ROLLBACK COOLDOWN REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate 0-1 failure (syntax/import): 15 minutes minimum
Gate 2-3 failure (isolated/cold start): 1 hour minimum
Gate 4-5 failure (rerender/tactical): 4 hours minimum
Gate 6-7 failure (navigation/state): 24 hours minimum
Hydration loop or EMERGENCY: 48 hours minimum
Contaminated runtime (rollback insufficient): 24 hours additional
```

---

## Appendix E: Operator Runtime Approval Template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPERATOR RUNTIME APPROVAL — GATE 8 SIGN-OFF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTRACTION DETAILS
  Module extracted:      [module name]
  Extraction date:       [YYYY-MM-DD]
  Extraction risk tier:  [SAFE / MODERATE / HIGH]
  Operator:              [operator name]
  Sign-off timestamp:    [YYYY-MM-DD HH:MM]

GATE VERIFICATION SUMMARY
  Gate 0 — Syntax:           [ ] PASS  Notes: ___
  Gate 1 — Import:           [ ] PASS  Notes: ___
  Gate 2 — Isolated Runtime: [ ] PASS  Notes: ___
  Gate 3 — Cold Start:       [ ] PASS  Notes: ___
  Gate 4 — Rerender:         [ ] PASS  Cycles observed: ___  Notes: ___
  Gate 5 — Tactical Flow:    [ ] PASS  Notes: ___
  Gate 6 — Navigation:       [ ] PASS  Routes tested: ___  Notes: ___
  Gate 7 — State Persistence:[ ] PASS  Test values used: ___  Notes: ___

OBSERVATION WINDOW SUMMARY
  Distinct runtime paths observed: ___  (minimum required: ___)
  Wall-clock elapsed:              ___  (minimum required: ___)
  Sessions observed:               ___  (minimum required for tier: ___)
  Cold-start session completed:    [ ] YES
  Overnight gap observation:       [ ] YES / [ ] N/A (SAFE tier)

ANOMALIES DURING OBSERVATION
  WARNINGs observed:      ___  All resolved: [ ] YES / [ ] NO
  CRITICALs observed:     ___  (If any: rollback required — do not proceed)
  INFOs observed:         ___  Logged: [ ] YES

TACTICAL FLOW WALKTHROUGH
  Full Slate load verified:               [ ] YES
  Player investigation flow verified:     [ ] YES
  Modal open/fill/close verified:         [ ] YES
  Escalation pacing acceptable:           [ ] YES
  No visual regressions observed:         [ ] YES
  Operator assessment of UX quality:      [ ] No change / [ ] Improved / [ ] Degraded

VISUAL VERIFICATION
  All columns present in Full Slate:      [ ] YES
  Color coding preserved:                 [ ] YES
  No layout shifts from baseline:         [ ] YES
  Shell controls present on all routes:   [ ] YES
  Contextual rails accurate:              [ ] YES

RUNTIME TRUST DECLARATION
  I, [operator name], confirm that I have personally verified the above gates,
  completed the tactical flow walkthrough, and observed no unresolved anomalies.
  I grant FULL RUNTIME TRUST to this extraction as of [YYYY-MM-DD HH:MM].

  I confirm the system is in a known-good state and authorize the observation
  window to be formally closed.

  Signature: _______________________  Date: _______________

NEXT EXTRACTION AUTHORIZATION
  This sign-off authorizes the next queued extraction to begin.
  Next extraction target: [module name or "TBD"]
  Authorized to begin after: [timestamp — typically immediately or after cooldown]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF GATE 8 SIGN-OFF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

*Document Status: COMPLETE — Architecture Governance Doctrine v1*  
*Phase: Division 09 — Step 6/8 Validation Sequencing & Runtime Verification*  
*No production systems modified. No code extracted. Doctrine only.*  
*Protected runtime systems remain isolated and unchanged.*
