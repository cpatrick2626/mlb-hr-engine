# SPEC: Player Threat Card v1
**Component:** `player_threat_card`  
**Spec Version:** v1  
**Status:** APPROVED FOR CODEX IMPLEMENTATION  
**Reference:** `Main Batters Card.png` (FINAL_DIRECTION APPROVED)  
**Author:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 3/12

---

## A. PURPOSE

Player threat card is the primary operator-facing intelligence surface for individual batter analysis. It communicates threat level, supporting metrics, and matchup context at scan speed. Operators scan multiple cards simultaneously to prioritize HR deployment decisions.

Card must be readable in 2 seconds without expansion. It is not a stats dashboard. It is not a leaderboard row. It is a threat signal with supporting context.

---

## B. CARD HIERARCHY

### Zone Structure (top to bottom)

```
┌─────────────────────────────────────────┐
│ [PLAYER IDENTITY ZONE]    [THREAT BADGE] │
│  Name · Team · Handedness               │
├─────────────────────────────────────────┤
│ [ESCALATION ZONE]                        │
│  Threat tier label · Confidence          │
├─────────────────────────────────────────┤
│ [METRICS ZONE]                           │
│  HR | PA | EV | FB% | Matchup score     │
├─────────────────────────────────────────┤
│ [TACTICAL SUMMARY ZONE]                  │
│  One-line insight · Park factor flag     │
└─────────────────────────────────────────┘
```

### Zone Definitions

**Player Identity Zone**
- Player full name — prominent, left-aligned
- Team abbreviation — muted weight, same line or immediate sub-line
- Handedness (L/R/S) — pill format, right of team or below name
- No headshot image in compact mode
- Threat badge anchored top-right corner of card

**Escalation Zone**
- Threat tier label (e.g., "PRIME TARGET" / "ELEVATED" / "MONITOR")
- Confidence value (e.g., "87% confidence")
- Tier label: high contrast, bold, color matches badge tier
- Confidence: muted weight, smaller size

**Metrics Zone**
- Horizontal row of key stats — no vertical stacking
- Required metrics: HR (season), PA, Exit Velocity avg, FB%
- Optional: Matchup score or park-adjusted score
- All metrics labeled with abbreviated header above value
- Values larger than headers
- No sparklines in compact mode

**Tactical Summary Zone**
- Single line of insight text — operator-readable, not raw stat
- Examples: "Elite EV vs. RHP. Wind out to RF." / "4 HRs last 7 days. Favorable park."
- Park factor flag if relevant (e.g., "HIGH HR PARK" pill)
- Muted visual weight — supporting, not dominant

**Expansion Behavior**
- Card expands vertically on click/hover to reveal:
  - Recent game log (last 5-7 games)
  - Split performance (vs. LHP/RHP, home/road)
  - Full pitch mix vulnerability
  - Expanded tactical notes
- Expansion never covers other cards (push-down, not overlay)
- One card expanded at a time per container (optional — see interaction rules)

---

## C. ESCALATION LOGIC

### Threat Tiers

| Tier | Label | Badge Color | Border Glow | Confidence Range |
|------|-------|-------------|-------------|-----------------|
| ELITE | PRIME TARGET | Amber/Gold | Strong amber glow | 85%+ |
| HIGH | ELEVATED | Orange | Moderate orange glow | 70–84% |
| MEDIUM | WATCH | Yellow-white | Subtle warm glow | 55–69% |
| LOW | MONITOR | Cool gray | No glow | <55% |
| SUPPRESSED | CAUTION | Muted blue | No glow — dim border | Any |

### Badge Behavior

- Badge displays tier label in all-caps, bold
- Badge background = tier color, border = darker shade of same
- Badge position: top-right corner, outside card content flow
- Badge never wraps to two lines — label must be 1-2 words max
- Badge size: consistent across all cards (no size escalation by tier)

### Glow Rules

- Glow is box-shadow on card border, not background color change
- Glow color matches tier color exactly
- Glow intensity: ELITE > HIGH > MEDIUM > none
- Glow does not animate in compact mode — static
- Glow may pulse slowly (2-3s cycle) in expanded mode for ELITE tier only
- No glow on MONITOR or SUPPRESSED tiers

### Confidence Presentation

- Displayed as percentage (e.g., "87%")
- Below tier label in escalation zone
- Font: muted, smaller than tier label
- Never hidden — confidence always present
- If confidence below 55% and tier shown: add "(Low Sample)" micro-label

### Suppression Behavior

- SUPPRESSED state triggered by: pitcher historically dominates this batter, or model explicitly flags suppression
- SUPPRESSED cards visually dimmed — reduced opacity on metrics zone
- "CAUTION" pill appears in tactical summary zone
- Glow suppressed entirely
- Card border becomes muted blue — cold temperature
- SUPPRESSED does not mean hidden — operators must see all cards

---

## D. INFORMATION PRIORITY

Highest to lowest operator importance:

1. Threat tier (badge) — immediately visible, no reading required
2. Player identity (name) — who is this
3. Escalation confidence — how reliable is the signal
4. Exit velocity — most predictive metric for HR probability
5. FB% — necessary for EV to translate to HRs
6. HR count (season) — baseline context
7. PA — sample size anchor
8. Matchup score — composite signal
9. Tactical summary — qualitative insight
10. Park factor flag — environmental modifier
11. Expansion content — deep analysis on demand

Cards must never invert this priority. Exit velocity must not be buried below PA. Threat badge must never be subordinate to player image.

---

## E. RESPONSIVE BEHAVIOR

### Desktop (≥1200px)

- Full card width: 280–340px
- All four zones visible in compact mode
- Metrics row: all 5 metrics displayed horizontally
- Tactical summary: full one-line insight visible
- 3–4 cards per row in game container grid

### Tablet (768px–1199px)

- Card width: 220–280px
- Player identity zone: name only (team moves to sub-line)
- Metrics row: 4 metrics max (drop matchup score)
- Tactical summary: visible but may truncate at 60 chars
- 2–3 cards per row

### Mobile (<768px)

- Card width: full width (single column)
- Compact mode only — no inline expansion
- Metrics row: 3 metrics (HR, EV, FB%)
- Tactical summary: hidden in compact, visible in expand
- One card per row
- Badge: visible, repositions to top-right of name zone

---

## F. INTERACTION RULES

### Hover Behavior

- Desktop: subtle lift effect (shadow depth increase) on hover
- Border glow brightens 10–15% on hover for ELITE/HIGH tiers
- Cursor changes to pointer — card is interactive
- Hover does not trigger data fetch — all data pre-loaded

### Expansion Philosophy

- Expansion is operator-initiated — never auto-expand
- Single click or tap expands
- Second click collapses
- Expanded state is non-destructive — game container layout adjusts
- No full-screen takeover on card expand
- Expansion reveals additional zones below tactical summary

### Progressive Disclosure

Level 1 (compact): Identity + badge + escalation + metrics row + tactical summary  
Level 2 (expanded): Level 1 + recent game log + splits + pitch vulnerability + notes  
Level 3 (modal — future): Full deep-dive analysis in overlay (see modal spec — deferred)

Operators should never need Level 3 for standard deployment decisions. Level 2 should resolve 95% of uncertainty.

### Motion Restraint Rules

- No entrance animations on card render
- No exit animations on card removal
- Expansion: smooth height transition only (200ms ease-out)
- Glow pulse: slow, subtle — never distracting
- No particle effects, no dramatic color flashes
- Motion budget: one animation per card at a time maximum

---

## G. DENSITY RULES

### Compact Scan Mode

- All four zones rendered
- No blank space between zones
- Metric values: large and readable — minimum 18px effective size
- Labels: minimum 10px, all-caps, muted
- Tactical summary: single line, no overflow wrap
- Card minimum height: 140px, maximum: 180px

### Expanded Tactical Mode

- Smooth push-down expansion — no overlay
- Additional content sections: labeled clearly
- No tables with more than 6 columns in expanded view
- Split data: two-column max (LHP vs. RHP, home vs. road)
- Recent game log: 5 games max in expanded card (not 30)
- Expanded height: proportional to content — no fixed expanded height

### No Dead Whitespace

- Cards never render with empty zones
- If tactical summary is unavailable: suppress zone, do not show empty row
- If PA too low for metrics: show metrics with "(small sample)" sub-label
- No placeholder text like "—" filling entire metric cells unless intentional suppression signal

### No Stat Flooding

- Compact mode: 5 metrics maximum
- Expanded mode: 12 metrics maximum across all zones
- Every metric must answer: "does this help the operator decide right now?"
- Remove metrics that require explanation to interpret — simplify or drop

---

## H. IMPLEMENTATION SAFETY NOTES FOR CODEX

### Component Isolation

- Player threat card is a pure render component
- Receives one prop: `player` object with all required fields
- Emits one callback: `onExpand(player_id)` — parent handles state
- No internal `st.session_state` reads or writes
- No internal `st.rerun()` calls
- No internal `st.cache_data` or `st.cache_resource` calls

### Route Coupling

- Card has zero awareness of current page route
- Card does not conditionally render based on URL parameters
- Card does not link to other pages internally
- Navigation, if needed, is handled by parent passing a callback

### Session State Ownership

- Expansion state owned by parent (game container or page shell)
- Card receives `is_expanded: bool` as prop
- Card emits expand/collapse event — does not manage its own expansion state
- This prevents expansion state from persisting across reruns unexpectedly

### Modal Coupling

- Card never opens modals directly
- If deep-dive modal is required (future): parent receives callback, opens modal
- Card does not import or reference modal components

### Rerun-Sensitive Logic

- All data for the card must be passed as props — no mid-render data fetching
- If live updates are needed: parent fetches, passes updated player object
- Card rerender should be cheap and idempotent

### Pure Render Architecture

```python
def player_threat_card(player: PlayerData, is_expanded: bool = False, on_expand=None):
    # Renders from props only
    # No session state reads
    # No API calls
    # No rerun triggers
    pass
```

---

## I. FORBIDDEN IMPLEMENTATION PATTERNS

### Reject These Patterns

**Nested rerun logic**
```python
# FORBIDDEN
if st.button("Expand"):
    st.session_state.expanded = player_id
    st.rerun()
```
Cards must not own rerun triggers. Parent handles state.

**Giant conditional render trees**
```python
# FORBIDDEN
if threat_tier == "ELITE":
    render_elite_card()
elif threat_tier == "HIGH":
    render_high_card()
# ... 50 more lines
```
Single render path. Tier drives style variables, not separate render branches.

**Duplicated badge systems**
```python
# FORBIDDEN — in player_threat_card.py
def render_badge(tier):
    # Custom badge logic here

# FORBIDDEN — in game_container.py
def render_badge(tier):
    # Different badge logic here
```
One shared badge component. No copies.

**Duplicated escalation styling**
```python
# FORBIDDEN
TIER_COLORS = {"ELITE": "#FFA500", ...}  # defined in card
TIER_COLORS = {"ELITE": "#FFB347", ...}  # different value defined in container
```
Single escalation system owns all tier → style mappings.

**Oversized player images**
```python
# FORBIDDEN
st.image(player_headshot, width=200)  # Dominates card
```
No headshots in compact mode. If headshots used in expanded mode: 48px max, circular crop, right-anchored.

**Sportsbook-style CTA visuals**
```python
# FORBIDDEN
st.button("🎯 BET NOW", type="primary")
st.metric("BEST ODDS", "+180")
```
No betting call-to-action language or styling. This is an intelligence tool.

**Self-managing expansion state**
```python
# FORBIDDEN
def player_threat_card(player):
    if "expanded" not in st.session_state:
        st.session_state.expanded = {}
    expanded = st.session_state.expanded.get(player.id, False)
```
Parent owns expansion state. Card is stateless.

---

## SPEC REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-05-20 | Initial spec. Full threat card definition. |
