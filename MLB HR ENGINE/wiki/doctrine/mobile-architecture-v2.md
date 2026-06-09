# Mobile Architecture V2 — Claude Design Preservation Version

**Version:** 2.0  
**Date:** 2026-06-09  
**Status:** AUTHORITATIVE  
**Owner:** Claude Code  
**Scope:** Production frontend (`frontend/`) mobile and responsive layout doctrine  
**Reconstruction note:** Original "Mobile Architecture V2" document was not located in the repo as of 2026-06-09. This document is reconstructed from canonical sources: `spec_global_shell_architecture_v1.md`, `spec_deployment_panel_architecture_v1.md`, `wiki/doctrine/app-shell-layout.md`, `wiki/doctrine/visual-design-doctrine.md`, `wiki/doctrine/visual-design-tokens.md`, `mlb_hr_engine_v4/Docs/01_SPECS/product-spec.md`. Treat this as the authoritative mobile doctrine record going forward.

---

## 1. Canonical Claude Design Layout

The MLB HR Engine shell is a **cinematic tactical command center**. The canonical desktop layout is the authoritative reference. Mobile is a disciplined reduction of it — not a separate product.

### Shell Zone Hierarchy (canonical)

| Zone | Component | Role | Mobile Behavior |
|------|-----------|------|-----------------|
| Top | TopBar (Command Strip) | Branding, date, slate status, data load | Fixed — never scrolls away. 60px height on mobile |
| Navigation | Engine-lens nav tabs | MAIN / JIG / FULL SLATE / PERFORMANCE / ADVANCED | Horizontal scroll strip — no hamburger. One-tap accessible |
| Banner | LiveTargets | Live HR threat summary, escalation badges | Collapsed by default. One-tap expand |
| Center | Stage / Main Viewport | Primary operator action surface | Single-column, full-width, scrollable |
| Right | RightRail / Sidebar | TCC controls, portfolio, P&L, ops buttons | Hidden by default. Drawer icon in Command Strip |
| Bottom | Deployment Tray | FD slip, stake, expand/collapse | Collapsed by default (36px trigger). Expands full-screen on mobile |
| Bottom/feed | Live Intelligence Feed | Steam alerts, lineup confirms | Collapsed by default. One-tap expand — max 5 entries shown |

### Layout ASCII — Desktop (reference)

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

### Layout — Mobile (canonical reduction)

```
[COMMAND STRIP — fixed, full-width, 60px]
[ENGINE NAV TABS — horizontal scroll strip]

[MAIN VIEWPORT — single column, full-width, scrollable]
[  Active tab content renders top to bottom           ]
[  Card stacks vertically, each self-contained        ]

[DEPLOYMENT TRAY TRIGGER — 36px sticky bottom strip]
  [Tray expanded = full-screen overlay]
```

---

## 2. Preserve Exactly

These design elements are doctrine-locked. Mobile must reproduce them without degradation.

### 2.1 Engine Identity Colors

| Engine | Color | Hex |
|--------|-------|-----|
| MAIN | Red | `#ff3344` |
| JIG | Cyan | `#00d9ff` |

Do not swap. Do not mute. Do not blend. Engine identity colors communicate intelligence layer at a glance — loss of identity at any viewport is a doctrine violation.

### 2.2 Escalation Visual Hierarchy

Visual weight must scale with signal strength at all viewport sizes:
- Low-confidence picks: visually quiet
- High-confidence picks: elevated via border weight, color intensity, and (FIRE tier only) pulse animation
- Pulse animations reserved for highest escalation tier — not added to lower tiers on mobile for "engagement"
- Corner brackets frame threat cards — do not remove at any breakpoint
- Semantic green barrel palette: green = barrel/hard-hit quality signal, not generic "good" or "active"

### 2.3 Command Strip Invariants

- Command strip is always fixed at top of viewport — never scrolled away
- No navigation inside command strip — navigation belongs in engine nav tabs only
- Touch target minimum **44px** on all breakpoints
- Contents (left to right): logo/name-mark, slate date + game count, status pill, auto-refresh toggle, data load button, API key indicator
- Strip height: 52px desktop, 60px mobile

### 2.4 Engine Navigation Tabs

- Primary tabs never collapse to hamburger — they collapse to horizontal scroll strip
- Tab order is doctrine-locked: TODAY'S PICKS | JIG | FULL SLATE | PERFORMANCE | ADVANCED
- `TODAY'S PICKS` = MAIN engine (EV/Edge ranked, Statcast calibrated)
- `JIG` = Matchup-Tactical engine (HVY modifier, pitch mix, pitcher vulnerability)
- Tab count badges show live counts from current slate

### 2.5 Typography and Tokens

Do not substitute or compress design tokens at mobile breakpoints:

| Token | Value |
|-------|-------|
| Display font | Barlow Condensed 800, uppercase, tracking 0.08em |
| Stats font | JetBrains Mono, tabular-nums |
| Body font | Barlow |
| Primary text | `#f1f5f3` |
| Secondary text | `#b8c2c0` |
| Tertiary text | `#6b7872` |
| Page background | `#04070a` |
| Primary panel | `#0a1014` |
| Raised card | `#0e1519` |

Tier pill spec unchanged: `inset 0 0 0 1.5px rgba(color, 0.6)`, background `rgba(8,12,16,0.6)`, Barlow Condensed 800, 12px, uppercase, tracking 0.12em.

### 2.6 Deployment Panel Zone Order

The nine-zone deployment panel zone order is fixed. No reordering for mobile. No zone may be hidden unless its definition explicitly allows it:

1. Deployment Header — NEVER collapsed
2. Escalation Summary — NEVER collapsed
3. Suppression Layer — NEVER collapsed, even at NONE tier
4. Tactical Evidence — may collapse for NONE/LOW suppression at operator preference
5. Risk Factors — collapses to "No active flags" when empty
6. Confidence Layer — always visible
7. Override Controls — hidden unless suppression = HIGH or LOCKDOWN
8. Exposure Summary — collapses to "Exposure: Normal" when no alerts
9. Action Layer — fixed to bottom of screen on mobile

---

## 3. Production-Safe Adaptations

These adaptations are approved for mobile/responsive behavior without doctrine approval. They reduce visual density without removing intelligence.

### 3.1 Sidebar (RightRail)

| Breakpoint | Behavior |
|------------|----------|
| Desktop ≥1280px | 280px fixed, always visible |
| Laptop | 240px fixed |
| Tablet 768px–1279px | Collapsible drawer, toggle at right edge |
| Mobile <768px | Hidden by default, accessible via drawer icon in Command Strip |

### 3.2 Deployment Tray

| Breakpoint | Collapsed | Expanded |
|------------|-----------|---------|
| Desktop | 36px sticky strip | Slides up 240px max |
| Mobile | 36px sticky strip | Full-screen modal overlay |

Main viewport has 36px bottom margin so tray trigger never obscures content.

### 3.3 Deployment Panel

| Breakpoint | Rendering |
|------------|-----------|
| Desktop ≥1280px | Right-side panel, 65–75% viewport width, Zone 9 sticky at bottom |
| Tablet 768px–1279px | Bottom sheet, 80% viewport height, Zones 1/2/3 above fold |
| Mobile <768px | Full-screen overlay, Zone 1 + Zone 3 above fold, Zone 9 fixed to bottom |

### 3.4 Card Layout

- Single-column always on mobile
- 2-column grid available at ≥900px main viewport width (Quick View alpha picks only)
- Full Slate game rows: single-column always — game rows need full width at all breakpoints
- Each card self-contained on mobile — no cross-card references visible in single-column flow

### 3.5 Progressive Disclosure (mobile-first collapse order)

Priority order — what collapses first when viewport shrinks:

1. Right sidebar → drawer (user toggle)
2. Live Intelligence Feed → collapsed by default (one-tap, last 5 steam alerts)
3. Deployment Tray → collapsed by default (36px trigger)
4. Card secondary stat rows → show on tap
5. Pitch Mix expanders → collapsed, lazy-load gated
6. Full Slate compact rows → unchanged (already minimal)

### 3.6 Responsive Width Floors

| Surface | Minimum width |
|---------|---------------|
| Main viewport | 640px desktop, 100% mobile |
| Sidebar | 280px desktop, 240px laptop, full-drawer tablet/mobile |

### 3.7 Live Intelligence Feed

- Collapsed by default on tablet/mobile
- One-tap expand: last 5 steam alerts
- Max 10 entries shown — older drop off
- Feed never auto-expands
- Feed does not cover card content at any breakpoint

---

## 4. Stale Technical Elements Not To Copy

These elements appear in older prototype code or earlier design iterations. Do not replicate into production mobile work.

### 4.1 Hamburger Menu for Primary Navigation

Rejected. Engine nav tabs must always be one-tap accessible via horizontal scroll strip. Hamburger menus are not acceptable for primary engine navigation — they hide the MAIN/JIG identity switch behind an extra gesture.

### 4.2 Giant Green Deploy Button

Rejected. The [Deploy] button is standard button styling. Green-dominant action surfaces communicate excitement — the opposite of measured deployment. `#1aff66` (green-500) is reserved for barrel/hard-hit quality signals, not action CTAs.

### 4.3 Sportsbook CTA Styling

Rejected. No gradient fills, no large rounded rectangles, no dollar signs in primary control labels. The deployment surface is muted, professional, and activated by context.

### 4.4 Auto-Collapsing Warnings

Rejected. Caution states do not auto-collapse on any viewport. Zone 3 (Suppression Layer) and Zone 7 (Override Controls) remain visible until the operator explicitly completes or abandons deployment.

### 4.5 Stacked Modal Chains

Rejected. One modal permitted in the entire deployment flow: the LOCKDOWN override confirmation. All other decisions are inline. Do not add mobile-specific "Are you sure?" overlays.

### 4.6 Hidden Suppression on Mobile

Rejected. Zone 3 (Suppression Layer) is never collapsed, never minimized, never deferred to a secondary screen on mobile. Smaller viewport is not a justification for hiding suppression intelligence.

### 4.7 Composite Merged Scores as Mobile Shortcuts

Rejected. No combined MAIN+JIG composite score displayed on mobile to "save space." MAIN and JIG scores are always separate, labeled distinctly. Space reduction is achieved via progressive disclosure, not by blending intelligence signals.

### 4.8 Forced Optimism Visuals

Rejected. FIRE escalation animation or glow must not overpower LOCKDOWN suppression rendering on any viewport. Both signals must be simultaneously legible.

---

## 5. MAIN/JIG Separation Preservation

Mobile adaptations must never compromise MAIN/JIG separation. These rules apply at all viewport sizes.

| Rule | Mobile Application |
|------|--------------------|
| Separate scoring | MAIN and JIG score columns never merged for mobile density |
| Engine identity colors | MAIN red / JIG cyan preserved at all breakpoints |
| HVY signal isolation | HVY pitch-mix modifier is display-only in JIG context. Never shown in MAIN cards at any breakpoint |
| Separate key namespaces | `tac_*` (MAIN), `jig_tac_*` (JIG). No cross-engine key reads |
| Separate output | MAIN and JIG produce separate pick lists. No merged mobile-view list |
| TCC orchestrates only | TCC filter controls (sidebar/drawer) do not compute MAIN or JIG scores |

**What counts as contamination on mobile:**
- Showing HVY modifier in MAIN card to fill mobile whitespace
- Displaying a single merged "top pick" list that blends MAIN and JIG rows
- Using JIG escalation badge colors (cyan) on MAIN cards for visual simplification
- Running identical filter presets on both layers on mobile

The operator must always be able to see which engine a card comes from without additional taps.

---

## 6. Production Fix Preservation

These production fixes are in the live frontend and must be preserved in any mobile-responsive work.

### 6.1 JIG Top Targets Source Fix

**File:** `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js`, lines 145–146  
**Fix:** JIG Top Targets reads from `jigRows`, MAIN Top Targets reads from `mainRows`. ELITE/EDGE tier filter applies to both. No cross-engine fallback.  
**Commit:** `9962d27`  
**Rule:** Any mobile-responsive refactor of the Top Targets component must preserve this source branch separation. Do not introduce a unified row source for mobile layout convenience.

### 6.2 MAIN/JIG Full Slate Source Separation

**File:** `frontend/assets/js/full-slate-matrix.js`  
**Rule:** Full Slate game rows for MAIN and JIG use separate data sources. Confirmed operational as of 2026-06-08. Mobile layout must not collapse the engine source branch.

### 6.3 JIG Builder Phase A Fix

**Context:** JIG Builder reads JIG-scored rows. MAIN surfaces read MAIN-scored rows.  
**Rule:** Mobile responsive work must not introduce a single shared data path for "simplicity."

---

## 7. Final Mobile Doctrine

Mobile is a **tactical vertical command flow**, not a separate product or a simplified version of the operator dashboard.

### Core Rules

1. **Desktop is primary.** Mobile is a degraded-access mode. No mobile-specific CSS, touch-only controls, or PWA configuration without explicit operator authorization and doctrine update.

2. **Command strip never scrolls.** Fixed. Always visible. Touch targets ≥44px. This is not negotiable at any viewport.

3. **Engine navigation is always one-tap.** Horizontal scroll strip. No hamburger. No nested menus for primary nav.

4. **Single column always.** Card stacks vertically. Each card self-contained. No cross-card reference visible in mobile flow.

5. **Intelligence density over whitespace.** Mobile adaptations reduce clutter by collapsing secondary content, not by removing intelligence. Progressive disclosure preserves all signals.

6. **Deployment tray expands full-screen.** On mobile, the tray cannot be partial-height without blocking content. Full-screen overlay is the only acceptable expanded state.

7. **Suppression is never hidden.** Zone 3 renders at all viewport sizes. No suppression bypass on mobile.

8. **MAIN/JIG identity survives.** Engine identity colors (red/cyan), separate score columns, and separate pick lists are preserved at all breakpoints.

9. **No auto-collapsing warnings.** Caution states and override requirements remain visible until operator takes deliberate action.

10. **No sportsbook visual patterns.** The deployment surface is a measured deliberation layer, not a betting CTA surface.

### Workflow Chain — Mobile Navigation Path

| Workflow | Mobile Navigation |
|----------|-------------------|
| MAIN: SCAN → QUALIFY → DEPLOY | TODAY'S PICKS tab → vertical card scroll → Deployment Tray (full-screen) |
| JIG: MATCHUP → CONFIRM → EXPLOIT | JIG tab → HVY cards scroll → Deployment Tray (full-screen) |
| FULL SLATE: SCAN FIELD → ISOLATE DANGER | FULL SLATE tab → single-column game rows |
| DEPLOYMENT: QUALIFY → DEPLOY → TRACK | Card → Tray overlay → Performance tab |

Deployment Tray always reachable without tab switch. Navigation never forces operator to leave workflow chain to reach deploy action.

---

## 8. ui-system.md Dependencies

**File:** `mlb_hr_engine_v4/Docs/01_SPECS/ui-system.md`  
**Status as of 2026-06-09:** Stub — file exists, content is empty (1 line).

Mobile architecture depends on the following tokens and systems that `ui-system.md` is intended to formalize:

| Dependency | Current Source | Status |
|------------|---------------|--------|
| Color tokens | `wiki/doctrine/visual-design-tokens.md` | Complete |
| Typography tokens | `wiki/doctrine/visual-design-tokens.md` | Complete |
| Tier pill spec | `wiki/doctrine/visual-design-tokens.md` | Complete |
| Breakpoint definitions | `mlb_hr_engine_v4/Docs/spec_global_shell_architecture_v1.md` (inferred from sidebar/panel rules) | Scattered — not formalized |
| Touch target minimums | `spec_global_shell_architecture_v1.md` § Command Strip | Documented (44px) |
| Shell zone component names | `wiki/doctrine/app-shell-layout.md` | Complete |
| Card component structure | `mlb_hr_engine_v4/Docs/01_SPECS/component-rules.md` | Stub |
| Escalation badge spec | `spec_escalation_badge_system_v1.md` | Referenced in deployment spec; file not verified in repo |

**Action when `ui-system.md` is populated:** Audit mobile-architecture-v2.md against the formalized token set and update any token values that diverge from the canonical `ui-system.md`. Until then, `visual-design-tokens.md` is authoritative.

---

## Cross-References

- [App Shell Layout](app-shell-layout.md)
- [Visual Design Doctrine](visual-design-doctrine.md)
- [Visual Design Tokens](visual-design-tokens.md)
- [MAIN/JIG Separation Rules](main-jig-separation.md)
- [Production Surface Truth](production-surface-truth.md)
- [Room Governance](room-governance.md)
- `mlb_hr_engine_v4/Docs/spec_global_shell_architecture_v1.md`
- `mlb_hr_engine_v4/Docs/spec_deployment_panel_architecture_v1.md`
- `mlb_hr_engine_v4/Docs/01_SPECS/product-spec.md` (Section 15 Non-Goals, Section 16 Shell Architecture)

---

*Documentation only. No runtime files modified. No frontend edits. No backend edits. No API edits.*  
*Authority: Claude Code (Mobile Architecture V2 Reconstruction) · 2026-06-09*
