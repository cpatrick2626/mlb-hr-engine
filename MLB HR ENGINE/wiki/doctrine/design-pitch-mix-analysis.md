# Design: Pitch Mix Analysis (Modal)

**Last Updated:** 2026-06-15

---

## Summary

The Pitch Mix modal surfaces pitcher arsenal and batter-vs-pitch-type matchup data inside the HR threat card. It is display-only and does NOT affect scoring.

---

## Prior State (Pre-2026-06-15) — Fabricated

The entire modal was fabricated via seeded RNG:
- `fsmH2HData` and `fsmPitchData` were randomly generated on every render.
- Pitcher stats (ERA, WHIP, K, BB), handedness, arsenal composition, H2H, and the 3×3 zone grid were all fake.
- **Confirmed: fabricated data NEVER affected scoring.** Scoring model uses real Savant + MLB Stats API data via the separate pipeline. The modal was a display-only fabrication.

---

## 2026-06-15 — De-fabricated, Wired to Real Data

**Change:** RNG fabrication removed. All modal fields now sourced from real data.

**Real data sources:**

| Field | Source |
|-------|--------|
| Pitcher ERA / WHIP / K / BB | Pipeline row fields (MLB Stats API season stats) |
| Barrel% allowed / HH% / FB% / GB% | Pipeline row fields (Baseball Savant) |
| Handedness | Pipeline row fields |
| HR/9 | Pipeline row fields |
| Arsenal composition / pitch stats / H2H | `/api/pitcher-detail` endpoint (on-demand, cached) |
| Batter-vs-pitch-type table | `/api/pitcher-detail` endpoint |

**Removed:** 3×3 strike-zone grid. No free real-time data source exists for zone-level data. Replaced with real batter-vs-pitch-type table.

**Insufficient data behavior:** Fields show `--` when data is unavailable. Data is never fabricated as a fallback.

**Commit:** `8fee765`

---

## Architecture Notes

- Modal triggered by clicking any HR Threat Meter / matchup element on MAIN or JIG boards.
- Pitcher detail data is fetched on-demand and cached per pitcher per day.
- The modal is display-only. No modal field influences `model_prob`, `model_tier_rank`, `jigScore`, or role flags.

---

## Cross-References

- [[ticket-roles]] — roles also display-only
- [[main-jig-separation]] — HVY pitch-mix signal display-only on JIG side
- [[jig-tactical-doctrine]] — arsenal hunting doctrine
