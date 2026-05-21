# Full Slate Parent Orchestrator Doctrine
**Session:** Chat 04 — Step 6/12  
**Date:** 2026-05-20  
**Status:** PLANNING / ARCHITECTURE ONLY — no runtime changes  
**Cross-references:** `full_slate_tactical_doctrine.md`, `spec_deployment_panel_architecture_v1.md`, `deployment_trust_hierarchy.md`, `escalation_vs_suppression_doctrine.md`, `operator_override_doctrine.md`

---

## Contents

1. [Parent Orchestrator Doctrine](#1-parent-orchestrator-doctrine)
2. [Full Slate View Hierarchy](#2-full-slate-view-hierarchy)
3. [Deployment Panel Doctrine](#3-deployment-panel-doctrine)
4. [Escalation Propagation Architecture](#4-escalation-propagation-architecture)
5. [Tactical Context Preservation Doctrine](#5-tactical-context-preservation-doctrine)
6. [Multi-Game Operational Flow](#6-multi-game-operational-flow)
7. [Deployment Queue Philosophy](#7-deployment-queue-philosophy)
8. [Battlefield Navigation Doctrine](#8-battlefield-navigation-doctrine)
9. [Cognitive Continuity Recommendations](#9-cognitive-continuity-recommendations)
10. [Future Orchestration Enhancement Opportunities](#10-future-orchestration-enhancement-opportunities)

---

---

# 1. Parent Orchestrator Doctrine

## 1.1 Role Definition

The Full Slate Parent Orchestrator is the conceptual coordination layer that sits above all individual UI surfaces. It does not execute business logic. It does not own session_state keys. It does not make model decisions.

Its sole responsibility is **coherence** — ensuring that as the operator moves through tactical investigation, deployment review, and navigation, the system presents a unified, continuous battlefield picture rather than a series of disconnected panels.

The Orchestrator is not a component. It is a set of rules that govern how components behave toward each other.

---

## 1.2 Orchestration Responsibilities

### 1.2.1 Battlefield-State Coordination

The Orchestrator maintains a coherent understanding of the current battlefield state — what the operator is investigating, what has been escalated, what has been deployed — and ensures all active views reflect the same state simultaneously.

Battlefield state consists of three layers:
- **Slate state** — which date, which games, which picks are loaded
- **Investigation state** — active player, active game, origin engine, escalation level
- **Deployment state** — logged picks, pending queue, exposure context

All three layers must be consistent at all times. A change in one layer propagates contextually to the others — but does not force a re-render of views the operator is not currently using.

### 1.2.2 Ownership Boundaries

The Orchestrator defines clear ownership to prevent state collisions:

| Domain | Owner | Notes |
|--------|-------|-------|
| Slate date / loaded data | `pipeline.py` + Streamlit `@st.cache_data` | Orchestrator reads, never writes |
| Active investigation context | `investigation_state.py` | Orchestrator reads + triggers writes via standard API |
| Escalation queue | `investigation_state.py:EscalationQueueState` | Orchestrator reads + surfaces; does not purge |
| Displayed picks pool (`_display_pool`) | `tab_picks()` scope | Orchestrator has no ownership |
| Tactical filter params (`_tac_params`) | `filter_controls.py` + `session_state` | Orchestrator reads for breadcrumb construction |
| Deployment log | `tracking/pick_tracker.py` | Orchestrator reads count; never writes directly |
| Portfolio optimizer state | `portfolio/optimizer.py` + session_state cache | Orchestrator reads selection count; never modifies |
| Card HTML caches (`_CARD_CACHE`) | `tab_picks()` scope | Orchestrator has no interaction |

### 1.2.3 Deployment Focus Synchronization

When an operator enters Deployment Focus Mode for a specific pick, the Orchestrator must ensure:

1. The active investigation context in `investigation_state` reflects that player and game
2. The deployment panel receives the current escalation level from the investigation context
3. After deployment confirmation, the investigation context is updated to `investigation_status: "deployed"` for that player
4. The card that launched Focus Mode receives a DEPLOYED badge on return

The Orchestrator does not enforce this by executing code — it defines the contract that the deployment panel and the investigation state module must honor.

### 1.2.4 Escalation Propagation Control

Escalation signals originate at the player level and must propagate coherently upward through the slate without losing context or creating contradictions. The Orchestrator governs propagation rules — see Section 4 for full architecture.

### 1.2.5 Tactical Context Preservation

Operator context must survive navigation events. The Orchestrator defines what context is mandatory to preserve, what is acceptable to lose, and what must be explicitly restored. See Section 5 for full doctrine.

### 1.2.6 View-State Hierarchy

The Orchestrator defines a hierarchy of view states that prevents contradictory UI configurations:

```
IDLE
  └─ SLATE_LOADED
       ├─ SCANNING          (operator reading Command Center)
       ├─ INVESTIGATING      (Intelligence Panel open for specific player)
       │    └─ ARSENAL_OPEN  (Arsenal Analysis expanded within Investigation)
       ├─ GAME_REVIEW        (Full Slate game-organized view active)
       └─ DEPLOYING          (Deployment Focus Mode active)
            └─ DEPLOYED      (Post-confirmation, returning to slate)
```

Only one primary view state is active at a time. Sub-states are nested. Transitioning between primary states has defined entry and exit behaviors (see Section 8).

---

## 1.3 What the Orchestrator Does NOT Do

- It does not own or directly modify `st.session_state`
- It does not replace the MAIN and JIG engines — they maintain separate identities
- It does not merge MAIN and JIG pick pools
- It does not alter model_prob, EV, edge, or any computed values
- It does not decide which picks appear in the deployment queue — that is operator action
- It does not auto-dismiss escalation badges
- It does not inject routing logic into `app.py` functions

---

## 1.4 Orchestration Failure Modes (and Mitigations)

| Failure | Symptom | Mitigation |
|---------|---------|------------|
| State fragmentation | Escalation shown on card but not in deployment panel | Investigation state written on escalation trigger, read by deployment panel |
| Context loss on navigation | Operator returns to slate, doesn't know where they were | Breadcrumb bar (see Section 8.2) |
| Stale escalation | Badge shows for event that has been resolved | Escalation TTL + re-validation on hydration |
| Deployment/investigation mismatch | Panel shows different player than investigation context | Panel always reads from investigation_state, never from local variable |
| Multi-tab confusion | MAIN and JIG show contradictory escalation states | Escalation is stored at player level, not engine level |

---

---

# 2. Full Slate View Hierarchy

## 2.1 Hierarchy Map

```
GLOBAL SLATE LAYER
│  Purpose: Slate-wide orientation and ambient awareness
│  Always visible at all depths
│
├── ESCALATION LAYER
│   Purpose: Cross-slate escalation state summary
│   Visibility: Active when any escalation present
│
├── GAME LAYER
│   Purpose: Game-organized view of all players
│   Visibility: Active in Full Slate "All Players" mode
│
│   └── TACTICAL CLUSTER LAYER
│       Purpose: Group players by tactical relationship within game
│       Visibility: Active when multiple picks share game/lineup
│
│       └── PLAYER THREAT LAYER
│           Purpose: Individual player investigation
│           Visibility: Active on card expand / Intelligence Panel
│
│           └── ARSENAL LAYER
│               Purpose: Pitch matchup analysis
│               Visibility: Active on Arsenal expand
│
│               └── DEPLOYMENT LAYER
│                   Purpose: Single-pick deployment decision
│                   Visibility: Active in Deployment Focus Mode
```

---

## 2.2 Layer Definitions

### Global Slate Layer

**Purpose:** Battlefield-wide situational awareness. The operator's ambient context regardless of drill-down depth.

**Visibility rules:** Always rendered. Never hidden. Never collapsed. Survives all navigation events.

**Persistence behavior:** Persists for the full session duration. Invalidated only on data reload.

**Interaction expectations:** Passive primarily. Operator reads, rarely interacts. Exception: manual refresh trigger.

**Tactical focus:** Date, slate status (LIVE/STALE), qualified pick count, active escalation count, deployment count.

**Collapse/expand philosophy:** This layer does not collapse. It is a fixed ambient strip, not a panel.

**Contents:**
- Slate date badge
- LIVE / STALE status with timestamp
- Count: qualified picks (post-filter)
- Count: active escalations (unacknowledged)
- Count: picks logged today (deployed)
- Lineup confirmation percentage pill
- Manual refresh control
- Weather threat summary (if |weather_factor − 1.0| ≥ 0.05)

---

### Escalation Layer

**Purpose:** Surfaces cross-slate escalation events that affect multiple picks or require operator-level attention rather than card-level attention.

**Visibility rules:** Renders when ≥1 active unacknowledged escalation exists. Hidden (not collapsed) when no escalations active.

**Persistence behavior:** Escalation state persists within session. ACK events persist in session — not across reloads.

**Interaction expectations:** Operator can view escalation summary without expanding individual cards. Can acknowledge all of same type in batch (e.g., "ACK all weather alerts").

**Tactical focus:** What has changed since last load that affects deployment decisions.

**Collapse/expand philosophy:** Collapses to a single count badge when operator dismisses the summary strip. Count badge always visible in Global Layer.

**Contents:**
- Escalation type groupings (pitcher changes, lineup changes, weather, line movement)
- Affected pick count per type
- Most critical escalation surfaced first
- Batch ACK control per type
- Timestamp of each escalation trigger

---

### Game Layer

**Purpose:** Game-organized view of all players on the slate. Primary surface for battlefield reconnaissance at the game level.

**Visibility rules:** Active in Full Slate "All Players" mode. Not the default view in Command Center (Command Center is rank-sorted, not game-organized).

**Persistence behavior:** Game groupings persist across filter changes. Filter changes highlight/dim rows — they do not reorganize game groups.

**Interaction expectations:** Operator scans across games, identifies opportunity clusters, drills into specific games or players.

**Tactical focus:** Which games have the most concentrated opportunity. Park factor, weather, combined escalation state per game.

**Collapse/expand philosophy:** Each game group can collapse to a header row showing: game name, start time, pick count, escalation count, weather summary. Expanded state shows all player rows for that game.

**Contents per game group header:**
- AWAY @ HOME, start time, urgency color
- Park factor value
- Weather factor direction (if significant)
- Pick count: qualified, elite, total
- Escalation count (unacknowledged)
- Pitcher attribution (each team faces the opposing starter)

**Contents per player row:**
- Batting order spot
- Player name, team
- Barrel%, Model prob, EV%, Edge%, Confidence
- Status badges: STEAM / ★ELITE / ✓QUAL / lineup-confirmed indicator
- Background tinting: qualified / borderline / no-odds

---

### Tactical Cluster Layer

**Purpose:** Identifies and visualizes tactical relationships between players within a game — stacks, correlated picks, same-pitcher targets.

**Visibility rules:** Active when 3+ picks from same game appear in qualified pool. For 1-2 picks from a game, players render as individuals in Game Layer without cluster grouping.

**Persistence behavior:** Cluster groupings rebuild on filter change. Cluster identity (same game, same team) is deterministic — does not depend on operator filter state.

**Interaction expectations:** Operator can view cluster as a unit — combined HR exposure, N_eff for this cluster, joint correlation context. Can deploy from cluster view or drill to individual players.

**Tactical focus:** Concentration risk identification and opportunity amplification for multi-pick games.

**Collapse/expand philosophy:** Cluster header always visible. Individual player rows within cluster expandable. Cluster summary (N_eff, combined exposure) expandable.

**Contents:**
- Cluster header: "NYY CLUSTER — 4 picks — N_eff: 1.6 — 40% exposure"
- Individual player rows (same as Game Layer player rows)
- Correlation note if same-lineup: "Lineup correlation active — stacked"
- Cluster-level combined HR probability (conceptual, display-only)

---

### Player Threat Layer

**Purpose:** Full intelligence on a single player and their matchup. The primary investigation surface.

**Visibility rules:** Active when operator expands a player card (Intelligence Panel) in any view. Always a child of the parent view — never replaces it.

**Persistence behavior:** Panel state (scroll position, sub-expansions) preserved while within same view. Closing and reopening resets to default state.

**Interaction expectations:** Operator reviews all model factors, Statcast profile, platoon split, park factor, pitcher context, calibration tier. Can launch Arsenal Layer or Deployment Layer from here.

**Tactical focus:** Is this pick confident enough to deploy? What is the model's reasoning?

**Collapse/expand philosophy:** Panel opens full by default. Sub-sections (HVY detail, calibration note) collapsed by default within the panel — reveal on demand.

**Contents:**
- Probability breakdown by factor
- Statcast profile (barrel%, exit velo, FB%, xSLG, hard hit%)
- Platoon split and advantage assessment
- Park factor and direction
- Pitcher factor (attenuated, with notation of PITCHER_FACTOR_SCALE)
- Weather factor
- Calibration tier (Elite Platt vs Standard Platt)
- Escalation state for this player
- Launch controls: "Open Arsenal" / "Deploy this pick"

---

### Arsenal Layer

**Purpose:** Pitch matchup analysis between batter profile and pitcher arsenal.

**Visibility rules:** Active on explicit "Open Arsenal" action from Player Threat Layer. Inline expansion within Player Threat Layer — does not navigate away.

**Persistence behavior:** Arsenal content lazy-loaded on first open per session. Cache keyed to slate_ts + player_id. Survives panel close/reopen within same session.

**Interaction expectations:** Operator reviews pitch mix, batter vs pitch performance, HVY modifier signals. This layer informs the final deployment decision but is not required before deployment.

**Tactical focus:** Does the matchup support or contradict the model signal? Is the HVY modifier directionally consistent?

**Collapse/expand philosophy:** Arsenal section is a single expandable within the Player Threat Layer. Default: collapsed (lazy-load gate). Expand: "▶ Load Full Arsenal Analysis."

**Contents:**
- Pitcher pitch mix (% by pitch type, avg velocity, whiff%)
- Batter vs pitch type performance splits
- HVY modifier score with signal breakdown
- Career H2H context (if available)
- Data vintage note (current-year vs prior-year sourcing)

---

### Deployment Layer

**Purpose:** Single-pick deployment decision surface. Maximum cognitive focus, minimum distraction.

**Visibility rules:** Active in Deployment Focus Mode. This is the deepest layer. All parent layers are visible at reduced opacity (20%) to provide spatial context without competing for attention.

**Persistence behavior:** Focus Mode state does not persist. Exiting Focus Mode (via CANCEL, ESC, or post-deployment) returns operator to exact prior view state.

**Interaction expectations:** Operator reviews consolidated deployment intelligence, inputs bet amount, selects sportsbook, confirms. No exploration — only confirmation or abandonment.

**Tactical focus:** Should I deploy this pick right now? What size? On which book?

**Collapse/expand philosophy:** No collapse within Deployment Layer. All deployment-critical information visible without scroll. If scrolling is required, the design has failed.

**Contents:** Per `spec_deployment_panel_architecture_v1.md` — 9 zones, fixed order.

---

---

# 3. Deployment Panel Doctrine

## 3.1 Philosophy Summary

The deployment panel is the final gate. It is not a research surface. It is not a review dashboard. It is a confirmation system that presents a single, coherent deployment brief and awaits a single, deliberate operator action.

Everything in the panel serves one purpose: allowing the operator to deploy with confidence or abandon with clarity.

---

## 3.2 What Belongs in the Deployment Panel

| Information | Why It Belongs |
|-------------|----------------|
| Player identity (name, team, position, game, date) | Confirmation that operator is looking at the correct pick |
| Escalation tier badge (large) | Primary deployment confidence signal |
| Model probability (calibrated) | The core number being acted upon |
| EV% and Edge% | The betting justification |
| Suppression tier and score | Mandatory — cannot be hidden |
| Top 3 model factors | Operator needs to understand why the model selected this pick |
| Recommended bet size (quarter-Kelly) | Decision input |
| Best odds and sportsbook | Where to execute |
| Trust-state indicator | Operator must know data freshness before deploying |
| Current exposure context | Prevents inadvertent concentration |
| Override controls (when required) | Active deployment gate for HIGH / LOCKDOWN suppression |
| LOG BET action + CANCEL | The decision |

---

## 3.3 What Must Be Excluded from the Deployment Panel

| Information | Why Excluded |
|-------------|--------------|
| Full stat tables | Stat browsing belongs in Player Threat Layer, not deployment |
| Historical betting records | Operator should not be second-guessing model with irrelevant history |
| All other players | Focus Mode collapses to one pick only |
| Sportsbook odds comparison table | Distracting — best book is pre-selected by model |
| Portfolio optimizer output | Macro context — Exposure Zone covers this sufficiently |
| Pitch mix tables | Already reviewed in Arsenal Layer pre-deployment |
| Calibration technical detail | Not actionable at deployment time |
| Bankroll history / P&L charts | Retrospective — not relevant to this decision |
| Diagnostic data | Background system health is not operator concern at deployment |

---

## 3.4 Escalation Carryover Behavior

When the operator reaches the Deployment Panel, escalation state must carry over from the investigation context:

- `escalation_level` from `investigation_state` drives the escalation tier badge in Zone 1
- If escalation_level was set during investigation (e.g., "watch", "active", "critical"), the deployment panel reflects this tier
- Escalation level cannot be downgraded within the deployment panel — it is read-only
- If no escalation level is set, panel renders with tier derived from model probability and barrel tier (standard tier assignment)

**Carryover rules:**
1. Escalation level from investigation always overrides tier auto-assignment if present
2. Suppression tier is computed independently from pitcher data — not inherited from escalation_level
3. Trust-state is computed from data source freshness — not inherited from anything

---

## 3.5 Confidence Presentation

Confidence is presented as a single compound statement in Zone 2, not scattered across the panel:

```
Model: 18.4%  |  Edge: +5.2pp  |  EV: +7.1%  |  Barrel tier: ELITE
Bet: $42 @ +380 DraftKings
```

**Color coding:**
- Model prob ≥ 15%: `#4ade80` (green)
- Model prob 10–15%: `#f59e0b` (amber)
- Model prob < 10%: `#94a3b8` (dimmed) — should not appear in Focus Mode; filter prevents
- EV positive: green
- EV negative: red — should not appear; filter prevents
- Edge positive: green
- Edge negative: red — should not appear; filter prevents

---

## 3.6 Tactical Summary Structure

Zone 4 tactical evidence follows this fixed structure:

```
TOP FACTORS
1. [Factor name] — [value] — [direction label]
2. [Factor name] — [value] — [direction label]
3. [Factor name] — [value] — [direction label]

Park: [stadium name] — [factor value] — [HITTER / NEUTRAL / PITCHER]
Platoon: [batter hand] vs [pitcher hand] — [FAVORABLE / NEUTRAL / DISADVANTAGE]
Matchup (HVY): [score] — [FAVORABLE / NEUTRAL / UNFAVORABLE]
```

Factor names use plain language, not internal variable names:
- "Barrel Quality" not "sc_barrel"
- "Fly Ball Rate" not "fb_pct"
- "Pitcher Suppression" not "pit_factor"
- "Weather Boost" not "weather_factor"

---

## 3.7 Distraction Elimination Rules

1. No animations in the deployment panel (not even subtle ones)
2. No auto-populating text (no typewriter effects on the confidence statement)
3. No social proof ("3 operators also picked this") — forbidden
4. No urgency language ("bet before tip-off", "lines closing soon") — forbidden
5. No sportsbook branding beyond name in selector
6. No odds comparison widget — one book, one line
7. No "related picks" or "you might also like" cross-sells
8. No expandable panels beyond Zone 3 pitcher profile — all other zones are fixed-height
9. Zone 9 action layer never changes background color based on suppression tier (the zone is always the same visual treatment — what changes is the override gate, not the button color)

---

## 3.8 Focus Mode Expectations

The deployment panel must feel:

**Disciplined:** Every element earns its presence. No information is shown unless it directly affects the deployment decision.

**Tactical:** The language is operational, not enthusiastic. "Model: 18.4%" not "Strong pick! 18.4%".

**Decision-oriented:** The panel guides toward one of two outcomes: LOG BET or CANCEL. No neutral third path.

**Operationally calm:** No color drama, no badge pulsing, no animation. The most alarming visual in Focus Mode is a HIGH or LOCKDOWN suppression badge — and even that is a structured, contained signal, not a flashing warning.

---

---

# 4. Escalation Propagation Architecture

## 4.1 Propagation Philosophy

Escalation is a bottom-up signal. It originates at the data level (pitcher stats, lineup data, weather, line movement) and propagates upward through the view hierarchy. It does not originate at the UI level.

The UI does not create escalations. It surfaces them.

---

## 4.2 Escalation Origination Points

| Signal Source | Origination Layer | Example |
|---------------|-------------------|---------|
| Pitcher data change | Arsenal Layer | Starter replaced, new pitcher_id |
| Lineup data change | Player Threat Layer | Player scratched or batting order shifted |
| Weather update | Game Layer | Wind shift exceeds 5% factor change |
| Line movement | Player Threat Layer | No-vig prob moved > 1pp since load |
| Barrel/Statcast update | Player Threat Layer | Rare — new Savant data with materially different barrel% |

---

## 4.3 Escalation Inheritance Rules

Escalation propagates **upward only** through the hierarchy on hydration:

```
PLAYER THREAT LAYER
  → escalation badge on player card (Player Threat Layer surface)
  → escalation count increment in Game Layer header
  → escalation count increment in Global Layer badge
```

Escalation does NOT propagate downward:
- A game-level weather event does NOT auto-escalate every player in that game
- Escalation is player-specific unless the event is systemic (see Section 4.6)

---

## 4.4 Suppression Behavior

Escalation signals can be suppressed (not surfaced to operator) when:

1. **Already acknowledged:** If operator has ACK'd an escalation for this player in this session, same-payload escalation is suppressed. New payload (different data fingerprint) breaks suppression.

2. **Below interruption threshold:** LOW tier escalations during active Deployment Focus Mode are suppressed at card level. They are logged but not surfaced as badges until Focus Mode exits.

3. **Stale signal:** If escalation trigger data is older than the current hydration timestamp minus TTL (defined per type in Section 4.8), escalation is suppressed at surface.

4. **Rate-capped:** If 3 escalation badges are already active across the slate, 4th and beyond are queued, not displayed. Queue surface order: by tier (CRITICAL first), then by timestamp.

---

## 4.5 Downgrade Logic

An escalation can be downgraded (tier reduced) when:

1. **Pitcher returns (scratched then confirmed):** If a pitcher flagged as changed returns to confirmed status on next hydration, escalation tier drops from CRITICAL to INFO ("Lineup change resolved"). Badge auto-clears after 5 minutes.

2. **Line movement reverses:** If a line moved adversely (triggering MEDIUM) and on next hydration the line returns to prior level, the escalation downgrades to LOW ("Line movement partially reversed").

3. **Weather improves:** If weather factor drops back toward 1.0, escalation tier reduces. Does not auto-clear — remains at INFO until ACK or TTL expiry.

Downgrade does NOT retroactively remove an acknowledged escalation. ACK'd events are session history.

---

## 4.6 Systemic vs Player-Specific Escalation

### Player-Specific Escalation (default)
- Affects one player's card only
- Appears as badge on that player's card
- Increments escalation count in Game Layer header and Global Layer
- Examples: lineup scratch, individual line movement, single pitcher change

### Systemic Escalation
- Affects all picks in one game or across the full slate
- Surfaced as a single top-of-slate banner, NOT as individual card badges
- Examples: weather event affecting one stadium (all picks in that game), API source degradation (all picks)
- Individual cards receive a small ambient indicator (1px border in escalation color) rather than full badge, to avoid badge flooding

**Transition rule:** If a systemic event resolves to affect only one specific player's outcomes (e.g., weather is system-wide but only one pick's model is materially affected), it becomes player-specific. The system banner dismisses; the individual card badge appears.

---

## 4.7 Conflict Handling

When escalation signals conflict (e.g., a player's line moved favorably AND the pitcher was scratched), priority rules apply:

1. **Highest tier wins for badge display.** CRITICAL suppresses LOW display.
2. **All signals are stored.** Even if only CRITICAL badge shows, the LOW signal is recorded in investigation context and visible in Diagnostics.
3. **Direction conflicts:** A favorable line movement (LOW positive) does NOT cancel a CRITICAL pitcher scratch. They coexist in investigation context. Badge shows CRITICAL only.
4. **Suppression conflict:** Pitcher suppression tier conflicts with escalation tier — they are displayed independently (Zone 1 vs Zone 3 in deployment panel). No merging.

---

## 4.8 Stale Escalation Handling

| Escalation Tier | Auto-expire TTL |
|-----------------|-----------------|
| CRITICAL | No auto-expire. Must be ACK'd explicitly. |
| HIGH | 20 minutes after hydration that contained the trigger |
| MEDIUM | 10 minutes |
| LOW | 5 minutes or next data hydration (whichever first) |
| INFO | 3 minutes |

**Stale check:** On each hydration event, escalation signals are re-validated against current data. If the triggering condition no longer exists in fresh data, the escalation is marked stale. Stale signals auto-expire per TTL above — they do not immediately disappear to avoid flickering during brief data gaps.

---

## 4.9 Escalation Persistence Rules

| Scenario | Escalation State |
|----------|------------------|
| Tab switch within app | Escalation state fully preserved |
| Navigation from MAIN to JIG | Escalation state preserved (stored in investigation_state, not in tab scope) |
| Data refresh (hydration) | Escalations re-validated; stale ones marked; new ones added |
| App session restart | Escalations cleared — session-only |
| Deployment of escalated pick | Escalation badge cleared for that player post-deployment (deployment implies operator has processed the escalation) |
| CRITICAL escalation during Focus Mode | Escalation surfaces as modal interruption in Focus Mode; does not auto-cancel Focus Mode |

---

---

# 5. Tactical Context Preservation Doctrine

## 5.1 What Context Must Persist

Context preservation prevents operator disorientation. The following context elements must survive every navigation event defined in this doctrine:

### Active Investigation Context (from `investigation_state.py`)
- `active_player_id` — which player is under investigation
- `active_player_name` — display name for breadcrumb
- `active_game_pk` — which game the player belongs to
- `origin_engine` — MAIN or JIG (for breadcrumb and return routing)
- `escalation_level` — what level has been assigned during this investigation
- `investigation_status` — idle / active / queued / deployed

### UI Context
- Slate scroll position (preserved until data reload)
- Expanded card states (which cards are open)
- Active tab within Command Center
- Full Slate mode selection (All Players / Qualified / Elite Targets)
- JIG Full Slate mode selection (Top Tactical / Qualified Tactical / All Tactical)
- Tactical filter params (`_tac_params`) — the operator's active filter configuration

### Session Context
- Escalation ACK history (which escalations have been acknowledged)
- Deployment count for today (from pick_tracker.csv, read at session start)
- Optimizer selection (which preset is active, which picks are selected)
- Pitch mix lazy-load state (which pitch mix panels have been loaded)

---

## 5.2 What Is Acceptable to Lose

| Context | Lost When | Acceptable |
|---------|-----------|------------|
| Arsenal Analysis scroll position | Panel close | Yes — reload is fast |
| Intelligence Panel sub-expansion state | Panel close | Yes — defaults are sensible |
| Card HTML cache | Data reload | Yes — cache rebuilt automatically |
| Escalation ACK history | App session restart | Yes — escalations re-validate on hydration |
| Optimizer cache | Ranked list fingerprint change | Yes — optimizer re-runs on new data |

---

## 5.3 Navigation Events and Context Behavior

### Tab Switch (within tab_picks)
**Context preserved:** Active investigation, scroll position, expanded cards, filter params, escalation ACKs  
**Context reset:** None  
**Operator experience:** Seamless — no visible transition

### Engine Switch (MAIN → JIG)
**Context preserved:** Active player investigation (if player exists in JIG universe), escalation ACKs, deployment count  
**Context reset:** Expanded cards (JIG has different card set), tactical filter params (MAIN and JIG use separate filter namespaces)  
**Context partially preserved:** origin_engine updated to reflect current engine  
**Operator experience:** Brief reorientation — normal. Breadcrumb shows engine switch.

### Full Slate Entry (from Command Center)
**Context preserved:** Active investigation, filter params, escalation ACKs  
**Context reset:** None  
**Operator experience:** Seamless — Full Slate is a view within MAIN, not a separate engine

### Intelligence Panel Open
**Context preserved:** Slate scroll position, filter params, escalation state  
**Context reset:** None  
**Operator experience:** Panel overlays without displacing slate

### Intelligence Panel Close
**Context preserved:** Slate scroll position restored exactly  
**Context reset:** Panel scroll position (intentional)  
**Operator experience:** Return to slate as left

### Deployment Focus Mode Entry
**Context preserved:** Active investigation context, escalation level, suppression state (computed fresh from pitcher data)  
**Context reset:** Nothing lost — Focus Mode is additive, not replacing  
**Operator experience:** Surrounding slate visible at 20% opacity — spatial anchor maintained

### Deployment Focus Mode Exit (post-LOG BET)
**Context restored:** All prior state  
**Delta applied:** DEPLOYED badge on card, deployment count +1  
**Operator experience:** Returns to slate, finds target card marked DEPLOYED

### Deployment Focus Mode Exit (CANCEL)
**Context restored:** All prior state, no delta  
**Operator experience:** Returns to slate as if Focus Mode never opened

### Interruption Recovery (session restored after browser suspend)
**Context available:** Data re-hydrates from cache if within 15 minutes  
**Context lost:** Escalation ACKs, UI scroll position, expanded cards  
**Context preserved:** Filter params (if stored in session_state which survived suspend), deployment count (re-read from CSV)  
**Operator experience:** Brief reorientation. STALE badge shown if cache age > 15 min.

### Live Update Event (background hydration completes)
**Context preserved:** All investigation context, scroll position, expanded cards  
**Delta applied:** Escalation badges update, LIVE/STALE badge flips  
**Operator experience:** No disruption. Badge updates are peripheral. Cards do not re-render unless fingerprint changed.

---

## 5.4 Tactical Filter Preservation

Tactical filter params (`_tac_params`) are the operator's lens on the slate. They represent an operator decision and must be preserved:

- Preserved across tab switches
- Preserved across Full Slate / Command Center transitions
- Preserved across data refreshes (filter params are in session_state, not derived from data)
- NOT preserved across session restart (operator re-applies on new session)

**Preset selection:** When operator selects a filter preset (Operational / Selective / Elite Only), the preset name is stored in session_state alongside the parameter values. On data refresh, parameters persist — the preset label reflects the currently active set.

---

---

# 6. Multi-Game Operational Flow

## 6.1 Philosophy

On heavy slates (12–15 games), the operator faces genuine decision paralysis without structured operational flow. The system must guide attention systematically without forcing a specific workflow.

The default multi-game flow moves from high-level slate reconnaissance to targeted game investigation to individual player confirmation. The operator can break out of this flow at any point — the system provides structure, not constraint.

---

## 6.2 Multi-Game Slate Reconnaissance

**Stage 1: Slate summary scan (0–20 seconds)**

Operator reads Global Layer:
- How many games have qualified picks?
- Is there weather affecting any games?
- Are there any CRITICAL escalations?
- What is the overall slate quality (lineup confirmation %)?

At this stage, the operator is not looking at individual picks. They are establishing whether this is a heavy deployment slate, a watch-and-see slate, or a minimal action slate.

**Decision:** Deploy broad / Deploy targeted / Monitor only

---

**Stage 2: Game-layer prioritization (20–60 seconds)**

Operator enters Full Slate → All Players mode. Scans game group headers:
- Which games have the most qualified picks?
- Which games have elite-tier picks?
- Which games have weather amplification?
- Which games have active escalations?

Operator mentally ranks games by opportunity density. No explicit ranking mechanism required — the game headers provide enough data.

**Output:** Mental priority order: Game 1 (highest opportunity) → Game N (lowest)

---

**Stage 3: Game investigation (60–180 seconds per game)**

For each priority game, operator drills into player rows within the game group. For high-density games (3+ qualified picks), the Tactical Cluster Layer surfaces.

**Actions available:**
- Expand individual player for Intelligence Panel
- Open Arsenal Layer for specific player
- Add player to informal watchlist (deployment queue — see Section 7)
- Skip game (collapse group header, move to next)

---

**Stage 4: Deployment decision cycle**

After reconnaissance, operator has identified deployment candidates. Enters Deployment Focus Mode per pick in priority order. See Section 7 for deployment queue philosophy.

---

## 6.3 Concurrent Deployment Candidates

When multiple picks qualify for deployment, they are reviewed sequentially — one at a time in Deployment Focus Mode. Parallel deployment decision (reviewing two picks simultaneously) is not supported and not desirable. Cognitive focus is the resource being protected.

Candidate ordering is governed by the Deployment Queue (Section 7). The operator controls ordering — the system provides a ranked default but does not enforce it.

---

## 6.4 Cross-Game Threat Comparison

Operators sometimes need to compare two picks across different games before choosing which to deploy (when bankroll is limited or exposure is a concern).

**Supported comparison paths:**
1. **Side-by-side in table:** `_render_qualified_table` in Full Slate Qualified mode provides sortable columns — operator can sort by EV, Edge, Barrel, Confidence to surface cross-game comparison
2. **Stack Panel:** If multiple picks share correlation factors (same pitcher being targeted, similar park conditions), Stack Panel provides cluster-level comparison
3. **Elite Targets mode:** Full Slate "Elite Targets" filters to barrel ≥ 8% across all games — natural cross-game comparison surface for elite picks

**Not supported:**
- Side-by-side Deployment Focus Mode panels for two picks simultaneously
- Auto-ranking that combines model score with portfolio exposure (this is the portfolio optimizer's job, not the orchestrator's)

---

## 6.5 Stack Competition

When two picks from the same lineup compete for deployment (bankroll constraint), the operator should use:

1. Stack Panel — shows both picks' combined correlation context
2. Portfolio tab — shows optimizer selection which handles same-team caps
3. Manual comparison — expand both cards, compare Intelligence Panel factors

The system does not auto-select between competing stacked picks. This is an operator judgment call.

---

## 6.6 Escalation Collisions

When two CRITICAL escalations surface in the same session (e.g., two different pitchers scratched, affecting two separate picks):

1. Both escalations surface independently on their respective cards
2. The Global Layer escalation count shows the total (e.g., "2 escalations")
3. The operator resolves them sequentially — ACK first, then second
4. Rate cap rule applies: if 3+ escalations already active, additional ones queue
5. Queue order for display: CRITICAL before HIGH before MEDIUM — within tier, chronological

---

## 6.7 Operator Prioritization Controls

The operator prioritizes games and picks through:

| Control | Purpose |
|---------|---------|
| Full Slate mode selector | All Players / Qualified / Elite Targets — narrows game layer |
| Tactical filter controls | Barrel/EV/Edge/Confidence thresholds — highlights within game layer |
| Game group collapse | Manually deprioritize games by collapsing their group header |
| Deployment queue ordering | Drag or reorder candidates in queue |
| Preset selection | One-click Operational / Selective / Elite Only filter state |

There is no explicit "game priority" button. Priority emerges from the combination of these controls. The system ranks picks globally by model score — game-level priority is operator-determined.

---

---

# 7. Deployment Queue Philosophy

## 7.1 What the Queue Is

The deployment queue is the operator's informal staging area for picks they intend to deploy. It is not a permanent record. It is not the pick_tracker. It is a session-scoped scratchpad that allows the operator to identify candidates during reconnaissance, then process them systematically during the deployment phase.

The queue exists in the operator's mental model. The system provides a structured surface to represent it.

---

## 7.2 Candidate Queuing Behavior

**How picks enter the queue:**
- Operator explicitly adds a pick during investigation (one-click "Queue for deployment")
- Picks do NOT auto-enter the queue based on model score
- The portfolio optimizer selection is distinct from the deployment queue — optimizer output can seed the queue but is not the queue

**How picks leave the queue:**
- Operator deploys the pick (LOG BET) — pick moves from queue to pick_tracker.csv
- Operator removes the pick (explicit remove action)
- Pick becomes invalid (player scratched — CRITICAL escalation auto-marks the queued pick as INVALID)
- Session ends — queue does not persist

**Queue capacity:** No hard limit. Operator-governed. If queue exceeds 15 picks, surface a gentle reminder ("Large queue — consider using portfolio optimizer").

---

## 7.3 Deployment Shortlist Logic

The deployment queue may be long (operator adds many candidates during reconnaissance). The shortlist is the subset the operator intends to act on given current bankroll and time constraints.

**Shortlist creation:** Operator reviews queue, marks picks as "Active" (deploy today) or "Monitor" (watch, no bet today).

**Shortlist display:** Active picks sorted by model score (default). Operator can reorder manually.

**Shortlist constraints:** Not enforced by system. Advisory only. Operator decides.

---

## 7.4 Escalation Ranking Persistence

When picks are in the queue and a new escalation arrives:

1. CRITICAL escalation on a queued pick: pick is flagged INVALID in queue. Operator must explicitly remove or re-evaluate.
2. HIGH escalation on a queued pick: pick is flagged CAUTION in queue. Operator must acknowledge before deploying.
3. MEDIUM/LOW escalation: informational badge on queue item. Deployment not blocked.

Escalation level at time of queueing is stored. If escalation resolves (downgrades), the queue item updates to reflect current state.

---

## 7.5 Confidence Ordering

Default queue sort: model probability descending (highest confidence first).

Alternative sorts available:
- EV% descending (highest expected value first)
- Edge% descending (largest model-to-market gap first)
- Composite score descending (EV×0.35 + Edge×0.30 + Confidence×0.20 + Barrel×0.15)
- Game time ascending (earliest game first — time urgency)

Sort is operator-controlled. Sort state persists within session.

---

## 7.6 Tactical Grouping Rules

Picks in the queue can be grouped for display:

- **By game** — useful for correlated-pick awareness
- **By tier** (ELITE / PRIME / QUALIFIED) — useful for prioritization
- **By sportsbook** — useful if operator is executing on multiple books sequentially
- **Flat** (default, no grouping) — simple ranked list

Grouping is display-only. Deployment proceeds one pick at a time regardless of grouping.

---

## 7.7 Operator Review Cadence

Recommended cadence for heavy slates (10+ games, 30+ picks):

1. **Reconnaissance phase** (30–60 min before first pitch): Add candidates to queue via game-layer review
2. **Refinement phase** (15–30 min before first pitch): Review queue, mark Active vs Monitor, check for escalations
3. **Deployment phase** (0–30 min before first pitch): Process Active queue picks in order via Focus Mode
4. **Monitoring phase** (post-deployment): Monitor queue for escalations on deployed and remaining Monitor picks

The system supports this cadence but does not enforce or time it. Operator paces themselves.

---

## 7.8 Preventing Deployment Chaos on Heavy Slates

Heavy slate deployment pressure (many picks, short window, multiple books) is the highest cognitive-load scenario. The following rules prevent chaos:

1. **One pick in Focus Mode at a time.** No exceptions.
2. **Queue is a list, not a checklist.** Operator is not required to deploy every queued pick.
3. **Escalations surface in the queue, not as interruptions.** Operator sees escalation status when they review the queue — they are not interrupted mid-deployment.
4. **Clock awareness is operator responsibility.** The system shows game time on cards but does not create urgency pressure (no countdown timers, no flashing).
5. **Partial deployment is normal.** It is fine to deploy 3 of 10 queued picks. The queue does not create pressure to deplete itself.
6. **Portfolio optimizer reduces queue pressure.** When optimizer is active, the queue naturally reduces to the optimizer-selected shortlist. This is the intended workflow for heavy slates.

---

---

# 8. Battlefield Navigation Doctrine

## 8.1 Navigation Philosophy

Navigation should feel like moving through a briefing room, not clicking through a website. Every transition is purposeful. No transition disorients. The operator always knows where they are and how to get back.

Speed is a secondary consideration. Coherence is primary. A fast navigation to a confusing view is worse than a slightly slower navigation to a well-oriented view.

---

## 8.2 Tactical Breadcrumbs

A persistent breadcrumb strip sits below the Global Layer. It shows the operator's current location in the view hierarchy and their navigation path.

**Format:**

```
MAIN > COMMAND CENTER > [Player Name] (Investigating)
MAIN > FULL SLATE > All Players > [Game: NYY vs BOS]
JIG > TACTICAL UNIVERSE > [Player Name] (Arsenal)
```

**Rules:**
- Maximum 3 segments. If deeper than 3 levels, show only last 3 with `...` prefix.
- Each segment is clickable — click returns to that level.
- Breadcrumb updates immediately on navigation (not on data load).
- Breadcrumb does not scroll — it is always visible.

**Breadcrumb persistence:** Breadcrumb state is derived from `investigation_state.current_route` and the current UI context. It does not store history — it reflects current position only.

---

## 8.3 Rapid Game Switching

When the operator needs to move between game groups quickly (common during reconnaissance):

**Pattern:** Game group headers are the navigation units. Collapsing a game header moves visual focus to the next game header without scrolling.

**Keyboard navigation (future):** J/K keys navigate between game group headers when in Full Slate / All Players mode.

**Fast-switch behavior:** When switching games, Intelligence Panels from the prior game auto-collapse. The prior game's group header collapses. The new game's group header expands. Scroll position moves to the new game header.

**No animation:** Game switching should feel instantaneous. No cross-fade, no scroll animation. Direct jump.

---

## 8.4 Escalation Jump Behavior

Operator can navigate directly to an escalated pick from the Global Layer escalation count badge:

1. Click escalation count badge → Escalation Layer expands (see Section 2.2)
2. Escalation Layer shows affected picks list
3. Clicking a pick in the escalation list → jumps directly to that player's Intelligence Panel in the appropriate view (MAIN or JIG based on `origin_engine`)

**Jump behavior:**
- If currently in MAIN and escalation is from MAIN: smooth scroll to card + Intelligence Panel opens
- If currently in JIG and escalation is from MAIN: engine switch to MAIN + scroll to card + Intelligence Panel opens
- Breadcrumb updates immediately on jump

---

## 8.5 Fast-Return Navigation

Every drill-down has a fast-return path. The operator should never need more than one click to return to the slate level from any depth.

| Current location | Fast-return destination | Control |
|------------------|------------------------|---------|
| Intelligence Panel | Slate (card collapsed) | ESC or back chevron in panel header |
| Arsenal Analysis | Intelligence Panel (Arsenal collapsed) | ESC or back chevron |
| Deployment Focus Mode | Slate (panel closed) | ESC or CANCEL |
| Stack Panel | Slate (panel closed) | ESC or backdrop click |
| JIG engine | MAIN Command Center | Engine switcher in header |

**ESC behavior is predictable:** ESC always closes the innermost open panel. Two ESCs return to slate from any two-level drill-down. This is guaranteed, not context-dependent.

---

## 8.6 Command Strip Synchronization

The command strip (primary navigation — COMMAND CENTER / FULL SLATE / etc.) reflects the current view state and must stay synchronized with actual content:

- Active tab is always highlighted accurately (no desync between strip selection and rendered content)
- Tab badge counts update on data refresh, not on navigation
- Switching tabs does not trigger data reload
- Command strip is always visible — it does not scroll or collapse

---

## 8.7 Mobile-Safe Transitions

Mobile navigation requires specific adaptations:

| Desktop behavior | Mobile adaptation |
|------------------|-------------------|
| Intelligence Panel as right-side overlay | Full-screen overlay with back button |
| Deployment Focus Mode as centered modal | Full-screen |
| Game groups in side-by-side column layout | Single-column stack |
| Breadcrumb strip persistent | Breadcrumb collapsed to back button + current level label |
| Hover reveals secondary info | Tap to reveal (no hover equivalent) |
| Keyboard navigation | Swipe navigation between game groups |

**Touch target sizing:** All interactive elements minimum 44px touch target. No interactive elements smaller than 44px on mobile, regardless of label size.

**Mobile scroll safety:** Game group expansion should not cause scroll position jump. New content pushes down, operator scrolls to it.

---

---

# 9. Cognitive Continuity Recommendations

## 9.1 The Disorientation Problem

The primary cognitive failure in tactical UI systems is disorientation — the operator loses track of where they are and what they were doing. On a heavy slate, this leads to missed plays, duplicate actions, and fatigue-driven errors.

Cognitive continuity is the property that prevents disorientation. It is achieved through four mechanisms: **spatial anchoring, temporal marking, action confirmation, and context persistence.**

---

## 9.2 Spatial Anchoring

The operator must always have a clear sense of where they are in the UI hierarchy.

**Mechanisms:**
- Breadcrumb strip (Section 8.2) — explicit location declaration
- Background slate visible at 20% opacity during drill-downs — maintains sense of "above" context
- ESC behavior always predictable — operator can navigate home from anywhere with confidence
- Global Layer always visible — provides constant spatial reference point

**Anti-patterns to avoid:**
- Views that replace the slate entirely (operator loses their place)
- Navigation that scrolls to an arbitrary position on return
- Panel transitions that obscure the spatial relationship between panel and parent view

---

## 9.3 Temporal Marking

The operator needs to understand what has changed since they last checked, without re-reading everything.

**Mechanisms:**
- LIVE / STALE badge with explicit timestamp — operator knows data age
- Delta badges on cards (line movement, escalation) mark what changed since last hydration
- Investigation context records `last_viewed` timestamp — operator can see when they last looked at a pick
- Deployment Focus Mode shows data refresh timestamp in Zone 6 — operator knows confidence currency

**Anti-patterns to avoid:**
- No timestamp on escalation badges (operator doesn't know how old the signal is)
- Re-rendering cards without delta indicators (operator can't distinguish fresh from cached)
- Clearing STALE badge too quickly (operator loses awareness of data age)

---

## 9.4 Action Confirmation

After every significant operator action, the system confirms the action completed and the state has changed.

**Mechanisms:**
- LOG BET: brief confirmation state in Zone 9, then DEPLOYED badge on card
- Escalation ACK: badge disappears immediately (instant visual confirmation)
- Escalation queue add: immediate badge on queued item
- Filter change: pick count updates immediately in tab badge and headline

**Anti-patterns to avoid:**
- Silent form submissions (operator doesn't know if LOG BET worked)
- Delayed badge updates after ACK (creates uncertainty)
- Filter changes that don't immediately reflect in visible content

---

## 9.5 Context Persistence (Summary)

Per Section 5 — key principles for cognitive continuity:

1. Investigation context (`investigation_state`) is the single source of truth for active player/game. Any view that needs this context reads from it — does not re-derive.
2. Filter params persist across navigation events — operator doesn't need to re-apply filters after switching views.
3. Escalation ACK history is session-persistent — operator is not re-alerted to already-acknowledged signals.
4. Scroll position is preserved across panel open/close — operator returns to exact prior position.

---

## 9.6 Cognitive Load Budget

**Per-session cognitive budget:** An operator working a heavy slate has finite cognitive capacity. The system should spend that budget on tactical decisions, not on navigating the interface.

**Budget rules:**
- Each navigation should cost ≤1 second of operator attention
- Each panel open should require 0 re-orientation time (spatial anchor maintained)
- Each escalation ACK should require ≤1 click
- Each deployment decision should require ≤4 inputs (bet size, sportsbook, confirmation, optional override)
- Each return-to-slate should require ≤1 action

If any of these budget items is being exceeded in testing, the navigation or interaction design has failed.

---

---

# 10. Future Orchestration Enhancement Opportunities

## 10.1 Orchestration State Machine (Near-Term)

Formalize the view-state hierarchy (Section 1.2.6) as an explicit state machine in `investigation_state.py`:

- States: IDLE → SLATE_LOADED → SCANNING → INVESTIGATING → ARSENAL_OPEN → DEPLOYING → DEPLOYED
- Transitions: defined entry and exit behaviors per state
- Guards: certain transitions require preconditions (e.g., DEPLOYING requires a valid player context)
- Benefits: prevents impossible state combinations, enables explicit transition logging for debugging

**Implementation note:** This is a pure data/state change — no UI change required. `investigation_state.py` would gain a `view_state` field and `transition_view_state(from_state, to_state)` function.

---

## 10.2 Cross-Engine Escalation Bus (Near-Term)

Currently, MAIN and JIG maintain separate escalation surfaces. A player who is escalated in MAIN but the operator is currently in JIG does not see that escalation.

**Enhancement:** A shared escalation bus — a session_state dictionary keyed by `player_id` — where both engines write escalation events and both engines read them. The Global Layer escalation count would source from this bus, not from engine-specific state.

**Benefits:** True cross-engine escalation awareness. Operator doesn't miss a CRITICAL event because they're in the wrong engine.

---

## 10.3 Persistent Session Recovery (Medium-Term)

Current: session restart clears all context. Enhancement: lightweight localStorage bridge via `st.components` JS injection persists:

- Active filter params (operator re-applies manually today)
- Deployment queue (today's queued picks — operator re-adds manually today)
- Escalation ACK history for same-day slate (operator re-encounters dismissed escalations today)
- Today's deployment count (re-read from pick_tracker.csv — already handled)

**Implementation note:** localStorage bridge must not persist sensitive data (API keys, odds data). Only session UI state is persisted.

---

## 10.4 Deployment Queue UI Surface (Medium-Term)

Formalize the deployment queue as an explicit UI component:

- Sticky bottom strip or collapsible side panel
- Shows queued picks count, CRITICAL/CAUTION flags, shortlist vs monitor split
- One-click "Deploy next" advances to Focus Mode for top-priority queued pick
- Integrates with portfolio optimizer: optimizer output can be imported as queue

**Dependencies:** Requires `investigation_state.py` escalation queue expansion to include deployment candidates (not just escalation targets). Current `EscalationQueueState` is close but needs `deployment_queue` concept separated from `escalation_queue`.

---

## 10.5 Automated Escalation Detection (Medium-Term)

Currently, escalation detection requires data to be re-hydrated. Enhancement: background differential check that compares current `investigation_state.active_player` pitcher_id against last-known pitcher_id from prior hydration, without full data reload.

**Mechanism:** After hydration completes, run a lightweight delta check:
1. Compare new pitcher_id vs stored pitcher_id for all picks in investigation state
2. If mismatch detected: generate CRITICAL escalation immediately
3. If no mismatch: no escalation (standard behavior)

**Benefits:** CRITICAL pitcher-change escalation surfaces faster — between full hydration cycles if operator has not refreshed.

---

## 10.6 Operator Session Replay (Long-Term)

Record operator navigation events with timestamps for post-session review:

- When did the operator first look at each pick?
- Which picks were investigated but not deployed?
- Which escalations were ignored (not ACK'd) and the pick was still deployed?
- How long did each Focus Mode session take?

**Purpose:** Operational self-review. Operator can understand their own decision patterns and improve workflow efficiency over time.

**Privacy:** Replay data is local-only (never sent to server). Session-scoped (cleared at session end unless operator explicitly saves).

---

## 10.7 Tactical Tag System (Short-Term)

Planned in Session 43 deferred work. Each player receives one or more tactical tags that describe why the model selected them:

| Tag | Condition |
|-----|-----------|
| FASTBALL HUNTER | Barrel% ≥ 10% + facing pitcher with ≥ 50% fastball usage |
| BARREL SPIKE | Recent barrel% significantly above season average |
| PARK EXPLOIT | Park factor ≥ 1.10 + player pull% ≥ 45% |
| PLATOON PRIME | Platoon advantage + HVY modifier FAVORABLE |
| WEATHER WINDOW | Weather factor ≥ 1.06 + wind to CF |
| SUPPRESSION FADE | Model prob above suppression signal (engine overrides suppressor) |

Tags are display-only in Full Slate game rows and Intelligence Panels. Tags do not affect model_prob, scoring, or filtering.

**Orchestration relevance:** Tags help the operator rapidly understand why a pick appeared — reducing the time spent in Intelligence Panel and accelerating the deployment decision cycle.

---

## 10.8 Multi-Day Orchestration Mode (Long-Term)

For early-posted next-day lines, extend the orchestration layer to span two slate dates:

- TODAY slate: full functionality (deploy, investigate, track)
- TOMORROW slate: research mode only (investigate, queue candidates — no deployment)
- Investigation context stores which date is active
- Escalation system only fires on TODAY slate
- Deployment queue for TOMORROW slate seeds TODAY slate automatically when date rolls over

**Implementation note:** Requires `investigation_state` to carry a `slate_date` field. No model changes — data pipeline already supports arbitrary date lookup.

---

---

*End of Full Slate Parent Orchestrator Doctrine — Session Chat 04, Step 6/12*  
*Planning only. No runtime files modified.*  
*Next: Step 7/12 — [TBD per session plan]*
