# SPEC: CLV Intelligence System v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_post_slate_review_v1.md`, `spec_historical_intelligence_archive_v1.md`, `spec_tactical_deployment_hud_v1.md`
**Runtime cross-reference:** `mlb_hr_engine_v4/tracking/clv.py`, `capture_closing_lines.py`, `analyze_clv.py`

---

## A. SYSTEM PURPOSE

The CLV Intelligence System tracks the quality of deployment timing decisions independent of game outcomes. Closing line value is the single most important metric for evaluating deployment quality in the long run.

**Core doctrine:** A bet that wins is not proof of good deployment. A bet that loses is not proof of bad deployment. CLV won or lost is the only objective measure of whether the operator beat the market.

**Why CLV matters:** The market is an efficient aggregation of all available information. A pick deployed before the market has processed the available edge (early, before smart money or injury news tightens the line) earns positive CLV. A pick deployed after the market has moved toward the model (late, after public steam or sharp action) earns neutral or negative CLV — even if the model was right.

---

## B. CLV TRACKING ARCHITECTURE

### Odds Timeline Structure

Every deployed pick tracks four odds timestamps:

| Timestamp | Label | Description |
|-----------|-------|-------------|
| `open_odds` | OPENING | Odds when the market first offered this prop |
| `deploy_odds` | DEPLOYED | Odds at moment of operator deployment |
| `current_odds` | CURRENT | Live odds at last refresh |
| `close_odds` | CLOSING | Final market odds ~30min before first pitch |

### CLV Calculation

```
CLV (pp) = close_no_vig_pct - deploy_no_vig_pct

Positive CLV = deployed before market tightened (sharp entry)
Negative CLV = deployed after market had already priced the edge
Zero CLV = entered at closing-line value (market-neutral entry)
```

CLV is computed at closing line capture (~30 minutes before first pitch). Until then, `current_odds` provides a live read.

### No-Vig Conversion

All CLV calculations use no-vig probability from the dynamic vig model (`engine/vig.py`).

```
no_vig_prob = market_no_vig_probability(american_odds, book)
```

Where `book` determines the per-book vig correction (FanDuel 9.5%, DraftKings 8.8%, etc.).

---

## C. TIMING-STATE HIERARCHY

Every deployed pick is assigned a timing state based on when it was deployed relative to market movement.

### Six Timing States

```
OPENING → EARLY STRIKE → MARKET DRIFT → LATE STEAM → PRICE COLLAPSE → DEAD ENTRY
```

---

### EARLY STRIKE
**Condition:** Deployed within the first 20% of the market timeline before the closing window.
**CLV typical:** +1.5 to +4.0 pp
**Operational meaning:** Operator deployed before public action or sharp steam moved the line. Maximum timing efficiency.

**Visual treatment:** Green label `EARLY STRIKE`. Clock icon with early-morning color.

---

### MARKET DRIFT
**Condition:** Deployed in the 20–60% window; no significant line movement since deployment.
**CLV typical:** -0.5 to +1.5 pp
**Operational meaning:** Entered during normal market maturation. Acceptable timing. Line has not moved significantly against or for the pick.

**Visual treatment:** Blue-gray label `MARKET DRIFT`. Neutral clock icon.

---

### LATE STEAM
**Condition:** Deployed in the 60–90% window; line moved toward pick since deployment.
**CLV typical:** +0.5 to +2.5 pp (positive because deployment was ahead of steam)
**Operational meaning:** Operator deployed just before sharp steam hit. Favorable outcome — operator was directionally right about timing.

**Visual treatment:** Amber label `LATE STEAM`. Upward arrow icon.

---

### PRICE COLLAPSE
**Condition:** Deployed odds significantly shorter than current/closing odds. Market moved against the pick.
**CLV typical:** -2.0 to -5.0 pp
**Operational meaning:** Operator deployed and then the market found information that made the pick more expensive (or sharps faded it). Deployed price now looks unfavorable vs closing line.

**Visual treatment:** Orange-red label `PRICE COLLAPSE`. Downward arrow icon.

---

### VALUE RECOVERED
**Condition:** Odds initially moved against pick, then recovered. Deployed odds are near or better than closing line despite mid-session adverse movement.
**CLV typical:** 0 to +2.0 pp
**Operational meaning:** The model was right; temporary adverse steam reversed. Timing was defensible.

**Visual treatment:** Teal label `VALUE RECOVERED`. Recovery arrow icon.

---

### DEAD ENTRY
**Condition:** Deployed within the final 10% of the market window (after sharp money and public action have fully priced the market). No CLV advantage vs closing line.
**CLV typical:** -1.5 to 0 pp
**Operational meaning:** Deployed too late. The edge that existed at opening has been consumed by market efficiency. At best, market-neutral. At worst, slightly unfavorable.

**Visual treatment:** Muted gray label `DEAD ENTRY`. Late clock icon.

---

## D. CLV TRACKING HUD ELEMENT

The CLV Intelligence System maintains a live HUD panel during active sessions.

```
CLV INTELLIGENCE
──────────────────────────────────────────────────────
Session timing states:
  EARLY STRIKE:    1 pick   +2.4pp avg
  MARKET DRIFT:    3 picks  +0.8pp avg
  LATE STEAM:      1 pick   +1.1pp avg
  PRICE COLLAPSE:  1 pick   -2.8pp avg
  DEAD ENTRY:      0 picks

Session CLV average: +0.7pp
Timing efficiency: SLIGHTLY SHARP

Best entry: Aaron Judge +220 → closed +190  (+3.1pp CLV)
Worst entry: P. Alonso +280 → closed +310   (-2.8pp PRICE COLLAPSE)
──────────────────────────────────────────────────────
```

This panel is accessible from the session HUD in Layer 3 (see `spec_tactical_deployment_hud_v1.md`). It does not demand attention when CLV is positive. It escalates visually when PRICE COLLAPSE or negative overall CLV is detected.

---

## E. MARKET MOVEMENT TIMELINE

The CLV system renders a per-pick market movement timeline in the post-deployment view and in the post-slate review.

```
AARON JUDGE (NYY) — HR Yes — +220 at deploy

Opening:   +240   ─┐
                    │ ↓ early steam (−20)
Deployed:  +220   ──┤ ← EARLY STRIKE entry
                    │ ↓ continued tightening
Current:   +200   ──┤
                    │ ↓ sharp action
Closing:   +190   ─┘

CLV won: +3.1pp
Timing state: EARLY STRIKE
```

The timeline is only rendered in the post-slate review and historical archive view. During the session, only the summary label is shown to avoid cognitive load during active deployment.

---

## F. MARKET LABELS AND DEPLOYMENT TIMING REVIEW

The CLV system assigns each deployed pick a retrospective timing grade as part of post-slate review.

### Timing Grade Definitions

| Grade | CLV Range | Timing Label |
|-------|-----------|-------------|
| A | +2.0pp+ | SHARP ENTRY |
| B | +1.0 to +2.0pp | GOOD TIMING |
| C | 0 to +1.0pp | NEUTRAL ENTRY |
| D | -1.0 to 0pp | LATE ENTRY |
| F | Below -1.0pp | POOR TIMING |

### Session Timing Grade

The session receives an aggregate timing grade based on average CLV across all deployed picks:

| Session Average CLV | Session Timing Verdict |
|--------------------|----------------------|
| +2.0pp+ | SHARP — consistent early market exploitation |
| +1.0 to +2.0pp | EFFECTIVE — good market timing discipline |
| 0 to +1.0pp | NEUTRAL — market-rate entries |
| -1.0 to 0pp | SOFT — late to market consistently |
| Below -1.0pp | POOR — consistent late/dead entries |

---

## G. CLV INTELLIGENCE ARCHIVE

Historical CLV data is preserved in the Historical Intelligence Archive (see `spec_historical_intelligence_archive_v1.md`) with the following dimensions for long-term analysis:

- CLV by barrel tier (are high-barrel picks entered earlier by habit?)
- CLV by escalation tier (are FIRE picks captured earlier than WATCH picks?)
- CLV by day-of-week (are certain days consistently better/worse for entry timing?)
- CLV by odds range (do long shots capture more timing edge than favorites?)
- CLV trend over time (is operator timing improving or degrading?)
- CLV by slip category (do Singles capture better CLV than Stacks?)

---

## H. OPERATIONAL CALIBRATION BETWEEN CLV AND ROI

CLV and ROI are complementary but separate measures. The operator must understand both.

**CLV answers:** Was the deployment process sharp? Did the operator exploit market inefficiency through timing?

**ROI answers:** Did the picks win? (Influenced heavily by variance in the short run.)

**Long-run relationship:** CLV predicts future ROI. Consistent positive CLV with negative ROI = variance; wait for larger sample. Consistent negative CLV with positive ROI = lucky; the process is broken even if results look good.

**Dashboard separation doctrine:** CLV metrics and ROI metrics are displayed in separate panels in the post-slate review. They are never merged into a single "performance" score. The operator must read both independently.

---

## I. CLV CAPTURE WORKFLOW

### Pre-Game Capture (30 minutes before first pitch)

1. Operator (or scheduled script) runs `capture_closing_lines.py`
2. Script fetches current odds from The Odds API for all deployed picks
3. Odds are stored as `snapshot_type=closing` in `line_snapshots.csv`
4. CLV is computed for each pick: `clv_pp = close_no_vig - deploy_no_vig`
5. CLV written to `pick_tracker.csv` (fields: `close_odds`, `close_no_vig_pct`, `clv_pp`, `clv_pct_rel`)
6. CLV intelligence panel in the session HUD updates

**Timing requirement:** Capture must occur before first pitch to count as "closing line." Post-game captures are marked as retrospective and excluded from timing efficiency analysis.

### Manual CLV Capture

If the scheduled capture fails or is missed, the operator can manually trigger CLV capture from the session sidebar. The manual capture is timestamped as `snapshot_type=manual` and included in CLV analysis but flagged as potentially post-deadline.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
