# Remaining Blocked Systems Registry
## MLB HR Engine — Master Stabilization

**Date:** 2026-05-20  
**Step:** 12 of 12  
**Owner:** Claude (doctrine)  
**Version:** Post-Step-12 Stabilization Baseline

---

## Purpose

Tracks all systems that are specified or partially developed but remain blocked pending validation, Codex session_state decisions, or dependency resolution. Each entry defines why it is blocked, the risk level, the dependency chain, and the required validation before unlock.

---

## Registry

---

### 1. Scroll Restoration Execution

**Spec:** `docs/spec_scroll_restoration_and_focus_v1.md`

**Why Blocked:**  
Doctrine fully specified in Step 10. Implementation requires DOM-settle timing mechanism that Codex must confirm. Also requires Codex to define session_state key ownership for the restoration stack write (push/pop) before scroll anchor capture and restoration can be wired safely. Claude has defined the scroll rules, anchor capture events, and restoration decision matrix — but implementation execution is Codex-owned.

**Risk Level:** MEDIUM  
Scroll restoration failure degrades operator experience but does not corrupt data or picks. Current fallback (scroll to page top) is acceptable for continued operation.

**Dependency Chain:**
1. Codex defines session_state key ownership for restoration stack
2. Codex confirms DOM-settle timing mechanism (post-rerender hook or JS callback)
3. Restoration stack write (push/pop) implemented and stable
4. Pre-expansion anchor capture validated in isolation
5. Full Slate expansion event hook confirmed by Codex

**Required Validation Before Unlock:**
- Restoration stack push/pop tested at max depth (10 entries)
- Fast-return scenario (< 5 min): engine + game + player + JIG state + scroll all restored
- Full Slate collapse restores pre-expansion game row to exact viewport position
- Scroll loop prevention tested: 500ms lock confirmed, no infinite restoration loop
- Mobile viewport: GAME_ROW anchor (not pixel-perfect) confirmed at 375px

**Ownership Boundaries:**  
Implementation: Codex. Doctrine compliance validation: Claude. Parent orchestration: Codex (must not alter active_workspace).

---

### 2. Escalation Snapshot Trigger

**Spec:** `docs/spec_interruption_recovery_v1.md`, `docs/escalation_jump_doctrine.md`

**Why Blocked:**  
Doctrine specifies that a context snapshot must be pushed to the restoration stack before any CRITICAL escalation loads. The escalation fire event is a Codex-owned runtime event. Claude cannot wire a snapshot trigger into the escalation system without risk of interfering with the session_state routing owned by Codex.

**Risk Level:** MEDIUM  
Without snapshot trigger, restoration prompt after escalation resolution cannot offer full context restoration. Operator must manually navigate back to prior game/player. Escalation itself still fires correctly — only the recovery path is degraded.

**Dependency Chain:**
1. Restoration stack write (push/pop) implemented and stable (unblocks item 1 above first)
2. Codex exposes escalation fire event as a hook point
3. Snapshot schema finalized (covered in Step 10 doctrine)
4. Codex confirms that snapshot push does not interfere with escalation state machine

**Required Validation Before Unlock:**
- CRITICAL escalation resolves → restoration prompt offered → context restored correctly
- Stack pre-snapshot and post-escalation contents confirmed via debug output
- Tray-only display confirmed: escalation does not replace main engine view
- Snapshot TTL (ESCALATION = 90 min) tested at expiry boundary

**Ownership Boundaries:**  
Escalation fire event: Codex. Snapshot schema and doctrine: Claude. Restoration UX: shared.

---

### 3. Mobile Drawer System

**Spec:** `docs/spec_responsive_tactical_layout_v1.md`

**Why Blocked:**  
Streamlit's native layout system does not support true mobile drawer/offcanvas components. The responsive layout spec was written with a future Streamlit custom component or a separate mobile-targeted rendering path in mind. Implementing a drawer requires either a third-party Streamlit component or custom HTML/JavaScript injection, both of which carry session_state interaction risk.

**Risk Level:** LOW  
Current mobile rendering is functional at ≤ 768px but lacks drawer navigation. Operators can use desktop or landscape mode as workaround. No pick or data corruption risk.

**Dependency Chain:**
1. Decision: custom Streamlit component vs HTML injection approach
2. Component isolation: drawer must not interact with main session_state keys
3. Responsive breakpoint strategy confirmed for Streamlit rendering model
4. Mobile-specific lazy load gates validated (pitch mix, JIG Power Profiles)

**Required Validation Before Unlock:**
- Drawer opens/closes without triggering full-page rerender
- Drawer does not alter any session_state key outside its own namespace (`_drawer_*`)
- All card types render legibly at 375px inside drawer
- GAME_ROW scroll anchor behavior confirmed on drawer close

**Ownership Boundaries:**  
Component implementation: Codex. Mobile doctrine compliance: Claude. Session_state isolation: Codex.

---

### 4. Player Detail Modal Rewrite

**Spec:** `docs/spec_modal_governance_v1.md`

**Why Blocked:**  
Current modal behavior (via `log_picks_bulk`, expander-based detail view) is functional. Full modal rewrite requires new session_state keys for modal open/close state, player identity pinning, and modal-scoped content. Premature before scroll restoration and restoration stack are stable, since modal open/close are restoration stack push events.

**Risk Level:** LOW  
Existing detail view is functional. Rewrite would improve UX density but carries session_state interaction risk if implemented before restoration stack is stable.

**Dependency Chain:**
1. Restoration stack write stable (items 1–2 above)
2. Modal session_state namespace defined by Codex
3. Modal open = restoration stack push
4. Modal content rendering isolated from MAIN TCC filter state

**Required Validation Before Unlock:**
- Modal open/close does not affect active player in MAIN or JIG
- Modal renders full Statcast profile, odds strip, CLV, and arsenal data correctly
- Closing modal restores viewport to triggering card (not page top)
- Modal does not interfere with lazy gate keys or card HTML cache

**Ownership Boundaries:**  
Modal session_state keys: Codex. Content specifications: Claude. Visual compliance: shared.

---

### 5. Automated Escalation Engine

**Spec:** `docs/escalation_vs_suppression_doctrine.md`, `docs/escalation_jump_doctrine.md`, `docs/deployment_command_center_doctrine.md`

**Why Blocked:**  
Doctrine defines when escalations should fire (STEAM alerts, lineup changes, pitcher changes, HVY modifier spike). Automated detection requires polling or event subscription against live data sources. Streamlit's stateless execution model makes persistent polling difficult without a background thread or external scheduler. Background thread introduces session_state race conditions.

**Risk Level:** HIGH  
Automated escalation engine that writes to session_state from a background thread risks corrupting operator filter state, active player selection, or deployment queue. Must be implemented as a Codex-isolated component with strict write-boundary enforcement.

**Dependency Chain:**
1. Escalation snapshot trigger stable (item 2 above)
2. Codex defines threading model or external scheduler approach (no background thread in Streamlit)
3. Escalation event schema finalized (CRITICAL / URGENT / ADVISORY / AMBIENT)
4. Escalation does NOT write to active_workspace, TCC state, or deployment queue

**Required Validation Before Unlock:**
- Automated escalation fires without corrupting active filter state
- Escalation level hierarchy respected (Level 4 never surfaces as Level 1)
- No escalation triggers full-page reroute
- Rate limit on escalation fire events confirmed (no escalation flood)
- Escalation tray clears correctly after dismiss

**Ownership Boundaries:**  
Event detection timing: Codex. Escalation hierarchy doctrine: Claude. Session_state write isolation: Codex.

---

### 6. Cross-Engine Event Bus

**Spec:** `docs/cross_engine_command_surface_doctrine.md`

**Why Blocked:**  
MAIN and JIG maintain strict operational independence. An event bus that synchronizes context between engines risks collapsing that independence, introducing pick contamination (MAIN filter state leaking into JIG universe, or vice versa). Until a safe event bus architecture is proven in isolation, the two-engine separation must be preserved.

**Risk Level:** HIGH  
Cross-engine state contamination would be silent and difficult to detect — picks from the wrong universe could appear in either engine without visible indication. This is the highest-risk architectural addition in the blocked registry.

**Dependency Chain:**
1. MAIN/JIG session_state key namespaces formally documented by Codex
2. Event bus limited to read-only context sharing (player identity, game context) — not filter state
3. Isolation test: confirm no MAIN filter key propagates to JIG and vice versa
4. Event bus does not trigger rerenders in both engines simultaneously

**Required Validation Before Unlock:**
- MAIN TCC filter change: confirmed zero propagation to JIG TCC state
- JIG HVY refresh: confirmed zero effect on MAIN display_pool or _tac_ranked
- Shared context (player identity): read-only from bus, confirmed not written back to owning engine
- Dual-rerender test: event bus event does not cause both engines to rerender simultaneously

**Ownership Boundaries:**  
Event bus architecture: Codex. Engine identity preservation doctrine: Claude. Isolation validation: shared.

---

### 7. Session Replay Systems

**Spec:** Referenced in operator memory doctrine; not yet formally specified.

**Why Blocked:**  
Not yet formally specified beyond references in operational attention pacing doctrine. Session replay requires persistent logging of operator actions and navigation events — a significant new data layer. Storage, privacy, and performance implications not yet analyzed.

**Risk Level:** LOW (at current stage)  
Session replay is an enhancement. No operational dependency.

**Dependency Chain:**
1. Formal spec document required (no spec exists)
2. Storage strategy defined (CSV? SQLite? External?)
3. Privacy boundary analysis (pick data in replay must not expose API keys or user credentials)
4. Performance impact of action logging assessed (per-action write overhead)

**Required Validation Before Unlock:**
- Spec document created and reviewed
- Storage strategy confirmed with rollback path
- Privacy audit complete
- Replay playback confirmed correct for navigation, filter, and escalation events

**Ownership Boundaries:**  
Spec authorship: Claude. Implementation: Codex.

---

### 8. Adaptive Orchestration Systems

**Spec:** `docs/full_slate_parent_orchestrator_doctrine.md` (partial)

**Why Blocked:**  
Adaptive orchestration — dynamically adjusting display pool size, filter thresholds, or engine priority based on slate size, game urgency, or live conditions — risks undermining the stable parent orchestrator architecture established in Step 12. The parent orchestrator doctrine requires static ownership boundaries. Adaptive changes to those boundaries must be proven in strict isolation before introduction.

**Risk Level:** HIGH  
Adaptive orchestration that modifies filter thresholds at runtime could cause pick list instability (picks appearing and disappearing mid-session) and undermine operator trust in the engine's consistency.

**Dependency Chain:**
1. Parent orchestrator boundaries formally locked (this step)
2. Adaptive rules defined as read-only signals (e.g., slate_status indicator already exists)
3. Adaptive adjustments limited to display hints (badges, urgency signals) — not filter mutations
4. No adaptive system modifies _tac_ranked, display_pool, or session_state filter keys

**Required Validation Before Unlock:**
- Adaptive signal does not alter filter state or pick list
- Adaptive display hints (urgency, confirmation%) tested across full slate conditions
- Parent orchestrator ownership boundaries verified intact after adaptive layer active

**Ownership Boundaries:**  
Adaptive doctrine: Claude. Implementation: Codex. Parent orchestrator: Codex (must not be modified).

---

### 9. Auto-Deployment Concepts

**Spec:** `docs/deployment_command_center_doctrine.md` (reference only)

**Why Blocked:**  
Auto-deployment (automatically placing picks without operator confirmation) is outside the current operational model. All deployment is operator-confirmed. Auto-deployment would require sportsbook API integration (no current integration), regulatory compliance review, and bankroll safety circuit breakers not yet implemented.

**Risk Level:** EXTREME  
Auto-deployment without operator confirmation creates financial exposure. This system must not be unblocked without explicit operator authorization, sportsbook API integration, bankroll circuit breakers, and regulatory review.

**Dependency Chain:**
1. Sportsbook API integration (not planned)
2. Regulatory compliance review (jurisdiction-dependent)
3. Bankroll circuit breaker (max loss per session, per day, per week)
4. Operator explicit opt-in per session
5. Full audit log of all automated deployments

**Required Validation Before Unlock:**
- This system requires explicit governance authorization from the engine owner
- Not a standard implementation task — requires a separate governance review session

**Ownership Boundaries:**  
Governance authorization: engine owner. If ever implemented, implementation: Codex with Claude doctrine oversight.

---

### 10. Advanced Persistence Systems

**Spec:** Beyond atomic CSV writes; not yet formally specified.

**Why Blocked:**  
Current persistence (atomic CSV writes for pick_tracker, pnl, line_snapshots) is operational and safe. Advanced persistence (SQLite, Supabase, real-time sync) adds infrastructure complexity and introduces new failure modes. Current atomic CSV approach is rollback-safe and auditable. Advanced persistence should not be introduced during stabilization.

**Risk Level:** MEDIUM  
Migration from CSV to a database layer carries data loss risk if migration fails mid-flight. Must be implemented with full migration validation and CSV fallback retained.

**Dependency Chain:**
1. Pick tracker n≥1000 (CSV performance at scale validated first)
2. Database schema designed to match current CSV schema exactly
3. Migration script tested with full backup/restore cycle
4. CSV fallback retained as emergency rollback
5. Atomic write guarantees verified in new persistence layer

**Required Validation Before Unlock:**
- Migration round-trip: CSV → database → CSV produces identical rows
- Concurrent write test: two sessions writing simultaneously without corruption
- Rollback test: database failure falls back to CSV without data loss
- Performance test: 10,000-row pick_tracker query < 100ms

**Ownership Boundaries:**  
Migration strategy: Claude. Implementation: Codex. Data integrity verification: shared.

---

## Registry Summary

| # | System | Risk | Blocked By |
|---|---|---|---|
| 1 | Scroll Restoration Execution | MEDIUM | Codex session_state ownership, DOM timing |
| 2 | Escalation Snapshot Trigger | MEDIUM | Item 1; Codex escalation event hook |
| 3 | Mobile Drawer System | LOW | Streamlit component gap |
| 4 | Player Detail Modal Rewrite | LOW | Items 1–2 first |
| 5 | Automated Escalation Engine | HIGH | Threading model; session_state race risk |
| 6 | Cross-Engine Event Bus | HIGH | MAIN/JIG namespace isolation not yet formal |
| 7 | Session Replay Systems | LOW | No spec exists |
| 8 | Adaptive Orchestration | HIGH | Parent orchestrator boundaries must lock first |
| 9 | Auto-Deployment Concepts | EXTREME | Requires governance authorization |
| 10 | Advanced Persistence | MEDIUM | CSV at scale must be validated first |

---

*Created: 2026-05-20 — Step 12 Final Stabilization Closeout*
