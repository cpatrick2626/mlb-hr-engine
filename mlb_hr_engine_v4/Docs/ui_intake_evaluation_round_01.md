# UI Intake Evaluation — Round 01
## MLB HR Engine — Claude Step 2/12

**Version:** 1.0  
**Date:** 2026-05-20  
**Phase:** Tactical UI Intake Evaluation & Visual Extraction  
**Status:** Documentation only. No runtime code modified.

---

## Section 1 — Image Scoring

Scored against the 10-dimension framework from Step 1 (`tactical_ui_reference_intake_doctrine.md`).  
Scale: 1=weak, 2=acceptable, 3=strong. Max 30. Approval ≥18. Rejection <12.

---

### IMAGE 1: Main Batters Card.png

**Primary Category:** 05_Card_Systems  
**Secondary Category:** 19_Alerts_Escalation  
**Escalation Relevance:** HIGH

| Dimension                  | Score | Notes |
|----------------------------|-------|-------|
| 1. Tactical Clarity        | 3     | 98 ELITE badge + "DEPLOY" implication immediate. No ambiguity on operator action. |
| 2. HR Intelligence         | 3     | Barrel% (21.4%), exit velo (93.7 mph), xSLG vs handedness (.742 vs LHH), pitch type damage%, pull-side power — all present |
| 3. Scan Speed              | 2     | Player hero image competes with threat score for first attention. Score visible but eye enters via face/jersey first |
| 4. Escalation Readability  | 3     | Gold/amber glow on 98 ELITE badge. Tier color language is unambiguous. Visible from peripheral vision |
| 5. Information Density     | 3     | Every zone working. Six stat clusters, environment panel, Up Next matchup, right sidebar tools — zero wasted space |
| 6. Operational Realism     | 3     | Feels like a real system. Percentile labels, "IMMING" live inning counter, update cadence shown |
| 7. Visual Hierarchy        | 3     | Threat score → HR prob % → Statcast profile → pitch destruction → environment → deployment tools |
| 8. Responsive Usefulness   | 1     | Full desktop layout. Eleven simultaneous panels impossible to preserve below 1024px |
| 9. Danger Signaling        | 2     | "HIGH HR RISK" shown in Up Next panel. Caution state present but not dominant signal in card itself |
| 10. Component Reuse        | 3     | Badge system, percentile label format, HR Threat Score meter, pitch destruction table, power persistency bar, environment tile all transferable |

**Total: 26/30**  
**Status: APPROVED**

**Strongest tactical qualities:**
- Threat score badge is the best escalation signal in the corpus — number + word tier + glow in one element
- Pitch Type Destruction table (damage% by pitch type vs handedness) is a completely novel component
- Percentile label pattern (value + "XXth NILE" subscript) is clean, fast-read, reusable across all stat displays

**Weakest operational qualities:**
- Scan entry point split: hero image draws eye before threat score
- Danger signaling limited to Up Next panel — card itself carries no suppression flag for adverse matchups
- HR Projected (base = 1.28) shown in small text — this is a critical deployment signal buried as secondary

**Reusable systems extracted:**
- `HRThreatBadge`: number + tier word + glow color. Configurable per tier.
- `PercentileStat`: value/unit | "Xth NILE" | tile color. Use for any Statcast metric display.
- `PitchDestructionTable`: pitch type | usage% | damage% | vs L/R. Direct extraction.
- `HREnvironmentTile`: score/10 | condition label | weather sub-row. Direct extraction.
- `PowerPersistencyBar`: rolling period | rate | relative bar fill. Direct extraction.
- `UpNextMatchupPanel`: pitcher face | suppressor signal | HR risk flag. Direct extraction.

**Anti-pattern risks:**
- Player hero image size is high — on lower-resolution or non-elite picks, a hero image this prominent becomes decorative. Must be conditional on tier.
- Too many sub-sections visible simultaneously — on a COLD or WATCH tier batter, this density level would feel noisy. Density must scale with escalation tier.

---

### IMAGE 2: Main Games Page.png

**Primary Category:** 14_Game_View_Layouts  
**Secondary Category:** 01_Command_Center  
**Escalation Relevance:** HIGH

| Dimension                  | Score | Notes |
|----------------------------|-------|-------|
| 1. Tactical Clarity        | 3     | PHI @ BOS matchup state, environment score, both lineup threats visible — operator can assess game in one glance |
| 2. HR Intelligence         | 3     | Per-batter barrel%, hard-hit%, HR rate, flyball% — full power profile per lineup row |
| 3. Scan Speed              | 3     | Game header (team vs team, environment 8.7/10) is top anchor. Both lineup tables load full context without drilling |
| 4. Escalation Readability  | 2     | Row-level color differentiation present but subtle. TOP HR THREAT banner visible but single. Other threats not tiered by row color |
| 5. Information Density     | 3     | Matchup Intel center panel, environment, both lineups, opportunity score, intelligence feed, system status — maximum density |
| 6. Operational Realism     | 3     | Live intelligence feed (1,137 data points), system status (43 systems operational), ops status — feels like a live command center |
| 7. Visual Hierarchy        | 3     | Game header → environment → matchup intel (center) → lineups (L/R) → live feed (bottom) |
| 8. Responsive Usefulness   | 1     | Dual 9-batter lineup tables with 8+ stat columns — fundamentally desktop-only |
| 9. Danger Signaling        | 3     | HIGH HR RISK row flag (red), HIGH OPPORTUNITY score (amber), live alert feed at bottom — three-layer danger system |
| 10. Component Reuse        | 3     | Lineup table component, game matchup header, matchup intel center panel, live intelligence feed bar, opportunity score badge |

**Total: 27/30**  
**Status: APPROVED**

**Strongest tactical qualities:**
- Dual lineup table with per-row HR risk flags is the single most operationally complete component in the corpus
- Matchup Intel center panel (batter advantage %, confidence, 2.15 multiplier) creates a visual decision anchor between the two lineup streams
- Live Intelligence Feed (bottom) is the best status-bar pattern in the corpus — shows scan depth, not just "online"

**Weakest operational qualities:**
- Row escalation coloring is subtle — TOP HR THREAT gets a banner but ranks 2-9 are not visually tiered
- Environment score (8.7/10) competes with matchup intel for prominence — should be a secondary signal to lineup threat, not co-equal
- Pitcher matchup card is small relative to its predictive weight — pitcher HR risk should be a larger signal

**Reusable systems extracted:**
- `GameMatchupHeader`: Team A logo/name @ Team B, record, game time, environment score, weather
- `LineupTable`: batting order | player name | hand | stat columns (barrel/hard-hit/HR/FB%) | HR risk flag
- `MatchupIntelPanel`: edge % | confidence | multiplier | advantage label (BATTER/PITCHER)
- `LiveIntelligenceFeed`: scan depth | last scan timestamp | alert count
- `OpportunityScoreBar`: game count | elite-edge count | top-score | avg projected (multi-game summary)

**Anti-pattern risks:**
- Pitcher matchup cards (Luzardo vs Suarez) are small relative to lineup tables. In the MLB HR Engine, pitcher suppressor is a primary filter signal — must not be relegated to a thumbnail within a batter-dominant layout
- Bottom status bar is excellent but the layout currently treats it as decoration. Must be actionable — clicking a live alert should navigate to the relevant pick

---

### IMAGE 3: Main Head to Head.png

**Primary Category:** 16_Pitch_Mix_Visuals  
**Secondary Category:** 15_Player_Profile  
**Escalation Relevance:** CRITICAL (highest value per deployment decision)

| Dimension                  | Score | Notes |
|----------------------------|-------|-------|
| 1. Tactical Clarity        | 3     | "+18% BATTER ADVANTAGE", S+ tier, EV +280, confidence 91 — operator has deployment signal in 1 second |
| 2. HR Intelligence         | 3     | xSLG by zone grid, pitch type vs batter stats (usage/vSLG/xSLG/ISO/HR%), career H2H OPS, swing stats |
| 3. Scan Speed              | 3     | Strike zone grid is the visual anchor — color gradient immediately communicates hot/cold zones without reading numbers |
| 4. Escalation Readability  | 3     | S+ TIER badge prominent, BATTER ADVANTAGE amber, EV displayed as actionable number |
| 5. Information Density     | 3     | Pitcher side (ERA/WHIP/HR9 + pitch mix table), strike zone center, batter side (AVG/OBP/SLG + hit profile table) — complete matchup picture |
| 6. Operational Realism     | 3     | Career H2H (PA 23, AVG .304, xSLG .550) provides real historical grounding — not synthetic |
| 7. Visual Hierarchy        | 3     | Strike zone center → edge advantage → EV/confidence → pitcher profile (left) → batter profile (right) |
| 8. Responsive Usefulness   | 1     | Three-column layout with equal-width panels requires wide viewport. Collapses to unusable below 1100px |
| 9. Danger Signaling        | 2     | Matchup advantage shown but suppressor risk (if pitcher-favored) not explicitly visualized. No caution state for when batter is disadvantaged |
| 10. Component Reuse        | 3     | Strike zone xSLG grid, pitch mix usage table, career H2H block, tier badge with EV |

**Total: 27/30**  
**Status: APPROVED**

**Strongest tactical qualities:**
- Strike zone xSLG grid is the highest information-to-space ratio component in the entire corpus — a 3×3 color gradient communicates heat map data instantly
- Three-panel architecture (pitcher | matchup center | batter) is the canonical Head-to-Head layout — clean, balanced, operationally complete
- EV displayed as American odds format (+280) creates immediate deployment context — operator can compare to market without mental conversion

**Weakest operational qualities:**
- No suppressor-advantage state modeled — if pitcher had +18% advantage, the layout lacks clear visual language for that inversion
- Career H2H sample (PA 23) is small — the layout does not flag sample size warnings, which is operationally risky
- Pitcher hand/batter hand advantage is present but platoon split signal is not highlighted as a first-class signal

**Reusable systems extracted:**
- `StrikeZoneGrid`: 3×3 or 5×5 grid, color-coded by xSLG value, hover shows exact value. Highest-priority component for Codex extraction.
- `MatchupEdgeBlock`: advantage direction | % | confidence | combined multiplier
- `PitchMixTable`: pitch type | usage% | vs L/R vSLG | xSLG | ISO | HR% — direct extraction
- `CareerH2HBlock`: PA | AVG | xSLG | HR | career OPS — with sample size annotation
- `TierBadgeWithEV`: tier label (S+/A/B/C) | confidence score | EV as odds format

**Anti-pattern risks:**
- The symmetric three-panel layout implies equal importance of pitcher and batter profiles. In MLB HR Engine, batter power profile (barrel, exit velo) outweighs pitcher ERA as a predictive signal — layout must give batter panel slightly more visual weight when batter-advantaged

---

### IMAGE 4: Main Pitcher Card.png

**Primary Category:** 15_Player_Profile  
**Secondary Category:** 19_Alerts_Escalation  
**Escalation Relevance:** HIGH (pitcher is primary context filter in engine)

| Dimension                  | Score | Notes |
|----------------------------|-------|-------|
| 1. Tactical Clarity        | 3     | "86 HIGH THREAT" badge tells operator to discount pitcher-suppressor confidence immediately |
| 2. HR Intelligence         | 3     | HR Suppression %, HR Allowance (season/last 10), Barrel% Allowed, Batted Ball Profile, pitch arsenal |
| 3. Scan Speed              | 2     | Pitcher image (Kershaw pose) occupies ~25% of card area. Threat score is left-column mid-point, not top-left anchor |
| 4. Escalation Readability  | 2     | "HIGH THREAT" badge uses amber color and strong word, but threat score (86) is not as visually dominant as batter card score (98). Pitcher card escalation language feels slightly weaker |
| 5. Information Density     | 3     | ERA/FIP/xFIP/SIERA/WHIP + K%/BB% + Barrel% allowed + batted ball profile + pitch arsenal + recent form + matchup summary |
| 6. Operational Realism     | 3     | Recent form chart (ERA last 5 starts with date axis), matchup summary vs specific opponent, release height annotation |
| 7. Visual Hierarchy        | 3     | Threat score → HR suppression → pitch metrics → arsenal → batted ball → recent form → next batter |
| 8. Responsive Usefulness   | 1     | Multi-panel layout with chart elements — desktop-only |
| 9. Danger Signaling        | 3     | "HIGH THREAT" explicitly framed as danger to picking opposing batters. Next Batter Up panel shows who's most at risk |
| 10. Component Reuse        | 3     | Batted ball donut chart, recent form line chart, pitch arsenal table with velocity/vSLG/xSLG, Next Batter Up panel |

**Total: 26/30**  
**Status: APPROVED**

**Strongest tactical qualities:**
- Batted Ball Profile donut (Ground Ball 42.7% / Fly Ball 36.8% / Line Drive 20.5%) is a compact, high-signal visualization — translates directly to FB% and HR carry risk
- Next Batter Up panel (top 4 upcoming threats vs this pitcher) converts a pitcher card into a deployment prompt — excellent workflow bridge
- Pitching Threat Summary uses a threat score frame (86 = HIGH, 87th Nile) that mirrors the batter threat score vocabulary — consistent escalation language across both card types

**Weakest operational qualities:**
- Pitcher hero image size pulls scan entry away from threat score. Batter card resolves this better with score positioned upper-left.
- HR Suppression stat (16.2%) is framed in small text under a circular meter. For a critical deployment decision, this number needs more weight.
- "MODERATE" environment score (6.3/10) is low contrast with the surrounding panel — weather/park context should be secondary but not invisible

**Reusable systems extracted:**
- `PitcherThreatScore`: circular meter | score number | tier label (HIGH/MODERATE/LOW) | percentile
- `HRSuppressionBlock`: suppression % | season allowance | last-10 allowance | trend indicator
- `BattedBallDonut`: three-segment donut (GB/FB/LD%), pullable to park interaction
- `RecentFormChart`: last-N starts sparkline, ERA/HR9 overlay, date axis
- `PitchArsenalTable`: type | usage% | velocity | vSLG | xSLG (vs L and vs R columns)
- `NextBatterUpPanel`: ordered list of upcoming batters with thumbnail, tier badge, career stats vs pitcher

**Anti-pattern risks:**
- The pitcher card should NOT be symmetric with the batter card in visual weight — pitcher is a context modifier, not a primary deployment decision. Pitcher cards in the MLB HR Engine should have a slightly lower visual "voltage" to reinforce this hierarchy
- Recent form chart is useful but could mislead if using ERA as the headline metric — HR/9 and Barrel% Allowed are stronger predictors and should be primary chart metrics

---

### IMAGE 5: Main Strategy Engine.png

**Primary Category:** 02_Main_Engine  
**Secondary Category:** 01_Command_Center  
**Escalation Relevance:** MEDIUM (aggregate deployment view, not per-pick decision)

| Dimension                  | Score | Notes |
|----------------------------|-------|-------|
| 1. Tactical Clarity        | 2     | Top 5 threats ranked. Strategy type grid visible. But no single clear "deploy this now" signal — more survey than directive |
| 2. HR Intelligence         | 2     | Top-level probabilities (32.7%, 28.4%, etc.) shown. No per-player statcast breakdown — this is aggregate intel layer |
| 3. Scan Speed              | 3     | Ranked threat list (1–5) with probability is the best scan-speed implementation in the corpus — fastest read pattern |
| 4. Escalation Readability  | 2     | Strategy cards have confidence badges (92%, 90%, etc.) but all cards share similar visual weight — no dominant FIRE-tier card |
| 5. Information Density     | 2     | Strategy cards have moderate density. Bottom card row has player faces but confidence % is the only differentiator |
| 6. Operational Realism     | 3     | "08 RUNNING NOW" strategies, 93% confidence build, live alignment check, correlation network count — operationally grounded |
| 7. Visual Hierarchy        | 2     | Hero graphic (batter + explosion) occupies center and dominates. Threat list (left) and environment (right) are secondary. Decorative image overshadows data |
| 8. Responsive Usefulness   | 2     | Strategy card grid is the most mobile-adaptable component in the corpus — could stack into 2-column with manageable loss |
| 9. Danger Signaling        | 1     | Zero suppression, danger, or risk signals. Purely opportunity-framed. No COLD, VOID, or CAUTION states visible anywhere |
| 10. Component Reuse        | 3     | Ranked threat list, strategy card (confidence + player faces + label), quick picks sidebar, environment code panel |

**Total: 22/30**  
**Status: APPROVED (Conditional)**

**Strongest tactical qualities:**
- Ranked threat list (1-5, name + team + probability) is the single fastest scan-speed pattern in the corpus. This exact format should anchor the Main tab header.
- Strategy card architecture (label + confidence % + player cluster) is the most mobile-friendly card pattern in the corpus
- Right sidebar Quick Picks with ELITE COMBO / POWER STACK / TRUE SPOT badges is a strong deployment shortcut panel

**Weakest operational qualities:**
- Center hero graphic (exploding baseball) is pure decoration — zero information value, significant visual weight. This is the most prominent anti-pattern in the corpus.
- No danger signals anywhere — this makes the Strategy Engine view feel like a promotional graphic rather than an operational tool
- All strategy cards carry equal visual weight — 92% confidence (Stars Aligned) looks identical to 87% confidence (Park Monster Parlays). Tier differentiation must be applied.

**Conditional approval — what must change before FINAL_DIRECTION:**
1. Hero graphic must be replaced with actionable content (live HR environment dashboard or live opportunity summary)
2. Strategy cards must receive visual tier differentiation (ELITE badge for top-2 strategies, visual weight reduction for lower-confidence cards)
3. At least one danger state must be represented — even a single "No optimal plays tonight" suppressed state

**Reusable systems extracted (conditional):**
- `RankedThreatList`: rank # | player | team | probability % — simple, fast, direct. Highest scan-speed pattern in corpus.
- `StrategyCard`: strategy name | confidence % | player face cluster | "LIVE" status badge
- `QuickPicksSidebar`: tiered pick shortcuts (ELITE COMBO / POWER STACK / TRUE SPOT) with player faces
- `EnvironmentCodePanel`: wind/temp/humidity/air density as monospaced readout with score badge

---

## Section 2 — Category Classification

| Image                      | Primary Category       | Secondary Category         | Escalation Relevance |
|----------------------------|------------------------|----------------------------|-----------------------|
| Main Batters Card.png      | 05_Card_Systems        | 19_Alerts_Escalation       | HIGH                  |
| Main Games Page.png        | 14_Game_View_Layouts   | 01_Command_Center          | HIGH                  |
| Main Head to Head.png      | 16_Pitch_Mix_Visuals   | 15_Player_Profile          | CRITICAL              |
| Main Pitcher Card.png      | 15_Player_Profile      | 19_Alerts_Escalation       | HIGH                  |
| Main Strategy Engine.png   | 02_Main_Engine         | 01_Command_Center          | MEDIUM                |

No physical files moved. Classification is documentation only.

---

## Section 3 — Design Signal Extraction

### 3.1 Spacing Behavior

**Preserve:**
- Panel-internal spacing uses dense 4px/8px rhythm. Content touches panel edges at 8–12px inset.
- Stat clusters use vertical rhythm: label → value → percentile on 3 stacked micro-lines. No wasted vertical space.
- Section headers ("STATCAST PROFILE", "PITCH ARSENAL") float at panel edge — content begins immediately below.

**Adapt:**
- Panel-to-panel gutter is 4px or less in all images. MLB HR Engine should use 6px minimum for visual separation at high resolution.
- Percentage-based column widths in lineup tables should become fixed minimums on mobile.

**Reject:**
- Any spacing pattern that creates empty horizontal bands between stat clusters. None present in these images — confirm no regression.

---

### 3.2 Typography Hierarchy

**Preserve:**
- Primary score numbers (98, 86, 91) use 48px+ bold numerals — dominant scale tier.
- Tier label words (ELITE, HIGH, S+) use uppercase tracking, ~18–22px — secondary scale tier.
- Stat values use 14–16px medium weight. Percentile labels use 10–12px light uppercase.
- Section headers use 10px uppercase tracking, minimal weight — structural not decorative.

**Adapt:**
- Percentile label convention ("94th NILE" / "99th SILE") should be standardized. MLB HR Engine should use "pXX" or "P-XX" for consistent reading.
- Number sizes in lineup table (barrel %, HR rate) can afford 1px larger for operators at arm's-length from screen.

**Reject:**
- No serif fonts appear in any reference. Serif is not part of this design language.
- No italic text. No mixed weight in the same stat cluster.

---

### 3.3 Glow Behavior

**Preserve:**
- Elite tier: amber/gold glow on badge border + subtle ambient behind score number. Single glow source.
- HIGH tier: cyan/teal glow on active panels, borders. Cooler color temperature = authority not excitement.
- Environment score: green glow (favorable) / amber glow (moderate) / red glow (unfavorable).
- Player action images: ambient glow behind figure, color-matched to team or threat tier.

**Adapt:**
- Glow radius should be constrained to 8–12px spread for badges. Background glow (behind player image) can extend to 40–60px but must fade to surface color, not to black.
- Glow on active panels should pulse only when live data updates. Static glow is texture — animated glow is a signal.

**Reject:**
- No pure neon green glow appears in any reference. This is the correct choice.
- No rainbow or multi-color glow on a single element.
- No full-element color fills for glow — only border and ambient, never solid background color swap.

---

### 3.4 Border Language

**Preserve:**
- Active/elite panels: 1px solid amber/gold with glow halo.
- Standard panels: 1px solid mid-opacity (30–40%) white/cyan — structural boundary, not a signal.
- Section headers: no border on the header itself; panel content below has 1px inner border.
- Lineup table rows: 1px bottom border only. Row hover: thin left-border accent in tier color.

**Adapt:**
- HR risk flag rows in lineup table currently use a full-row color change. MLB HR Engine should use left-border accent (3px amber/red) + subtle row tint — less aggressive, equally readable.

**Reject:**
- Thick borders (>2px) as decorative elements.
- Double borders or nested border boxes.
- Rounded corners >4px on data panels. Cards/deployment elements can have 6px max radius.

---

### 3.5 Tactical Badge Logic

**Preserve:**
- Tier word + color: ELITE (amber), HIGH (amber), S+ (cyan/green), MODERATE (amber), TARGET (red)
- Confidence as number inside badge: "91 CONFIDENCE", "93%"
- EV displayed as American odds format: "+280" — creates betting context immediately
- "LIVE" status micro-badge: small capsule, green fill, white text — appears on active panels

**Adapt:**
- MLB HR Engine badge vocabulary should standardize on: FIRE / STRONG / WATCH / COLD / VOID
- Confidence number should always appear adjacent to or inside tier badge
- EV% badge should appear as: "+XX.X% EV" (not American odds) for model consistency

**Reject:**
- Badges showing stat labels without values ("BARREL" with no number).
- Decorative star/icon badges with no text meaning.
- More than 3 badges visible simultaneously on a single card section.

---

### 3.6 Density Rhythm

**Preserve:**
- Cards have three density zones: HERO (large number/image, max attention) → BODY (dense stat clusters) → TAIL (small supporting context).
- All five images maintain this three-zone rhythm. It maps directly to the MLB HR Engine SCAN → QUALIFY → DEPLOY workflow.
- Lineup tables compress effectively: 9 rows × 8 columns with no visible overflow or wrapping.

**Adapt:**
- HERO zone should scale with tier. FIRE tier = large hero. COLD tier = compressed hero, more body.
- Density should reduce on VOID cards — a scratched player card should have near-empty HERO zone and a single VOID state message.

**Reject:**
- Uniform density across all tier states. Density is a signal system, not a fixed layout.

---

### 3.7 Panel Layering

**Preserve:**
- All images use dark surface (#0A0F1E range) with raised panel surfaces (~15–20% lighter).
- Player images bleed into panel backgrounds with soft edge — no hard rectangular crop.
- Secondary context panels (environment, pitcher next up) use slightly lower luminance surface than primary panels.

**Adapt:**
- MLB HR Engine should define three surface levels: L0 (page bg) | L1 (primary panels) | L2 (secondary context) | L3 (active/alert states). Luminance steps: ~4% between L0 and L1, ~8% between L1 and L3.

**Reject:**
- Pure black (#000000) backgrounds. The references all use near-black with slight blue tone — this prevents eye fatigue during long sessions.
- White or light-mode surfaces.

---

### 3.8 Command Emphasis

**Preserve:**
- Deployment signals (EV %, bet size, confidence score) always appear in a dedicated zone separate from analytical stats. In Batters Card, this is the ELITE COMBO / POWER STACK section. In H2H, it's the EV + tier badge.
- The quick picks sidebar appears in ALL views — it is a persistent deployment shortcut layer. This is correct.

**Adapt:**
- MLB HR Engine should formalize the "deployment zone" as a distinct panel — never mixed with analytical stats.
- Quick picks sidebar should show today's top 3 regardless of which view is active.

**Reject:**
- Deployment signals buried inside dense stat tables.

---

### 3.9 Interaction Assumptions

**Preserve:**
- Expandable depth pattern: compact card → click → full card. Visible in Games Page (batter rows that presumably expand to full card view).
- Pitcher + Batter cards exist as separate views — the H2H view is a third view synthesizing both.
- Right sidebar panel contains quick navigation shortcuts in all views — consistent across all 5 images.

**Adapt:**
- Expand/collapse affordances should be explicit (chevron icon or subtle indicator) — none visible in references but must be present.

**Reject:**
- Any interaction that navigates away from current context to load a new page from scratch. All depth should be in-place expansion.

---

### 3.10 Escalation Flow

**Preserved pattern (consistent across all 5 images):**

```
LIVE CONTEXT (inning, score, environment)
        ↓
THREAT SCORE / TIER BADGE (dominant visual anchor)
        ↓
PRIMARY METRICS (barrel, HR prob, EV)
        ↓
CONTEXT ANALYSIS (pitch mix, park, weather)
        ↓
DEPLOYMENT PROMPT (quick picks, bet size, EV)
```

This five-stage escalation flow is the backbone of the MLB HR Engine visual language.  
Every view must honor this sequence — top to bottom, general to specific, context to action.

---

## Section 6 — FINAL_DIRECTION Candidates

### APPROVED for FINAL_DIRECTION

| Image                    | Rationale |
|--------------------------|-----------|
| Main Batters Card.png    | Highest complete single-player threat card. Badge system, Statcast density, and escalation hierarchy are all extractable standards. |
| Main Games Page.png      | Best game-container command view. Lineup table with per-row risk flags + live intelligence feed = Full Slate anchor. |
| Main Head to Head.png    | Highest tactical efficiency per screen area. Strike zone grid + pitch mix table + EV badge = JIG engine visual standard. |
| Main Pitcher Card.png    | Only pitcher-perspective card in corpus. Batted ball donut + threat score + next batter panel = pitcher context module standard. |

### CONDITIONAL for FINAL_DIRECTION

| Image                       | Condition to clear |
|-----------------------------|-------------------|
| Main Strategy Engine.png    | Remove center hero graphic. Add danger/suppression state to at least one strategy card. Add tier differentiation to strategy cards. |

---

## Section 7 — Operational Consistency

### MAIN Tab (Quantitative Deployment)

- **Structure:** Ranked threat list (top 5, strategy engine format) → individual player threat cards (batter card format)
- **Escalation:** FIRE picks use full batter card density. STRONG picks use compressed card. WATCH/COLD use minimal card.
- **Navigation:** Right sidebar quick picks persistent. Environment score in header.
- **Feel:** Dense, data-forward, every pixel working. Operator arrives with a deployment agenda.

### JIG Tab (Tactical Exploit Confirmation)

- **Structure:** H2H matchup view (head to head format) → strike zone grid center → pitch mix tables bottom
- **Escalation:** Matchup edge badge (batter vs pitcher advantage %) is primary visual anchor. Confidence + EV as secondary.
- **Navigation:** Pitcher select (left) → Batter select (right) → matchup loads center. Same right sidebar.
- **Feel:** Surgical, confirmation-oriented. Operator arrives to verify a pick, not to browse.

### FULL SLATE Tab (Battlefield Command Scanning)

- **Structure:** Game containers stacked (games page format) → within each game, compressed batter rows → expandable to full batter card
- **Escalation:** Game-level environment score first. Per-row HR risk flags. Batch filter by tier.
- **Navigation:** Scroll through games. Each game has expand-to-full-lineup affordance. Right sidebar shows slate summary.
- **Feel:** Wide field scan. Operator reviews entire day. Escalation flags direct attention to high-value games.

### Shared Standards (All Three Views)

- Top navigation bar with live context (inning count, games live, model version, update cadence) — identical in all 5 images, confirmed standard.
- Right sidebar with Player & Game Tools + Quick Picks — present in all 5 images, must be preserved.
- HR Engine logo + "MLB HOME RUN INTELLIGENCE" masthead — consistent brand anchor.
- Dark surface palette, amber/cyan glow language, percentile label format — identical across all views.

---

## Validation Checklist

- [x] No runtime code modified
- [x] No Streamlit files modified
- [x] No app.py modifications
- [x] No execution-path changes
- [x] Documentation only
- [x] All 5 images evaluated
- [x] Scores recorded in `_INTAKE_LOG.md`
- [x] FINAL_DIRECTION candidates identified
- [x] Design signals extracted per dimension

---

*Document end. Claude Step 2/12 evaluation complete. No runtime files modified.*
