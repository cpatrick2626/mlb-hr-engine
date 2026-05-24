# Operational Attention Pacing Doctrine

**Owner:** Claude (tactical workflow doctrine, cognitive continuity, command-center pacing)
**Codex scope:** visual implementation only — no pacing rule changes without Claude review

---

## OVERVIEW

MLB HR ENGINE handles dozens of signals simultaneously during live slate operation.
Attention pacing governs how those signals reach the operator — the rate, the hierarchy, and the boundaries.

**Design principle:** The system should feel alive, responsive, and focused — not like a slot machine operated by a caffeinated military contractor.

---

## A. SIMULTANEOUS ESCALATION LIMITS

Too many simultaneous escalations eliminate prioritization. The operator loses ability to rank.

### Active escalation caps
- **CRITICAL tier:** Maximum 2 active CRITICAL cards at any time.
  - If a 3rd CRITICAL fires: oldest CRITICAL is downgraded to PRIORITY unless it is pinned.
  - Pinned CRITICAL cards are exempt from demotion — they must be manually dismissed.
  
- **PRIORITY tier:** Maximum 4 active PRIORITY cards at any time.
  - If a 5th PRIORITY fires: oldest PRIORITY is downgraded to WATCH.

- **WATCH tier:** Maximum 6 active WATCH cards.
  - Overflow goes directly to archive — no visual card created.

- **INFO tier:** Maximum 5 active INFO cards.
  - Overflow suppressed entirely (no card, no archive entry).

### Rationale
An operator who sees 12 simultaneous CRITICAL alerts treats them all as noise.
Hard caps force the system to decide what is truly critical before competing for operator attention.

---

## B. CRITICAL ALERT CAPS

CRITICAL alerts must be reserved for time-sensitive, action-required events only.

### Qualifying CRITICAL events
- Active steam move with deployment window < 20 minutes to game
- Lineup scratched for a player in deployment queue
- Weather factor shift ≥ 0.06 for a game with deployed picks
- Pitch mix data shows extreme suppressor (GB% ≥ 65%) for a pick already in tracker

### Events that must NOT trigger CRITICAL
- General escalation upgrades (use PRIORITY)
- Data freshness warnings unless odds data is completely unavailable (use WATCH)
- Environment spikes for players not in deployment queue (use PRIORITY)
- Model recalibration events (use INFO)
- Any event that can safely wait 15+ minutes for operator review

### CRITICAL saturation response
If both CRITICAL slots are occupied and a new CRITICAL event fires:
1. Evaluate whether new event is higher urgency than either existing CRITICAL
2. If yes: demote lowest-urgency existing CRITICAL to PRIORITY; insert new CRITICAL
3. If no: new event enters as PRIORITY
4. Operator is shown "1 additional CRITICAL suppressed — review feed" indicator

---

## C. SIDEBAR DENSITY LIMITS

The sidebar must remain scannable in < 3 seconds under live slate conditions.

### Per-zone content limits
- Zone 1 (Live Slate Summary): 4 lines maximum, no expansion
- Zone 2 (Top Escalations): 3 entries maximum visible, link to full list
- Zone 3 (Deployment Queue): 1-line summary + count, expansion on demand
- Zone 4 (Tactical Alerts): 3 entries maximum visible, link to full feed
- Zone 5 (Suppression Warnings): count indicator only unless ≥ 1 (then show top 2)
- Zone 6 (Live HR Environment): 1-line composite + top 3 parks, no expansion needed
- Zone 7 (Trust-State Indicators): 4–5 rows, no expansion
- Zone 8 (Quick Navigation): 5 buttons max, no labels beyond engine names
- Zone 9 (Operator Shortlist): 5 entries max, "+N more" overflow

### Sidebar total line count target
Fully expanded sidebar: maximum 30 lines of content across all zones.
A sidebar with more than 30 lines of simultaneous content is too dense.

### Sidebar refresh throttle
Sidebar zones update at most once per data load cycle.
CRITICAL alert in Zone 4 may update mid-cycle (exception for real-time urgency).
All other zones are snapshot-consistent with the last full data load.

---

## D. FEED SATURATION RULES

The Live Intelligence Feed must not become a fire hose.

### Event throttle rules
- Same event type + same player: minimum 5-minute cooldown before re-firing (e.g., STEAM_MOVE for Judge fires, then fires again 3 min later → second event suppressed)
- Same event type + different players: no throttle (two STEAM_MOVE events for different players can coexist)
- LINEUP_CONFIRMED events: one per game, not per player on that team
- WEATHER_SHIFT: one per game per load cycle regardless of magnitude

### Feed health indicator
When feed has ≥ 8 active events, show a "High activity" indicator at top of feed.
This is informational only — it does not suppress further events, it signals to the operator that the environment is busy.

### Auto-archive triggers
Batch-archive events when:
- More than 15 events are in the active queue (archive oldest non-CRITICAL down to 10)
- Operator has been idle for > 10 minutes (archive all INFO and WATCH, preserve PRIORITY+)

---

## E. VISUAL COOLDOWN PHILOSOPHY

Visual activity should reflect actual signal activity — not manufacture urgency.

### Animation budget
Per render cycle, maximum active animations:
- 1 CRITICAL pulse (opacity oscillation, 2s interval)
- 0 simultaneous card slide-ins (queue entrance, not simultaneous burst)
- 0 persistent looping animations (loading spinners excepted)

New card entries: stagger by 150ms if multiple cards fire simultaneously. One card visible entry at a time.

### Color saturation cooldown
When CRITICAL tier is empty: maximum color accent is PRIORITY blue (#3b82f6).
High-saturation colors (reds, bright yellows) are reserved for CRITICAL+ states only.
Overuse of warning colors trains operators to ignore them.

### "Silence after action" principle
After a CRITICAL event is dismissed or resolved:
- No immediate new animation or color change to fill the void
- System returns to ambient state (dim, settled)
- Next signal enters on its own merit, not to fill the visual gap

### Urgency escalation ladder
Visual escalation follows a strict ladder. Levels cannot be skipped.

```
Ambient → INFO (dim text, no border) → WATCH (soft border, no animation) 
  → PRIORITY (blue border, card entrance) → CRITICAL (red hairline, pulse)
```

A state that jumps directly from ambient to CRITICAL (without PRIORITY existing first) is a system malfunction signal, not a feature.

---

## F. SUPPRESSION EMPHASIS BALANCE

Suppression signals must be visible without overwhelming positive signals.

### Suppression visibility rules
- Suppressed picks are visually dimmed but NOT removed from view
- Suppression reason is always visible (inline badge, not tooltip-only)
- Suppression badges use `⊘` prefix (defined in `tactical_language_dictionary.md`)
- Suppression state persists across engines (per `cross_engine_command_surface_doctrine.md`)

### Suppression-to-signal ratio
If ≥ 50% of visible picks in a single view have active suppression badges:
- Trigger Zone 5 sidebar summary (suppression event, not individual cards)
- Do NOT add individual WATCH events for each suppressed pick — that's noise
- Single Zone 5 indicator covers the batch: "7 picks with active suppression"

### Suppression vs no-line distinction
A pick with no market line (no odds) is NOT the same as a suppressed pick.
No-odds picks use `NO LINE` badge (neutral gray).
Suppressed picks use `⊘ SUPPRESSED` badge (warning amber).
These must be visually distinct — operators act differently on each.

### Suppression lift visibility
When suppression is lifted (event: `SUPPRESSION_LIFTED`):
- Badge changes from `⊘ SUPPRESSED` to normal state over 300ms transition
- A single WATCH event fires in the feed: "Suppression lifted: [Player] — [reason]"
- No fanfare. No escalation to PRIORITY just because suppression lifted.

---

## G. SCAN RHYTHM DOCTRINE

Operators run scans repeatedly throughout the day. The system must support a consistent scan rhythm.

### Default scan cadence
- Full data load: operator-triggered (not automated — operator decides when to load)
- Sidebar refresh: synced with full data load
- Feed events: fire when underlying data changes after a load
- Weather refresh: operator-triggered or on full data load (not on a timer)

### Scan-ready state
System is in "scan-ready state" when:
- Data freshness is GREEN on all Trust-State Indicators (Zone 7)
- No CRITICAL events are unacknowledged
- Odds API data is < 15 minutes old

Operator should be able to confirm scan-ready state in < 5 seconds by glancing at the sidebar.

### Scan completion signals
After completing a scan cycle (MAIN → JIG confirms → deployments logged):
- Zone 3 (Deployment Queue) count updates
- Zone 5 (Suppression Warnings) refreshes
- Zone 2 (Top Escalations) updates to reflect any new tier assignments

No explicit "scan complete" notification. Completion is evident from state changes.

---

## H. OPERATOR FATIGUE PROTECTION

Extended sessions create cognitive fatigue. The system must not amplify it.

### Anti-fatigue rules
- No element blinks or pulses continuously for > 30 minutes without operator interaction
- CRITICAL alerts that remain unacknowledged for > 30 minutes auto-downgrade to PRIORITY (game likely started)
- After 3+ hours of session activity: no new animation types introduced (system stays in established visual rhythm)

### Information density ceiling
At no point should any single engine view contain:
- More than 25 simultaneously visible player cards
- More than 3 open pitch mix expanders
- More than 2 active modal/overlay elements

Pagination and lazy loading enforce this ceiling — they are not just performance tools, they are cognitive density controls.

### Quiet mode consideration (future)
Future: operator-toggleable "quiet mode" that:
- Suppresses all animations
- Reduces all non-CRITICAL color accents to grayscale
- Disables all feed sounds (when sounds are implemented)
This is not a current implementation requirement — it is a placeholder for future operator preference support.
