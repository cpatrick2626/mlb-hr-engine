# Navigation Continuity Specification v1
## MLB HR Engine — Operator Experience Doctrine

**Status:** ACTIVE  
**Step:** 10/12  
**Owner:** Claude (navigation doctrine)  
**Runtime Owner:** Codex (implementation)

---

## 1. Purpose

Navigation continuity governs how the platform preserves operator context across all transitions — engine switches, escalation jumps, deployment actions, and route changes. Operators must never feel reset, lost, or disoriented after any navigation event.

The platform behaves as a **persistent tactical workspace**, not a multi-page web app.

---

## 2. Navigation Hierarchy

```
SHELL (persistent frame)
  └── MAIN ENGINE
        ├── Game Row (active selection)
        │     └── Player Cards (investigation targets)
        │           └── JIG (deep-dive context)
        │                 └── Full Slate (expansion state)
        └── Deployment Queue (parallel context)
```

Navigation within this hierarchy is **additive**, not destructive. Descending into JIG does not discard game context. Ascending from Full Slate does not discard player selection.

---

## 3. Breadcrumb Doctrine

### 3.1 Breadcrumb Requirements

Every navigation state must emit a breadcrumb. Breadcrumbs are:

- **Implicit** — generated automatically on route change
- **Minimal** — capture only: `engine`, `game_id`, `player_id`, `view_state`, `scroll_anchor`
- **Ordered** — LIFO stack, max depth = 10
- **Typed** — tagged as INVESTIGATION, ESCALATION, DEPLOYMENT, or BROWSE

### 3.2 Breadcrumb Display

Breadcrumbs surface in the tray header as a path indicator:
```
MAIN > ATL @ NYM > Acuña Jr. > JIG
```

Operators can click any crumb to return to that context without losing deeper context items in the stack (stack is not truncated on manual return — insertion point is updated).

### 3.3 What Breadcrumbs Do NOT Track

- Sidebar open/close state (restored via sidebar doctrine)
- Filter transient state (not persisted across engines)
- Hover/tooltip state (ephemeral, never tracked)
- Empty investigations (no player selected = no crumb)

---

## 4. Route Persistence Philosophy

### 4.1 Core Contract

**A navigation event does not destroy prior context unless the operator explicitly clears it.**

Implicit navigations (escalation pop-in, data refresh, trust-state update) must never:
- Change active engine
- Change active game selection
- Change active player selection
- Collapse expanded Full Slate entries

Explicit navigations (operator clicks a route) do change context but preserve prior context in the restoration stack.

### 4.2 Route Stability Rules

| Trigger | Route Behavior |
|---|---|
| Escalation fires | Overlay/tray — does not reroute |
| Data source refresh | In-place — no navigation |
| Trust-state degradation | Flag indicator only — no reroute |
| Operator clicks engine tab | Stack push — prior context preserved |
| Operator clicks game row | Game context updated — player cleared if different game |
| Operator clicks player card | Player context updated — game context preserved |
| Operator opens JIG | JIG overlay — no route change |
| Operator closes JIG | Return to prior card position — game preserved |

---

## 5. Engine Transition Continuity

### 5.1 MAIN ↔ JIG

JIG opens as a **contextual overlay** within the active game frame. It does not trigger a route change.

- Opening JIG: snapshots `{game_id, player_id, scroll_position, filter_state}`
- Closing JIG: restores snapshot exactly
- JIG context persists if operator switches to tray and returns
- JIG context expires: on explicit engine navigation or after 45-minute inactivity

### 5.2 MAIN ↔ Full Slate

Full Slate expansion is a **view-state modification**, not a navigation event.

- Expansion state is tracked per game row
- Collapsing Full Slate returns scroll to pre-expansion anchor
- Expanding Full Slate from a collapsed state does not reset player selection
- Multiple Full Slate rows can be expanded simultaneously (no forced collapse)

### 5.3 MAIN → Deployment → Return

Deployment actions trigger a confirmation flow. On confirmation or cancellation:

- Return is **always** to the exact game/player context that triggered deployment
- Deployment queue state is additive — adding a player to queue does not change active investigation
- Deployment conflicts surface as inline flags, not reroutes

---

## 6. Fast-Return Contracts

Fast-return: operator navigates away and returns within **5 minutes**. Full-return: operator navigates away and returns after **5–45 minutes**.

| Return Type | Context Restored |
|---|---|
| Fast-return (< 5 min) | Full: engine, game, player, JIG state, scroll |
| Full-return (5–45 min) | Engine, game, player — scroll at player anchor |
| Stale-return (> 45 min) | Engine only — game/player require reselection |
| Cross-session return | Engine only — prior state discarded |

---

## 7. Investigation Continuity

An **investigation** is defined as: active player selection with at least one JIG interaction or escalation review event recorded.

Investigations are preserved across:
- Tab switches within engine
- Tray open/close events
- Sidebar expand/collapse
- Full Slate expand/collapse
- Non-critical escalation interruptions

Investigations are terminated by:
- Explicit "clear investigation" operator action
- Operator selects different player in different game context
- Session expiry (45 min inactivity)

---

## 8. Deployment Return Behavior

After any deployment action completes, the platform must return the operator to:

1. The **same player card** that was the investigation target
2. The **same game row** that was active
3. The **same Full Slate expansion state** that existed pre-deployment

If the deployed player is no longer available in the slate (removed from consideration), return to the game row with a dismissible "deployed" indicator on the now-absent card position.

---

## 9. Escalation Jump Return Behavior

When an escalation interrupt fires and the operator engages it:

1. Current investigation state is **snapshotted** before escalation context loads
2. Escalation context loads in the **tray layer** (does not replace main engine view)
3. On escalation dismiss or resolution: snapshot is restored exactly
4. If operator navigated during escalation handling: restoration prompt offered ("Return to prior investigation?")

---

## 10. Tab and Game Persistence

- Active game selection persists across tab switches within same engine session
- Active player persists if same game is active on return
- Tab state (which engine tab is active) is the top-level navigation anchor
- Switching engine tabs does NOT clear the prior tab's investigation — it is preserved in the restoration stack

---

## 11. Rejected Patterns

The following patterns are explicitly rejected from this platform:

| Pattern | Reason |
|---|---|
| Full reset on engine tab switch | Destroys operator work |
| Route-change on escalation fire | Disorienting; escalations are overlay events |
| Scroll-to-top on any data refresh | Breaks investigation flow |
| Clearing player selection on game data update | Data updates are in-place |
| Forced single-game expansion | Operators manage multiple games simultaneously |
| "Back" behavior that loses forward context | Stack must preserve full depth |

---

*This spec is documentation-only. Runtime implementation owned by Codex.*
