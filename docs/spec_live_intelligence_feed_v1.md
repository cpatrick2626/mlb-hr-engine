# Live Intelligence Feed — Architecture Specification v1

**Owner:** Claude (tactical workflow doctrine, intelligence presentation philosophy)
**Codex scope:** shell implementation only — no doctrine changes without Claude review

---

## A. FEED PURPOSE

The Live Intelligence Feed is the real-time operational awareness layer of MLB HR ENGINE.
It does not narrate. It surfaces signal.

Primary functions:
- Escalation visibility — surface threshold crossings before operator notices them
- Scan acceleration — collapse research time by pre-flagging exploit conditions
- Battlefield awareness — show live environment state (lineups, weather, lines) without operator polling
- Operator prioritization — pull attention toward the highest-urgency targets at the right time
- Deployment urgency signaling — distinguish "track now" from "deploy now"

The feed should feel like a tactical intelligence terminal. Minimal. Purposeful. Machine-readable.

---

## B. FEED EVENT TYPES

### Escalation Events
- `ESCALATION_UPGRADE` — pick tier advanced (B→A, A→S)
- `ESCALATION_DOWNGRADE` — pick tier reduced (suppression trigger)
- `BARREL_THRESHOLD_CROSS` — batter barrel% crosses a tier boundary (8%, 10%, 12%)
- `COMPOSITE_SCORE_SPIKE` — score crosses 80th percentile within live slate

### Context Events
- `LINEUP_CONFIRMED` — official batting order posted for a game
- `LINEUP_CHANGE` — player scratched or moved in order vs projected
- `PITCHER_CHANGE` — scheduled starter replaced (pre-game)
- `WEATHER_SHIFT` — wind/temp/humidity factor changes ≥ 0.03 from last load
- `PARK_CONDITION_FLAG` — roof open/closed status change (where applicable)

### Market Events
- `STEAM_MOVE` — line moves ≥ 15 cents toward a batter's hit prop in ≤10 min
- `LINE_OPEN` — market opens for a previously unavailable prop
- `ODDS_DRIFT` — line drifts ≥ 25 cents without steam detection
- `SHARP_BOOK_DIVERGENCE` — Pinnacle/BetOnline price diverges ≥ 30 cents from retail

### Trust Events
- `TRUST_DEGRADATION` — confidence score drops below deploy threshold post-load
- `SUPPRESSION_ACTIVATED` — pitcher factor or weather pushes pick below threshold
- `SUPPRESSION_LIFTED` — prior suppression condition resolved
- `DATA_FRESHNESS_WARNING` — Statcast or odds data exceeds stale threshold

### Operational Events
- `DEPLOYMENT_CONFIRMED` — pick saved to tracker
- `DEPLOYMENT_REJECTED` — pick failed post-deployment validation
- `HR_ENVIRONMENT_SPIKE` — wind + temp + park combination reaches ≥ +8% composite lift
- `PITCH_MIX_EXPLOIT_ALERT` — HVY modifier ≥ 120 + barrel ≥ 10% combination detected
- `TACTICAL_CONFLICT` — same batter has conflicting signals (high barrel, extreme suppressor pitcher)

---

## C. PRIORITY TIERS

### INFO
Purpose: Ambient awareness. No action required.
- Visual: dim left border (#2a2a4a), muted text (#888)
- Persistence: 90 seconds, then auto-expire
- Animation: none
- Sound: none (future: none)
- Placement: bottom of queue
- Stacking: max 5 INFO cards visible; oldest pushed to archive

### WATCH
Purpose: Developing signal. Monitor, don't act.
- Visual: yellow-tinted left border (#4a4a20), body text (#aaa)
- Persistence: 5 minutes, then fade
- Animation: none
- Sound: none (future: soft chime, single)
- Placement: mid-queue
- Stacking: max 3 WATCH cards visible simultaneously; displace oldest INFO

### PRIORITY
Purpose: Actionable signal. Operator should evaluate now.
- Visual: blue left border (#1e3a5f → #3b82f6 gradient), body text (#ccc), label badge (#3b82f6)
- Persistence: 10 minutes or until acknowledged
- Animation: card slides in from right on creation; no pulse
- Sound: none (future: medium chime, single)
- Placement: upper queue, below CRITICAL
- Stacking: max 2 PRIORITY cards visible; WATCH cards compressed to 1-line when PRIORITY present

### CRITICAL
Purpose: Immediate attention required. Time-sensitive signal.
- Visual: red left border (#7f1d1d → #ef4444 gradient), accent hairline (#ef444466), body text (#eee), label badge (#ef4444)
- Persistence: until manually dismissed or event expires (lineup lock, game start)
- Animation: hairline pulse (2s interval, subtle, opacity 0.4→0.8); no flash
- Sound: none (future: alert tone, distinct from PRIORITY)
- Placement: pinned top of feed
- Stacking: max 2 CRITICAL cards pinned; third CRITICAL triggers sweep-to-queue behavior

---

## D. FEED CARD STRUCTURE

Each card contains:

```
[TIER BADGE] [EVENT TYPE LABEL]              [TIMESTAMP — relative: "4m ago"]
[PRIMARY LINE — player name / game context]
[SECONDARY LINE — tactical detail]
[SOURCE TAG: Statcast | Odds API | Weather | Model]  [CONFIDENCE INDICATOR]
[SUPPRESSION BADGE if applicable]  [→ CONTEXT LINK]
```

**Timestamp hierarchy:**
- Primary: relative ("just now", "3m ago", "12m ago")
- Secondary on hover: absolute ET time
- Age indicator: text dims progressively after 50% of persistence window

**Tactical labels:**
Match terminology from `tactical_language_dictionary.md`. No ad hoc language.
Examples: `BARREL SPIKE`, `STEAM DETECTED`, `EXPLOIT WINDOW`, `SUPPRESSION ACTIVE`

**Escalation badge placement:**
Top-left corner of card. Uses `spec_escalation_badge_system_v1.md` tier colors.

**Source visibility:**
Every card shows data source. Operators must know whether a signal is model-derived vs market-derived vs environmental.

**Confidence indicators:**
- HIGH: green dot (#22c55e)
- MODERATE: yellow dot (#eab308)
- LOW: red dot (#ef4444)
- UNKNOWN: gray dot (#666)

**Suppression indicators:**
When suppression is active, show `⊘ SUPPRESSED` badge with suppressor name (e.g., `⊘ SUPPRESSED · Snell GB-bias`).

**Contextual links:**
Every card with a player target includes `→ VIEW PLAYER` and `→ VIEW MATCHUP` jump anchors.

---

## E. EVENT LIFECYCLE

### Creation
Event fires → card instantiated with creation_ts, tier, event_type, payload, expiry_ts.

### Persistence
Card remains in active queue until:
- Expiry reached (tier-defined)
- Manually dismissed by operator
- Superseded by a higher-tier event of the same type + player

### Aging
- 0–33% of window: full opacity
- 33–66%: 90% opacity
- 66–100%: 75% opacity, label dims

### Fade behavior
At expiry: 500ms opacity fade → card removed from active queue.
No abrupt disappearance. No bouncing.

### Archive behavior
Expired cards accessible via "View Feed History" (not default-visible).
Archive stores last 100 events per session.
Archive is read-only. No further action from archive.

### Suppression replacement rules
If a SUPPRESSION_ACTIVATED event fires for a player who has an active ESCALATION_UPGRADE card:
- ESCALATION_UPGRADE card is downgraded visually (dimmed, badge updated to `SUPERSEDED`)
- SUPPRESSION_ACTIVATED card placed above it
- Both remain visible for 60 seconds, then ESCALATION_UPGRADE auto-expires

---

## F. INTERACTION RULES

### Click behavior
Click any card → expands to show full payload detail (all available data fields).
Second click → collapse.

### Jump-to-context behavior
`→ VIEW PLAYER` link → navigates to that player's card in the currently active engine (MAIN or JIG based on context).
`→ VIEW MATCHUP` link → opens JIG with that player pre-selected.
Navigation adds breadcrumb (see `escalation_jump_doctrine.md`).

### Hover expansion
Hover on source tag → shows data freshness timestamp.
Hover on confidence indicator → shows brief tooltip with contributing factors.

### Queueing
New events enter at tier-appropriate position.
If feed is full for tier, oldest card of same tier is archived.

### Pinning
Operator can pin any card — pinned cards ignore expiry, remain at top of their tier section.
Max 3 pinned cards. Fourth pin attempt shows "Unpin another card first."

### Dismissal doctrine
CRITICAL cards: require explicit dismiss (X button) OR triggering event expires naturally.
PRIORITY and below: dismiss with single click on X, or auto-expire.
Pinned cards: require explicit unpin before dismiss.

---

## G. FORBIDDEN PATTERNS

The following are explicitly rejected. Codex must not implement them regardless of perceived UI benefit.

- **Fake AI commentary:** No generated narrative about what a card "means." No "Claude thinks this batter is ready." Signal is signal.
- **Gambling hype text:** No "🔥 HOT PICK," "MUST BET," "LOCK." This is an analysis surface, not a sportsbook ad.
- **Scrolling chaos:** No auto-scrolling feed. Operator controls scroll position.
- **Flashing alerts:** No element flashes. Pulse animations only on CRITICAL, only opacity-based, max 1 element at a time.
- **Notification spam:** INFO events do not make sound. WATCH events do not make sound. Future sound only for PRIORITY+ with user opt-in.
- **Ticker overload:** No horizontal scrolling tickers. No news-style marquee elements.
- **Casino urgency tactics:** No countdown timers on picks (except lineup lock — that is real). No "Only X spots left" language. No artificial scarcity framing.
- **Unattributed signals:** Every card must show its data source. Sourceless cards are forbidden.
