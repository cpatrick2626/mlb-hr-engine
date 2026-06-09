# MLB HR Engine v4 — UI System Specification

**Version:** 1.0
**Date:** 2026-06-09
**Status:** AUTHORITATIVE
**Scope:** mlb_hr_engine_v4 production UI surfaces
**Sources:** architecture.md, product-spec.md, wiki/doctrine/mobile-architecture-v2.md, wiki/doctrine/app-shell-layout.md, wiki/doctrine/visual-design-doctrine.md, wiki/doctrine/visual-design-tokens.md, wiki/doctrine/tier-vocabulary.md, wiki/doctrine/main-jig-separation.md, FULL_SLATE_UX_DOCTRINE.md, PHASE3_REFINEMENT_DOCTRINE.md, MASTER_TCC_DOCTRINE.md, ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md

---

## 1. UI System Purpose

The MLB HR Engine UI is an **operator-facing decision-support system**, not a consumer sports dashboard. Its sole purpose is to support a single disciplined operator in making MLB HR prop deployment decisions during pre-game windows.

UI success criteria:
- Operator completes full-slate reconnaissance in under 90 seconds (12-game slate)
- Critical and Dangerous escalation cards surface above the fold without operator action
- All deployment decisions are made with full context visible — no hidden signals
- MAIN and JIG intelligence layers remain visually distinct at all times

The UI is never for entertainment, sharing, or public consumption. Every design decision must earn its place by improving operational clarity.

---

## 2. Platform Visual Identity

**Identity statement:** Cinematic Tactical MLB Intelligence

The platform IS:
- Tactical — every element communicates operational signal
- Cinematic — dark, high-contrast, HUD aesthetic
- Predictive — conveys intelligence-in-motion
- Machine-driven — operationally credible, not consumer-facing
- Escalation-focused — visual weight scales with signal strength
- Premium — sparse, composed, not decorated

The platform IS NOT:
- A generic sportsbook UI
- A fantasy dashboard or ESPN-style layout
- Spreadsheet analytics
- Flat SaaS design
- Cartoon cyberpunk or neon-overloaded

**Design principle:** Color, glow, and animation are used only to communicate intelligence escalation. Overuse degrades the signal hierarchy. Every decoration that carries no meaning is a liability.

---

## 3. Production Surface Map

Four independent operational surfaces. No runtime cross-dependency.

| Surface | Entry Point | Runtime | Deployment |
|---------|-------------|---------|------------|
| Streamlit Dashboard | `app.py` | Python / Streamlit | Local operator machine |
| Static Frontend | `frontend/index.html` | Static HTML / JavaScript | Vercel — https://mlb-hr-engine-one.vercel.app |
| FastAPI Service | `api/main.py` | Python / uvicorn | Fly.io (`mlb-hr-api`, region `iad`) |
| CLI Pick Runner | `main.py` | Python | Local / GitHub Actions |

**Frontend disambiguation:**
- `frontend/` (repo root) — **production** static frontend deployed to Vercel. Entry point: `frontend/index.html`.
- `mlb_hr_engine_v4/frontend/` — Next.js design-iteration prototype. Standalone. No Python runtime, Fly.io, or Vercel deployment invokes it as of 2026-06-09.

Do not conflate the two frontend surfaces.

**Session state, auth, and cache are not shared between any surfaces.**

---

## 4. App Shell Layout

The MasterDashboard is the canonical top-level shell. All layout truth derives from the Master Dashboard handoff.

### 4.1 Canonical Shell Zones

| Zone | Component | Role |
|------|-----------|------|
| Top | TopBar (Command Strip) | Branding, date, slate status, data load — fixed, never scrolls away |
| Navigation | Engine-lens nav tabs | Switch between MAIN engine and JIG engine surfaces and lens views |
| Banner | LiveTargets | Live HR threat summary, escalation badges — collapsed by default |
| Center | Stage / Main Viewport | Primary operator action surface — scrollable |
| Right | RightRail / Sidebar | TCC controls, portfolio optimizer, P&L, ops buttons |
| Left/overlay | NavPanel | Navigation and view control |
| Right/secondary | StrategyRail | Strategy and bet-sizing context |
| Bottom | Deployment Tray | FD slip, stake entry, expand/collapse trigger |
| Bottom/feed | Live Intelligence Feed | Steam alerts, lineup confirms — collapsed by default |

### 4.2 Desktop Layout

```
[COMMAND STRIP — full width, fixed, 52px]
[ENGINE NAV TABS — full width, 1 tap per tab]

[MAIN VIEWPORT — scrollable]  [SIDEBAR 280px fixed]
[  Tab content              ] [  TCC controls     ]
[  Card grid / game rows    ] [  Portfolio toggle  ]
                              [  CLV / Ops buttons ]
                              [  P&L mini          ]

[DEPLOYMENT TRAY — sticky bottom, 36px collapsed]
[LIVE FEED — collapsible below tray trigger]
```

### 4.3 Command Strip (Zone 1 — TopBar)

Always fixed. Never scrolled away. Five structural zones left to right:

```
[ZONE 1: PIPELINE]  [ZONE 2: LIVE GAME COUNT]  [ZONE 3: ESCALATION SUMMARY]  [ZONE 4: ENVIRONMENT]  [ZONE 5: SYNC STATE]
```

- **Zone 1:** Engine version + run timestamp. Amber `STALE` label if pipeline >2 hours old.
- **Zone 2:** Game count, TBD pitcher count (amber).
- **Zone 3:** Escalation counts — Critical / Elevated / Active. Zero counts hidden. Tap count → filter slate.
- **Zone 4:** Active environmental threats only. Suppressed when all neutral.
- **Zone 5:** `Synced Xm ago`. Amber on failure. No "Conditions nominal" filler.

Contents left to right: logo/name-mark · slate date + game count · status pill · auto-refresh toggle · data load button · API key indicator.

Strip heights: 52px desktop, 60px mobile.

---

## 5. Claude Design Mobile Doctrine

**Authority:** `wiki/doctrine/mobile-architecture-v2.md` — this is the canonical mobile doctrine source.

Mobile is a **disciplined reduction** of the desktop command center, not a separate product. Desktop is primary. Mobile is a degraded-access mode.

### 5.1 Core Mobile Rules (non-negotiable)

1. Command strip never scrolls. Fixed. Always visible. Touch targets ≥44px.
2. Engine navigation is always one-tap. Horizontal scroll strip. No hamburger. No nested menus for primary nav.
3. Single column always on mobile. Cards stack vertically, each self-contained.
4. Intelligence density over whitespace. Collapse secondary content, never remove intelligence.
5. Deployment tray expands full-screen on mobile. No partial-height blocking.
6. Suppression (Zone 3 of deployment panel) is never hidden at any viewport.
7. MAIN/JIG identity survives at all breakpoints — engine colors, separate score columns, separate pick lists.
8. No auto-collapsing warnings. Caution states remain visible until operator acts.
9. No sportsbook visual patterns — no gradient fills, large rounded CTAs, or dollar-sign labels.

### 5.2 Mobile Layout

```
[COMMAND STRIP — fixed, full-width, 60px]
[ENGINE NAV TABS — horizontal scroll strip]

[MAIN VIEWPORT — single column, full-width, scrollable]
[  Active tab content renders top to bottom           ]
[  Card stacks vertically, each self-contained        ]

[DEPLOYMENT TRAY TRIGGER — 36px sticky bottom strip]
  [Tray expanded = full-screen overlay]
```

### 5.3 Mobile Workflow Navigation

| Workflow | Mobile Navigation |
|----------|-------------------|
| MAIN: SCAN → QUALIFY → DEPLOY | TODAY'S PICKS tab → vertical card scroll → Deployment Tray (full-screen) |
| JIG: MATCHUP → CONFIRM → EXPLOIT | JIG tab → HVY cards scroll → Deployment Tray (full-screen) |
| FULL SLATE: SCAN FIELD → ISOLATE DANGER | FULL SLATE tab → single-column game rows |
| DEPLOYMENT: QUALIFY → DEPLOY → TRACK | Card → Tray overlay → Performance tab |

Deployment Tray always reachable without tab switch.

---

## 6. Navigation System

### 6.1 Navigation Model

Navigation is **engine → lens**. Top-level switch: MAIN engine vs JIG engine. Within each engine: lens views.

Tab order is doctrine-locked:

```
TODAY'S PICKS | JIG | FULL SLATE | PERFORMANCE | ADVANCED
```

- `TODAY'S PICKS` = MAIN engine (EV/Edge ranked, Statcast-calibrated)
- `JIG` = Tactical engine (HVY modifier, pitch mix, pitcher vulnerability)
- `FULL SLATE` = Battlefield scan layer (game-organized, all players)
- `PERFORMANCE` = P&L, CLV, calibration
- `ADVANCED` = Strategies, portfolio, ops tools

Tab count badges show live counts from current slate.

### 6.2 Engine Identity Colors (doctrine-locked)

| Engine | Color | Hex |
|--------|-------|-----|
| MAIN | Red | `#ff3344` |
| JIG | Cyan | `#00d9ff` |

Do not swap. Do not mute. Do not blend. Engine identity colors communicate intelligence layer at a glance. Loss of identity at any viewport is a doctrine violation.

### 6.3 Engine-Lens Navigation is a Closed Surface

Engine-lens navigation routing is protected per `PHASE3_REFINEMENT_DOCTRINE.md`. Do not modify without explicit operator authorization.

---

## 7. MAIN Lens Layout

### 7.1 Workflow: SCAN → QUALIFY → DEPLOY

**SCAN:** Full Slate tab → All Players mode. All batters across all games, batting order within each game. TCC filters highlight but do not remove. Purpose: situational awareness.

**QUALIFY:** TCC filter controls narrow the pool. Two filter layers:
- Profile gate: raw Statcast thresholds (Barrel, HH, xSLG, ISO, Pull Air, HR Window)
- Market gate: EV%, Edge%, Model Probability

Picks ranked by composite score: `score = EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`

**DEPLOY:** Operator constructs FD slip. Sequential review per pick. Four non-skippable checkpoints. `pick_tracker.csv` write only at Checkpoint 4.

### 7.2 MAIN Presets (from `filter_controls.py`)

| Preset | Parameters |
|--------|-----------|
| `Operational` | No batter-profile floors; EV/Edge gates qualify (default) |
| `Selective` | Barrel ≥ 5%, HH ≥ 35% |
| `Elite Only` | Barrel ≥ 8%, HH ≥ 40%, EV ≥ 2%, Edge ≥ 1.5% |

### 7.3 MAIN Signal Display Priority

Reading order matches betting decision order:
1. Market signals (EV, EDGE, ODDS) — the bet viability question
2. Quality signals (MDL, BRL, tier badge) — the confidence question
3. Context signals (HVY, weather, park) — the situational question

Do not reorder for visual aesthetics.

### 7.4 Card Anatomy (established — do not deviate)

```
[top accent hairline — grade color, 0.55-0.60 opacity]
[rank badge / player name]
[game urgency countdown / badges: STEAM / OPT / barrel tier]
[PRIMARY stat pills: MDL / EV / EDGE — 13-14px, bg #0c0c22, label #4a4a70]
[SECONDARY stat pills: BRL / ENV — 10-12px, bg #0a0a18]
[border-right separator on EDGE pill]
[HVY bar at bottom — JIG context only]
[weather fragment — only when |wf-1.0| >= 0.04]
```

---

## 8. JIG Lens Layout

### 8.1 Workflow: MATCHUP → CONFIRM → EXPLOIT

**MATCHUP:** Full universe scan with `All Tactical` preset. Identify pitcher arsenal vulnerabilities and HVY pitch-mix modifier distribution.

**CONFIRM:** Validate environmental and handedness edges for top targets. Check pitcher lineup confirmation, weather, park factor, handedness split.

**EXPLOIT:** Stack confirmed JIG signals. Aggressive posture: stricter matchup thresholds, higher positional concentration acceptable when signals converge.

### 8.2 JIG Presets

| Preset | Parameters |
|--------|-----------|
| `All Tactical` | Full universe, broad matchup exploration (default) |
| `Selective` | Barrel ≥ 5%, modifier ≥ 100%; neutrals filtered out |
| `Matchup+` | Barrel ≥ 6%, modifier ≥ 110%, HVY ≥ 40; elite exploit only |

### 8.3 JIG-Specific Display Rules

- Picks ranked by HVY modifier descending. JIG scoring is not EV-driven.
- HVY pitch-mix modifier is **display-only**. Range [0.70, 1.40]. Must be labeled "Tactical Signal" — never implied to be a probability.
- HVY modifier must never appear in MAIN cards at any breakpoint.
- JIG cards never display EV% or Edge% as primary signals.
- Cards labeled with engine identity (JIG / Cyan) at all viewport sizes.

---

## 9. Full Slate Intelligence Matrix

### 9.1 Purpose

Full Slate is the **battlefield scan layer** — complete game-day universe visibility before lineup confirmation. Not a pick list. A situational awareness surface.

Operator scan target: full-slate reconnaissance in under 90 seconds for a 12-game slate.

### 9.2 Three Modes

| Mode | Behavior |
|------|---------|
| All Players | All batters shown game-organized, batting order within game. TCC filters highlight, not remove |
| Qualified | TCC-passing batters only |
| Elite Targets | Highest-tier picks only |

Mode selector placement: above content, below tab. Label: `View: All Players | Qualified | Elite Targets`.

### 9.3 Full Slate Operator Scan Sequence

```
[COMMAND STRIP]         ← Tier 1: Situational awareness in <1 second
    ↓
[GAME COUNT / STATUS]   ← Tier 2: Slate geometry
    ↓
[ESCALATED GAME CARDS]  ← Tier 3: Danger first (Critical → Dangerous → Elevated)
    ↓
[ACTIVE GAME CARDS]     ← Tier 4: Qualified picks, no escalation
    ↓
[QUIET GAME CARDS]      ← Tier 5: No actionable plays — compressed, skippable
```

### 9.4 Full Slate Escalation Card Order

A game card's escalation level = highest-escalation player within that game. Critical cards pin to top of slate regardless of game order. Quiet cards sink to bottom.

### 9.5 Game Card Information Priority

```
Priority 1: Game identity      — Teams, Time, Escalation state
Priority 2: Pitcher danger     — Starting pitcher, pitcher_factor, fatigue, pitch profile
Priority 3: Top batter(s)      — Best 1-2 qualifying batters, EV%, rank
Priority 4: Environmental risk — Park factor (extreme only), weather (threat only)
Priority 5: Market context     — Best odds, implied probability delta
Priority 6: Expansion handle   — "See all X batters / pitcher detail / arsenal"
```

Priority 1–3 visible in collapsed state. Priority 4–6 on single-tap expand.

### 9.6 Environmental Visibility Rules

Environmental signals suppressed when neutral. Active triggers:
- Park factor ≥1.08 → `HITTER PARK` badge (green)
- Park factor ≤0.93 → `PITCHER PARK` badge (red-muted)
- Wind ≥8mph toward CF → `WIND: Xmph IN` (amber)
- Wind ≥8mph away from CF → `WIND: Xmph OUT` (green)
- Temp ≤45°F → `COLD: 41°F` (blue-muted)
- Dome → render nothing

Never show "Neutral environment." Suppression of neutral signals is a feature.

### 9.7 Full Slate Source Ownership

**Protected fix — do not regress:**
- MAIN Full Slate reads from MAIN-scored data source
- JIG Full Slate reads from JIG-scored data source
- File: `frontend/assets/js/full-slate-matrix.js`
- Commit: confirmed operational as of 2026-06-08
- Mobile layout must not collapse the engine source branch

---

## 10. Top Targets

### 10.1 Source Ownership (protected)

**JIG Top Targets source fix — do not regress:**
- File: `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js`, lines 145–146
- Fix: JIG Top Targets reads from `jigRows`. MAIN Top Targets reads from `mainRows`. ELITE/EDGE tier filter applies to both. No cross-engine fallback.
- Commit: `9962d27`
- Any mobile-responsive refactor of Top Targets must preserve this source branch separation.

### 10.2 Display Rules

- MAIN Top Targets shows picks ranked by composite score (`EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`)
- JIG Top Targets shows picks ranked by HVY modifier descending
- No merged list — engine identity is always labeled
- ELITE / EDGE tier filter: applies to both surfaces independently

---

## 11. JIG Builder

### 11.1 Source Ownership (protected)

JIG Builder reads JIG-scored rows. MAIN surfaces read MAIN-scored rows. No shared data path for "simplicity." This rule applies to mobile-responsive refactors.

### 11.2 JIG Builder Purpose

Phase A: surface JIG-scored batters organized by matchup quality and HVY signal. All-in-one tactical view combining:
- HVY pitch-mix modifier distribution
- Arsenal exploitation slots
- Handedness edge summary
- Environmental signal for each game

Phase B: game-command module + tactical tag system (deferred — per `PHASE3_REFINEMENT_DOCTRINE.md` deferred queue item 2).

---

## 12. Tactical Command Center

### 12.1 TCC Purpose

TCC is the **single operational control layer** shared across all engines.

```
TCC: ORCHESTRATES
Engines: CALCULATE
```

TCC does NOT compute, score, or calculate. It exposes:
- Raw threshold filters (what qualifies)
- Tactical posture controls (how aggressive)
- Visibility controls (what is shown)
- Engine scope governance (which engine is affected)

### 12.2 Canonical Filter Vocabulary

| Filter Key | Display Label | Units | Scope |
|---|---|---|---|
| `min_barrel` | Barrel % | % (0–20) | All engines |
| `min_hh` | Hard Hit % | % (0–100) | All engines |
| `min_xslg` | xSLG | decimal (0–4.0) | All engines |
| `min_iso` | ISO | decimal (0–0.400) | All engines |
| `min_pull_air` | Pull Air % | % (0–100) | All engines |
| `min_hr_window` | HR Window | % (0–30) | All engines |
| `min_ev` | EV % | % (0–15) | MAIN + Deployment only |
| `min_edge` | Edge % | % (0–15) | MAIN + Deployment only |
| `min_conf` | Confidence | % (0–100) | MAIN + Deployment only |
| `min_model_prob` | Model Prob | % (0–30) | MAIN + Deployment only |
| `min_matchup_pct` | Matchup Modifier | % (70–140) | JIG + Full Slate only |
| `min_hvy_score` | HVY Score | integer (0–100) | JIG + Full Slate only |

### 12.3 Engine Key Namespacing

| Engine | Key Prefix | Example |
|--------|-----------|---------|
| MAIN | `tac_` | `tac_min_barrel` |
| JIG | `jig_tac_` | `jig_tac_min_barrel` |
| Full Slate | `fs_tac_` | `fs_tac_min_barrel` |
| Deployment | `dep_tac_` | `dep_tac_min_barrel` |

Cross-key reads are a contamination violation. MAIN reads only `tac_*`. JIG reads only `jig_tac_*`.

### 12.4 Filter Effect by Engine

| Filter | MAIN | JIG | Full Slate | Deployment |
|---|---|---|---|---|
| Barrel / HH / xSLG / ISO | narrows pool | narrows pool | highlights only | narrows pool |
| EV % / Edge % / Model Prob | narrows pool | NOT APPLICABLE | NOT APPLICABLE | narrows pool |
| Matchup % / HVY Score | Matchup Edge tab only | narrows pool | highlights only | NOT APPLICABLE |

"highlights only" = Full Slate All Players shows all batters; filters change row color/rank, not visibility.

### 12.5 TCC Implementation File

`filter_controls.py` is the single implementation file for all TCC widget rendering. No TCC logic lives outside it.

---

## 13. Right Rail / Strategy Rail

### 13.1 Sidebar (RightRail) Contents

Operational controls only. Not an analytics panel. Display order:

1. API key input + validation status
2. Auto-refresh toggle + countdown
3. Load data button + last-load timestamp
4. Slate status pill (CONFIRMED / MIXED / PROJECTED)
5. Portfolio Optimizer toggle + preset selector
6. Capture Closing Lines (CLV)
7. Update Yesterday's Results / Settle Yesterday
8. P&L summary (cached 5 min, shown only when n_settled > 0)
9. Coverage expander

### 13.2 Sidebar Authority Levels

**Level 1 — Platform controls** (always visible, always functional):
- API key input, Load data button, Auto-refresh toggle

**Level 2 — Session intelligence** (visible after data loads):
- Optimizer toggle + preset, CLV Capture, Slate status pill

**Level 3 — Retrospective tracking** (lower urgency):
- Settle Yesterday, P&L summary, Coverage expander

Level 1 → 2 → 3 top to bottom. No exceptions.

### 13.3 Sidebar Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| Desktop ≥1280px | 280px fixed, always visible |
| Laptop | 240px fixed |
| Tablet 768px–1279px | Collapsible drawer, toggle at right edge |
| Mobile <768px | Hidden by default, accessible via drawer icon in Command Strip |

### 13.4 Sidebar Rules

- Labels use plain operational English. No jargon. No marketing language.
- Every button triggering a background operation shows a spinner or status message. No silent executions.
- Error states: categorized error only (Odds API key invalid / MLB connectivity / generic). Never Python exception text.
- Do not put analytics content (calibration drift, signal rankings) in the sidebar.
- Do not put filter controls in the sidebar (they belong in TCC).

---

## 14. Live Target Banner

### 14.1 Purpose

The LiveTargets banner surfaces the highest-conviction current HR threats above the main content area. Communicates:
- Active escalation count (Critical / Dangerous / Elevated)
- Pipeline freshness
- Active environmental threats

Collapsed by default. One-tap expand.

### 14.2 Tactical Notifications (Command Strip)

**Notification types:**
- Line movement: `↑ Devers line moved +20 pts (sharp side)`
- Lineup change: `⚡ Juan Soto scratched — BOS lineup pending`
- Pitcher change: `⚠ Cole scratched — TBD pitcher for NYY`
- Weather escalation: `🌬 Wind 14mph OUT at Fenway — recalculate`

**Rules:**
- Maximum 2 notifications visible at once
- Dismissible (single-tap ×)
- 3+ notifications → `2 alerts +` → tap opens notification drawer
- No auto-dismiss — these are operational signals
- No post-3-second animations

**Priority queue:**
```
P1: Lineup scratches (pitcher or top qualifier)
P2: Significant line movement on qualified plays
P3: Weather changes affecting qualified plays
P4: Pipeline staleness beyond threshold
P5: Sync failure
```

---

## 15. Card System

### 15.1 Card Types

Four card types share a fixed anatomy (established per `PHASE3_REFINEMENT_DOCTRINE.md`):

```
[top accent hairline — grade color, 0.55-0.60 opacity]
[rank badge / player name]
[game urgency countdown / badges: STEAM / OPT / barrel tier]
[PRIMARY stat pills: MDL / EV / EDGE — 13-14px, bg #0c0c22, label #4a4a70]
[SECONDARY stat pills: BRL / ENV — 10-12px, bg #0a0a18]
[border-right separator on EDGE pill]
[HVY bar at bottom — JIG context only]
[weather fragment — only when |wf-1.0| >= 0.04]
```

### 15.2 Collapse / Expand Default by Escalation Level

| Escalation | Default State |
|-----------|--------------|
| QUIET | Collapsed (header only) |
| ACTIVE | Collapsed (header + pitcher + top 1 batter) |
| ELEVATED | Expanded (all Priority 1–4 visible) |
| DANGEROUS | Expanded + deployment zone visible |
| CRITICAL | Pinned + fully open + deployment zone |

### 15.3 Deployable Batter Indicator

The word "DEPLOYABLE" is never shown. Instead: thin vertical colored bar (left margin, matching escalation color) on rows that pass all 7 filters. Non-qualified batters: muted contrast, no indicator bar.

### 15.4 Card Signal Display — Label Compression Standards

| Verbose (avoid) | Compressed (use) |
|---|---|
| "Expected Value Percentage" | `EV%` |
| "Market No-Vig Probability" | `Mkt%` |
| "Composite Confidence Score" | `Conf` |
| "Batter Lineup Position" | `Spot` |
| "Quarter-Kelly Bet Size" | `Bet $` |
| "Pitcher Danger Factor" | `Ptch` |
| "Park Home Run Factor" | `Park` |
| "Barrel Percentage" | `Brl%` |

Labels are dim — values are bright.

### 15.5 Suppression Rules

| Field | Show condition |
|---|---|
| `park_factor` | Only if ≤0.93 or ≥1.08 |
| `weather_factor` | Only if ≤0.92 or ≥1.08 |
| `pitcher_factor` label | Never "NEUTRAL"; show HITTABLE or DANGER only |
| `lineup_spot` | Only if ≤5 |
| `pitcher_fatigue` | Only if short-rest (≤4 days) |
| `market_no_vig_prob` | Only in Game Detail, not on card |
| `soft_flags` | Only in expanded state |
| `HVY modifier` | Only in Arsenal view — never on collapsed card |
| `correlation ρ` | Only when deploying 2+ picks from same lineup |

### 15.6 Degraded State Card Behavior

| State | Card Behavior |
|-------|-------------|
| No odds | Card renders muted (`opacity: 0.6`). ODDS/EV/EDGE pills show "—". `no odds` badge in gray. Card not hidden. |
| No lineup | Urgency shows "🔵 PROJECTED" in blue. Platoon fields labeled estimated. Card not hidden. |
| No Statcast | Power badge shows "BLENDED" or "PRIOR" in amber. |
| Prior-year pitch data | Pitcher label shows "(PRIOR YEAR)" |
| No pitch context | Pitch mix expander shows "No pitch data available for this matchup." No infinite spinner. |

**Hard rules:**
- Never remove cards from display solely due to missing one data source
- Never show Python exception text
- Never show "None" or "nan" as a displayed value — coerce to "—"

---

## 16. Tier / Badge System

Three distinct tier vocabularies. They apply to different surfaces. Do not merge or cross-apply.

### 16.1 Vocabulary 1 — Deployment / Data Tiers

Used by: MAIN model scoring output, pick ranking, operator dashboard leaderboard.

| Tier | Meaning |
|------|---------|
| APEX | Highest model confidence, strongest EV |
| ELITE | Very high model confidence |
| EDGE | Above-threshold model confidence |
| SIGNAL | Moderate model confidence, reportable |
| WATCH | Below deployment threshold, monitor only |
| COLD | No meaningful signal |

These tiers reflect model probability and EV output from `pipeline.py` and `config.py`.

### 16.2 Vocabulary 2 — Full Slate Escalation States

Used by: Full Slate Matrix game-card escalation hierarchy (visual escalation, not pick ranking).

| State | Meaning | Escalation Threshold |
|-------|---------|---------------------|
| QUIET | No threat | Below all thresholds |
| ACTIVE | Qualified picks exist | EV filter passed |
| ELEVATED | Strong play | EV ≥15% OR Edge ≥8% OR Barrel ≥10% |
| DANGEROUS | High conviction | EV ≥20% AND Edge ≥8% AND Barrel ≥10% |
| CRITICAL | Max convergence | EV ≥25% + Edge ≥12% + Barrel ≥12% + favorable env |

These states reflect visual escalation within Full Slate. Not pick ranking.

### 16.3 Vocabulary 3 — Prototype Card Tiers

Used by: `mlb_hr_engine_v4/frontend/` prototype only. CRITICAL / HIGH / MODERATE / LOW. Not production scoring tiers. Do not promote without operator-authorized mapping.

### 16.4 Grade Labels (per `PHASE3_REFINEMENT_DOCTRINE.md`)

| Tier | Label | When | Color |
|---|---|---|---|
| S | GOAT / ELITE MISMATCH | barrel≥12% or HVY=elite | `#f59e0b` amber |
| A | ELITE / FAVORABLE | barrel 10-12% or HVY=favorable | `#818cf8` violet |
| B | SOLID / NEUTRAL | barrel 8-10% | `#4ade80` green |
| C | CONTACT / UNFAVORABLE | barrel 5-8% | `#60a5fa` blue |
| D | — / AVOID | barrel<5% | `#ef4444` red |

JIG and Matchup Edge grade labels must read "MATCHUP: [LABEL]" to prevent confusion with QUANT tier.

### 16.5 Badge Restraint

| Card State | Max Badges |
|---|---|
| Collapsed (Quiet) | 0 |
| Collapsed (Active) | 1 (escalation level only) |
| Collapsed (Elevated) | 2 (escalation + one signal) |
| Expanded | 3 (escalation + barrel tier + one environmental) |
| Deployment briefing | Unlimited within deployment zone |

Badges never used: "HOT", emoji indicators, animated count badges, blinking indicators.

---

## 17. Color System

**Authority:** `wiki/doctrine/visual-design-tokens.md` (HR_Engine_Design_System-handoff, 2026-05-26)

### 17.1 Core Color Tokens

```css
/* Engine identity */
--red-500:   #ff3344   /* MAIN engine identity / danger signal */
--red-300:   #ff8a93   /* medium red */
--red-glow:  rgba(255,51,68,0.55)
--cyan-500:  #00d9ff   /* JIG engine identity / neutral/info */

/* Signal colors */
--green-500: #1aff66   /* advantage / live / hit — barrel/hard-hit quality ONLY */
--green-300: #6dffae
--green-glow: rgba(26,255,102,0.55)
--blue-500:  #3b6fff   /* signal tier */
--amber-500: #ffb020   /* watch / warning */

/* Surface colors */
--bg-void:     #04070a  /* page background */
--bg-base:     #0a1014  /* primary panel */
--bg-raised:   #0e1519  /* raised card */
--bg-elevated: #131b21  /* hover/chip */

/* Text colors */
--fg-1: #f1f5f3  /* primary — player names */
--fg-2: #b8c2c0  /* secondary — labels */
--fg-3: #6b7872  /* tertiary — captions */
```

### 17.2 Escalation Color Tokens

```css
--escalation-quiet:     #3a3a3a   /* neutral gray */
--escalation-active:    #4a7fa5   /* steel blue */
--escalation-elevated:  #c8a035   /* tactical amber */
--escalation-dangerous: #b84040   /* tactical red — muted */
--escalation-critical:  #8a0000   /* deep red — border ring only */

--surface-quiet:        #141414
--surface-active:       #161820
--surface-elevated:     #1e1a0e
--surface-dangerous:    #1c0e0e
--surface-critical:     #1a0808
```

### 17.3 Heatmap Ramp

```css
--heat-cold: #2a0a10   /* pitcher favored */
--heat-cool: #6a1622
--heat-mid:  #2a1e1a   /* neutral */
--heat-warm: #0e3a20
--heat-hot:  #14c451   /* batter favored */
```

### 17.4 Color Rules

- `#1aff66` (green-500) is **exclusively** for barrel/hard-hit quality signals. Never used for action CTAs or "deploy" buttons.
- Warning states: amber only (`#c8a035`), never orange.
- Error states: tactical red (`#b84040`), never bright red.
- Maximum 3 simultaneous accent colors in any single card.
- No gradient fills on card surfaces.
- No neon colors beyond the canonical token set.

---

## 18. Typography System

**Authority:** `wiki/doctrine/visual-design-tokens.md`

### 18.1 Font Stack

| Use | Font | Spec |
|-----|------|------|
| Display / headers | Barlow Condensed | 800 weight, uppercase, tracking 0.08em |
| Stats / numbers | JetBrains Mono | tabular-nums |
| Body / labels | Barlow | variable weight |

### 18.2 Typography Budget (per `PHASE3_REFINEMENT_DOCTRINE.md`)

| Element | Size | Weight | Color |
|---|---|---|---|
| Player name | 14-15px | 700 | `#e0e0f0` |
| Primary stat label | 8-9px | 400 | `#4a4a70` |
| Primary stat value | 13-14px | 700 | white / tier color |
| Secondary stat label | 7-8px | 400 | `#444`–`#555` |
| Secondary stat value | 11-12px | 600 | `#aaa` |
| Micro labels | 7-9px | 400 | `#555`–`#666` |

Floor: 7px for any visible label. Ceiling: 15px for stat values. No more than three type sizes in any single card.

### 18.3 Tier Pill Spec

```
Style: inset 0 0 0 1.5px rgba(color, 0.6)
Background: rgba(8,12,16,0.6)
Font: Barlow Condensed 800, 12px, uppercase, tracking 0.12em
```

### 18.4 Typography Rules

- Monospace / tabular figures for all stat columns
- Hierarchy by weight and size, not decoration
- No oversized headers that waste vertical space
- Labels are dim — values are bright. Operator reads values, not labels.

---

## 19. Responsive / Mobile Behavior

### 19.1 Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| Desktop ≥1280px | Sidebar 280px fixed, always visible |
| Laptop | Sidebar 240px fixed |
| Tablet 768px–1279px | Sidebar collapsible drawer |
| Mobile <768px | Sidebar hidden by default, drawer icon in Command Strip |

### 19.2 Progressive Disclosure (mobile-first collapse order)

Priority order — what collapses first as viewport shrinks:
1. Right sidebar → drawer (user toggle)
2. Live Intelligence Feed → collapsed by default (one-tap, last 5 steam alerts)
3. Deployment Tray → collapsed by default (36px trigger)
4. Card secondary stat rows → show on tap
5. Pitch Mix expanders → collapsed, lazy-load gated
6. Full Slate compact rows → unchanged (already minimal)

### 19.3 Deployment Tray

| Breakpoint | Collapsed | Expanded |
|------------|-----------|---------|
| Desktop | 36px sticky strip | Slides up 240px max |
| Mobile | 36px sticky strip | Full-screen modal overlay |

Main viewport has 36px bottom margin so tray trigger never obscures content.

### 19.4 Card Layout

- Single-column always on mobile
- 2-column grid available at ≥900px main viewport width (Quick View alpha picks only)
- Full Slate game rows: single-column always — game rows need full width at all breakpoints
- Each card self-contained on mobile — no cross-card references visible in single-column flow

### 19.5 Mobile Escalation Visibility

On mobile, escalation color shifts from border-only to:
- Full-width background tint on game header row (~44px) matching escalation surface color
- Escalation label rendered as a small chip, not a full badge
- EV% pill remains on first batter row even at Level 1

### 19.6 Mobile Card Progressive Disclosure

**Level 1 (default on mobile):**
- Game header (teams + time + escalation badge)
- Top 1 batter only (name + EV% + lineup spot)
- Tap anywhere to advance

**Level 2 (first tap):**
- All Priority 1–4 fields. Top 3 batters. Environmental summary. Pitcher danger.

**Level 3 (second tap / expand all):**
- Full batter stack. Arsenal/pitch mix. Deployment briefing. Bet sizing.

Level 3 is sticky for Dangerous/Critical cards (doesn't auto-collapse).

### 19.7 Mobile Full Slate Hierarchy

```
[COMMAND STRIP] — sticky top
[ESCALATION SUMMARY] — "2 Critical · 3 Elevated · 7 Active" one line
[CRITICAL CARDS] — full width, stacked
[ELEVATED CARDS] — full width, stacked
[ACTIVE CARDS] — full width, collapsed by default on mobile
[QUIET CARDS] — hidden behind "Show X quiet games" toggle
```

---

## 20. Tablet Behavior

### 20.1 Deployment Panel on Tablet

| Breakpoint | Rendering |
|------------|-----------|
| Desktop ≥1280px | Right-side panel, 65–75% viewport width, Zone 9 sticky at bottom |
| Tablet 768px–1279px | Bottom sheet, 80% viewport height, Zones 1/2/3 above fold |
| Mobile <768px | Full-screen overlay, Zone 1 + Zone 3 above fold, Zone 9 fixed to bottom |

### 20.2 Tablet Navigation

Primary engine nav tabs remain one-tap accessible on tablet — horizontal scroll strip, no hamburger. Same rule as mobile.

### 20.3 Tablet Sidebar

Collapsible drawer with toggle at right edge. Not auto-hidden. Operator can pin open.

---

## 21. Anti-Patterns

These patterns are explicitly prohibited. Sources: `FULL_SLATE_UX_DOCTRINE.md` §8-9, `mobile-architecture-v2.md` §4.

### 21.1 Navigation Anti-Patterns

| Anti-Pattern | Reason |
|---|---|
| Hamburger menu for primary engine nav | Hides MAIN/JIG identity switch behind an extra gesture |
| Tabs for Critical / Elevated / Active filter | Tabs hide content — cards surface it |
| Infinite scroll for game cards | Operator loses position, misses games |
| Tooltip-only data | Mobile hostile, defeats rapid scan |

### 21.2 Visual Anti-Patterns

| Anti-Pattern | Reason |
|---|---|
| Giant green deploy button (`#1aff66`) | Green-500 is reserved for barrel/hard-hit, not CTAs |
| Gradient fills on card surfaces | Carries no information, adds noise |
| Neon accent colors outside token set | Degrades signal hierarchy |
| Color-coded only by team | Team colors have no tactical meaning |
| All cards same height | No visual priority differentiation |
| Pop-up modals for batter detail | Breaks context — use inline expansion |
| "Loading..." placeholder cards | Uncertainty, breaks scan rhythm |

### 21.3 Deployment Anti-Patterns

| Anti-Pattern | Reason |
|---|---|
| Sportsbook CTA styling | Deployment surface must be measured, not exciting |
| Auto-collapsing warnings | Caution states do not auto-collapse at any viewport |
| Stacked modal chains | One modal in entire deployment flow: LOCKDOWN override only |
| Hidden suppression on mobile | Zone 3 never collapsed, minimized, or deferred on small viewport |
| Composite merged scores as mobile shortcuts | No MAIN+JIG composite displayed to "save space" |
| Forced optimism visuals | FIRE animation must never overpower LOCKDOWN rendering |

### 21.4 Data Display Anti-Patterns

| Anti-Pattern | Reason |
|---|---|
| Showing fractional barrel rates (0.085) | Show 8.5% |
| Truncating player names below 12 chars in compact rows | Loss of identity |
| Sorting All Players mode by anything other than batting order | Destroys game context |
| Showing "Conditions nominal" or "Neutral" environment | Don't tell operator nothing is happening |
| Using "—" as a visible value for actual data | Coerce only when data is genuinely missing |

---

## 22. Protected UI Surfaces

These surfaces must not be modified without explicit operator authorization.

### 22.1 Architectural Closed Surfaces (per `PHASE3_REFINEMENT_DOCTRINE.md`)

- Engine-lens navigation routing
- `session_state` ownership and hydration sequence
- Cache ownership and invalidation rules
- Full Slate orchestrator logic
- Modal architecture
- MAIN/JIG identity boundaries (colors, scoring, filter namespaces)

### 22.2 Production Frontend Fixes (do not regress)

| Fix | File | Protection |
|-----|------|-----------|
| JIG Top Targets reads from `jigRows` | `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js` lines 145–146 | Commit `9962d27` |
| MAIN/JIG Full Slate source separation | `frontend/assets/js/full-slate-matrix.js` | Confirmed 2026-06-08 |
| JIG Builder reads JIG-scored rows | JIG Builder data path | All mobile refactors |

### 22.3 MAIN/JIG Identity Invariants

| Rule | What Cannot Change |
|------|-------------------|
| MAIN identity color | Red (`#ff3344`) — never swapped, muted, or blended |
| JIG identity color | Cyan (`#00d9ff`) — never swapped, muted, or blended |
| MAIN score formula | `EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25` — TCC does not alter |
| JIG HVY modifier | Display-only [0.70, 1.40] — never in MAIN model_prob or λ |
| Separate pick lists | MAIN and JIG produce separate pick lists — no composite list without new doctrine |

---

## 23. Implementation Boundaries

### 23.1 What ui-system.md Governs

This document governs:
- Visual identity and design tokens
- Shell layout and zone definitions
- Navigation model and tab order
- Card anatomy and information hierarchy
- Escalation visual system
- Color, typography, and spacing specifications
- Mobile/responsive behavior rules
- Anti-patterns and protected surfaces

### 23.2 What ui-system.md Does NOT Govern

- `pipeline.py` data flow (governed by `architecture.md`)
- `config.py` parameter values (governed by `config.py` itself)
- MAIN/JIG score formulas (governed by `AGENTS.md`)
- TCC filter logic (governed by `MASTER_TCC_DOCTRINE.md`)
- Deployment workflow checkpoints (governed by `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md`)
- session_state key ownership (governed by `PHASE3_REFINEMENT_DOCTRINE.md`)

### 23.3 Do Not Rules (per CLAUDE.md)

- Do not modify runtime code on the basis of this document
- Do not modify `frontend/` code without explicit operator authorization
- Do not modify `app.py`, `pipeline.py`, `config.py`, or any engine module
- Do not commit or push changes to these spec documents without operator authorization

### 23.4 Data Field → UI Element Mapping

| UI Element | Source Field | Module |
|---|---|---|
| Model probability | `model_prob` | `engine/probability.py` |
| EV% pill | `ev_pct` | `engine/ev.py` |
| Edge% | `edge_pct` | `engine/ev.py` |
| Rank number | `rank` | `output/ranker.py` |
| Lineup spot | `lineup_spot` | `clients/mlb_stats.py` |
| Pitcher factor | `pitcher_factor` | `engine/probability.py` |
| Park factor | `park_factor` | `data/park_factors.py` |
| Barrel % | `barrel_pct` | `clients/statcast.py` |
| Bet size | `bet_dollars` | `engine/sizing.py` |
| Confidence | `confidence` | `output/ranker.py` |
| Soft flags | `soft_flags` | `engine/filters.py` |
| HVY modifier | `hvy_modifier` | `clients/pitch_mix.py` |
| Best odds | `best_american` | `clients/odds_api.py` |
| Market prob | `market_no_vig_prob` | `engine/market.py` |
| Composite score | `score` | `output/ranker.py` |

---

## 24. Future Work / Deferred Items

These items are non-blocking and not yet authorized. Do not implement without new doctrine and operator authorization.

### 24.1 Deferred UI Features

| Feature | Status | Reference |
|---------|--------|-----------|
| Slate Heat Map (threat board grid, one cell per game) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.1 |
| Correlation Cluster Visualization (connected nodes diagram) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.2 |
| Dynamic Escalation History (per-card EV timeline) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.3 |
| Deployment Session State in Command Strip | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.4 |
| Operator Dismissal Flow (Critical/Dangerous deliberate skip) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.5 |
| Arsenal Fingerprint Badge (pitch-mix band below pitcher name) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.6 |
| Predictive Escalation Indicator (dashed border for TBD-pitcher games) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.7 |
| Portfolio Exposure Overlay (slate overlay dim by session exposure) | NON-IMPLEMENTED CONCEPT | `FULL_SLATE_UX_DOCTRINE.md` §10.8 |
| JIG Phase 2B: game-command module + tactical tag system | DEFERRED | `PHASE3_REFINEMENT_DOCTRINE.md` deferred item 2 |
| Sound / push notifications | OUT OF SCOPE | `product-spec.md` Non-Goals |
| PWA configuration | OUT OF SCOPE | `product-spec.md` Non-Goals |

### 24.2 ui-system.md Pending Formalization

Per `mobile-architecture-v2.md` §8, audit this document against formalized token set when populated and update any token values that diverge from `wiki/doctrine/visual-design-tokens.md`. These items remain unformalized:

| Item | Current Source | Gap |
|------|---------------|-----|
| Breakpoint definitions | Scattered across arch specs | Not yet consolidated into single table |
| Card component structure | `component-rules.md` (stub) | Stub not yet populated |
| Escalation badge spec | `spec_escalation_badge_system_v1.md` | File existence in repo not verified |
| Full Slate compact row spec | `PHASE3_REFINEMENT_DOCTRINE.md` §8 | In refinement doc, not formalized here |

---

## Source Authority Map

| Section | Primary Sources |
|---------|----------------|
| 1. UI System Purpose | product-spec.md §1-2 |
| 2. Platform Visual Identity | visual-design-doctrine.md |
| 3. Production Surface Map | architecture.md §1-2 |
| 4. App Shell Layout | app-shell-layout.md, mobile-architecture-v2.md §1 |
| 5. Claude Design Mobile Doctrine | mobile-architecture-v2.md §2-7 |
| 6. Navigation System | app-shell-layout.md, mobile-architecture-v2.md §2.4, product-spec.md §16 |
| 7. MAIN Lens Layout | product-spec.md §4, PHASE3_REFINEMENT_DOCTRINE.md §3 |
| 8. JIG Lens Layout | product-spec.md §5, mobile-architecture-v2.md §5 |
| 9. Full Slate Intelligence Matrix | FULL_SLATE_UX_DOCTRINE.md §1-6, mobile-architecture-v2.md §6.2 |
| 10. Top Targets | mobile-architecture-v2.md §6.1 |
| 11. JIG Builder | mobile-architecture-v2.md §6.3 |
| 12. Tactical Command Center | MASTER_TCC_DOCTRINE.md §1-4 |
| 13. Right Rail / Strategy Rail | PHASE3_REFINEMENT_DOCTRINE.md §4-5, mobile-architecture-v2.md §3.1 |
| 14. Live Target Banner | FULL_SLATE_UX_DOCTRINE.md §5 |
| 15. Card System | PHASE3_REFINEMENT_DOCTRINE.md §3, FULL_SLATE_UX_DOCTRINE.md §3, §7 |
| 16. Tier / Badge System | tier-vocabulary.md, FULL_SLATE_UX_DOCTRINE.md §2 |
| 17. Color System | visual-design-tokens.md, FULL_SLATE_UX_DOCTRINE.md §2.2 |
| 18. Typography System | visual-design-tokens.md, PHASE3_REFINEMENT_DOCTRINE.md §3 |
| 19. Responsive / Mobile Behavior | mobile-architecture-v2.md §3-4, FULL_SLATE_UX_DOCTRINE.md §4 |
| 20. Tablet Behavior | mobile-architecture-v2.md §3.3 |
| 21. Anti-Patterns | FULL_SLATE_UX_DOCTRINE.md §8-9, mobile-architecture-v2.md §4, PHASE3_REFINEMENT_DOCTRINE.md §3 |
| 22. Protected UI Surfaces | mobile-architecture-v2.md §6, PHASE3_REFINEMENT_DOCTRINE.md §10 |
| 23. Implementation Boundaries | CLAUDE.md, architecture.md §12 |
| 24. Future Work | FULL_SLATE_UX_DOCTRINE.md §10, PHASE3_REFINEMENT_DOCTRINE.md deferred queue |

---

*Documentation only. No runtime files modified. No frontend edits. No backend edits. No API edits. No commits made.*
*Authority: Claude Code (UI System Reconstruction) · 2026-06-09*
