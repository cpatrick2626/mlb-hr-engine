# Interruption Recovery Specification v1
## MLB HR Engine — Operator Experience Doctrine

**Status:** ACTIVE  
**Step:** 10/12  
**Owner:** Claude (interruption doctrine)  
**Runtime Owner:** Codex (implementation)

---

## 1. Purpose

Interruption recovery governs how the platform behaves when external events — escalations, data failures, trust-state changes, or deployment conflicts — interrupt an operator's active investigation. The doctrine ensures interruptions feel **controlled and intentional**, not like the app panicked and threw the operator somewhere new.

---

## 2. Interruption Hierarchy

Interruptions are classified by severity. Higher severity = more aggressive surface behavior.

| Level | Name | Description |
|---|---|---|
| 1 | CRITICAL | Escalation requiring immediate operator action |
| 2 | URGENT | Trust-state degradation mid-review, deployment conflict |
| 3 | ADVISORY | Data source warning, slow refresh, stale data indicator |
| 4 | AMBIENT | Non-blocking status change, minor data update |

### 2.1 Hierarchy Rules

- Level 1 interruptions may surface a modal/overlay — cannot be silently dismissed
- Level 2 interruptions surface as persistent banner/tray indicator — can be temporarily dismissed
- Level 3 interruptions surface as inline flag — auto-dismiss after 30 seconds if not engaged
- Level 4 interruptions are indicator-only — no operator action required

No interruption at any level may:
- Reroute the operator without confirmation
- Clear active player selection
- Destroy investigation context
- Collapse expanded Full Slate entries

---

## 3. CRITICAL Escalation Interruption

### 3.1 Behavior on Fire

When a CRITICAL escalation fires:

1. Investigation context is **immediately snapshotted** to restoration stack
2. Escalation surfaces in the **tray layer** — does not replace main engine view
3. If tray is closed, tray **pulses** with CRITICAL indicator
4. Operator sees: current main view + escalation indicator, not a replaced view

### 3.2 Operator Engagement Flow

If operator clicks escalation:
1. Tray expands to escalation context
2. Main engine view **remains visible** (side-by-side or behind tray, per implementation)
3. Escalation state is displayed in tray
4. Operator can dismiss or act on escalation from tray without losing main view

### 3.3 If Operator Ignores CRITICAL

If operator does not engage within operator-configurable threshold (default: 3 minutes):
- Tray indicator escalates to persistent banner (cannot be dismissed until engaged)
- No further interruption — platform does not force navigate

### 3.4 Post-Escalation Recovery

After escalation is resolved or dismissed:
1. Restoration prompt: "Return to [player] investigation?" (yes/no)
2. YES: pop restoration stack, restore full investigation context
3. NO: remain in current view (escalation tray closed, main view whatever operator left it in)

---

## 4. Trust-State Degradation Mid-Review

Trust-state: the platform's confidence in the underlying data validity for a given player/game.

### 4.1 Degradation During Active Investigation

If trust-state degrades while operator is reviewing a player:

1. Player card displays trust-state indicator (inline flag)
2. JIG displays trust-state warning at top of active section
3. No navigation event occurs
4. Operator can continue reviewing with awareness of degraded state

### 4.2 Degradation Severity

| Trust Delta | Surface Behavior |
|---|---|
| Minor (score drops < 10%) | Subtle inline indicator only |
| Moderate (score drops 10–25%) | JIG warning banner, persistent |
| Severe (score drops > 25%) | JIG warning + main card flag + advisory prompt |
| Invalidation (data source fails) | URGENT-level interruption (Section 5) |

### 4.3 Trust Recovery

If trust-state recovers (data source restored, stale signal resolved):
- Indicators clear automatically
- No navigation required
- JIG state preserved throughout

---

## 5. Deployment Conflicts

A deployment conflict occurs when: another operator (or system) deploys a player that the current operator has in their shortlist or active investigation.

### 5.1 Conflict Handling

1. URGENT-level indicator fires on the conflicted player entry
2. Shortlist entry updates to `DEPLOYED` status
3. If player is currently active in JIG: JIG header shows conflict warning
4. No navigation event

### 5.2 Conflict Resolution Options

Operator sees inline options:
- "Continue investigating" (dismiss conflict indicator, keep investigating)
- "Remove from shortlist" (manual cleanup)
- "Mark as acknowledged" (conflict logged, no further alerts)

### 5.3 Queue Conflict

If player is in operator's deployment queue AND another operator deploys them:
- Queue entry flagged with `CONFLICT`
- Operator must resolve before deployment can proceed
- Conflict resolution does not affect investigation state

---

## 6. Data Source Failures

### 6.1 Failure During Active Session

If a data source fails mid-session:

1. ADVISORY indicator surfaces on affected components
2. If failure is severe (primary data unavailable): URGENT banner
3. Investigation context preserved — operator can continue reviewing cached/last-good data
4. Stale data indicator shows on all affected player cards and JIG sections

### 6.2 Recovery Behavior

On data source recovery:
- Indicators clear automatically
- Stale data is replaced in-place (no viewport change)
- If player data has materially changed since failure: `data_updated_since_review` flag set on shortlist entry
- No navigation event

### 6.3 Total Failure

If all data sources fail:
- Full URGENT banner (cannot be dismissed)
- Platform remains navigable — operators can still review cached data
- No forced navigation or session reset

---

## 7. Rapid Engine Switches

When an operator switches engines rapidly (two engine transitions within 10 seconds):

1. Each transition pushes to restoration stack normally
2. Stack depth limit applies — oldest entries may be pruned
3. No special behavior beyond standard navigation continuity
4. Rapid switching does not trigger recovery prompts

This is treated as intentional operator behavior, not an error state.

---

## 8. Full Slate Context Changes

If Full Slate data changes (new entries appear, entries removed) while operator is reviewing:

| Change Type | Behavior |
|---|---|
| New entry added to Full Slate | Added at bottom; no scroll change |
| Entry removed from Full Slate | Entry fades/removes in place; scroll preserved |
| Active investigation target removed | ADVISORY indicator; player preserved in shortlist |
| Game taken off slate entirely | URGENT indicator; investigation context preserved in shortlist |

If the active investigation target is removed from the slate:
1. Player is automatically parked in shortlist with `data_updated_since_review` flag
2. Advisory prompt: "This player was removed from the active slate."
3. Operator can dismiss and continue reviewing (last-good data shown)

---

## 9. Interruption Persistence

### 9.1 How Long Interruptions Persist

| Level | Persistence |
|---|---|
| CRITICAL | Until operator engages (cannot auto-dismiss) |
| URGENT | Until operator dismisses OR condition resolves |
| ADVISORY | 30-second auto-dismiss OR operator dismisses |
| AMBIENT | Auto-dismiss after indicator timeout (implementation detail) |

### 9.2 Interruption State in Restoration Stack

Interruption state is captured in the restoration stack snapshot at time of push. On restoration:
- Active CRITICAL interruptions re-surface (they cannot be silently resolved)
- URGENT interruptions re-evaluated against current state (may or may not re-surface)
- ADVISORY and AMBIENT interruptions are not restored

---

## 10. Recovery Prompts

Recovery prompts are the operator-facing "what do you want to do?" moments after an interruption is resolved.

### 10.1 Prompt Doctrine

- Prompts are **optional actions**, not required steps
- Prompts appear in a dismissible inline banner — not a blocking modal
- Prompts auto-dismiss after 20 seconds if not engaged
- One prompt at a time — if a new interrupt fires before prompt is dismissed, prompt is replaced

### 10.2 Standard Prompt Templates

| Scenario | Prompt Text |
|---|---|
| Escalation resolved | "Return to [Player] investigation?" [YES] [STAY HERE] |
| Deployment cancelled | "Return to [Player]?" [YES] [STAY HERE] |
| Data source recovered | "Data refreshed. [Player] context may have changed." [DISMISS] |
| Conflict acknowledged | "[Player] deployed. Remove from shortlist?" [YES] [KEEP] |

---

## 11. Tactical Continuity Safeguards

These are the non-negotiable guarantees the interruption recovery system must always uphold:

1. **No context destruction** — no interruption clears investigation state
2. **No forced rerouting** — all navigation during/after interruption is operator-initiated
3. **Escalation in tray** — CRITICAL escalations surface in tray, not as full-screen takeovers
4. **Stack snapshot before interrupt** — context is always saved before interrupt context loads
5. **Restoration prompt after interrupt** — operator is always offered return to prior context
6. **Interruption hierarchy respected** — Level 4 never escalates visually to Level 1 behavior

---

*This spec is documentation-only. Runtime implementation owned by Codex.*
