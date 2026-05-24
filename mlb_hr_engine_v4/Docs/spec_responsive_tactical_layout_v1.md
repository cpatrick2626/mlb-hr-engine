# Responsive Tactical Layout v1
## MLB HR ENGINE — Multi-Breakpoint Behavior Doctrine

**Owner:** Claude (UX Doctrine)
**Codex:** Implementation
**Status:** Documentation Only — No Runtime Code

---

## 1. Core Principle

**Never simply shrink desktop. Mobile must become a tactical vertical command flow.**

Desktop is a battlefield overview. Mobile is a weapon aimed at a single target. Both serve the same operator; neither is a degraded version of the other.

---

## 2. Breakpoint Definitions

| Name | Viewport Width | Primary Device |
|---|---|---|
| Desktop | ≥1200px | Monitor, wide laptop |
| Laptop | 900px–1199px | Standard laptop |
| Tablet | 600px–899px | iPad, large phone landscape |
| Mobile | <600px | Phone portrait |

---

## 3. Desktop (≥1200px)

**Column rules:**
- Sidebar: 280px fixed right
- Main viewport: fills remainder (minimum 640px effective)
- Quick View alpha grid: 2-column
- Elite tab: 2-column at ≥1400px, 1-column at 1200–1399px
- Matchup Edge: 1-column always (cards are wide)
- JIG HVY cards: 1-column always
- Full Slate game rows: 1-column always (game headers need full width)

**Card density:** Full card visible — all stat pills, weather strip, HVY bar, pitch badges.

**Sidebar behavior:** Always visible. Not collapsible. TCC and portfolio controls always accessible without interaction.

**Feed behavior:** Live Intelligence Feed inline below deployment tray trigger. Expanded by default in active-slate session.

**Deployment tray behavior:** Collapsed strip by default. Expands in-place. Does not push content up — overlays with 36px bottom margin reserved.

**Navigation behavior:** All 5 primary tabs visible in horizontal tab bar. No overflow.

**Touch targets:** N/A (cursor-based). Minimum target size 28px height.

**What collapses first:** Nothing collapses on desktop. All content surfaces visible.

**What must remain visible:** Everything. Desktop is the full command view.

---

## 4. Laptop (900px–1199px)

**Column rules:**
- Sidebar: 240px fixed right
- Main viewport: fills remainder (minimum 520px effective)
- Quick View alpha grid: 2-column only at ≥1100px, else 1-column
- Elite tab: 1-column
- All other tabs: 1-column

**Card density:** Full card visible. Stat pill font sizes may reduce 1px. Badge labels remain.

**Sidebar behavior:** Always visible. Not collapsible. Width compresses to 240px. Section labels may truncate.

**Feed behavior:** Inline below tray trigger. Collapsed by default on laptop to preserve main viewport space.

**Deployment tray behavior:** Same as desktop.

**Navigation behavior:** All 5 tabs visible. Tab labels may shorten (e.g., "ADVANCED" → "ADV" if overflow).

**Touch targets:** Minimum 36px height (laptop trackpad users, not touch).

**What collapses first:** Live Feed (collapsed default), card secondary rows (collapsed).

**What must remain visible:** Command strip, nav tabs, sidebar primary controls (TCC preset bar, load button).

---

## 5. Tablet (600px–899px)

**Column rules:**
- Sidebar: Drawer (hidden by default, toggle via sidebar icon in command strip)
- Main viewport: 100% width
- All card grids: 1-column
- Full Slate game rows: 1-column

**Card density:** Cards render full height but may compress secondary stat strips to 2 rows instead of 3. Primary stats (MDL, EV, EDGE, BRL) always visible on card face. Arsenal pitch badges: max 4 shown, "+N more" if overflow.

**Sidebar behavior:** Hidden behind drawer. User taps sidebar icon (top-right command strip) to open. Drawer slides in from right at 320px width, overlays content. Tap outside closes drawer. TCC controls fully functional inside drawer.

**Feed behavior:** Collapsed strip only. Tap to see last 3 alerts.

**Deployment tray behavior:** Collapsed strip. Tap to expand to 50% screen height drawer from bottom.

**Navigation behavior:** 5 tabs in horizontal scroll strip (not truncated labels). User can scroll left-right in tab bar. First 3 tabs visible without scroll.

**Touch targets:** Minimum 44px height and 44px width for all interactive elements.

**What collapses first:** Sidebar (drawer), Live Feed (strip), card secondary stat row (2 → 1 line), pitch badge overflow (>4 → "+N more").

**What must remain visible:** Command strip, nav tabs (scrollable), player name + primary stats on every card face, Deployment Tray strip.

---

## 6. Mobile (<600px)

**Column rules:**
- Single column always, no exceptions
- 100% viewport width for all content
- Cards take full width

**Card density:** Mobile card is a tactical single-player card:
- Row 1: Rank badge + Player name + Team + Badge strip (STEAM/OPT/ELITE)
- Row 2: MDL | EV | EDGE (primary stat pills, bold)
- Row 3: BRL | ODDS (secondary, smaller)
- Row 4: HVY bar (if available) — 1 line only
- Weather strip: Only if |weather_factor − 1.0| ≥ 0.04
- Pitch badge strip: Hidden by default, tap "Pitches" to expand

**Sidebar behavior:** Hidden. Accessible via "Filters" button in command strip (opens full-screen overlay with TCC controls). This overlay is NOT a modal — it is a filter panel page. Pressing X returns to current tab without data reload.

**Feed behavior:** Hidden. Steam alerts shown only as notification badges on nav tab (e.g., "STEAM: 2" badge on TODAY'S PICKS tab).

**Deployment tray behavior:** Full-screen modal when expanded. Bottom anchored trigger strip 48px height. Tap to expand → full screen overlay showing FD Slip list. "Done" button closes back to current tab.

**Navigation behavior:** Tab bar horizontal scroll strip. Tab labels shortened: "PICKS" / "JIG" / "SLATE" / "PERF" / "ADV". All tabs remain one-tap accessible.

**Touch targets:** Minimum 48px height, 44px width for all tappable elements.

**What collapses first:** Everything non-critical. Arsenal, pitch mix, secondary stats, weather strips, game context rows, card rank numbers (ranks shown as color only, number revealed on tap).

**What must remain visible:** Player name, team, MDL, EV, EDGE on every card without any tap. Command strip. Nav tabs. Deployment tray trigger strip.

---

## 7. Responsive Behavior Matrix

| Element | Desktop | Laptop | Tablet | Mobile |
|---|---|---|---|---|
| Sidebar | Fixed 280px | Fixed 240px | Drawer | Filter page overlay |
| Nav tabs | Full labels | May shorten | Scroll strip | Scroll strip, short labels |
| Card grid | 2-col (QV) | 2-col ≥1100px | 1-col | 1-col |
| Card stats | Full 3 rows | Full 3 rows | 2 rows | 2 rows (primary only) |
| Pitch badges | Up to 6 | Up to 6 | Max 4 | Hidden (tap to show) |
| HVY bar | Full label | Full label | Compact | Compact |
| Weather strip | Always | Always | If >threshold | If >threshold |
| Live Feed | Inline expanded | Collapsed strip | Collapsed strip | Steam badge on tab |
| Deployment Tray | Bottom strip | Bottom strip | Bottom drawer | Full-screen overlay |

---

## 8. What Mobile Is

Mobile is not a shrunken desktop. Mobile is:
- **One pick at a time.** Full attention on the card in view.
- **Filters are a separate action.** Open filter panel, set, return.
- **Deploy is always reachable.** Tray trigger never hidden.
- **No horizontal scroll in content.** Cards never overflow viewport width.

Mobile users are operators acting under time pressure. The layout must support rapid vertical scanning of ranked picks and one-tap deployment actions.

---

*Documentation only. No implementation. No app.py changes. No session_state changes.*
