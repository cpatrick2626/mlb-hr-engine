# Pitcher Vulnerability Strip — Live Board Build (Phase 2A)
**Date:** 2026-06-23  
**Status:** BUILT — local validation pending  
**Owner:** Claude Code (Sonnet 4.6)  
**Surface:** root `frontend/` (live production static board)  
**Risk:** LOW-MEDIUM

---

## What Was Built

New component `PitcherVulnerabilityStrip` (pvs-*) wired directly to existing `window.LEADERBOARD_ROWS` globals (MAIN). No new fetch, no new API fields, no backend touch.

**New file:**
- `frontend/assets/js/pitcher-vulnerability-strip.js`

**Edited files:**
- `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js` (Stage) — one-line injection between `<HRThreatZone>` and `<div className="md-room">`
- `frontend/index.html` — pvs-* CSS block appended to Phase 1 style block; one `<script type="text/babel">` tag added after hr-threat-zone.js

**Wiki only:**
- `wiki/doctrine/known-gaps.md` — opphr/pitcher_hr9 ambiguity recorded
- `wiki/sessions/2026-06-23-pvs-live-board-build.md` (this file)
- `wiki/log.md` — session log entry prepended

---

## Data Wiring

**Source:** `window.LEADERBOARD_ROWS` (MAIN only; returns null on JIG context)  
**Dedup key:** `pitcher_id` (fallback: `pitcher_name`)  
**Sort:** `opphr` desc; tiebreak `pitcher_barrel_allowed` desc  
**Display:** top 6 desktop, top 4 mobile (mobile via `.pvs-mobile` column layout)

| Display field | Source field | Formatter |
|---|---|---|
| HR/9 | `opphr` | `.toFixed(2)` |
| ERA | `pitcher_era` | `.toFixed(2)` |
| BRLR% | `pitcher_barrel_allowed × 100` | `.toFixed(1) + "%"` |
| K% | `pitcher_k_pct` | `.toFixed(1)` |
| Name (desktop) | `pitcher_name` | full name |
| Name (mobile) | `pitcher_name` | last name only |
| Hand | `pitcher_hand` | "LHP" / "RHP" |

---

## Bucket Ruleset

| opphr | Label | Color |
|---|---|---|
| null | PENDING | `#6b7872` (distinct label — unknown ≠ low-vulnerability) |
| ≥ 1.3 | EXPLOITABLE | `#1aff66` |
| ≥ 0.9 | ELEVATED | `#ffb020` |
| < 0.9 | STANDARD | `#6b7872` |

Thresholds sourced from existing FSM `opphr` bucketsHi: [1.5, 1.3, 1.0, 0.7]. No new numbers introduced.

---

## Null Safety

- Any null display field → `"—"` (never 0, never fabricated)
- null `opphr` → PENDING bucket, not STANDARD — distinct label preserves missing ≠ low-vulnerability distinction
- null/missing pitcher_id AND pitcher_name → row skipped in dedup (no ghost cards)
- Empty pitchers array after dedup → component returns null (no empty strip renders)

---

## MAIN/JIG Isolation

- `isJigContext` prop checked first; returns `null` immediately on JIG context
- Source is exclusively `window.LEADERBOARD_ROWS` (MAIN)
- No JIG rows consumed, no JIG scoring touched

---

## Known Issue Recorded

`opphr` (FSM_COLS, confirmed in LEADERBOARD_ROWS) and `pitcher_hr9` (FsmPitchMix) may be the same underlying field under two names, or may diverge. Recorded in `wiki/doctrine/known-gaps.md`. Build uses `opphr` exclusively (confirmed column). Requires one targeted backend audit to resolve.

---

## Preserved

- Phase 1: SlateCommandStrip, HRThreatZone — untouched
- Full Slate Matrix — untouched
- Mobile flow — pvs-* mobile breakpoint at 768px; pvs-desktop hidden, pvs-mobile column shown
- No backend / API / scoring / config / Next.js prototype touched

---

## Validation Checklist (local)

```
cd frontend && python -m http.server 4173
```

- [ ] PVS strip appears between HR Threat Zone and Full Slate Matrix
- [ ] Real pitchers render (deduped from batter rows, not duplicated)
- [ ] Green EXPLOITABLE / amber ELEVATED / muted STANDARD buckets visible
- [ ] null opphr → PENDING label (not STANDARD)
- [ ] BRLR% / K% show "—" when null, show real value when present
- [ ] Full Slate Matrix unchanged below the strip
- [ ] Mobile (≤768px): pvs-mobile column renders, pvs-desktop hidden
- [ ] JIG lens: PVS strip absent (returns null)
- [ ] No console errors

---

## Cross-References

- `wiki/sessions/2026-06-23-phase1-tactical-layer-shipped.md` — Phase 1 (SlateCommandStrip + HRThreatZone)
- `wiki/doctrine/known-gaps.md` — opphr/pitcher_hr9 ambiguity
- `wiki/sessions/2026-06-22-pitcher-vulnerability-live-wire.md` — prior Next.js prototype build (NOT this surface)
- Phase 2B next: Escalation Feed (escalation-feed.js) — separate build after this validates
