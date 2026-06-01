# VISUAL PRIMITIVE STANDARDS
**Owner:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 3/12

Single source of truth for all shared visual primitives. Codex implements each primitive once. No component redefines a primitive already defined here.

---

## 1. THREAT BADGE

**Purpose:** Communicate threat tier at scan speed. Appears on all player threat cards.

```
Shape:     Rounded rectangle (border-radius: 4px)
Position:  Top-right corner of parent card
Size:      Fixed height 24px, width auto-fit to label
Text:      All-caps, bold, white or near-white
Font size: 11–12px
```

**Tier Definitions:**

| Tier | Label | Background | Text Color |
|------|-------|-----------|-----------|
| ELITE | PRIME TARGET | #D97706 (amber) | #FFFFFF |
| HIGH | ELEVATED | #EA580C (orange) | #FFFFFF |
| MEDIUM | WATCH | #CA8A04 (yellow-warm) | #1A1A1A |
| LOW | MONITOR | #6B7280 (cool gray) | #FFFFFF |
| SUPPRESSED | CAUTION | #2563EB (muted blue) | #FFFFFF |

**Rules:**
- One badge per card. No stacked badges.
- Label never wraps. If tier label exceeds 2 words: abbreviate.
- No icon inside badge — label only.
- Padding: 4px vertical, 8px horizontal.

---

## 2. GLOW LANGUAGE

**Purpose:** Reinforce threat tier through border luminosity. Highest-tier cards visually advance, lowest recede.

```
Implementation: CSS box-shadow on card border
Direction:      All sides (no directional glow)
```

**Glow Definitions:**

| Tier | Glow Style | Glow Color | Spread |
|------|-----------|-----------|--------|
| ELITE | `0 0 12px 2px` | `rgba(217, 119, 6, 0.65)` | Strong |
| HIGH | `0 0 8px 1px` | `rgba(234, 88, 12, 0.45)` | Moderate |
| MEDIUM | `0 0 4px 1px` | `rgba(202, 138, 4, 0.25)` | Subtle |
| LOW | None | N/A | None |
| SUPPRESSED | None | N/A | None |

**Rules:**
- Glow is static in compact mode.
- Glow may pulse (2–3s ease-in-out cycle, 0.65→0.35 opacity) for ELITE in expanded mode only.
- Glow never applied to game containers or page-level elements — cards only.
- Glow does not replace border — border + glow are additive.

---

## 3. BORDER HIERARCHY

**Purpose:** Communicate container level through border weight and opacity.

| Level | Component | Border Style | Weight | Opacity |
|-------|-----------|-------------|--------|---------|
| L1 | Player threat card | Solid, tier color | 1px | 70–100% by tier |
| L2 | Game container shell | Solid, neutral | 1px | 40% |
| L3 | Page section dividers | Solid, neutral | 1px | 20% |
| L4 | Sidebar containers | Dashed or subtle solid | 1px | 20% |

**Rules:**
- Border color for L1 matches threat tier color (same palette as badge).
- L2+ borders are always neutral — never tier-colored.
- No double borders. No inset borders.
- Cards in SUPPRESSED state: L1 border = muted blue at 30% opacity.

---

## 4. DENSITY RHYTHM

**Purpose:** Ensure consistent spacing that communicates information grouping without dead whitespace.

```
Card internal padding:    12px all sides
Zone separation:          8px between zones
Metric column gap:        16px between metric cells
Label to value gap:       2px (label directly above value)
Card-to-card gap:         8px in grid
Container internal pad:   16px
```

**Rules:**
- No margin larger than 16px within a card.
- No section with only whitespace and no content.
- Zones with no available data are hidden, not emptied.
- Consistent rhythm: every 4px increment (4, 8, 12, 16, 24).

---

## 5. TACTICAL LABELS

**Purpose:** Short, high-contrast operator-readable labels for status, priority, and context.

**Format:**
```
Style: All-caps, letter-spacing: 0.08em, font-weight: 600
Size:  10–11px
Color: Muted (60–70% opacity of primary text color)
```

**Standard Labels:**

| Label | Context |
|-------|---------|
| HR/PA | Home run count / plate appearances |
| EV AVG | Exit velocity average |
| FB% | Fly ball percentage |
| MATCH | Matchup score |
| CONF | Confidence |
| HOME | Home game indicator |
| ROAD | Away game indicator |
| vs. LHP | Versus left-handed pitcher |
| vs. RHP | Versus right-handed pitcher |
| LAST 7 | Performance in last 7 days |
| SEASON | Full season stat |

**Rules:**
- Labels are always shorter than values.
- Labels never bold — values are bold.
- No sentence-case labels. All-caps or nothing.
- Custom labels must follow same format before being added.

---

## 6. PERCENTILE FORMATTING

**Purpose:** Communicate metric ranking within league context.

```
Format:   "{N}th" or "{N}st" or "{N}rd" — e.g., "94th", "1st", "83rd"
Size:     Slightly smaller than raw value
Color:    Tier-appropriate — high percentile = warm, low = cool/muted
Position: Inline with value, slightly muted, or below value in sub-line
```

**Percentile Color Tiers:**

| Range | Color | Signal |
|-------|-------|--------|
| 90–100 | Amber/gold | Elite |
| 75–89 | Orange-warm | High |
| 50–74 | Neutral white | Average |
| 25–49 | Cool gray | Below average |
| 0–24 | Muted blue | Poor |

**Rules:**
- Percentile always references MLB-wide population unless labeled otherwise.
- Percentile and raw value never compete for prominence — raw value is primary.
- Percentile shown only when it adds context (e.g., EV percentile = useful; PA percentile = not useful).

---

## 7. STATUS PILLS

**Purpose:** Communicate discrete states — game status, player status, data freshness.

```
Shape:    Rounded rectangle (border-radius: 10px — more circular than badge)
Height:   20px
Padding:  3px vertical, 10px horizontal
Text:     All-caps, 10px, bold
```

**Standard Pills:**

| Pill | Background | Text | Context |
|------|-----------|------|---------|
| LIVE | #16A34A (green) | White | Game in progress |
| SCHEDULED | #374151 (dark gray) | #9CA3AF | Game not started |
| FINAL | #1E40AF (dark blue) | #93C5FD | Game complete |
| RAIN DELAY | #7C3AED (purple) | White | Weather hold |
| HR PRONE | #DC2626 (red) | White | Pitcher vulnerability |
| SUPPRESSOR | #1D4ED8 (blue) | White | Pitcher suppresses HRs |
| HIGH HR PARK | #D97706 (amber) | White | Park factor elevation |
| SMALL SAMPLE | #4B5563 (gray) | #D1D5DB | Low PA warning |
| LOW SAMPLE | #4B5563 (gray) | #D1D5DB | Confidence caveat |

**Rules:**
- Pills do not glow.
- Pills do not animate.
- Maximum 2 pills per card zone.
- Pills are read-only — not interactive unless spec explicitly defines click behavior.

---

## 8. ESCALATION INDICATORS

**Purpose:** Surface-level signals that communicate escalation state without requiring badge inspection.

**Types:**

**Border Escalation:** L1 border color + weight communicates tier (see Border Hierarchy).

**Tier Label:** Text label in escalation zone — "PRIME TARGET", "ELEVATED", etc.

**Confidence Bar (optional):**
```
Width: 100% of escalation zone
Height: 3px
Fill: Percentage of confidence (87% confidence = 87% fill)
Color: Matches tier color
Background: Dark neutral
```

**Rules:**
- Confidence bar is supplementary — tier label is always present.
- Do not use traffic light (red/yellow/green) alone — always include label.
- Never show escalation indicator without tier label — indicators are reinforcement, not replacement.

---

## 9. CAUTION AND SUPPRESSION STATES

**Purpose:** Communicate when a player's HR probability is actively suppressed by pitcher, park, or model signal.

**Suppression Visual Treatment:**

```
Card opacity:      Metrics zone at 60% opacity (identity zone remains full)
Border color:      Muted blue (#1D4ED8 at 30%)
Glow:              None
Badge:             "CAUTION" in muted blue
Tier label:        "SUPPRESSED" — cool, not warm color
Card temperature:  Cool (no warm tones in suppressed state)
```

**Caution vs. Suppression:**

| State | Meaning | Visual |
|-------|---------|--------|
| CAUTION | Operator should review before acting | Yellow-warm CAUTION pill in tactical zone |
| SUPPRESSED | Model actively recommends against | Full suppression visual treatment |

**Rules:**
- Suppression does not hide the card — operators must see all players.
- Suppression dims data, not identity — name/team always full opacity.
- Suppressed card cannot have warm glow — any existing glow is cleared.
- CAUTION pill may coexist with any tier — it is independent of threat tier.

---

## IMPLEMENTATION RULES FOR ALL PRIMITIVES

1. Primitives are defined here. They are not redefined inside components.
2. Codex creates one shared file (e.g., `styles/primitives.py` or `components/primitives.py`) that exports all primitive values.
3. Each component imports from that shared file — never hardcodes colors, sizes, or tier logic.
4. If a primitive needs to change: change it here and in the shared file. Every component inherits the change automatically.
5. Do not add new primitives to this document without Claude review.
6. Do not deprecate primitives without confirming no active component references them.
