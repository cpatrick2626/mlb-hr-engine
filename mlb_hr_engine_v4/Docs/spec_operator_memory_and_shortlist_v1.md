# Operator Memory and Shortlist Specification v1
## MLB HR Engine — Operator Experience Doctrine

**Status:** ACTIVE  
**Step:** 10/12  
**Owner:** Claude (memory doctrine)  
**Runtime Owner:** Codex (session_state implementation)

---

## 1. Purpose

Operator memory governs how the platform allows operators to park, track, and revisit tactical candidates across the span of an active session. The shortlist is the primary mechanism: a lightweight, operator-curated list of players under active investigation.

The goal: operators can pause work on one candidate, handle other investigations, and resume without losing tactical continuity.

---

## 2. Shortlist Doctrine

### 2.1 What the Shortlist Is

The shortlist is an **operator-managed set of investigation targets** for the current session. It is:

- **Session-scoped** — not persisted across sessions
- **Manually curated** — operator explicitly adds/removes entries
- **Contextually enriched** — each entry carries investigation metadata at time of parking
- **Not a deployment queue** — the shortlist is for investigation tracking, not deployment decisions

The shortlist and the deployment queue are separate systems with separate purposes. A player can appear in both.

### 2.2 Shortlist Limits

| Constraint | Value |
|---|---|
| Max entries | 12 players |
| Max games represented | No limit (cross-game shortlists supported) |
| Entry lifetime | Session duration or manual removal |
| Auto-expiry | None — operator clears explicitly |

### 2.3 Priority Ordering

Shortlist entries display in **operator-set priority order** with the following default ordering on first add:

1. CRITICAL escalation-flagged players (auto-sorted to top)
2. Active investigation (most recently interacted)
3. Manual additions (in order added)

Operators can manually reorder entries within non-critical tiers. CRITICAL-flagged players cannot be manually demoted below non-critical entries while the escalation is active.

---

## 3. Investigation Bookmarking

### 3.1 Bookmark vs. Shortlist

| Concept | Scope | Persistence | Purpose |
|---|---|---|---|
| Shortlist entry | Session | Session only | Active candidate tracking |
| Bookmark | Conceptual | Session only | "Come back to this" flag |
| Restoration stack entry | System | Session only | Navigation history |

Bookmarks are a lightweight sub-feature within the shortlist. A shortlisted player can be bookmarked to indicate it needs explicit follow-up before session close.

### 3.2 Bookmark Behavior

- Bookmarked players display a visual indicator (implementation detail: Codex)
- Bookmarks survive shortlist reordering
- Bookmarks are cleared when player is removed from shortlist
- Session-close warning: if bookmarked players exist without deployment decision, show warning prompt before session ends

---

## 4. Temporary Memory Systems

### 4.1 Investigation Notes

Operators may attach a freeform text note to any shortlisted player. Notes are:

- Max 280 characters
- Session-scoped (not persisted)
- Displayed inline on shortlist entry
- Preserved across fast-return navigation

### 4.2 Revisit Indicators

Each shortlist entry tracks:

| Indicator | Meaning |
|---|---|
| `last_reviewed` | Timestamp of last JIG interaction |
| `review_count` | Number of JIG opens this session |
| `escalation_seen` | Whether operator acknowledged escalation for this player |
| `data_updated_since_review` | Whether underlying data changed since last review |

`data_updated_since_review` is the most critical indicator — it signals the operator should re-examine a previously reviewed candidate because the data basis has changed.

---

## 5. Candidate Parking Behavior

### 5.1 Parking Flow

"Parking" means: operator is mid-investigation and needs to switch context without losing work.

Parking sequence:
1. Operator initiates park (via shortlist add or explicit "park" action)
2. System snapshots current investigation context (see context restoration stack spec)
3. Player appears in shortlist with `status: PARKED`
4. Operator can now navigate freely
5. Clicking parked shortlist entry restores investigation context via restoration stack

### 5.2 Park Status States

| Status | Meaning |
|---|---|
| `PARKED` | Investigation paused, context preserved |
| `ACTIVE` | Currently under investigation |
| `FLAGGED` | Escalation pending review |
| `DEPLOYED` | Deployment decision made this session |
| `DISMISSED` | Operator cleared without deployment |

A player can transition: PARKED → ACTIVE → PARKED → DEPLOYED (or DISMISSED).

### 5.3 Multiple Parked Investigations

Operators may have up to **12 parked investigations simultaneously** (matches shortlist max). The platform supports full multi-game investigation context across all parked entries.

---

## 6. Escalation Revisit Behavior

When an escalation fires on a player who is already in the shortlist:

1. Player status upgrades to `FLAGGED`
2. Player auto-sorts to top of shortlist (within CRITICAL tier)
3. Escalation indicator overlaid on shortlist entry
4. Operator receives restoration prompt when engaging escalation: "Resume prior investigation context for [player]?"
5. On resolution: player returns to `PARKED` or `ACTIVE` (not auto-dismissed from shortlist)

---

## 7. Deployment History Visibility

Within the active session, the shortlist surfaces deployment history for context:

| Information | Visible |
|---|---|
| Whether player was deployed today | YES |
| Deployment time (this session) | YES |
| Prior session deployments | NO (out of scope for shortlist) |
| Deployment outcome | NO (post-deployment data, separate system) |

Deployed players in the shortlist show a `DEPLOYED` badge. They are not auto-removed — operators may wish to review them again or compare against parked candidates. Operators manually remove them when done.

---

## 8. Expiration Philosophy

The shortlist does **not** have automatic expiration within a session. This is an explicit design choice:

- Operators work long sessions
- Auto-expiry creates surprise context loss
- The operator is responsible for shortlist hygiene
- Session end clears all entries (no cross-session persistence)

The only automatic shortlist changes are:
- CRITICAL escalation auto-sort (not removal)
- `data_updated_since_review` indicator updates (not removal)

---

## 9. Rejected Patterns

| Pattern | Reason |
|---|---|
| Auto-remove players after X minutes | Unexpected; operators lose intentionally parked work |
| Cross-session shortlist persistence | Stale tactical data from prior sessions is dangerous |
| Shortlist doubles as deployment queue | Conflates investigation tracking with operational decisions |
| Max 3–5 shortlist entries | Insufficient for multi-game sessions |
| Alphabetical/statistical auto-sort | Operator priority is more important than algorithmic order |

---

*This spec is documentation-only. Runtime implementation owned by Codex.*
