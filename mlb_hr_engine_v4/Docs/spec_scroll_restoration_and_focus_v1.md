# Scroll Restoration and Focus Specification v1
## MLB HR Engine — Operator Experience Doctrine

**Status:** ACTIVE  
**Step:** 10/12  
**Owner:** Claude (scroll/focus doctrine)  
**Runtime Owner:** Codex (implementation)

---

## 1. Purpose

Scroll restoration and focus management govern where the operator's viewport is positioned after navigation events, data updates, and context switches. Poor scroll behavior is one of the most disorienting UX failures — it makes a working app feel broken and breaks investigation flow.

---

## 2. Core Scroll Doctrine

### 2.1 Guiding Principle

**Scroll position is operator-owned.** The platform does not move the viewport unless the operator explicitly navigated to a new context that requires repositioning.

Data refreshes, trust-state updates, and filter changes do not move the scroll position.

### 2.2 Scroll Anchor Types

| Anchor Type | Description |
|---|---|
| `PLAYER_CARD` | Position at specific player card element |
| `GAME_ROW` | Position at top of game row |
| `FULL_SLATE_ENTRY` | Position at specific entry within Full Slate |
| `JIG_SECTION` | Position at top of JIG section/tab |
| `ENGINE_TOP` | Scroll to top of engine view |
| `PRESERVED` | No scroll change — maintain current position |

---

## 3. Scroll Restoration Rules

### 3.1 When to Restore Scroll

| Event | Scroll Behavior |
|---|---|
| JIG close → return to player card | Restore to `PLAYER_CARD` anchor |
| Full Slate collapse → return to row | Restore to `GAME_ROW` anchor (pre-expansion position) |
| Escalation dismiss → return to investigation | Restore to `PLAYER_CARD` anchor from snapshot |
| Deployment cancel → return to investigation | Restore to `PLAYER_CARD` anchor |
| Shortlist entry click (fast-return) | Restore to `PLAYER_CARD` anchor from parked snapshot |
| Breadcrumb navigation | Restore to anchor saved in breadcrumb |
| Engine tab switch → return to prior tab | Restore to `PRESERVED` (maintain prior position) |
| Data refresh (any) | `PRESERVED` — do not touch scroll |
| Filter change (same engine) | `PRESERVED` — do not scroll |
| Trust-state update | `PRESERVED` — do not scroll |

### 3.2 When NOT to Restore Scroll

Scroll restoration is **explicitly disabled** in these scenarios:

| Scenario | Reason |
|---|---|
| Stale return (> 45 min) | Anchor element may not exist; disorienting jump |
| Cross-session return | No scroll state persisted |
| Engine home navigation (explicit) | Operator intentionally navigated to top |
| After game slate fully changes | Prior anchors reference stale elements |
| After player removed from slate | Anchor element no longer exists |
| Initial page load | Default position is top |
| After hard data failure/recovery | State validity unknown |

---

## 4. Viewport Focus Doctrine

### 4.1 Focus Anchor Behavior

Focus anchors define what element receives visual focus (highlight, ring, etc.) after context restoration. Focus anchors are distinct from scroll anchors — scroll positions the viewport, focus indicates the active element.

| Context | Focus Anchor |
|---|---|
| Player card restored | Focus ring on player card |
| Game row restored (no player) | Focus ring on game row header |
| JIG restored | Focus on JIG section header |
| Full Slate restored | Focus on first visible entry |
| Engine home | No focus ring (ambient state) |

### 4.2 Focus Stability Rules

- Focus must not jump to a different element than the operator was last interacting with
- Focus must not fire visual animations on restoration (rings appear, not animate-in)
- Focus must clear after 3 seconds of operator inactivity (ambient mode)
- Keyboard focus (accessibility) follows the same rules as visual focus anchors

---

## 5. Full Slate Return Positioning

Full Slate expansion changes the visual height of the list significantly. Return positioning after Full Slate interaction must be precise.

### 5.1 Pre-Expansion Anchor

Before Full Slate expands, the platform captures:
- `scroll_offset_before_expansion`: pixel position of the game row top edge in the viewport
- `game_row_id`: the row that triggered expansion

### 5.2 On Full Slate Collapse

On collapse, restore scroll so the **game row top edge** is at the same viewport position it was pre-expansion. Not scroll-to-top. Not scroll-to-row-in-list. Exact pre-expansion viewport position.

### 5.3 On Multiple Full Slate Expansions

If multiple rows are expanded and one is collapsed:
- Restore only that row's pre-expansion anchor
- Other expanded rows remain at their current positions
- No global scroll reset

---

## 6. Mobile Scroll Philosophy

Mobile viewports have significantly less visible area. Mobile scroll doctrine:

### 6.1 Mobile-Specific Rules

- Scroll restoration on mobile uses `GAME_ROW` anchors preferentially over `PLAYER_CARD` anchors (larger touch targets)
- Full Slate scroll restoration on mobile scrolls the expanded row to top of viewport (not to pre-expansion pixel position — too small to be meaningful)
- JIG on mobile is full-screen overlay; close returns to viewport top of the triggering game row
- Shortlist on mobile: clicking parked entry scrolls to `GAME_ROW` anchor (player card may require additional scroll)

### 6.2 Mobile Anti-Patterns

| Anti-Pattern | Why Rejected |
|---|---|
| Pixel-perfect scroll restoration on mobile | Viewport is 1/3 size; "exact" position means nothing |
| Restoring Full Slate to mid-expansion position | Player cards may be off-screen on return |
| Focus rings on mobile | Touch devices do not use focus rings |

---

## 7. Expansion-State Restoration

Expansion state refers to which Full Slate rows are open, which sidebar sections are expanded, and which JIG tabs are open.

### 7.1 Restoration Table

| State | Restored? | Condition |
|---|---|---|
| Full Slate rows expanded | YES | Same game context |
| Sidebar sections expanded | YES | Always (sidebar state persists) |
| JIG active tab | YES | Fast-return only |
| Player card collapsed/expanded | YES | Same game context |
| Tray expanded | YES | Always |

### 7.2 Expansion Mismatch Prevention

Expansion mismatch occurs when restored expansion state references elements that don't match current data (e.g., Full Slate entries have changed).

Prevention: validate each expanded element's ID against current data before restoring expansion. Invalid elements default to collapsed.

---

## 8. Scroll-Loop and Rerender Prevention

Scroll-loop: restoration triggers a rerender that triggers another scroll event that triggers another restoration.

### 8.1 Prevention Rules

- Scroll restoration is a **one-shot operation** per navigation event
- After restoration fires, scroll restoration lock is set for 500ms
- Data refreshes within the 500ms lock do not trigger additional scroll events
- Scroll restoration does not react to Streamlit rerun events — only to explicit navigation events

### 8.2 Rerender Safety

- Scroll anchor is captured before rerender
- Restoration fires after DOM settle (Codex determines mechanism)
- Restoration does not retry on failure — if anchor is not found, fallback to `ENGINE_TOP`

---

*This spec is documentation-only. Runtime implementation owned by Codex.*
