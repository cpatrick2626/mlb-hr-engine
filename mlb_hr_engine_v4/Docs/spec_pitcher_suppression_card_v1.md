# SPEC: Pitcher Suppression Card v1
**Component:** `pitcher_suppression_card`  
**Spec Version:** v1  
**Status:** SPECIFICATION ONLY — awaiting Codex implementation  
**Author:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 4/12 — Escalation Infrastructure & Pitcher Suppression Stabilization

---

## A. OPERATIONAL PURPOSE

The pitcher suppression card is a caution-first intelligence module. It does not predict outcomes. It communicates risk modifiers that may reduce operator confidence in an otherwise-qualified deployment pick.

### Tactical Suppression Role
A qualified batter (FIRE or STRONG tier) may face a pitcher whose profile structurally limits HR outcomes — independent of the batter's own power metrics. The suppression card surfaces that risk so the operator can apply informed judgment before deploying.

### Deployment Caution Role
Suppression cards do not block deployment. They inform it. An operator seeing a HIGH-suppression card may still deploy, but they have been given the signal. The decision remains with the operator.

### False-Positive Prevention Role
Without suppression intelligence, the engine can produce FIRE picks against elite pitchers with low barrel-allowed profiles. Suppression cards prevent these cases from appearing indistinguishable from a FIRE pick against a vulnerable pitcher. Deployment without suppression context is false confidence.

---

## B. CARD STRUCTURE

The pitcher suppression card renders inside the Player Threat Card's EXPANDED state and inside the H2H Matchup Card. It is never a standalone top-level card.

### Zone Layout

```
┌───────────────────────────────────────────────┐
│ [PITCHER IDENTITY ZONE]        [SUPPRESSION   │
│  Name · Team · Hand · Role     TIER BADGE]    │
├───────────────────────────────────────────────┤
│ [SUPPRESSION SCORE ZONE]                      │
│  Suppression score value · Tier word          │
│  Primary reason label                         │
├───────────────────────────────────────────────┤
│ [RISK INDICATORS ZONE]                        │
│  Signal pills — one per active signal         │
├───────────────────────────────────────────────┤
│ [CAUTION EXPLANATION LAYER]                   │
│  Short plain-language summary of suppression  │
│  "Why this pitcher suppresses HR confidence"  │
├───────────────────────────────────────────────┤
│ [MATCHUP SUPPRESSION LAYER]                   │
│  Batter vs pitcher handedness risk            │
│  HVY modifier direction indicator             │
│  Career H2H context (if available)            │
├───────────────────────────────────────────────┤
│ [RECENT TREND LAYER]                          │
│  Last 3 starts: barrel allowed, HR allowed    │
│  Velocity trend: flat / rising / declining    │
├───────────────────────────────────────────────┤
│ [ENVIRONMENTAL SUPPRESSION LAYER]             │
│  Weather interaction with pitcher tendency    │
│  Park factor interaction note                 │
└───────────────────────────────────────────────┘
```

### Zone Definitions

**Pitcher Identity Zone**
- Full pitcher name, team abbreviation, throwing hand (L/R)
- Role: STARTER / OPENER / BULK (starters only receive full suppression treatment)
- Identity zone never includes ERA or surface-level stats — those belong in the risk indicators zone

**Suppression Score Zone**
- Numerical score 0–100 (higher = more suppressed)
- Score drives tier assignment — thresholds in Section C
- Primary reason: single most impactful suppression signal displayed in text
- Score is a composite internal signal — not exposed as raw math

**Risk Indicators Zone**
- Pill-format badges, one per active suppression signal
- Maximum 5 pills shown — additional signals collapsed behind "+(N) more" control
- Pills are not interactive in compact state — expand reveals detail

**Caution Explanation Layer**
- Single paragraph, 1–3 sentences
- Written in tactical language — see `tactical_language_dictionary.md`
- Never alarmist, never vague
- Example: "Dominant weak-contact profile. Barrel-allowed rate in bottom 10th percentile of MLB starters. HR risk suppressed across handedness."

**Matchup Suppression Layer**
- Handedness disadvantage: explicit if batter faces same-hand pitcher with documented platoon weakness
- HVY modifier direction: UNFAVORABLE / NEUTRAL / FAVORABLE (from `pitch_mix.py`)
- Career H2H: if ≥5 PA, show OPS + HR/PA — otherwise suppress this layer

**Recent Trend Layer**
- Last 3 starts: barrel-allowed rate per start, HR allowed Y/N
- Velocity trend: arrow indicator (→ stable, ↑ gaining, ↓ declining)
- Trend window is 3 starts — no rolling-season aggregation here

**Environmental Suppression Layer**
- If pitcher is a ground-ball dominant arm and park has low RF wall: flag interaction
- If wind is blowing in and pitcher generates elevated popup rate: note as compounding suppressor
- If neither interaction applies: suppress this layer entirely — do not show empty

---

## C. SUPPRESSION TIERS

Five suppression tiers map from the suppression score (0–100).

| Tier | Score Range | Meaning |
|------|-------------|---------|
| NONE | 0–19 | No meaningful suppression. Pitcher not a threat to HR confidence. |
| LOW | 20–39 | Minor signal. Note present but deployment confidence unaffected. |
| MODERATE | 40–59 | Notable risk. Operator should review before deploying at full size. |
| HIGH | 60–79 | Strong suppression. Deployment confidence materially reduced. Consider reduced size. |
| LOCKDOWN | 80–100 | Elite suppressor. Deployment against this pitcher has structural risk. Caution strongly indicated. |

---

### NONE (Score 0–19)

**Color Treatment:** No suppression color active. Pitcher information renders in standard muted palette.

**Border Behavior:** No border on suppression card. It renders as an informational section with no visual emphasis.

**Glow Restraint:** No glow. No color accent. Neutral surface.

**Caution Wording:** "No suppression signals active. Pitcher profile does not reduce HR deployment confidence for this matchup."

**Deployment Impact:** Zero impact. Batter's escalation tier carries unmodified.

**Tactical Implication:** Operator may treat batter confidence as stated by engine. No cross-reference needed.

---

### LOW (Score 20–39)

**Color Treatment:** Muted steel-blue accent (`#7A8FA6` at 50% opacity). Applied to suppression tier badge only.

**Border Behavior:** 1px solid steel-blue at 20% opacity on suppression card section border.

**Glow Restraint:** No glow.

**Caution Wording:** "Minor suppression signal present. Pitcher shows marginal risk in one or more areas. Deployment confidence nominally affected."

**Deployment Impact:** Minimal. Operator note only.

**Tactical Implication:** Note the signal. Full size deployment acceptable. Check the specific signal pill to understand which factor is marginal.

---

### MODERATE (Score 40–59)

**Color Treatment:** Amber at 30% opacity (`#F5A623` at 30%). Applied to suppression tier badge and section header rule.

**Border Behavior:** 1px solid amber at 25% opacity on suppression card container.

**Glow Restraint:** No outer glow. Border color only — no spread.

**Caution Wording:** "Moderate suppression detected. Pitcher profile introduces measurable HR risk reduction for this matchup. Review signal detail before deploying at full confidence."

**Deployment Impact:** Operator should treat FIRE picks as STRONG confidence in presence of MODERATE suppression. STRONG picks require review before deployment.

**Tactical Implication:** Not a deployment block. A deployment pause. Review the risk indicator pills. If the primary suppressor directly conflicts with the batter's strength (e.g., elite GB pitcher vs. batter with below-average xSLG on grounders), consider reduced position size.

---

### HIGH (Score 60–79)

**Color Treatment:** Orange-red (`#E87040` at 70% opacity). Applied to badge, section border, and section header text.

**Border Behavior:** 1px solid `#E87040` at 50% opacity on suppression card container. No dashing — solid line signals active caution.

**Glow Restraint:** Micro-glow only: 4px spread `#E87040` at 15% opacity behind card border. Not perceptible without focus.

**Caution Wording:** "High suppression active. Pitcher profile materially reduces HR deployment confidence. Multiple signals compound against this batter. Deployment at reduced size recommended."

**Deployment Impact:** FIRE picks downgrade to WATCH-level confidence in presence of HIGH suppression. STRONG picks are deployment-blocked pending operator override. Operator must explicitly acknowledge suppression before proceeding.

**Tactical Implication:** The deployment panel (when active) must surface the HIGH suppression signal inline — not buried in expanded state. Operator cannot reach the deploy confirmation without seeing the caution.

---

### LOCKDOWN (Score 80–100)

**Color Treatment:** Deep crimson-steel (`#C0392B` at 80% opacity). Applied to badge, border, section header, and primary reason label.

**Border Behavior:** 1px solid `#C0392B` at 70% opacity. Left border emphasized at 3px — directional caution marker.

**Glow Restraint:** 6px spread `#C0392B` at 20% opacity behind left border only. Restrained — present but not alarming.

**Caution Wording:** "LOCKDOWN suppressor. This pitcher's profile presents elite suppression across barrel allowed, put-away rate, and pitch mix match for this handedness. HR deployment against this pitcher carries structural risk regardless of batter tier."

**Deployment Impact:** Regardless of batter escalation tier, LOCKDOWN suppression requires operator override to proceed. No deployment without explicit acknowledgement. The engine does not block — but it requires active confirmation.

**Tactical Implication:** A FIRE batter vs a LOCKDOWN pitcher is not automatically a bad pick. It is a high-risk pick that must be consciously accepted. The engine surfaces both signals. The operator resolves the conflict using judgment. See `escalation_vs_suppression_doctrine.md` for precedence rules.

---

## D. SUPPRESSION SIGNALS

Each active signal appears as a pill in the Risk Indicators Zone. Signals are not mutually exclusive — multiple may fire simultaneously.

### Elite Weak Contact Profile
**Trigger:** Pitcher barrel-allowed rate in bottom 15th percentile (MLB starters, rolling season).  
**Pill Label:** WEAK CONTACT ELITE  
**Pill Color:** `#7A8FA6` steel-blue  
**Weight:** High (15–20 suppression score points)  
**Explanation:** Pitcher consistently generates weak contact, limiting hard-hit outcomes regardless of batter quality.

### Low Barrel Allowed
**Trigger:** Barrel-allowed rate ≤ 4.5% (below league average `LEAGUE_AVG_BARREL_RATE = 0.055`).  
**Pill Label:** LOW BARREL ALLOWED  
**Pill Color:** `#7A8FA6` steel-blue  
**Weight:** High (15–20 points)  
**Explanation:** Batters make contact but not the quality contact required for HR probability.

### Pitch Mix Mismatch
**Trigger:** HVY modifier ≤ 0.88 (UNFAVORABLE threshold).  
**Pill Label:** PITCH MIX MISMATCH  
**Pill Color:** Amber `#F5A623` at 40% opacity  
**Weight:** Moderate (10–15 points)  
**Explanation:** This pitcher's arsenal structurally exploits this batter's contact weaknesses.

### Weather Suppression
**Trigger:** Wind blowing in ≥ 8mph toward home + pitcher GB rate ≥ 50%.  
**Pill Label:** WEATHER SUPPRESSION  
**Pill Color:** Cyan `#00D4FF` at 30% opacity (environmental signal)  
**Weight:** Low-moderate (5–10 points)  
**Explanation:** Environmental conditions compound groundball tendency against HR probability.

### Handedness Suppression
**Trigger:** Same-hand pitcher + batter platoon split showing ≥ 15% ISO reduction vs same side.  
**Pill Label:** HANDEDNESS SUPPRESSOR  
**Pill Color:** `#7A8FA6` steel-blue  
**Weight:** Moderate (10–12 points)  
**Explanation:** Platoon disadvantage reduces expected power output for this batter against this pitcher's arsenal.

### Groundball Dominance
**Trigger:** Pitcher GB rate ≥ 55% (above league threshold).  
**Pill Label:** GB DOMINANT  
**Pill Color:** `#7A8FA6` steel-blue at 60%  
**Weight:** High (15 points)  
**Explanation:** Groundball-dominant pitchers structurally reduce fly ball rate — and therefore HR surface area — for any batter.

### Recent Velocity Spike
**Trigger:** Pitcher average fastball velocity increased ≥ 1.5mph over last 3 starts vs season average.  
**Pill Label:** VELO SPIKE — 3-START  
**Pill Color:** Orange `#E87040` at 50%  
**Weight:** Moderate (8–12 points)  
**Explanation:** Velocity increase typically corresponds to elevated put-away rate and reduced contact quality.

### Elite Put-Away Profile
**Trigger:** K% ≥ 28% + SwStr% ≥ 13% over rolling 30 days.  
**Pill Label:** ELITE PUT-AWAY  
**Pill Color:** `#C0392B` at 50%  
**Weight:** High (15–20 points)  
**Explanation:** Elite strikeout-generating pitchers reduce plate appearances that end in contact, limiting HR surface area per PA.

---

## E. INTERACTION RULES

### Hover Behavior (Desktop)
- Hovering over risk indicator pills reveals tooltip: signal name, threshold breached, current pitcher value, league average comparison
- Tooltip appears after 200ms delay — not instant
- Tooltip dismisses on mouse exit with 100ms fade
- Hover does not trigger any state change — informational only

### Expansion Behavior
- Suppression card renders collapsed to **Identity Zone + Tier Badge + Score + Primary Reason** in default embedded state
- Clicking expands inline to reveal all 7 zones
- Expansion is push-down — never overlay — when embedded in Player Threat Card expanded state
- One suppression card expanded at a time when multiple matchups rendered

### Caution Reveal Hierarchy
Level 1 (collapsed): Tier badge + score + primary reason label  
Level 2 (expanded): Full 7-zone layout  
Level 3 (operator override required at HIGH/LOCKDOWN): Explicit acknowledgement before deployment panel unlocks

### Progressive Disclosure
- Risk indicator pills: show 3 highest-weight signals; remaining behind "+(N) more" toggle
- Environmental suppression layer: rendered only when active environmental interaction exists
- Career H2H layer: rendered only when ≥5 career PA exist between this pitcher and batter
- Recent trend layer: always rendered when pitcher data available

---

## F. RESPONSIVE RULES

### Desktop (≥1280px)
- Suppression card renders as a full-width section below player metrics in EXPANDED state
- All 7 zones visible without scrolling when card is expanded
- Risk indicator pills on single horizontal row (max 5 visible)
- Caution explanation: full 1–3 sentence paragraph

### Tablet (768px–1279px)
- Suppression card renders in single column below player metrics
- Zones: Identity + Score + Risk Indicators + Caution Explanation only (Matchup, Trend, Environmental collapsed behind "Show more" toggle)
- Risk indicator pills wrap to 2 rows if needed

### Mobile (<768px)
- Suppression card renders as bottom-sheet panel triggered from Player Threat Card
- Identity + Tier Badge + Primary Reason visible in trigger row
- Full expansion opens as bottom sheet (not inline push-down)
- Risk indicator pills: 2 pills visible, "+(N) more" for remainder
- Caution explanation: condensed to 1 sentence

---

## G. FORBIDDEN PATTERNS

The following patterns are rejected. They break suppression credibility and the platform's operational tone.

**REJECTED: Giant warning banners**  
Do not render full-width red or orange banners above card sections. Suppression is one input. It does not override all other signals with a banner.

**REJECTED: Sportsbook-style "fade" language**  
Do not write: "FADE THIS PITCHER", "AVOID", "STAY AWAY", "BAD MATCHUP." These are gambling-influencer terms. Use: "suppression active", "caution warranted", "risk signal present."

**REJECTED: Exaggerated danger visuals**  
No skull icons, no ❌ symbols, no crossed-out player names. Suppression is a measured signal, not a death sentence.

**REJECTED: Red flashing alerts**  
No flashing, no blinking, no pulsing on suppression signals. Static color is sufficient. The system communicates through restraint, not alarm.

**REJECTED: Cluttered suppression explanations**  
No paragraph-length technical explanations in the caution layer. One to three sentences maximum. Operators read quickly. If they want depth, expansion reveals it.

**REJECTED: Suppression hidden until expansion**  
MODERATE and above suppression tiers must be visible in the Player Threat Card's STANDARD state — not buried behind expansion. The tier badge and primary reason must surface without requiring a click.

---

## SUPPRESSION VISUAL SUMMARY

| Tier | Score | Badge Color | Border | Glow | Caution Language |
|------|-------|-------------|--------|------|-----------------|
| NONE | 0–19 | Neutral gray | None | None | "No suppression active" |
| LOW | 20–39 | Steel-blue 50% | 1px steel-blue 20% | None | "Minor signal present" |
| MODERATE | 40–59 | Amber 30% | 1px amber 25% | None | "Moderate suppression detected" |
| HIGH | 60–79 | Orange-red 70% | 1px orange-red 50% | 4px micro | "High suppression active" |
| LOCKDOWN | 80–100 | Crimson 80% | 3px left + 1px full crimson 70% | 6px left-only | "LOCKDOWN suppressor" |

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
