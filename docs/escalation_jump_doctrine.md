# Escalation Jump & Investigation Flow Doctrine

**Owner:** Claude (tactical workflow doctrine, escalation rhythm, cognitive continuity)
**Codex scope:** routing implementation only — no jump hierarchy changes without Claude review

---

## OVERVIEW

Operators inside MLB HR ENGINE move through a continuous investigation loop, not a static dashboard.
The escalation jump system defines how that movement happens — what carries forward, what resets, and how operators always know where they are.

**Design principle:** Operators should never feel lost inside the platform.

---

## A. JUMP HIERARCHY

Escalation investigation follows a defined hierarchy of depth. Each level adds specificity.

```
Level 1: SLATE OVERVIEW (Full Slate — battlefield scan)
    ↓
Level 2: TARGET IDENTIFICATION (MAIN — EV/Edge qualification)
    ↓
Level 3: MATCHUP CONFIRMATION (JIG — pitch mix / HVY validation)
    ↓
Level 4: DEPLOYMENT REVIEW (Deploy panel — odds, edge, tracker)
    ↓
Level 5: QUEUE MANAGEMENT (Tracker + CLV — position tracking)
```

Operators move forward through this hierarchy by escalating.
Operators move backward by tracking (breadcrumb) or by suppression events forcing re-evaluation.

Lateral moves (e.g., MAIN → Full Slate without following a specific player) are context switches, not escalation jumps. They do not create breadcrumbs.

---

## B. BACKTRACK BEHAVIOR

Backtracking means returning up the hierarchy with context intact.

### Rules
- Backtrack always returns to the previous level's last scroll position and player focus.
- Backtrack does not reload data unless operator explicitly requests it.
- Backtrack clears the current level's breadcrumb stage (returns to parent level).
- Backtrack button is visible whenever a breadcrumb trail exists (not on Level 1 entry points).

### Backtrack triggers
- Browser/app back button → follows breadcrumb, not navigation history
- Explicit "← Back" control in engine header
- Keyboard shortcut (future: Escape key)
- Breadcrumb trail click (click any ancestor in the trail)

### What backtrack preserves
- Player focus at destination level
- Game selection at destination level
- TCC filter state at destination level
- Any escalation confirmations made at current level (they are not undone by backtrack)

### What backtrack does not undo
- Escalation tier promotions
- Suppression activations
- Deployments to tracker
- Live Intelligence Feed events

---

## C. BREADCRUMB DOCTRINE

Breadcrumbs show the operator's investigation path, not page navigation history.

### Format
```
[Level Name] › [Player Name] (if player in focus)
```
Examples:
- `MAIN › Judge`
- `MAIN › Judge › JIG`
- `FULL SLATE › Judge › JIG › DEPLOY`

### Rules
- Max breadcrumb depth: 4 levels visible. Deeper history truncated with `...` at left.
- Breadcrumb appears in engine header, below engine title.
- Breadcrumb updates on escalation jumps only (not on filter changes or tab switches within an engine).
- No breadcrumb on Level 1 entry from a fresh load.
- Clicking any breadcrumb stage fires a backtrack to that level.

### Breadcrumb preservation
Breadcrumb survives:
- Tab switches within the same engine
- Sidebar interactions
- Data refreshes (unless player is no longer in the refreshed data set)

Breadcrumb resets:
- On manual navigation to a different player
- On "Clear investigation" action (explicit operator action)
- On engine switch without player in focus

---

## D. RAPID INVESTIGATION LOOPS

A rapid investigation loop is the pattern of quickly escalating and returning for multiple targets.

### Single-target loop
```
Identify in MAIN → Jump to JIG → Confirm → Deploy → Return to MAIN position
```
Time target: < 60 seconds per pick with experienced operator and loaded data.

### Multi-target loop
```
Identify top 5 in MAIN (scan) → Jump to JIG for #1 → Confirm → Return to MAIN → 
Jump to JIG for #2 → (etc.)
```
MAIN must remember the operator's position and the scan state from before the first jump.

### Implementation requirements for rapid loops
- JIG must load pitch context for a player within 2 seconds of jump arrival (or show loading state immediately)
- Return from JIG must restore MAIN scroll position exactly
- TCC filter state must not drift during rapid loops
- Escalation badges on MAIN cards must update immediately after JIG confirmation (no stale state)

---

## E. MULTI-TARGET HANDLING

When operator is tracking multiple targets simultaneously:

### Investigation queue
Operators can add up to 10 players to the "investigation queue" (distinct from deployment queue).
Investigation queue is visible in Zone 9 (Operator Shortlist) of the sidebar.

### Queue navigation
Within queue: keyboard navigation (future) or prev/next arrows in engine header when investigation queue is active.
Current queue position shows in breadcrumb: `JIG (3/7)` = investigating target 3 of 7 in queue.

### Queue state
Each queue entry tracks:
- Investigation level reached (Level 1–5)
- Current escalation tier
- Last action taken (investigated, suppressed, deployed, skipped)

### Interruption handling
If operator leaves investigation queue mid-session:
- Queue persists for session duration
- Re-opening queue from sidebar resumes at last investigated target
- Targets confirmed or deployed are marked complete in queue list

---

## F. INTERRUPTION HANDLING

Interruptions happen when operator must context-switch before completing an investigation.

### Interruption triggers
- Incoming CRITICAL feed event
- Real-time lineup change alert
- Steam move detection
- Operator stepping away and returning

### Interruption behavior
On CRITICAL event while operator is mid-investigation:
1. Feed card appears at top of queue (always visible)
2. System does NOT force-navigate away from current investigation
3. Feed card shows `→ INTERRUPT: View Alert` link
4. Operator chooses: complete current investigation or switch to alert

On operator return after idle period:
1. System shows "You were investigating [Player] in JIG. Continue?" banner
2. One click resumes exact investigation state
3. State includes: last scroll position, last expanded card, last breadcrumb

### Interruption state preservation
Investigation state survives:
- Short idle periods (< 30 minutes)
- Tab switching within same session
- Sidebar interactions

Investigation state does NOT survive:
- App restart
- Full data reload with player no longer in data set
- Session expiry

---

## G. FOCUS RESTORATION

Focus restoration is the system's ability to return operator attention to the right context after any disruption.

### Restoration points
After each of these actions, the system remembers restoration point:
- Starting a JIG investigation jump
- Opening a deployment panel
- Following a feed event link
- Switching engines

### Restoration mechanism
Each restoration point stores:
- Engine (MAIN / JIG / Full Slate)
- Player in focus (player_id or null)
- Game in focus (game_pk or null)
- Scroll position index
- Breadcrumb depth

### Restoration triggers
- Explicit "← Back" action
- Dismissing a modal/panel
- Completing a deployment (returns to originating engine + player)
- Dismissing a CRITICAL feed card (returns operator to pre-interrupt investigation state)

### Restoration limits
- Max restoration stack depth: 5 levels
- Restoration state is session-scoped
- No cross-session restoration

---

## H. INVESTIGATION FLOW SUMMARY TABLE

| Action | Breadcrumb Updates? | Context Preserved? | Data Reloads? | Restoration Point Created? |
|--------|--------------------|--------------------|---------------|---------------------------|
| Jump MAIN → JIG | Yes | Yes | No | Yes |
| Jump to Deploy panel | Yes | Yes | No | Yes |
| Follow feed alert | No (lateral) | Yes | No | Yes |
| Engine switch (no player) | No | Partial | No | No |
| Backtrack via breadcrumb | Yes (pops) | Yes | No | No |
| Clear investigation | Yes (resets) | No | No | No |
| Data reload | No | Yes (if player still in data) | Yes | No |
| App restart | No | No | Yes | No |
