# COMPONENT IMPLEMENTATION PRIORITY
**Owner:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 3/12

Ranks all major UI components for Codex implementation ordering. Goal: prevent broad rewrites, unsafe dependency sequencing, and visual fragmentation.

---

## PRIORITY RANKING

### RANK 1 — Threat Score Badge

**Implementation Complexity:** LOW  
**Tactical Importance:** CRITICAL — appears on every card, every tier  
**Runtime Risk:** LOW — pure render, no session state  
**Reuse Value:** MAXIMUM — shared by player card, game container, sidebar  
**Dependency Chain:** None — no component depends on it arriving late  
**Codex Suitability:** IDEAL — isolated, stateless, pure visual  
**Isolation Strategy:** Single shared component file. No conditional logic inside badge. Caller passes tier string, badge renders color + label. Zero routing coupling.

**Why first:** Every other component depends on threat badge being stable. Build it wrong here and every downstream component inherits the defect.

---

### RANK 2 — Player Threat Card

**Implementation Complexity:** MEDIUM  
**Tactical Importance:** CRITICAL — primary information surface  
**Runtime Risk:** MEDIUM — receives live data props, must handle missing values gracefully  
**Reuse Value:** HIGH — same card used in game containers and standalone views  
**Dependency Chain:** Requires Rank 1 (threat badge) to be complete  
**Codex Suitability:** HIGH — isolatable, pure render architecture achievable  
**Isolation Strategy:** Card receives all data as props. No internal API calls. No session_state reads. No modal ownership. Parent passes player object; card renders. See `spec_player_threat_card_v1.md`.

**Why second:** Foundation of all game page and slate page views. Must stabilize before game container shell is built around it.

---

### RANK 3 — Game Container Shell

**Implementation Complexity:** MEDIUM  
**Tactical Importance:** HIGH — structural wrapper for all player cards per game  
**Runtime Risk:** LOW — mostly layout, minor conditional rendering  
**Reuse Value:** HIGH — used on games page and full slate shell  
**Dependency Chain:** Requires Rank 2 (player threat card) complete  
**Codex Suitability:** HIGH — layout component, low runtime entanglement  
**Isolation Strategy:** Container receives game object (teams, time, status, player list). Renders game header + iterated player cards. No internal data fetching. No route awareness.

**Why third:** Can't build game page without stable card and container. Container must not be built before card is locked or it will need immediate revision.

---

### RANK 4 — Escalation Badge System

**Implementation Complexity:** MEDIUM-HIGH  
**Tactical Importance:** CRITICAL — governs visual escalation language across entire app  
**Runtime Risk:** MEDIUM — must stay synchronized with live threat tier changes  
**Reuse Value:** MAXIMUM — touches every escalation surface  
**Dependency Chain:** Rank 1 (badge) is prerequisite. Rank 4 extends Rank 1 into a full system  
**Codex Suitability:** MEDIUM — complexity in tier logic, but still isolatable  
**Isolation Strategy:** Centralized tier → style mapping. Single source of truth for all badge/glow/border assignments. No component implements its own escalation logic — all delegate to this system.

**Why fourth:** Without centralized escalation system, each component invents its own tier logic. Results in fragmentation and visual inconsistency. Must be codified before sidebar and feed are built.

---

### RANK 5 — Right Operational Sidebar

**Implementation Complexity:** MEDIUM  
**Tactical Importance:** HIGH — command center operational context  
**Runtime Risk:** MEDIUM — likely receives live updates, must handle streaming gracefully  
**Reuse Value:** MEDIUM — appears on most pages but not a shared sub-component  
**Dependency Chain:** Requires Rank 4 (escalation badge system) and intelligence feed entry format  
**Codex Suitability:** MEDIUM — layout is simple, content sourcing adds complexity  
**Isolation Strategy:** Sidebar receives pre-fetched intel list as prop. No internal data fetching. No modal triggers. Renders priority-sorted intel entries using shared entry format.

**Why fifth:** Sidebar is secondary to core card/container hierarchy. Can be stubbed initially with static content, stabilized after primary surfaces are locked.

---

### RANK 6 — Pitch Mix Matchup Table

**Implementation Complexity:** MEDIUM  
**Tactical Importance:** MEDIUM — required for Head to Head page  
**Runtime Risk:** LOW — static display of pre-fetched pitch data  
**Reuse Value:** MEDIUM — specific to head-to-head context  
**Dependency Chain:** Requires batter card and pitcher card components (Rank 2 + prerequisite pitcher card)  
**Codex Suitability:** HIGH — pure table render, no escalation logic  
**Isolation Strategy:** Receives pitch mix array as prop. Renders rows. No session ownership. No modal coupling.

**Why sixth:** Not day-one critical. Head to Head page is secondary to games page in operator workflow.

---

### RANK 7 — Live Intelligence Feed

**Implementation Complexity:** HIGH  
**Tactical Importance:** HIGH — real-time operational awareness  
**Runtime Risk:** HIGH — streaming data, update frequency, stale state risk  
**Reuse Value:** MEDIUM — appears in sidebar and potentially on strategy page  
**Dependency Chain:** Requires Rank 4 (escalation system) and Rank 5 (sidebar) structural context  
**Codex Suitability:** MEDIUM — runtime risk is the limiting factor  
**Isolation Strategy:** Feed receives pre-processed intel entries. Does not own data fetching. Renders entry list with priority ordering. If streaming required, parent owns subscription, passes updates as props.

**Why seventh:** High runtime risk means it should not be built until surrounding structure is stable. Streaming bugs in an early component contaminate everything.

---

### RANK 8 — Deployment Card

**Implementation Complexity:** MEDIUM  
**Tactical Importance:** MEDIUM — operator action surface  
**Runtime Risk:** MEDIUM — involves bet/pick recording, must not corrupt session state  
**Reuse Value:** LOW — specific to deployment workflow  
**Dependency Chain:** Requires player threat card (Rank 2) and escalation system (Rank 4)  
**Codex Suitability:** MEDIUM — action component, needs careful state isolation  
**Isolation Strategy:** Deployment card is read-only display. Action callbacks passed from parent. No internal state mutation. No direct session_state writes.

**Why eighth:** Action components carry higher risk. Build last within the card family after display-only components are stable.

---

### RANK 9 — Modal Escalation Overlays

**Implementation Complexity:** HIGH  
**Tactical Importance:** MEDIUM — contextual detail surface  
**Runtime Risk:** HIGH — modal state is a common source of rerun contamination  
**Reuse Value:** LOW — each modal is context-specific  
**Dependency Chain:** Requires all underlying card components complete  
**Codex Suitability:** LOW — modal state management in Streamlit is highest-risk category  
**Isolation Strategy:** Modal state owned exclusively by top-level page component. Cards never own or trigger modal state directly. Cards emit events; parent decides whether to open modal.

**Why ninth:** Modals are highest runtime risk in Streamlit. Defer until all surface components are stable. Build last.

---

### RANK 10 — Full Slate Battlefield Shell

**Implementation Complexity:** VERY HIGH  
**Tactical Importance:** CRITICAL — primary daily operator view  
**Runtime Risk:** HIGH — aggregates all components, must handle full data load  
**Reuse Value:** N/A — top-level page shell  
**Dependency Chain:** Requires ALL lower-ranked components complete  
**Codex Suitability:** LOW for full implementation, HIGH for shell scaffolding  
**Isolation Strategy:** Shell is assembly point only. No business logic. Receives pre-processed slate data. Orchestrates game containers, sidebar, and header. Can be scaffolded early with stub components, but full implementation is last.

**Why tenth:** Cannot be fully built until every component it contains is locked. Scaffolding can begin at Rank 5-6 phase using stubs.

---

## IMPLEMENTATION ORDERING SUMMARY

```
Rank 1:  Threat Score Badge          → CODEX READY (no dependencies)
Rank 2:  Player Threat Card          → CODEX READY after Rank 1
Rank 3:  Game Container Shell        → Start after Rank 2 locked
Rank 4:  Escalation Badge System     → Start after Rank 1, before Rank 5
Rank 5:  Right Operational Sidebar   → Start after Rank 4
Rank 6:  Pitch Mix Table             → Parallel track after Rank 2
Rank 7:  Live Intelligence Feed      → Start after Rank 5
Rank 8:  Deployment Card             → Start after Rank 4
Rank 9:  Modal Escalation Overlays   → Start after Rank 8
Rank 10: Full Slate Battlefield Shell → Final integration
```

---

## UNSAFE SEQUENCING WARNINGS

**Do not build Rank 10 before Rank 4.** Full slate shell without centralized escalation = every game container invents its own badge logic.

**Do not build Rank 9 before Rank 8.** Modal state before action components are stable = rerun contamination risk.

**Do not build Rank 7 before Rank 5.** Live feed without sidebar structure = layout thrash on integration.

**Do not build Rank 3 before Rank 2 is locked.** Game container wrapping an unstable card = immediate forced revision.

---

## CURRENT GATE STATUS

| Component | Spec Exists | Reference Approved | Codex Unblocked |
|-----------|-------------|-------------------|-----------------|
| Threat Score Badge | Partial (in card spec) | YES | YES — pending full badge spec |
| Player Threat Card | YES (v1 in progress) | YES | YES — pending spec completion |
| Game Container Shell | NO | YES | NO |
| Escalation Badge System | NO | YES | NO |
| Right Operational Sidebar | NO | CONDITIONAL | NO |
| Pitch Mix Table | NO | YES | NO |
| Live Intelligence Feed | NO | CONDITIONAL | NO |
| Deployment Card | NO | NO | NO |
| Modal Overlays | NO | NO | NO |
| Full Slate Shell | NO | YES | NO |
