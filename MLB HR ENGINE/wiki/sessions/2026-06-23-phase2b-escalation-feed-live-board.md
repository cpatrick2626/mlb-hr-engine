# Phase 2B — Escalation Feed on Live Board

**Date:** 2026-06-23
**Agent:** Claude Code
**Risk:** LOW (live frontend/, same strip pattern as Phase 2A)
**Status:** BUILT / LOCAL VALIDATION PENDING

---

## Task

Build the Escalation Feed as a vertical priority list on the live board (`root frontend/`), positioned after the Pitcher Vulnerability Strip (Phase 2A) and before the `<div className="md-room">` Full Slate Matrix container.

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/assets/js/escalation-feed.js` | NEW — EscalationFeed + EscRow components |
| `frontend/index.html` | CSS block (`esc-*`) added before `</head>`; script tag added after `pitcher-vulnerability-strip.js` |
| `frontend/assets/js/cfdd4178-a139-4f84-b282-b84f76971c49.js` | +1 line: `<EscalationFeed rows={rows} isJigContext={engine.id === "jig"} />` injected after PitcherVulnerabilityStrip, before md-room div |

---

## Derivation as Wired

**Tier → Level mapping:**
- APEX → CRITICAL (#ff3344)
- ELITE → HIGH (#ff8a93)
- EDGE → HIGH (#1aff66)
- SIGNAL → MODERATE (#3b6fff)
- WATCH → LOW (#ffb020)
- COLD → excluded (no entry in ESC_LEVEL map)

**Headline waterfall (first match wins, null-safe):**
1. `barrel ≥ 8` → `"BARREL X.X%"`
2. `hh ≥ 45` → `"HH X.X%"`
3. `opphr ≥ 1.3` → `"HVY PITCHER X.XX HR/9"`
4. `hrpa != null` → `"HR PROB X.X%"` (hrpa × 100)
5. Any step where the field is null → skip to next rule; never render null/0 as signal

**Sort:** level priority (CRITICAL=0, HIGH=1, MODERATE=2, LOW=3) ascending, then `hrpa` descending within level.

**Display caps:** desktop top 8, mobile top 5. Because sort places WATCH (LOW=3) after MODERATE (MODERATE=2), WATCH naturally falls off the 8-cap before MODERATE does — satisfying the "drop WATCH before MODERATE" spec requirement without special logic.

---

## Desktop Behavior

Vertical list, `esc-desktop` visible. Each `esc-row` has:
- Left border accent in `--tc` color (tier color)
- LEVEL label (CRITICAL / HIGH / MODERATE / LOW) in tier color
- Player name (uppercase, truncated with ellipsis)
- Team abbrev
- Headline stat (derived, in tier color, tabular-nums mono)
- Flat "LIVE" badge (no timestamp)

## Mobile Behavior (≤768px)

`esc-desktop` hidden, `esc-mobile` shown. Same `esc-row` markup, capped at 5.

---

## MAIN/JIG Isolation

- `EscalationFeed` returns `null` immediately if `isJigContext === true`.
- Source is the `rows` prop passed from Stage, which is already LEADERBOARD_ROWS (MAIN) in the fullSlate context.
- No JIG data is ever rendered.

---

## Protected Surfaces — Untouched

- Phase 1: SlateCommandStrip, HRThreatZone — unchanged
- Phase 2A: PitcherVulnerabilityStrip — unchanged
- Full Slate Matrix — unchanged
- Mobile flow — unchanged
- Next.js prototype (`mlb_hr_engine_v4/frontend/`) — not touched
- Backend / API / scoring / config / pipeline / Fly.io — not touched

---

## Validation (local — operator to confirm)

```
python -m http.server 4173  # from frontend/
# Open localhost:4173
```

Checks:
- [ ] Escalation Feed appears between PVS strip and Full Slate Matrix
- [ ] Real players with derived level labels + headline stats
- [ ] Flat LIVE badge visible, no timestamps
- [ ] COLD tier not rendered
- [ ] Null field → skips to next waterfall rule (no "null%" or "HR PROB 0.0%")
- [ ] CRITICAL rows appear above HIGH, HIGH above MODERATE, MODERATE above LOW
- [ ] Desktop: up to 8 rows visible
- [ ] Mobile (≤768px): esc-desktop hidden, esc-mobile shows up to 5 rows
- [ ] PVS strip, HR Threat Zone, Slate Command Strip all intact
- [ ] No console errors

---

## Self-Review

**Changed files:** 3 (1 new JS, 2 modified — index.html, cfdd4178-*.js)

**Derivation as wired:** Tier→level colors match spec exactly. Waterfall null-guards at each step (null field → skip, not false-positive zero). Sort is priority asc / hrpa desc. Caps at 8 desktop / 5 mobile via `.slice()`.

**MAIN/JIG isolation:** Hard null-return on `isJigContext`. rows prop is already MAIN data when this component renders.

**DO NOT COMMIT / DO NOT PUSH** without operator authorization.
