# Master Modularization Governance Framework v1.0
## MLB HR ENGINE — Room 09 Final Consolidation
### Status: EXECUTION-READY BASELINE | Planning Complete | No Production Changes

---

## PREAMBLE

This document is the **single authoritative source** for all modularization governance in MLB HR ENGINE. It supersedes no prior doctrine on its own terms but resolves all conflicts between them and establishes precedence order.

**What this document IS:**
- Unified governance baseline
- Doctrine hierarchy authority
- Execution readiness certification
- Protected-system law registry
- Operator authority framework

**What this document IS NOT:**
- Permission to begin extraction
- A code change
- A file movement
- A runtime modification
- An import restructure

---

## SECTION 1: WHY GOVERNANCE CONSOLIDATION EXISTS

### 1.1 The Problem with Unify-Later Modularization

Seven doctrines without a master hierarchy create:
- Conflicting freeze authority (which doc wins when two docs disagree?)
- Execution ambiguity (which module extracts first when two docs list different orders?)
- Contamination risk (engineer follows wrong doctrine during extraction)
- Rollback confusion (which rollback authority overrides which?)

### 1.2 Why Unified Law Prevents Failure

Single authoritative hierarchy means:
- **One precedence chain.** When rules conflict, precedence is deterministic.
- **One extraction order.** No ambiguity about what ships first.
- **One rollback authority.** No debate about who can freeze or halt.
- **One protected-system registry.** No system accidentally touched due to missing coverage.

### 1.3 Core Principle

> Modularization without unified governance is refactoring without a net.
> Runtime trust is a hard-won asset. Modular purity is a preference.
> When they conflict, runtime trust wins.

---

## SECTION 2: GOVERNANCE HIERARCHY

### 2.1 Authoritative Precedence Order

When any two governance rules conflict, this order resolves:

| Rank | Document | Authority Domain |
|------|----------|-----------------|
| **1** | `master_modularization_governance_framework_v1.md` (THIS DOC) | Final authority. Resolves all conflicts. |
| **2** | `production_extraction_readiness_doctrine_v1.md` | Go/No-Go gate. Blocks extraction if criteria unmet. |
| **3** | `runtime_isolation_boundary_doctrine_v1.md` | Runtime protection law. Defines what cannot be touched. |
| **4** | `validation_runtime_verification_doctrine_v1.md` | Validation authority. Defines what "success" means. |
| **5** | `extraction_execution_governance_doctrine_v1.md` | Execution rules. Defines how extraction proceeds. |
| **6** | `phase1_extraction_prioritization_doctrine_v1.md` | Extraction ordering. Defines what extracts first. |
| **7** | `modularization_dependency_audit_doctrine_v1.md` | Dependency law. Defines allowable import direction. |
| **8** | `controlled_modularization_doctrine_v1.md` | Philosophy foundation. All other docs inherit from this. |

### 2.2 Conflict Resolution Rule

> **If any two lower-ranked docs conflict, the higher-ranked doc governs.**
> **If this document (Rank 1) is silent on a topic, the highest-ranked doc covering it governs.**
> **If no doc covers it, the operator decides. The decision becomes doctrine.**

### 2.3 Supporting Context Documents (non-binding for conflicts)

These inform but do not govern extraction decisions:
- `ai_workforce_orchestration_doctrine_v1.md` — workforce role boundaries
- `known_good_baseline_definition.md` — stabilization baseline reference
- `runtime_validation_playbook_v1.md` — validation procedure reference
- `production_extraction_readiness_doctrine_v1.md` — checklist reference
- `stabilization_closeout_summary.md` — historical context only

---

## SECTION 3: FINAL MODULARIZATION PHILOSOPHY

### 3.1 Five Core Laws (Inherited from All Prior Docs, Consolidated Here)

**Law 1 — Deterministic Architecture**
Every extraction produces a deterministic, reproducible result. No probabilistic rewrites. No "should be equivalent" changes. Behavior-preserving only.

**Law 2 — Rollback First**
Before any extraction begins, rollback is verified. If rollback cannot be demonstrated, extraction does not begin. This is non-negotiable.

**Law 3 — Stabilization Before Expansion**
No new features during extraction phases. No parallel modularization and feature development. Stabilization owns the runway until extraction completes.

**Law 4 — Bounded Ownership**
Every extracted module has a single declared owner (Claude or Codex). No shared ownership. No ambiguous authority. Crossing ownership boundaries requires operator approval.

**Law 5 — Runtime Trust Over Modular Purity**
A working monolith is preferable to a broken module. If extraction introduces any regression, the module returns to monolith immediately. Modular structure is an optimization, not an obligation.

### 3.2 Tactical Continuity Preservation

Modularization must never interrupt:
- MAIN tab render continuity
- JIG scoring continuity
- Full Slate orchestration continuity
- Escalation hierarchy integrity
- Investigation flow state

Tactical continuity is a **hard constraint**, not a preference.

---

## SECTION 4: FINAL RUNTIME PROTECTION LAW

### 4.1 Absolute Protected Systems — FROZEN UNTIL OPERATOR LIFTS FREEZE

The following systems are frozen. No extraction, no rewrite, no import change, no structural modification without explicit operator written authorization:

#### 4.1.1 Routing & Navigation
- `active_workspace` ownership and mutation
- `active_route` synchronization logic
- Navigation continuity startup sequence (`spec_navigation_continuity_v1.md`)
- Route dispatch table

#### 4.1.2 Session State
- All `st.session_state` initialization blocks
- Session state key namespace (no additions, no removals, no renames)
- State mutation ordering (startup → hydration → render)
- Session fingerprint guard

#### 4.1.3 Cache Systems
- All `@st.cache_data` ownership boundaries
- Cache invalidation triggers
- Cache key schemas
- Cross-tab cache sharing contracts

#### 4.1.4 Shell Orchestration
- Shell render sequence
- Shell startup execution order
- Active workspace shell dispatch
- Shell-to-tab communication contract

#### 4.1.5 Hydration & Fingerprinting
- Hydration fingerprint guard logic
- Context restoration stack (`spec_context_restoration_stack_v1.md`)
- Startup hydration ordering
- Operator memory hydration sequence

#### 4.1.6 Pipeline Contract
- `pipeline.py` output schema (field names, types, column order)
- Pipeline → tab data contract
- Probability output format
- Pick ranking output format

#### 4.1.7 Tactical Render Chains
- MAIN tab render sequence
- JIG tab render sequence
- Full Slate tab render sequence
- Strategy tab render sequence
- Performance tab render sequence
- TCC shell render contract (`universal_tcc_shell_doctrine_v1.md`)

#### 4.1.8 Modal Containment
- Modal z-index governance (`spec_modal_governance_v1.md`)
- Modal open/close state ownership
- Modal-to-session state communication

#### 4.1.9 Orchestration Chains
- Full Slate parent orchestrator (`full_slate_parent_orchestrator_doctrine.md`)
- Escalation hierarchy chain (`spec_full_slate_escalation_hierarchy_v1.md`)
- Deployment command center chain (`deployment_command_center_doctrine.md`)

#### 4.1.10 Config Hub
- `config.py` — no structural changes during extraction
- All model constants remain frozen during extraction phases
- No config key renames during extraction

### 4.2 Freeze Enforcement

Any PR, commit, or execution that touches a protected system without operator lift:
1. **Blocked immediately**
2. **Operator notified**
3. **No merge until operator approves or rejects**

---

## SECTION 5: FINAL EXTRACTION EXECUTION LAW

### 5.1 Official Extraction Order

Derived from `phase1_extraction_prioritization_doctrine_v1.md` and `extraction_execution_governance_doctrine_v1.md`. Conflict resolved: this order is final.

#### Phase 1 — Safe Helper Extraction (Pure Functions, Zero Runtime Risk)
| Step | Target | Rationale |
|------|--------|-----------|
| 1a | Formatting utilities | No state, no imports upward, pure output |
| 1b | Color/badge mapping constants | Declarative, no runtime dependency |
| 1c | Metric calculation helpers | Pure math, no session_state |
| 1d | Display string builders | No cache, no session dependency |

#### Phase 2 — State-Adjacent Extraction (Read-Only State Access)
| Step | Target | Rationale |
|------|--------|-----------|
| 2a | Stateless filter functions | Read config only, return filtered data |
| 2b | Stateless ranker helpers | Read picks, return ranked picks |
| 2c | Display table builders | Accept data in, return display artifact |

#### Phase 3 — Thin Orchestration Layer (Post-Phase-2 Stabilization Only)
| Step | Target | Rationale |
|------|--------|-----------|
| 3a | Tab content renderers | Thin wrappers calling Phase 1/2 modules |
| 3b | Sidebar component modules | Isolated sidebar logic |
| 3c | Card render components | Threat card, suppression card modules |

**Phase 3 does not begin until Phase 2 has been stable for ≥2 production sessions.**

### 5.2 Extraction Concurrency Rules

- **One extraction per session.** No parallel extractions.
- **One module per extraction step.** No bundled multi-module extractions.
- **No extraction while a runtime incident is open.** Freeze until resolved.
- **No extraction during Full Slate active deployment window.**

### 5.3 Observation Requirement

After each extraction step:
1. Run full app cold start → observe no error
2. Navigate to all 5 tabs → observe no regression
3. Trigger Full Slate run → observe output matches pre-extraction baseline
4. Observe for ≥1 full production session before proceeding to next step

### 5.4 Deployment Pacing

- Phase 1 steps: minimum 1 session between steps
- Phase 2 steps: minimum 2 sessions between steps
- Phase 3 steps: minimum 3 sessions between steps

### 5.5 Rollback Authority

Any of the following may initiate rollback without operator pre-approval:
- Any render regression on MAIN, JIG, or Full Slate tabs
- Any session_state KeyError post-extraction
- Any pipeline output schema mismatch
- Any escalation hierarchy render failure

Rollback procedure: revert the single extracted file, restore original import. Do not attempt to fix in-place during rollback — restore first, diagnose second.

---

## SECTION 6: FINAL VALIDATION AUTHORITY

### 6.1 Validation Hierarchy

| Level | Validator | Authority |
|-------|-----------|-----------|
| **L1** | Automated import check | Confirms no circular imports post-extraction |
| **L2** | Cold start observation | Confirms app launches without error |
| **L3** | Tab navigation observation | Confirms all 5 tabs render correctly |
| **L4** | Full Slate run observation | Confirms orchestration output matches baseline |
| **L5** | Operator sign-off | Confirms subjective visual/behavioral parity |

All 5 levels must pass before an extraction step is marked complete.

### 6.2 Rerender Observation Law

- No extraction step complete until ≥3 consecutive cold starts pass L1–L4 without error
- Intermittent pass does not count — must be consistent
- Flaky render after extraction = rollback, not observation window extension

### 6.3 False-Success Prevention

Known false-success patterns to watch for:
- Streamlit cached state masking import errors on warm reload (always cold-start test)
- Module appearing imported but actually falling back to inline duplicate (check with `import sys; sys.modules`)
- Tab appearing correct but session_state partially missing (validate with state inspector)

### 6.4 Runtime Observation Windows

- Phase 1 extraction: 1 production session minimum
- Phase 2 extraction: 2 production sessions minimum
- Phase 3 extraction: 3 production sessions minimum

Observation window starts from **first successful L5 operator sign-off**, not from extraction commit date.

---

## SECTION 7: FINAL RUNTIME BOUNDARY LAW

### 7.1 Layer Hierarchy (Strict Dependency Directionality)

```
Layer 0: config.py              ← no imports from any layer above
Layer 1: Pure helpers           ← import Layer 0 only
Layer 2: Data clients           ← import Layer 0-1 only
Layer 3: Engine modules         ← import Layer 0-2 only
Layer 4: Pipeline               ← import Layer 0-3 only
Layer 5: Tab renderers          ← import Layer 0-4 only
Layer 6: Shell / app.py         ← import Layer 0-5 only
```

**No upward imports.** Layer N cannot import Layer N+1 or higher. Violation = extraction blocked.

### 7.2 Ownership Domains

| Domain | Owner | Import Boundary |
|--------|-------|-----------------|
| config.py | Operator (frozen) | Layer 0 — no imports |
| engine/ | Claude | Layer 3 — engine logic |
| clients/ | Claude | Layer 2 — data fetch |
| pipeline.py | Claude (frozen contract) | Layer 4 |
| tracking/ | Claude | Layer 2-3 |
| portfolio/ | Claude | Layer 3 |
| output/ | Claude | Layer 3 |
| app.py tabs | Claude (frozen render) | Layer 5-6 |
| Shell orchestration | Claude (frozen) | Layer 6 |

### 7.3 State Mutation Law

- Only `app.py` and shell orchestration modules may write `st.session_state`
- Extracted modules receive state values as **function arguments**, never direct state access
- No extracted module calls `st.session_state` directly
- Violation = extraction rejected before merge

### 7.4 Cache Ownership Law

- `@st.cache_data` decorators remain in `pipeline.py` and `app.py`
- No extracted module introduces new `@st.cache_data`
- No extracted module calls `st.cache_data.clear()`
- Cache ownership changes require operator approval

---

## SECTION 8: FINAL TACTICAL PROTECTION LAW

### 8.1 Protected Tactical Systems

The following tactical systems are protected from extraction-induced regression:

**MAIN Tab:**
- Batter threat card display (`spec_player_threat_card_v1.md`)
- Escalation badge rendering (`spec_escalation_badge_system_v1.md`)
- TCC shell render (`universal_tcc_shell_doctrine_v1.md`)
- Batters table sort/filter state

**JIG Tab:**
- JIG composite score calculation
- JIG sort type safety
- JIG modal persistence

**Full Slate Tab:**
- Parent orchestrator chain (`full_slate_parent_orchestrator_doctrine.md`)
- Escalation hierarchy (`spec_full_slate_escalation_hierarchy_v1.md`)
- Slate-level risk governance (`spec_risk_governance_v1.md`)

**Strategy Tab:**
- Portfolio exposure system (`spec_portfolio_exposure_system_v1.md`)
- Bankroll command layer (`spec_bankroll_command_layer_v1.md`)

**Performance Tab:**
- CLV intelligence system (`spec_clv_intelligence_system_v1.md`)
- Live intelligence feed (`spec_live_intelligence_feed_v1.md`)
- Post-slate review (`spec_post_slate_review_v1.md`)

**Shared Infrastructure:**
- Operational sidebar (`spec_operational_sidebar_v1.md`)
- Global shell architecture (`spec_global_shell_architecture_v1.md`)
- Deployment panel (`spec_deployment_panel_architecture_v1.md`)
- Interruption recovery (`spec_interruption_recovery_v1.md`)

### 8.2 Extraction Impact Assessment (Required for Every Step)

Before any extraction, complete this checklist:
- [ ] Does extracted code touch any protected tactical system? If yes → stop.
- [ ] Does extracted module require state access? If yes → pass as argument, not direct access.
- [ ] Does extracted module introduce new cache behavior? If yes → operator approval required.
- [ ] Does extracted module change import topology for any Layer 5+ module? If yes → runtime boundary audit required.

---

## SECTION 9: FINAL OPERATOR AUTHORITY DOCTRINE

### 9.1 Operator Override Powers

The operator may, at any time:
- Freeze any active extraction step
- Accelerate pacing beyond recommended observation windows (at operator's risk)
- Expand or contract the protected-system registry
- Demote or promote extraction priority order
- Approve or reject any module boundary change

### 9.2 Freeze Powers

The operator may declare a **Total Extraction Freeze** which:
- Halts all extraction activity immediately
- Requires explicit operator lift to resume
- Cannot be overridden by Claude or Codex

Freeze triggers:
- Any production incident during extraction phases
- Any calibration drift event (|bias|>3pp at n≥50)
- Any runtime regression in protected system
- Operator discretion

### 9.3 Rollback Authority Chain

| Trigger | Who Can Initiate | Approval Required |
|---------|-----------------|-------------------|
| Render regression | Claude | None — immediate |
| session_state error | Claude | None — immediate |
| Pipeline schema mismatch | Claude | None — immediate |
| Escalation hierarchy failure | Claude | None — immediate |
| Discretionary rollback | Claude | Operator notification |
| Rollback of rollback (re-extract) | Claude | Operator approval required |

### 9.4 Advancement Approval Authority

Each phase boundary requires explicit operator approval:
- Phase 1 → Phase 2: operator confirms Phase 1 complete, stable, signed off
- Phase 2 → Phase 3: operator confirms Phase 2 complete, stable, signed off
- Phase 3 complete: operator formally closes modularization roadmap

No AI workforce member may self-authorize phase advancement.

---

## SECTION 10: FINAL AI WORKFORCE GOVERNANCE

### 10.1 Claude Authority Zones

Claude MAY independently execute:
- Phase 1 extractions (pure helpers, zero state)
- Validation observation and reporting
- Rollback execution (when trigger conditions met)
- Governance documentation updates
- Dependency audit analysis

Claude REQUIRES operator approval for:
- Phase 2 extraction steps
- Phase 3 extraction steps
- Any change to protected systems
- Any change to this governance document
- Any change to doctrine hierarchy precedence

### 10.2 Codex Authority Zones

Codex MAY independently execute:
- Phase 1 implementations where explicitly scoped
- Test creation for extracted modules
- Import verification scripts

Codex REQUIRES operator approval for:
- Any extraction that modifies session_state access patterns
- Any extraction that modifies cache behavior
- Any Phase 2 or Phase 3 work

Codex MUST NOT:
- Modify app.py shell orchestration
- Modify pipeline.py contract
- Modify config.py
- Modify any protected tactical system

### 10.3 Blocked-State Governance

If extraction is blocked (trigger condition met, rollback complete, no path forward):
1. Claude documents the block with exact failure description
2. Operator is notified
3. No further extraction attempted until operator reviews
4. Claude may propose remediation — operator decides

### 10.4 Stabilization Sequencing

Stabilization work and modularization work do not run concurrently. If a stabilization-owned system requires attention, modularization pauses entirely. Stabilization takes full runway priority.

---

## SECTION 11: EXECUTION READINESS CRITERIA

### 11.1 Required Conditions Before First Extraction Begins

All of the following must be true simultaneously:

**Stabilization Conditions:**
- [ ] All stabilization-owned systems in known-good state (`known_good_baseline_definition.md`)
- [ ] No active runtime regression in any of the 5 tabs
- [ ] Full Slate orchestration passing consistently
- [ ] No active operator-declared freeze

**Rollback Conditions:**
- [ ] Git state is clean (all prior work committed)
- [ ] Rollback procedure tested and confirmed working on at least one dry run
- [ ] Branch is isolated from main — extraction work on dedicated branch

**Trust Conditions:**
- [ ] Production data pipeline producing output for current date
- [ ] Calibration bias within acceptable range (|bias|<3pp at n≥50)
- [ ] No active model-layer incidents

**Runtime Observation Conditions:**
- [ ] At least 2 consecutive cold-start L1–L4 passes with no errors before extraction begins
- [ ] All 5 tabs navigable without error

**Governance Conditions:**
- [ ] All 7 prior doctrines reviewed and confirmed not conflicting with this document
- [ ] This master framework reviewed and operator-acknowledged
- [ ] Extraction order confirmed by operator (Phase 1 target identified)

### 11.2 Formal Go/No-Go Gate

Before first extraction commit:

> **OPERATOR MUST EXPLICITLY STATE: "Ready to begin Phase 1 extraction."**
>
> Without this statement, no extraction work begins regardless of all other criteria being met.

This gate cannot be satisfied by implication. It requires explicit operator authorization.

---

## SECTION 12: FUTURE MODULARIZATION ROADMAP

### 12.1 Phase 1 — Helper Extraction (Current)

**Target:** Pure formatting, badge/color mapping, metric calculation utilities

**Duration estimate:** 4–6 extraction steps, minimum 4 sessions

**Success criteria:** All helpers extracted, all 5 tabs stable, zero state access in extracted modules

**Thin-orchestrator progress:** 0% (not applicable — Phase 1 only removes leaf nodes)

### 12.2 Phase 2 — State-Adjacent Extraction

**Target:** Stateless filter/ranker helpers, display table builders

**Prerequisites:** Phase 1 complete + stable for ≥2 sessions + operator approval

**Duration estimate:** 3–5 extraction steps, minimum 6 sessions

**Thin-orchestrator progress:** ~20% (tab renderers begin receiving external data, not constructing it)

### 12.3 Phase 3 — Orchestration Thinning

**Target:** Tab content renderers, sidebar components, card render components

**Prerequisites:** Phase 2 complete + stable for ≥3 sessions + operator approval

**Duration estimate:** 6–10 extraction steps, minimum 12 sessions

**Thin-orchestrator progress:** ~60% (shell and pipeline remain monolithic; tabs become thin coordinators)

### 12.4 Long-Term Bounded Architecture Vision

**Target state (not a commitment — a directional goal):**

```
app.py              → thin shell: routing, session init, dispatch only
pipeline.py         → data contract layer (unchanged structure)
tabs/               → thin coordinators calling component modules
components/         → self-contained render modules (no state write)
helpers/            → pure function library (no imports above Layer 1)
engine/ clients/    → unchanged (already well-bounded)
config.py           → unchanged hub
```

**What never modularizes:**
- Session state mutation (stays in shell)
- Cache ownership (stays in pipeline.py / app.py)
- Startup execution order (stays in app.py)
- Pipeline output contract (stays frozen)

---

## SECTION 13: FINAL GOVERNANCE SUMMARY

### 13.1 Authoritative Governance Pyramid

```
                    ┌─────────────────────────────────┐
                    │  master_modularization_          │  ← Rank 1: THIS DOC
                    │  governance_framework_v1         │     Resolves all conflicts
                    └────────────────┬────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ production_       │  │ runtime_         │  │ validation_      │  ← Rank 2-4
   │ extraction_       │  │ isolation_       │  │ runtime_         │     Gate + Law
   │ readiness_v1      │  │ boundary_v1      │  │ verification_v1  │     + Authority
   └──────────────────┘  └──────────────────┘  └──────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ extraction_       │  │ phase1_          │  │ modularization_  │  ← Rank 5-7
   │ execution_        │  │ extraction_      │  │ dependency_      │     Execution
   │ governance_v1     │  │ prioritization_  │  │ audit_v1         │     + Ordering
   └──────────────────┘  └──────────────────┘  └──────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  controlled_modularization_      │  ← Rank 8: Foundation
                    │  doctrine_v1                     │     All docs inherit from this
                    └─────────────────────────────────┘
```

### 13.2 Execution Flow Summary

```
PLANNING COMPLETE
      │
      ▼
Operator: "Ready to begin Phase 1 extraction."
      │
      ▼
Pre-extraction checklist (Section 11.1) → ALL pass
      │
      ▼
Phase 1, Step 1a: Extract formatting utilities
      │
      ▼
Validate L1→L5 (Section 6.1) → ALL pass
      │
      ▼
Observe ≥1 production session
      │
      ▼
Phase 1, Step 1b: Extract color/badge constants
      │
      ▼
[Continue Phase 1 steps...]
      │
      ▼
Operator: Phase 1 complete sign-off
      │
      ▼
Phase 2 begins (operator approval required)
      │
      ▼
[Continue to Phase 3 with operator approval]
```

### 13.3 Freeze/Escalation Flow

```
Trigger event occurs (regression / incident / operator discretion)
      │
      ▼
Extraction STOPS immediately
      │
      ▼
Claude rolls back (if trigger = runtime regression)
      │
      ▼
Claude documents failure
      │
      ▼
Operator notified
      │
      ▼
Operator reviews → Decision:
├── Resume: explicit operator lift, re-run Section 11.1 checklist
└── Escalate: redesign extraction step scope, re-plan
```

### 13.4 Rollback Hierarchy Summary

| Severity | Trigger | Rollback Speed | Approval |
|----------|---------|---------------|----------|
| P0 | Protected system regression | Immediate | None |
| P1 | Tab render failure | Immediate | None |
| P1 | session_state KeyError | Immediate | None |
| P2 | Intermittent render issue | Next session | Operator notification |
| P3 | Non-critical display regression | Planned | Operator approval |

### 13.5 Final Go/No-Go Framework

```
GO conditions (ALL must be true):
  ✓ Stabilization clean
  ✓ No active regression
  ✓ Rollback verified
  ✓ Branch isolated
  ✓ Calibration stable
  ✓ Operator explicit authorization

NO-GO conditions (ANY triggers hold):
  ✗ Any open runtime incident
  ✗ Active operator freeze
  ✗ Calibration alert active (|bias|>3pp at n≥50)
  ✗ Full Slate orchestration unstable
  ✗ Branch not isolated from main
  ✗ Operator authorization not given
```

---

## APPENDIX A: UNIFIED PROTECTED SYSTEMS REGISTRY

| System | Location | Protection Level | Lift Authority |
|--------|----------|-----------------|----------------|
| active_workspace ownership | app.py | ABSOLUTE | Operator only |
| active_route sync | app.py | ABSOLUTE | Operator only |
| Navigation startup sequence | app.py | ABSOLUTE | Operator only |
| st.session_state init | app.py | ABSOLUTE | Operator only |
| Session state key namespace | app.py | ABSOLUTE | Operator only |
| State mutation ordering | app.py | ABSOLUTE | Operator only |
| Hydration fingerprint guard | app.py | ABSOLUTE | Operator only |
| @st.cache_data ownership | pipeline.py / app.py | ABSOLUTE | Operator only |
| Cache invalidation triggers | pipeline.py | ABSOLUTE | Operator only |
| Shell render sequence | app.py | ABSOLUTE | Operator only |
| Shell startup order | app.py | ABSOLUTE | Operator only |
| Shell-to-tab contract | app.py | ABSOLUTE | Operator only |
| pipeline.py output schema | pipeline.py | ABSOLUTE | Operator only |
| Pipeline → tab data contract | pipeline.py | ABSOLUTE | Operator only |
| MAIN tab render sequence | app.py / tabs | ABSOLUTE | Operator only |
| JIG tab render sequence | app.py / tabs | ABSOLUTE | Operator only |
| Full Slate render sequence | app.py / tabs | ABSOLUTE | Operator only |
| TCC shell render | app.py | ABSOLUTE | Operator only |
| Modal containment | app.py | ABSOLUTE | Operator only |
| Full Slate orchestrator chain | app.py | ABSOLUTE | Operator only |
| Escalation hierarchy chain | app.py | ABSOLUTE | Operator only |
| config.py structure | config.py | ABSOLUTE | Operator only |
| config.py key names | config.py | ABSOLUTE | Operator only |

---

## APPENDIX B: UNIFIED EXTRACTION ORDER MATRIX

| Phase | Step | Target Module | Risk Level | Observation Window |
|-------|------|--------------|------------|-------------------|
| 1 | 1a | Formatting utilities | LOW | 1 session |
| 1 | 1b | Color/badge constants | LOW | 1 session |
| 1 | 1c | Metric calculation helpers | LOW | 1 session |
| 1 | 1d | Display string builders | LOW | 1 session |
| 2 | 2a | Stateless filter functions | MEDIUM | 2 sessions |
| 2 | 2b | Stateless ranker helpers | MEDIUM | 2 sessions |
| 2 | 2c | Display table builders | MEDIUM | 2 sessions |
| 3 | 3a | Tab content renderers | HIGH | 3 sessions |
| 3 | 3b | Sidebar component modules | HIGH | 3 sessions |
| 3 | 3c | Card render components | HIGH | 3 sessions |

**Pacing rule:** Steps within same phase may not run concurrently. One step at a time, always.

---

## APPENDIX C: UNIFIED VALIDATION HIERARCHY

| Level | Check | Method | Pass Criteria |
|-------|-------|--------|---------------|
| L1 | Import graph | `python -c "import app"` | No ImportError, no circular import |
| L2 | Cold start | Full app launch | No Streamlit error on startup |
| L3 | Tab navigation | Navigate all 5 tabs | No render error, no empty tab |
| L4 | Full Slate run | Trigger Full Slate | Output matches pre-extraction baseline |
| L5 | Operator sign-off | Visual inspection | Operator confirms behavioral parity |

All 5 levels required. No skipping. No "close enough."

---

## APPENDIX D: UNIFIED FREEZE & ROLLBACK MATRIX

| Event | Freeze Scope | Rollback Scope | Operator Notif. |
|-------|-------------|----------------|-----------------|
| P0 protected system regression | All extraction | Immediate full revert | Required |
| P1 tab render failure | Active step only | Immediate step revert | Required |
| P1 session_state error | Active step only | Immediate step revert | Required |
| P2 intermittent regression | Active step + next | Step revert next session | Recommended |
| P3 non-critical regression | Active step | Step revert when scheduled | Advisory |
| Operator discretion freeze | All extraction | Operator-directed | N/A (operator initiated) |
| Calibration alert (|bias|>3pp) | All extraction | No revert (model issue) | Required |
| Full Slate instability | All extraction | No revert (orchestration issue) | Required |

---

## APPENDIX E: UNIFIED OPERATOR APPROVAL FRAMEWORK

| Action | Operator Approval Required | Method |
|--------|--------------------------|--------|
| Begin Phase 1 extraction | YES — explicit statement | Verbal/written |
| Advance Phase 1 → Phase 2 | YES — phase sign-off | Written |
| Advance Phase 2 → Phase 3 | YES — phase sign-off | Written |
| Lift any protected system freeze | YES — explicit statement | Written |
| Approve Phase 2+ step | YES — per-step | Written |
| Rollback (P0/P1) | NO — Claude executes immediately | Post-hoc notification |
| Rollback (P2/P3) | Notification only | Post-hoc |
| Modify this document | YES | Written |
| Modify doctrine hierarchy | YES | Written |
| Accelerate observation window | YES — at operator risk | Written |
| Declare Total Extraction Freeze | Operator only (no delegation) | Verbal/written |
| Lift Total Extraction Freeze | Operator only (no delegation) | Written |

---

## DOCUMENT METADATA

```
Document:     master_modularization_governance_framework_v1.md
Status:       COMPLETE — Execution-Ready Governance Baseline
Phase:        Room 09, Step 8 (Final Step)
Owner:        Claude (governance); Operator (authority)
Created:      2026-05-23
Supersedes:   No prior document — resolves conflicts between all 7 prior docs
Inherited by: All future modularization execution sessions
Review:       Required before any Phase 2 or Phase 3 work begins
```

---

*Consolidation complete. All governance conflicts resolved. Execution-ready baseline established.*
*No production changes made. No files moved. No code modified.*
*Next step: Operator explicit authorization to begin Phase 1 extraction.*
