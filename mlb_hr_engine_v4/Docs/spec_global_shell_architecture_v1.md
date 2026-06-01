# Global Shell Architecture v1
## MLB HR ENGINE — Runtime Operational Shell

**Owner:** Claude (UX Doctrine)
**Codex:** Implementation
**Status:** Documentation Only — No Runtime Code

---

## 1. Shell Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│  COMMAND STRIP (top, fixed, full-width)                 │
├──────────────────────────────────┬──────────────────────┤
│                                  │                      │
│  MAIN CONTENT VIEWPORT           │  RIGHT OPERATIONAL   │
│  (scrollable, takes remaining    │  SIDEBAR             │
│   width)                         │  (fixed, collapsible)│
│                                  │                      │
│  ┌──────────────────────────┐    │  • TCC Controls      │
│  │  ENGINE NAV TABS          │   │  • Portfolio opts    │
│  │  MAIN | JIG | FULL SLATE │   │  • P&L summary       │
│  └──────────────────────────┘    │  • CLV capture btn   │
│                                  │  • Ops buttons       │
│  [Active tab content renders]    │                      │
│                                  │                      │
├──────────────────────────────────┴──────────────────────┤
│  DEPLOYMENT TRAY (bottom, collapsible, persistent)      │
│  + LIVE INTELLIGENCE FEED (inline, below tray trigger)  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Command Strip

**Position:** Top of viewport, fixed during scroll.

**Contents (left to right):**
- Engine logo / name mark (non-interactive)
- Slate date display — today + game count
- Slate status pill: `🟢 CONFIRMED` / `🟡 MIXED` / `🔵 PROJECTED`
- Auto-refresh toggle + countdown timer
- Data load button (primary CTA)
- API key status indicator (green dot / red dot, no key shown)

**Rules:**
- Never scroll out of view on any screen size
- No navigation inside command strip — navigation belongs in engine nav tabs
- Touch target minimum 44px height on all breakpoints
- Strip height: 52px desktop, 60px mobile

---

## 3. Engine Navigation

**Structure:** Horizontal tab bar immediately below command strip.

**Primary tabs (permanent, always visible):**
```
[  TODAY'S PICKS  ]  [  JIG  ]  [  FULL SLATE  ]  [  PERFORMANCE  ]  [  ADVANCED  ]
```

**Identity separation:**
- `TODAY'S PICKS` = MAIN engine: Quantitative Market-Aware Intelligence, EV/Edge ranked, Statcast calibrated
- `JIG` = Matchup-Tactical engine: HVY modifier, pitch mix, pitcher vulnerability
- `FULL SLATE` = Field command: all batters, game-organized, qualification overlay
- `PERFORMANCE` = Results, CLV, P&L, drift monitoring
- `ADVANCED` = Strategies, portfolio, market analysis

**Tab count badges:** Show live counts from current slate (not filtered counts except where noted).

**Mobile behavior:** Tabs collapse to horizontal scroll strip (no hamburger menu for primary nav — tabs must remain one-tap accessible).

---

## 4. Right Operational Sidebar

**Desktop width:** 280px fixed
**Laptop width:** 240px fixed
**Tablet:** Collapsible drawer (toggle button at right edge)
**Mobile:** Hidden by default, accessible via drawer icon in command strip

**Content zones (top to bottom):**
1. **Filter Presets** — OPERATIONAL / SELECTIVE / ELITE ONLY (MAIN); ALL TACTICAL / SELECTIVE / MATCHUP+ (JIG)
2. **Main TCC** — universe filter controls (number inputs, not sliders)
3. **Portfolio Optimizer** — toggle + preset selector
4. **CLV / Ops Buttons** — Capture Closing Lines, Settle Yesterday, Save for Results Tracking
5. **P&L Summary** — mini dashboard (Win%, ROI, n settled)

**Sidebar scroll:** Internal scroll within sidebar, independent of main viewport scroll.

**Sidebar state:** Persists within session. Remembers collapsed/expanded state per section. Does not reset on tab switch.

---

## 5. Main Content Viewport

**Width:** Remaining after sidebar — minimum 640px desktop, 100% mobile.

**Content rules:**
- Primary content area always scrollable
- Tab content replaces in-place (no nested routing)
- Cards render in vertical column flow by default
- 2-column grid available at ≥900px viewport for Quick View alpha picks
- Pagination caps applied per tab (see Render Density spec)
- Tab switch does not reset scroll position (Streamlit default — accept)

---

## 6. Deployment Tray

**Position:** Sticky bottom strip, always present but collapsible.

**Collapsed state:**
- Height: 36px
- Shows: FD Slip count, total stake, expand chevron
- Does not obscure main content (main viewport has 36px bottom margin)

**Expanded state:**
- Slides up 240px max
- Shows: full FD Slip list, individual slip cards, Clear Slip (two-step confirm), Copy Slip
- Main viewport scrolls above it

**Mobile:** Full-screen modal overlay when expanded (tray cannot be partial-height on small screens without blocking content).

**Placement rationale:** Deployment is the final step of QUALIFY → DEPLOY → TRACK → LEARN. Tray is persistent because deployment decisions happen continuously during session, not at a single terminal point.

---

## 7. Live Intelligence Feed

**Location:** Below tray trigger, collapsible strip.

**Desktop:** Shows inline below the deployment tray trigger line (not in sidebar, not floating).

**Tablet/Mobile:** Collapsed by default. One-tap expand shows last 5 steam alerts.

**Content:**
- Steam move alerts (most recent 3–5)
- Lineup confirmation updates
- Auto-refresh events

**Rules:**
- Feed never auto-expands. User controls.
- Feed does not cover any card content.
- Feed entries are time-stamped.
- Max 10 entries shown. Older entries drop off.

---

## 8. Desktop Battlefield Layout

```
[COMMAND STRIP — full width, fixed]
[ENGINE NAV TABS — full width, below strip]

[LEFT: MAIN VIEWPORT                    ] [RIGHT: SIDEBAR 280px fixed]
[  Engine tab content (scrollable)      ] [  TCC controls             ]
[  Card grid / table / game rows        ] [  Portfolio toggle         ]
[                                        ] [  CLV / Ops buttons       ]
[                                        ] [  P&L mini                ]
[                                        ]
[DEPLOYMENT TRAY — sticky bottom, collapsible strip]
[LIVE FEED — collapsible below tray trigger]
```

**Desktop rules:**
- Sidebar never collapses automatically
- Main viewport minimum 640px
- Card grid 2-column at ≥900px main viewport width
- Full Slate game rows: single-column always (game rows need full width)

---

## 9. Mobile Collapse Behavior

**What collapses first (priority order):**
1. Right sidebar → drawer (user toggle)
2. Live Intelligence Feed → collapsed by default
3. Deployment Tray → collapsed by default
4. Card secondary rows → progressive disclosure (show on tap)
5. Pitch Mix expanders → collapsed by default (always lazy-load gated)
6. Full Slate compact rows → unchanged (already minimal)

**What never collapses:**
- Command strip
- Engine nav tabs
- Primary card content (player name, team, model prob, EV, edge)
- Deployment tray trigger line

**Mobile becomes tactical vertical command flow:**
- Single column always
- Card stacks vertically
- Each card self-contained (no cross-card references visible)
- Touch targets ≥44px
- Scroll is the primary navigation gesture within a tab

---

## 10. Workflow Chain Mapping

| Chain | Navigation Path |
|---|---|
| MAIN: SCAN → QUALIFY → DEPLOY | TODAY'S PICKS → Quick View / Elite → Deployment Tray |
| JIG: MATCHUP → CONFIRM → EXPLOIT | JIG tab → Matchup Edge → HVY cards → Deployment Tray |
| FULL SLATE: SCAN FIELD → ISOLATE DANGER → ESCALATE TARGETS | FULL SLATE tab → All Players mode → Qualified mode → Elite Targets mode |
| DEPLOYMENT: QUALIFY → DEPLOY → TRACK → LEARN | Elite / Qualified → Tray → Performance tab → P&L / CLV |

**Shell rule:** Navigation never forces users to leave their current workflow chain to reach a deploy action. Deployment Tray is always reachable without tab switch.

---

*Documentation only. No implementation. No app.py changes. No session_state changes.*
