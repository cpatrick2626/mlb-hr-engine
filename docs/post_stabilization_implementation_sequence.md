# Post-Stabilization Implementation Sequence
## MLB HR Engine — Master Stabilization

**Date:** 2026-05-20  
**Step:** 12 of 12  
**Owner:** Claude (sequencing doctrine)  
**Version:** v1.0 — Post-Step-12

---

## Purpose

Defines the safe implementation order after stabilization closeout. Prevents uncontrolled feature expansion, accidental destabilization of validated systems, and simultaneous broad architecture rewrites. Each phase must reach a validated stable state before the next phase begins.

**Core Rule:** One phase at a time. No concurrent phases. No simultaneous architecture rewrites.

---

## Phase 1 — Safe Shell Enhancements

**Risk Level:** LOW  
**Owner:** Codex (implementation) / Claude (doctrine compliance)

### Scope

Enhancements that add display information to existing rendering paths without touching session_state ownership, routing, or filter logic. These are the safest possible additions.

### Eligible Work

- `tab_advanced_strategies` lazy gate (identified Session 41)
- `tab_hits` lazy gate (identified Session 41)
- Adding QUANT tier pill or contextual badge variants to existing card types
- Expanding slate_status indicator logic (CONFIRMED / MIXED / PROJECTED)
- UI label improvements (font sizes, color refinements, wording clarity)

### Prerequisites

- Known-good baseline from `known_good_baseline_definition.md` locked
- All Step 12 documentation complete
- No open FAIL items in release readiness checklist

### Validation Gates

- `audit_pitch_mix.py` — all 7 tests pass after any pitch-related change
- Visual: collapsed pitch mix expanders cost ≤ 2 widget registrations
- Rerender: filter change ≤ 2 seconds with lazy gates active
- No regression to existing SAFE systems

### Rollback Expectations

All Phase 1 changes are display-layer only. Rollback by reverting the specific `app.py` edit. No session_state cleanup required.

---

## Phase 2 — Validation Expansions

**Risk Level:** LOW  
**Owner:** Claude (analysis) / Codex (plumbing fixes if needed)

### Scope

Statistical validation work that expands understanding of engine performance without modifying model logic. Analysis scripts only — no pipeline changes.

### Eligible Work

- Re-calibrate Platt parameters after n≥100 settled picks post-Session 23 regression ceiling (`analyze_calibration.py`)
- Re-evaluate optimizer EV/edge thresholds at n≥200 settled optimized picks
- Re-run `analyze_vig.py` after cache includes FD/DK empirical overround data
- Validate barrel-Kelly sizing advantage at n≥500 CLV picks
- Monitor 12-15% calibration bucket via `monitoring_dashboard.py Phase 4`

### Prerequisites

- Daily `ops_daily.py` running (settle + drift + CLV)
- `capture_closing_lines.py` running ~30min before first pitch
- n≥100 settled picks for Platt re-calibration
- n≥200 settled optimized picks for threshold re-evaluation
- n≥500 CLV picks for sizing validation

### Validation Gates

- New Platt parameters: CV Brier improvement confirmed vs prior parameters on held-out data
- Threshold changes: simulate ROI impact before applying to live picks
- All calibration changes require `monitoring_dashboard.py` baseline comparison

### Rollback Expectations

Config.py flags: `CALIBRATION_ENABLED`, `CALIBRATION_PLATT_A/B`, `ELITE_PLATT_ENABLED`. Rollback is config-only — no code change required.

---

## Phase 3 — Lightweight Tactical Rendering

**Risk Level:** LOW-MEDIUM  
**Owner:** Codex (implementation) / Claude (doctrine compliance)

### Scope

JIG Phase 2B tactical display improvements. Additive rendering only — does not modify pick scoring, HVY modifier formula, or MAIN engine.

### Eligible Work

- JIG Full Slate game-command module layout (three-panel: pitcher zone / player targets / live conditions)
- Tactical live strip at top of JIG Full Slate
- Game-organized view within All Tactical Players mode
- Return-to-top navigation in Full Slate
- Tactical tag system (FASTBALL HUNTER, BARREL SPIKE, ELITE MISMATCH) as display-only badges

### Prerequisites

- Phase 1 complete and stable (lazy gates confirmed working)
- JIG Full Slate 3-mode radio selector stable (Session 43)
- HVY modifier formula unchanged

### Validation Gates

- JIG Full Slate renders all 3 modes without exception
- Tactical tags are display-only: do not filter or reorder picks
- Game-organized view groups correctly by `game_pk`
- No MAIN pick list affected by JIG rendering changes
- Performance: JIG Full Slate (All Tactical Players mode) renders ≤ 3 seconds on cold build

### Rollback Expectations

Additive rendering changes. Rollback by reverting specific `app.py` edits. No session_state or data layer impact.

---

## Phase 4 — Scroll Restoration Execution

**Risk Level:** MEDIUM  
**Owner:** Codex (implementation) / Claude (doctrine compliance validation)

### Scope

Implementing the scroll restoration stack and anchor capture as defined in Step 10 doctrine. This is the first phase that writes to session_state in a new namespace.

### Eligible Work

- Restoration stack session_state structure (push/pop/prune, max depth 10)
- Pre-navigation anchor capture (read-only DOM snapshot)
- Breadcrumb renderer (display, reads from restoration stack)
- Shortlist core (add/remove/reorder, status state machine)
- Investigation notes (280-char, session-scoped)

### Prerequisites

- Phase 3 complete and stable
- Codex defines session_state key namespace for restoration stack (separate from active_workspace)
- Phase 1 lazy gates stable (scroll restoration fires after lazy gate resolution)
- DOM-settle timing mechanism confirmed by Codex

### Validation Gates

- Restoration stack depth never exceeds 10 (FIFO eviction confirmed)
- Fast-return (< 5 min): engine + game + player + JIG state + scroll all restored correctly
- Stack cleared completely on session end (no cross-session persistence)
- Partial restoration confirmed: stack pop with missing keys delivers available context
- No MAIN or JIG filter state corrupted by restoration stack push/pop
- Scroll loop prevention: 500ms lock confirmed, no infinite loop

### Rollback Expectations

New session_state namespace only. Rollback by removing restoration stack push/pop calls. Active_workspace and all existing filter keys unaffected.

---

## Phase 5 — Escalation Snapshot Integration

**Risk Level:** MEDIUM  
**Owner:** Codex (implementation) / Claude (doctrine compliance)

### Scope

Wiring escalation fire events to the restoration stack snapshot trigger, and implementing the recovery prompt after escalation resolution.

### Eligible Work

- Escalation snapshot trigger (push to restoration stack before CRITICAL loads)
- Recovery prompt display (after escalation resolves)
- Revisit indicator (`data_updated_since_review`) on shortlist entries
- Park action (snapshot + shortlist write)

### Prerequisites

- Phase 4 complete: restoration stack write stable
- Codex exposes escalation fire event as hook point
- Restoration stack push/pop schema matches Step 10 doctrine (ESCALATION TTL = 90 min)

### Validation Gates

- CRITICAL escalation: snapshot pushed before escalation tray loads
- Tray-only display: escalation does not replace main engine view
- Recovery prompt offered after escalation resolve (not auto-navigated)
- Restoration prompt restores correct pre-escalation context
- Stack TTL test: ESCALATION context expires correctly at 90 min

### Rollback Expectations

Snapshot trigger is additive to escalation fire event. Rollback by removing hook from escalation fire. Restoration stack unaffected.

---

## Phase 6 — Mobile Adaptation Layer

**Risk Level:** MEDIUM  
**Owner:** Codex (implementation) / Claude (spec compliance)

### Scope

Mobile drawer system implementation per `spec_responsive_tactical_layout_v1.md`. First phase that introduces a new rendering path distinct from the desktop layout.

### Eligible Work

- Mobile drawer component (offcanvas or custom Streamlit component)
- Mobile-specific card layout (GAME_ROW anchor, larger touch targets)
- Drawer session_state namespace (`_drawer_*` keys only)
- Mobile lazy load gates for pitch mix and JIG Power Profiles

### Prerequisites

- Phase 4-5 stable (scroll restoration must work before mobile drawer)
- Codex decision on component approach (custom HTML vs Streamlit component)
- Privacy and session_state isolation confirmed
- Desktop rendering path unchanged and stable

### Validation Gates

- Drawer opens/closes without full-page rerender
- No session_state key outside `_drawer_*` namespace modified by drawer
- All card types legible at 375px inside drawer
- GAME_ROW anchor confirmed on drawer close
- Desktop layout completely unaffected by mobile drawer code path

### Rollback Expectations

Mobile drawer is a conditional render path (viewport width check). Rollback by disabling the mobile branch. Desktop rendering unaffected.

---

## Phase 7 — Full Slate Advanced Orchestration

**Risk Level:** MEDIUM-HIGH  
**Owner:** Codex (implementation) / Claude (parent orchestrator doctrine)

### Scope

Advanced Full Slate orchestration features that require cross-engine context sharing within strict read-only bounds.

### Eligible Work

- Full Slate "All Players" game-organized advanced view (pitcher context, live conditions strip)
- Slate-level urgency routing (CONFIRMED / MIXED / PROJECTED pill logic expansion)
- Cross-engine player identity sharing (read-only context bus — player identity only, not filter state)
- Full game-command module (Phase 2B final implementation)

### Prerequisites

- Phase 6 stable
- Cross-engine event bus design reviewed and doctrine-compliant (see `remaining_blocked_systems_registry.md` item 6)
- MAIN/JIG session_state key namespaces formally documented by Codex
- Isolation test confirming zero MAIN→JIG filter propagation

### Validation Gates

- MAIN TCC filter change: zero propagation to JIG TCC state
- JIG HVY refresh: zero effect on MAIN display_pool or _tac_ranked
- Cross-engine player identity: read-only from bus, not written back to owning engine
- Full Slate renders all 3 modes correctly with advanced orchestration active
- Parent orchestrator ownership unchanged

### Rollback Expectations

Cross-engine bus is isolated in its own module. Rollback by disabling bus import. Both engines revert to standalone operation.

---

## Phase 8 — Advanced Deployment Tooling

**Risk Level:** MEDIUM  
**Owner:** Codex (implementation) / Claude (doctrine)

### Scope

Operational tooling improvements that support the daily deployment workflow without modifying the prediction engine.

### Eligible Work

- Windows Task Scheduler automation for `ops_daily.py` (8AM daily)
- Player detail modal rewrite (per `spec_modal_governance_v1.md`)
- CLV capture automation integration into app.py
- Advanced performance monitoring (Phase 3 dashboard expansion)
- Portfolio optimizer threshold re-evaluation (post-n≥200 settled optimized picks)

### Prerequisites

- Phase 5 stable (modal rewrite requires restoration stack)
- n≥200 settled optimized picks for portfolio optimizer threshold work
- CLV data pipeline operational (n≥50 CLV entries)

### Validation Gates

- `ops_daily.py` Task Scheduler run confirmed via `reports/daily_YYYY-MM-DD.txt`
- Modal rewrite: open/close does not affect active player in MAIN or JIG
- CLV capture: line_snapshots.csv updated with correct timestamps; clv_log.csv updated
- All atomic write paths confirmed after tooling changes

### Rollback Expectations

Each tool is independent. Scheduler task deleted from Task Scheduler. Modal reverted via `app.py` edit. No pipeline impact.

---

## Phase 9 — Historical Intelligence Systems

**Risk Level:** MEDIUM-HIGH  
**Owner:** Claude (design) / Codex (implementation)

### Scope

Systems that learn from accumulated pick history and produce structured intelligence. Not prediction model changes — analysis and surfacing layers only.

### Eligible Work

- Historical intelligence archive (`spec_historical_intelligence_archive_v1.md`)
- Automated calibration drift alerting (beyond current monitoring_dashboard)
- Archetype scoring bonus in `ranker.py` (barrel≥10% + power≥1.15 picks) — pending n≥200 settled confirmation
- Pitcher signal coefficient reduction automation (rank #17/21 validation)
- Seasonal mid-point model constant refresh workflow (config.py league constants)

### Prerequisites

- Phase 8 stable
- n≥500 real settled picks in pick_tracker.csv
- n≥100 CLV entries
- Historical intelligence spec formally approved by engine owner

### Validation Gates

- Historical analysis does not modify model_prob or EV% in real-time
- Archetype scoring bonus: backtest ROI improvement confirmed on held-out data before production
- Calibration drift alert: integration test with synthetic drift data confirms alert fires at correct threshold
- All historical analysis is read-only from pick_tracker.csv; no writes to production data layer

### Rollback Expectations

Analysis layers are read-only. Rollback by removing import. Ranker.py bonus is config-flagged; rollback by disabling flag.

---

## Phase 10 — Future Automation Systems

**Risk Level:** HIGH  
**Owner:** Requires governance authorization (engine owner decision)

### Scope

Systems that operate without per-action operator confirmation. These carry the highest risk and are gated behind explicit governance authorization, not just technical readiness.

### Eligible Work

- Automated escalation engine (see `remaining_blocked_systems_registry.md` item 5)
- Session replay systems (item 7)
- Adaptive orchestration (item 8)
- Advanced persistence migration (item 10)
- Auto-deployment concepts (item 9 — EXTREME risk; requires separate governance session)

### Prerequisites

- All Phases 1–9 stable
- Explicit engine owner authorization for each system
- Separate governance review session for each Phase 10 system
- Auto-deployment: regulatory compliance review (jurisdiction-dependent)

### Validation Gates

- Per system, per governance review
- Auto-deployment: NOT eligible for implementation under current operational model

### Rollback Expectations

Each system must have a documented rollback path before implementation begins. Auto-deployment must have bankroll circuit breaker with hard daily loss cap before any testing.

---

## Sequencing Rules

1. **One phase at a time.** Do not begin Phase N+1 until Phase N is validated stable.
2. **No broad rewrites.** Each phase adds specific, isolated components. No simultaneous architecture changes.
3. **Rollback before expand.** Confirm rollback path before starting any phase.
4. **Validation before claiming stability.** Runtime evidence required — not visual assumptions.
5. **Parent orchestration is untouchable.** No phase modifies active_workspace ownership or MAIN/JIG engine separation without explicit doctrine authorization.
6. **Documentation precedes implementation.** Any new component that isn't covered by existing spec requires Claude to author the spec before Codex implements.

---

*Created: 2026-05-20 — Step 12 Final Stabilization Closeout*
