# SPEC: Escalation Badge System v1
**Component:** `escalation_badge` (shared)  
**Spec Version:** v1  
**Status:** SPECIFICATION ONLY — awaiting Codex implementation  
**Author:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 4/12 — Escalation Infrastructure & Pitcher Suppression Stabilization  
**Cross-reference:** `escalation_tier_visual_spec.md`, `card_hierarchy_spec.md`

---

## A. BADGE PURPOSE

The escalation badge is the single most scan-critical element in the MLB HR Engine. It must communicate tier at zero reading speed — through color, shape, and weight alone.

### Scan Acceleration
In a Full Slate list with 30+ picks, an operator must locate top-tier picks without reading individual labels. The badge enables this by making FIRE/STRONG visually dominant at any scan distance.

### Escalation Clarity
Every surface where a batter's tier is referenced — card, table, sidebar, ticker, modal — uses the same badge. Consistency builds operator spatial memory. The badge means the same thing everywhere.

### Tactical Prioritization
Badge hierarchy governs operator attention sequencing. FIRE badges pull first. STRONG badges pull second. WATCH, COLD, VOID recede in proportion to their deployment priority.

### Deployment Confidence Visibility
The badge communicates not just tier — it communicates deployment readiness. A FIRE badge signals "deploy with high confidence." A COLD badge signals "deployment suppressed." The operator reads this without label interpretation.

---

## B. STANDARDIZED TIERS

Five tiers. Each tier has exactly one badge treatment. No variation across views, components, or routes.

---

### VOID (T5)

**Tactical Meaning:** Pick is invalid. Player did not start, was scratched, game postponed, or data unavailable. No deployment action possible.

**Typography:**
- Label: "VOID" — 10px, uppercase, white at 25% opacity
- No additional label text

**Icon Allowance:** None.

**Glow Intensity:** None.

**Border Hierarchy:** No border, or 1px dashed white at 10% opacity.

**Density Behavior:** Single flat text label only. No background fill. No capsule shape — flat rectangle or no visible container.

**Confidence Behavior:** No confidence value shown.

**Animation Allowance:** None.

**Background Treatment:** No fill. Transparent on card surface.

**Token Reference:**
```
--badge-void-text: rgba(255, 255, 255, 0.25);
--badge-void-border: rgba(255, 255, 255, 0.10);
```

---

### COLD (T4)

**Tactical Meaning:** Pick is suppressed. Failed one or more engine filters. Do not deploy. Reason is available on expansion.

**Typography:**
- Label: "COLD" — 12px, uppercase, steel-blue `#7A8FA6` at 60% opacity
- Confidence shown only if available — muted, same weight as label

**Icon Allowance:** None. No icon.

**Glow Intensity:** None.

**Border Hierarchy:** 1px dashed, white at 20% opacity. Dashed border = discontinuous = suppressed signal. Critical visual distinction from WATCH.

**Density Behavior:**
- Capsule shape, 18px height
- No fill
- Border: 1px dashed as above

**Confidence Behavior:** Confidence shown in steel-blue at 40% if present. Not emphasized.

**Animation Allowance:** None.

**Background Treatment:** No fill. Badge surface matches card surface.

**Token Reference:**
```
--badge-cold-text: rgba(122, 143, 166, 0.60);
--badge-cold-border: rgba(255, 255, 255, 0.20);
--badge-cold-border-style: dashed;
```

---

### WATCH (T3)

**Tactical Meaning:** Marginal edge. Caution flags present. Not recommended for deployment without operator review. Visible but not prioritized.

**Typography:**
- Label: "WATCH" — 14px, uppercase, white at 60% opacity
- Confidence adjacent: white at 50%, 14px

**Icon Allowance:** Optional: `⚠` symbol prefix at white 40% opacity. Use only in EXPANDED badge size. Not in micro or standard.

**Glow Intensity:** None.

**Border Hierarchy:** 1px solid, white at 40% opacity. Solid border distinguishes WATCH from COLD's dashed border. No halo.

**Density Behavior:**
- Capsule shape, 20px height
- No fill
- Border: 1px solid white at 40%

**Confidence Behavior:** Confidence shown in white at 50%. Smaller than FIRE/STRONG confidence.

**Animation Allowance:** None.

**Background Treatment:** No fill. Badge surface matches card surface.

**Token Reference:**
```
--badge-watch-text: rgba(255, 255, 255, 0.60);
--badge-watch-border: rgba(255, 255, 255, 0.40);
--badge-watch-border-style: solid;
```

---

### STRONG (T2)

**Tactical Meaning:** High-confidence pick. Above-average power profile, positive EV. All filters passed. Deploy with confidence. Second deployment priority after FIRE.

**Typography:**
- Label: "STRONG" — 16px, uppercase, tracking +0.12em, cyan `#00D4FF`
- Confidence adjacent: white bold, 15px

**Icon Allowance:** None. Icon reserved for FIRE tier only.

**Glow Intensity:**
- Badge border glow: 6px blur, `#00D4FF` at 70% opacity, 6px spread
- No inner glow

**Border Hierarchy:**
- 1px solid cyan `#00D4FF` at 60% opacity
- 8px outer halo at 25% opacity — present on standard/expanded badge sizes
- No halo on micro badge

**Density Behavior:**
- Capsule shape, 22px height
- Fill: cyan at 10% opacity
- Border: 1px solid as above

**Confidence Behavior:** Confidence displayed adjacent to label. White bold. Visually prominent.

**Animation Allowance:**
- Live data refresh: 0.2s border opacity pulse (30%→80%→50%)
- No continuous animation

**Background Treatment:** Cyan at 10% opacity fill inside badge capsule.

**Token Reference:**
```
--badge-strong-text: #00D4FF;
--badge-strong-border: rgba(0, 212, 255, 0.60);
--badge-strong-fill: rgba(0, 212, 255, 0.10);
--badge-strong-glow: 0 0 8px 6px rgba(0, 212, 255, 0.70);
```

---

### FIRE (T1)

**Tactical Meaning:** Elite barrel batter in favorable context. All filters passed. EV above threshold. Highest deployment priority. Operator deploys without hesitation.

**Typography:**
- Label: "FIRE" — 18px, uppercase, tracking +0.15em, amber `#F5A623`
- Confidence adjacent: white bold, 16px

**Icon Allowance:** `⚡` lightning icon prefix allowed at T1 only. Used in standard and expanded badge sizes. Never in micro badge.

**Glow Intensity:**
- Badge border glow: 8px blur, `#F5A623` at 90% opacity, 8px spread
- Ambient glow behind score in score context: 40px radial amber at 25% opacity (card context only — not badge-only contexts)

**Border Hierarchy:**
- 1px solid amber `#F5A623`
- 12px outer halo at 40% opacity — standard and expanded sizes
- 3px left border only in micro badge context — no halo at micro

**Density Behavior:**
- Capsule shape, 24px height
- Fill: amber at 15% opacity
- Border: 1px solid amber

**Confidence Behavior:** Confidence displayed adjacent. White bold. Largest confidence display of all tiers.

**Animation Allowance:**
- Initial card load: 1-second slow pulse on badge glow (fade from 0 to 100% intensity, once only)
- Live data refresh: 0.3s border opacity pulse (40%→100%→70%)
- No continuous animation

**Background Treatment:** Amber at 15% opacity fill inside badge capsule.

**Token Reference:**
```
--badge-fire-text: #F5A623;
--badge-fire-border: #F5A623;
--badge-fire-fill: rgba(245, 166, 35, 0.15);
--badge-fire-glow: 0 0 16px 8px rgba(245, 166, 35, 0.90);
--badge-fire-ambient: radial-gradient(40px, rgba(245, 166, 35, 0.25), transparent);
```

---

## C. UNIVERSAL BEHAVIOR RULES

Badges must behave identically regardless of where they appear. An escalation badge in a Full Slate table row must look identical to the same badge in the MAIN tab card or the header ticker.

**Applies uniformly to:**
- MAIN tab — player cards
- JIG tab — matchup context rows
- Full Slate — scrolling game/player list
- Sidebar — quick-pick summary list
- Modals — deployment confirmation and deep-dive overlays
- Tables — Full Slate sortable table view
- Live feed — header threat ticker

**Consistency rule:** If the badge color, border style, fill opacity, or label typography differs between any two views, the implementation is wrong. There is one badge component. There are no view-specific badge overrides.

**Suppression interaction:** When pitcher suppression is active at MODERATE or above, the escalation badge for the batter does not change tier. The suppression card renders alongside — not instead of — the escalation badge. See `escalation_vs_suppression_doctrine.md`.

---

## D. SIZE HIERARCHY

Four badge sizes. Same tier treatment at all sizes — only geometry scales.

### Micro Badge
**Use context:** Table rows, ticker, sidebar compact list, inline text references  
**Dimensions:** Height 16px, padding 4px horizontal  
**Typography:** 10px uppercase label, no confidence number  
**Icon:** Never  
**Glow:** Replaced by left-border accent at 3px in tier color — no spread  
**Border:** 1px solid (FIRE/STRONG), 1px dashed (COLD), none (VOID)

### Standard Badge
**Use context:** Player Threat Card compact state, matchup card header, game card threat reference  
**Dimensions:** Height 20–24px depending on tier (FIRE: 24px, STRONG: 22px, WATCH: 20px, COLD: 18px, VOID: auto)  
**Typography:** Per-tier spec in Section B  
**Icon:** FIRE only — `⚡` at this size  
**Glow:** Full tier glow as specified — restrained  
**Border:** Full capsule border as specified

### Expanded Badge
**Use context:** Player Threat Card STANDARD state score zone, escalation module standalone  
**Dimensions:** Height 32–40px, variable width  
**Typography:** Label + confidence + optional percentile sub-label  
**Icon:** FIRE only — `⚡` at larger scale  
**Glow:** Full tier glow — maximum intensity per spec  
**Border:** Full capsule border + full outer halo

### Hero Badge
**Use context:** Player Threat Card EXPANDED state hero zone, deployment modal header  
**Dimensions:** Height 48px+, full block treatment  
**Typography:** Label at 24px, confidence at 20px, percentile sub-label at 12px  
**Icon:** FIRE only  
**Glow:** Maximum glow — card-level ambient included  
**Border:** Full capsule + halo + ambient card border treatment

---

## E. IMPLEMENTATION RULES FOR CODEX

### Single Shared Component
One `escalation_badge(tier, confidence=None, size="standard")` function.  
Called from every surface that displays an escalation tier.  
No surface defines its own badge logic.

### Tokenized Color System
All tier colors defined in a single token dictionary. No color values hardcoded at call sites.

```python
BADGE_TOKENS = {
    "FIRE":   {"text": "#F5A623", "fill": "rgba(245,166,35,0.15)", "border": "#F5A623",         "glow": "0 0 16px 8px rgba(245,166,35,0.90)", "border_style": "solid"},
    "STRONG": {"text": "#00D4FF", "fill": "rgba(0,212,255,0.10)",  "border": "rgba(0,212,255,0.60)", "glow": "0 0 8px 6px rgba(0,212,255,0.70)",  "border_style": "solid"},
    "WATCH":  {"text": "rgba(255,255,255,0.60)", "fill": "transparent", "border": "rgba(255,255,255,0.40)", "glow": "none", "border_style": "solid"},
    "COLD":   {"text": "rgba(122,143,166,0.60)", "fill": "transparent", "border": "rgba(255,255,255,0.20)", "glow": "none", "border_style": "dashed"},
    "VOID":   {"text": "rgba(255,255,255,0.25)", "fill": "transparent", "border": "rgba(255,255,255,0.10)", "glow": "none", "border_style": "dashed"},
}
```

### Centralized Style Logic
All badge style decisions — size scaling, glow application, border style selection — live inside `escalation_badge()`. Callers pass tier and size. They receive rendered HTML/CSS. They do not make style decisions.

### Avoid Duplicated Badge Render Logic
The following pattern is explicitly forbidden:

```python
# FORBIDDEN — separate badge logic in player_card.py
def render_player_badge(tier): ...

# FORBIDDEN — separate badge logic in game_container.py
def render_game_badge(tier): ...
```

### Avoid Route-Owned Escalation State
Escalation tier is computed by the engine. It is passed as a prop. No UI component determines what tier to show based on local state or URL parameters.

---

## F. MOTION RULES

### Allowed Animations

**Subtle pulse (FIRE only):**
- Occurs once at initial badge render on card load
- Glow fades from 0 to full intensity over 1 second
- Does not repeat. Does not loop.

**Restrained hover glow:**
- FIRE: glow brightens from 90% to 100% opacity on hover
- STRONG: glow brightens from 70% to 90% opacity on hover
- Duration: 0.15s ease-out
- WATCH/COLD/VOID: no hover glow change — border brightens 10%

**Confidence shimmer (FIRE/STRONG only, live data refresh):**
- On live data update: border opacity pulses once (40%→100%→70%)
- Duration: 0.3s (FIRE), 0.2s (STRONG)
- Does not repeat until next data refresh

### Rejected Animations

**REJECTED: Flashing**  
No rapid on/off animation at any frequency. Badge state must be stable between data refreshes.

**REJECTED: Blinking**  
No CSS `blink` or equivalent. Blinking is inaccessible and communicates malfunction, not urgency.

**REJECTED: Casino behavior**  
No spinning, rotating, or multi-color cycling effects. The badge communicates a signal. It does not perform.

**REJECTED: Constant animation**  
Once the load pulse completes, FIRE badges are static. No continuous glow animation. The glow is a property of the badge, not an event.

---

## BADGE CROSS-TIER SUMMARY

| Property | FIRE (T1) | STRONG (T2) | WATCH (T3) | COLD (T4) | VOID (T5) |
|----------|-----------|-------------|------------|-----------|-----------|
| Label color | Amber `#F5A623` | Cyan `#00D4FF` | White 60% | Steel-blue 60% | White 25% |
| Fill | Amber 15% | Cyan 10% | None | None | None |
| Border | 1px solid amber | 1px solid cyan 60% | 1px solid white 40% | 1px dashed white 20% | 1px dashed white 10% |
| Glow | 8px amber 90% | 6px cyan 70% | None | None | None |
| Icon | ⚡ (standard+) | None | ⚠ (expanded only) | None | None |
| Standard height | 24px | 22px | 20px | 18px | auto |
| Confidence display | Bold prominent | Bold | Muted | Muted | None |
| Load animation | 1s glow pulse | Fade-up | Fade | None | None |
| Hover response | Glow +10% | Glow +20% | Border +10% | Border +10% | None |

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
