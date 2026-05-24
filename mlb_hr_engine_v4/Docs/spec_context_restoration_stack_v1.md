# Context Restoration Stack Specification v1
## MLB HR Engine — Operator Experience Doctrine

**Status:** ACTIVE  
**Step:** 10/12  
**Owner:** Claude (restoration doctrine)  
**Runtime Owner:** Codex (session_state implementation)

---

## 1. Purpose

The context restoration stack governs how the platform captures, stores, and restores operator context snapshots. Every navigation event that could interrupt active investigation work must push a restorable snapshot onto this stack.

---

## 2. Stack Structure

### 2.1 Stack Schema

Each stack entry is a **context snapshot** with the following fields:

```
ContextSnapshot {
  id:                   UUID (generated at push time)
  timestamp:            ISO 8601
  type:                 INVESTIGATION | ESCALATION | DEPLOYMENT | BROWSE
  engine:               "MAIN" | "JIG" | "FULL_SLATE"
  
  # Game context
  game_id:              string | null
  game_display:         string | null  (e.g. "ATL @ NYM")
  
  # Player context
  player_id:            string | null
  player_display:       string | null
  
  # View state
  jig_open:             boolean
  jig_section:          string | null  (active JIG tab/section)
  full_slate_expanded:  [game_id, ...]  (list of expanded rows)
  sidebar_open:         boolean
  active_tab:           string
  
  # Scroll context
  scroll_anchor:        string | null  (element ID or semantic anchor)
  scroll_offset:        integer | null  (px from anchor)
  
  # Filter state
  active_filters:       {filter_key: value, ...}
  
  # Escalation state
  escalation_pending:   boolean
  escalation_id:        string | null
  
  # Deployment state
  deployment_queue:     [player_id, ...]
  
  # Expiry
  expires_at:           ISO 8601  (timestamp + TTL based on type)
}
```

### 2.2 Stack Constraints

- **Max depth:** 10 entries
- **Overflow behavior:** Oldest entry dropped (FIFO eviction from bottom of stack)
- **Stack is per-session:** Not persisted across browser reloads or session expiry
- **Stack is per-operator-tab:** Multiple open tabs do not share a stack

---

## 3. Push Rules

A snapshot is pushed onto the stack when:

| Event | Push? | Type |
|---|---|---|
| Operator clicks engine tab | YES | BROWSE |
| Operator opens JIG | YES | INVESTIGATION |
| Escalation fires and operator engages | YES | ESCALATION |
| Operator initiates deployment flow | YES | DEPLOYMENT |
| Operator navigates to different game | YES | BROWSE |
| Data refresh occurs | NO | — |
| Sidebar opens/closes | NO | — |
| Filter applied (no engine change) | NO | — |
| Full Slate expanded/collapsed | NO | — |
| Tray opens/closes | NO | — |

---

## 4. Pop and Restore Rules

### 4.1 Pop Triggers

- Operator explicitly clicks "Back" or breadcrumb crumb
- Escalation dismissed/resolved → auto-pop to pre-escalation snapshot
- Deployment confirmed/cancelled → auto-pop to pre-deployment snapshot
- Restoration prompt accepted → pop to specified entry

### 4.2 Restore Behavior

On pop, restoration must:

1. Restore all fields tagged **ALWAYS** (see Section 5)
2. Evaluate and conditionally restore fields tagged **CONDITIONAL**
3. Discard fields tagged **DISCARD**
4. Validate restored context is still valid (game/player still exist in data)
5. If invalid: restore to nearest valid ancestor in stack

### 4.3 Non-destructive Return

Returning to a mid-stack entry does **not** clear entries above it. The stack insertion point updates, but deeper entries remain available for forward navigation.

---

## 5. Restoration Priority Table

### 5.1 Always Restored

| Field | Reason |
|---|---|
| `engine` | Primary workspace anchor |
| `active_tab` | Tab state is top-level context |
| `game_id` | Core investigation anchor |
| `player_id` | Core investigation target |
| `jig_open` | JIG state is investigation-critical |
| `jig_section` | Operator was mid-review |
| `deployment_queue` | Queue is additive; never auto-cleared |
| `escalation_pending` | Pending escalations must re-surface |

### 5.2 Conditionally Restored

| Field | Condition |
|---|---|
| `full_slate_expanded` | Only if game_id matches restored context |
| `scroll_anchor` | Only if fast-return (< 5 min since snapshot) |
| `scroll_offset` | Only if scroll_anchor restored |
| `active_filters` | Only if same engine; discarded on engine switch |
| `sidebar_open` | Only if fast-return; default-collapsed on stale return |

### 5.3 Intentionally Discarded

| Field | Reason |
|---|---|
| `hover/tooltip state` | Ephemeral; meaningless on restore |
| `modal open state` | Modals require intentional re-open |
| `animation state` | No restore value |
| `transient loading states` | Will re-trigger from data layer |
| `error state` | Data re-fetch determines current validity |
| Filter state across engine switches | Each engine has independent filter context |

---

## 6. Expiration Behavior

| Snapshot Type | TTL |
|---|---|
| INVESTIGATION | 45 minutes from push |
| ESCALATION | 90 minutes from push (escalations have longer operational life) |
| DEPLOYMENT | 30 minutes from push |
| BROWSE | 20 minutes from push |

Expired entries are **silently removed** from the stack. They do not generate errors or prompts. If the stack is empty when operator triggers back navigation, return to default engine home state.

---

## 7. Context Snapshot Doctrine

### 7.1 Snapshot Timing

Snapshots are taken **before** the navigation event executes. The snapshot represents "where I was" not "where I'm going."

### 7.2 Snapshot Validity

On restoration, snapshot validity is checked against current data:
- `game_id` must exist in current slate
- `player_id` must exist in current game
- If `game_id` is invalid → restore to engine home
- If `player_id` is invalid but `game_id` is valid → restore to game row (no player selection)

### 7.3 Partial Restoration

Partial restoration is always preferred over full restoration failure. The platform must restore as much valid context as possible rather than refusing to restore due to one invalid field.

---

## 8. Persistence Rules

| Scenario | Stack Behavior |
|---|---|
| Browser tab refresh | Stack discarded — session-scoped only |
| App hot-reload (dev) | Stack preserved if session_state preserved |
| Streamlit rerun | Stack unchanged — rerun does not affect stack |
| Network reconnect | Stack preserved |
| Data source failure | Stack preserved; restoration validates against cached data |
| 45-min inactivity | All INVESTIGATION entries expired; stack not cleared |
| Explicit logout | Stack discarded |

---

## 9. Implementation Interface

Codex owns the implementation. The stack must be exposed to the rest of the app via a clean interface. Claude defines the contract:

```
# Read
get_current_context() → ContextSnapshot
get_stack() → [ContextSnapshot]
can_go_back() → boolean

# Write
push_context(snapshot: ContextSnapshot) → void
pop_context() → ContextSnapshot | null
restore_to(snapshot_id: UUID) → ContextSnapshot | null
clear_stack() → void

# Maintenance
prune_expired() → int  (returns count pruned)
```

Codex selects the session_state implementation pattern. Claude does not prescribe the session_state key names or storage mechanism.

---

*This spec is documentation-only. Runtime implementation owned by Codex.*
