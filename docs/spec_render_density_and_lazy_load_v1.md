# Render Density & Lazy Load Doctrine v1
## MLB HR ENGINE — Performance and Cognitive Load

**Owner:** Claude (UX Doctrine)
**Codex:** Implementation
**Status:** Documentation Only — No Runtime Code

---

## 1. Core Principle

**Performance and cognitive load must improve together.**

A 15-game slate with 400+ batters cannot render everything. Every component that renders when the user doesn't need it wastes CPU cycles and dilutes operator attention. Density decisions are simultaneously performance decisions.

---

## 2. Visible Card Limits by Tab

| Tab | Default Visible | Max Before Pagination | Expansion Mechanism |
|---|---|---|---|
| Quick View Alpha | 12 | 12 (fixed) | "View Full Slate" expander |
| Quick View Extended | 25 | 50 | Load more button |
| Elite tab | All barrel≥8% (no cap) | 50 | Pagination |
| Matchup Edge | 25 | 50 | Pagination with page size control |
| JIG Power Profiles | 25 | 50 | Pagination + lazy gate |
| JIG Full Tactical | 25 per mode | 50 | Pagination + lazy gate |
| Full Slate (All Players) | All batters (no card render — compact rows only) | No cap | Game group scroll |
| Full Slate (Qualified) | 25 | 50 | Pagination |
| Full Slate (Elite Targets) | All barrel≥8% from all_players | 50 | Pagination |
| Advanced Strategies | 3 strategy groups visible | All on click | Lazy gate |
| Hits (tab_hits) | 25 | 50 | Lazy gate + pagination |

---

## 3. Game Group Loading Behavior

**Full Slate All Players mode** renders game-by-game:
- Each game group is a collapsible section by default on slates ≥12 games
- First 4 games expand by default (top of card with earliest start time)
- Remaining games collapsed — user taps game header to expand
- Each game header shows: AWAY @ HOME · time · park factor · player count

**Why:** 15 games × 18 batters = 270+ rows. Rendering all at once produces visible lag even with compact rows. Game-group collapse reduces initial render to ~72 rows.

**Exception:** Slates ≤8 games render all game groups expanded by default.

---

## 4. Lazy-Load Gates

**All pitch mix expanders use lazy-load gates.** See Sessions 40 & 41 for implementation pattern.

**Gate rule:** Content builds ONLY after explicit user interaction (button click), not on collapsed state.

**Gate key format:** `_pm_loaded_{key_prefix}_{player_id}_{slate_ts}` — unique per (tab, player, slate). Switching slate dates resets all gates.

**Additional lazy gates required (documented, not yet implemented):**

| Component | Gate Key Pattern | Default State |
|---|---|---|
| tab_advanced_strategies content | `_adv_loaded_{slate_ts}` | Collapsed, load button |
| tab_hits cards | `_hits_loaded_{slate_ts}` | Collapsed, load button |
| JIG Power Profiles | `_jig_pp_loaded_{jig_slate_ts}` | Implemented Session 41 |
| JIG Full Tactical | `_jig_fts_loaded_{jig_slate_ts}_{mode}` | Implemented Session 41 |
| Full Slate game groups (≥12 games) | Per-game group expand state | Collapsed (games 5+) |

---

## 5. Pagination Rules

**Standard page size options:** 10 / 25 / 50 (number input or selectbox)
**Default page size:** 25
**Page state key format:** `{tab_key}_page_size_{context}` — persists within session
**Page navigation:** Simple prev/next buttons. No page number input. No "jump to" field.

**Forbidden pagination patterns:**
- Auto-advance (never auto-scroll to next page)
- Infinite scroll (causes unpredictable Streamlit rerender)
- Server-side pagination (all data already in ranked list — pagination is display only)

---

## 6. Collapsed-by-Default Rules

The following sections **must be collapsed by default** on initial render:

| Section | Reason |
|---|---|
| Pitch mix expander (all tabs) | High computation; lazy-gate required |
| Live Intelligence Feed | Feed content is supplemental |
| Deployment Tray | User opens when ready to act |
| JIG Power Profiles | 25 cards × heavy HTML = significant widget load |
| JIG Full Tactical | Same as above |
| Full Slate game groups (games 5+ on large slates) | Render pressure reduction |
| Advanced Strategies tab | Scoring loops run on first expand |
| Hits tab | Score loops run on first expand |
| Player detail secondary stats (in-card) | Stat row 3 is contextual |
| Full Slate "Full Universe" accordion | Large raw list; supplemental only |

---

## 7. Expanded-State Limits

**Maximum simultaneous expanded pitch mix sections:** 5
- If user has 5 pitch mix sections open and opens a 6th, oldest open section auto-collapses
- Implementation: session_state list of open keys, FIFO eviction at cap

**Maximum simultaneous expanded JIG game-command views:** 3 (Phase 2B future rule)

**Card HTML cache:** Cards rebuild on fingerprint change only. Stable fingerprint = zero rebuild. Cache is session-global with slate_ts-based invalidation (implemented Session 41).

---

## 8. Heavy Component Isolation

**Components classified as heavy (require isolation/gating):**

| Component | Classification | Isolation Method |
|---|---|---|
| Pitch Mix tables (arsenal + batter-vs-pitch + splits) | Heavy | Lazy-load gate |
| HVY card HTML (up to 25) | Medium-heavy | HTML fingerprint cache |
| Intelligence card HTML (up to 12+25) | Medium | HTML fingerprint cache |
| Elite card HTML | Medium | HTML fingerprint cache |
| Portfolio optimizer | Heavy | session_state fingerprint cache |
| Steam detection (`_cached_steam_moves`) | Medium | @st.cache_data TTL=120s |
| P&L CSV read (`_cached_pnl_results`) | Light-medium | @st.cache_data TTL=300s |
| Full Slate compact rows (270+ rows) | Medium | Game-group collapse |
| tab_advanced_strategies scoring loop | Heavy | Lazy gate |
| tab_hits scoring loop | Heavy | Lazy gate |

---

## 9. Table Density Limits

**Qualified table (`_render_qualified_table`):**
- Default columns shown: rank, player, team, barrel, model, EV, edge, confidence, odds, tier, HVY
- Max column count: 12 (Streamlit st.dataframe scrolls horizontally; more than 12 becomes unreadable)
- Row height: compact (default Streamlit data_editor compact mode)

**Full Slate compact rows:**
- 6 stat values per batter row maximum on desktop (BRL/MDL/EV/EDG/CNF/ODDS)
- 4 stat values on mobile (BRL/MDL/EV/EDG)

**Arsenal table inside pitch mix:**
- Max 10 pitches shown. Pitchers rarely throw more than 8; cap at 10 handles outliers.
- Columns: pitch type, usage%, whiff%, avg speed (if available)

---

## 10. Live Feed Saturation Limits

**Maximum feed entries shown at once:** 10
**Maximum steam alerts shown in feed:** 5 (older steam alerts are archived)
**Update frequency (auto-refresh):** User-controlled. Default off. When on: 5-minute minimum interval.
**Feed entry lifetime in UI:** Entries are time-stamped. Entries older than 4 hours are shown with dimmed opacity but not removed (for session audit trail).

**Feed does not:** auto-expand, play sounds, push notifications, block content, or affect model scores.

**Steam badge on mobile:** Shows count only. Clears when user opens feed.

---

*Documentation only. No implementation. No app.py changes. No session_state changes.*
