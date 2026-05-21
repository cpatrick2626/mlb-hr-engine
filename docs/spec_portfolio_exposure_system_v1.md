# SPEC: Portfolio Exposure System v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_deployment_queue_v1.md`, `spec_bankroll_command_layer_v1.md`, `spec_risk_governance_v1.md`

---

## A. SYSTEM PURPOSE

The Portfolio Exposure System monitors concentration risk across every active deployment session. It surfaces the invisible risk created when picks cluster around the same team, pitcher, game, or market segment.

**Core doctrine:** Individual pick quality does not protect against portfolio fragility. A slate of ten FIRE-tier picks from the same team is worse than a slate of ten STRONG-tier picks distributed across ten teams. The exposure system makes this visible before it becomes a problem.

---

## B. SEVEN EXPOSURE DIMENSIONS

Every active deployment session is analyzed across seven dimensions simultaneously. All seven dimensions are monitored in real-time as picks are added and removed.

### Dimension 1: Player Exposure %
The percentage of total session capital allocated to a single player's HR prop.

- **Normal:** ≤ 10% per player
- **Elevated:** 10–20% — amber advisory
- **High:** > 20% — orange-red warning; auto-flag in queue

### Dimension 2: Team Exposure %
The percentage of total session capital across all picks from a single team.

- **Normal:** ≤ 25% per team
- **Elevated:** 25–35% — amber advisory
- **High:** > 35% — warning + queue suppression of additional team picks

### Dimension 3: Game Exposure %
The percentage of total session capital concentrated in a single `game_pk`.

- **Normal:** ≤ 30% per game
- **Elevated:** 30–45% — amber advisory
- **High:** > 45% — orange-red warning + correlated risk note

### Dimension 4: Pitcher-Target Concentration
The number of picks whose outcome depends on a single opposing pitcher.

- **Normal:** ≤ 3 picks vs same pitcher
- **Elevated:** 4 picks — advisory: "Concentrated pitcher target"
- **High:** 5+ picks — warning: "Pitcher dependency risk"

This dimension is unique because it creates reverse-correlation risk: if the pitcher is dominant, multiple picks fail simultaneously. This is different from team concentration.

### Dimension 5: Weather Correlation
The degree to which picks cluster around similar weather environments.

Relevant when:
- 3+ picks share the same outdoor game in high-wind or high-temp conditions
- Environmental factor (temp/wind/humidity) creates a shared tail-risk scenario

**Weather correlation label:** `⚠ ENV CLUSTER` — shown when 3+ picks share outdoor weather in the same environmental quartile.

### Dimension 6: Market Duplication
The degree to which picks target the same EV tier or odds band.

If 4+ picks all have odds between +200 and +280, they are sharing market positioning and may reflect the same market pricing error rather than independent edges.

**Market duplication label:** `ℹ MARKET OVERLAP` — informational; not a hard flag.

### Dimension 7: Overstack Indicator
Combined measure of same-lineup + same-game + same-pitcher concentration.

When all three dimensions converge on a single game:
- Same-lineup picks (team concentration) +
- Multiple batters vs same pitcher (pitcher concentration) +
- Multiple picks from same `game_pk` (game concentration)

**Overstack states:**

| Score | Overstack State | Treatment |
|-------|----------------|-----------|
| 0–1 | None | No indicator |
| 2 | MILD | Blue advisory |
| 3 | MODERATE | Amber advisory |
| 4+ | HEAVY | Orange-red warning + operator acknowledgement required |

---

## C. EXPOSURE HEATMAP ARCHITECTURE

The exposure heatmap is the primary visual surface for the Portfolio Exposure System.

### Heatmap Layout

A compact grid. Teams on rows, games on columns. Cell fill intensity = capital concentration. Pitch targets annotated below team rows.

```
EXPOSURE HEATMAP — 2026-05-20
───────────────────────────────────────────────────────────────
           │ NYY-BOS  │ HOU-LAA  │ SD-COL  │ CHC-MIL │ Total
───────────────────────────────────────────────────────────────
NYY        │ ████████ │          │         │         │ 34% ⚠
BOS        │          │          │         │         │  0%
HOU        │          │ ████     │         │         │ 16%
NYM        │          │          │         │ ██       │  8%
COL        │          │          │ ██       │         │  8%
───────────────────────────────────────────────────────────────
Game %     │   34%⚠  │   16%    │  8%     │  8%     │ 66%

PITCHER TARGETS:
  G. Cole (NYY/BOS): 4 picks ⚠
  C. Bassitt (BOS): 0 picks
  F. Valdez (HOU): 3 picks
───────────────────────────────────────────────────────────────
Bankroll deployed: 66% · N_eff: 3.8 · Fragility: 52/100 MODERATE
```

### Heatmap Color Scale

- **Empty** — no picks in this cell
- `#1a1a35` (very faint) — 1–5% concentration
- `#2a2a55` — 5–15%
- `#4a4a80` — 15–25%
- `#F5A623` (amber) — 25–35% (elevated)
- `#E87040` (orange-red) — 35%+ (high)

### Heatmap Update Frequency

The heatmap updates after every pick is added to or removed from the Slip Builder. It does not require a page refresh. It is a live reflection of current session state.

---

## D. SATURATION INDICATORS

Bankroll saturation is tracked across three levels.

### Level 1: Session Saturation
Total session capital deployed (all categories combined) as a percentage of the session bankroll.

```
SESSION BANKROLL: $250.00
Deployed:         $138.50  (55%)
Remaining:        $111.50
```

Visual indicator: horizontal bar. Color shifts:
- 0–50%: `#4a4a70` (normal)
- 50–70%: `#F5A623` (elevated — consider slowing)
- 70–85%: `#E87040` (high — advisory shows)
- 85%+: `#C0392B` (saturated — new picks soft-blocked)

### Level 2: Category Saturation
Each slip category has its own saturation indicator. Prevents over-allocation to one category.

Category caps (configurable in bankroll command layer):
- Singles: max 60% of session bankroll
- Doubles: max 30%
- Stacks: max 15%
- Longshots: max 10%
- Volatility: max 10%

### Level 3: Quality Saturation
The percentage of deployed capital in sub-optimal archetypes (barrel < 6%, WATCH tier).

If quality saturation exceeds 30% of deployed capital, an advisory appears: "Low-quality allocation high — consider repositioning."

---

## E. OPERATIONAL RISK STATES

The Portfolio Exposure System assigns the session an overall operational risk state based on combined dimension readings.

| State | Meaning | System Behavior |
|-------|---------|----------------|
| BALANCED | No dimension ≥ elevated | No advisories; normal queue operation |
| ELEVATED | 1 dimension ≥ elevated | Amber advisory in heatmap; normal queue operation |
| CONCENTRATED | 2+ dimensions ≥ elevated OR 1 dimension ≥ high | Orange-red banner; soft gate on new picks in affected dimensions |
| FRAGILE | 3+ dimensions ≥ elevated OR 2 ≥ high | Warning banner; new picks in all affected dimensions suppressed until operator acknowledges |
| OVEREXPOSED | Fragility score > 70 OR bankroll saturation > 85% | Hard soft gate; session pause advisory shown |

The operational risk state banner appears at the top of the Queue and Slip Builder at all times when state ≥ ELEVATED.

---

## F. DIVERSIFICATION SYSTEM

The Portfolio Exposure System does not just warn about concentration — it provides diversification guidance.

### Diversification Advisory

When state ≥ CONCENTRATED, the system surfaces 2–3 available queue picks that would improve balance:

```
┌──────────────────────────────────────────────────────────────┐
│  DIVERSIFICATION ADVISORY                                    │
│                                                              │
│  Session concentration: NYY 34% · G. Cole target 4 picks   │
│                                                              │
│  Diversification options in queue:                          │
│  ● Manny Machado (SD)  — STRONG · EV:+3.8% · 0% SD exposure │
│  ● Ian Happ (CHC)      — STRONG · EV:+3.2% · 0% CHC/CHC     │
│                                                              │
│  Adding either would reduce fragility score from 52 → 38.   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

This is advisory only. The system suggests — the operator decides. The diversification panel cannot force pick changes.

### Balance Score

Every session state includes a **Balance Score** (0–100):
- 100 = perfectly distributed across teams, games, and capital
- 0 = all capital in a single game

Balance Score is not the primary KPI — N_eff and fragility score are more operationally meaningful — but it is surfaced as a quick read in the session HUD.

---

## G. EXPOSURE DIMENSION INTERACTION

Two-dimensional risk compound when multiple dimensions elevate simultaneously.

**Compounding pairs:**

| Dimension A | Dimension B | Compounded Risk |
|------------|------------|----------------|
| Team Exposure HIGH | Game Exposure HIGH | Same-game lineup saturation — correlated loss risk extreme |
| Pitcher Target HIGH | Team Exposure HIGH | Single pitcher failure destroys multiple picks |
| Weather Correlation | Game Exposure HIGH | Environmental collapse wipes multiple picks |
| Market Duplication | Pitcher Target HIGH | Same market mispricing + same pitcher = single factor risk |

When two dimensions compound at HIGH level, the system flags a **COMPOUND RISK** alert:

```
⚠ COMPOUND RISK: Team + Pitcher Target both at HIGH
   NYY (4 picks) all face G. Cole domination risk.
   If Cole is dominant tonight, 4 separate bets lose.
   This is not 4 independent bets — it is 1 effective bet.
```

---

## H. CORRELATION RISK DISPLAY

Correlation risk is surfaced as a separate panel below the heatmap.

```
CORRELATION PROFILE
──────────────────────────────
Portfolio N_eff: 3.8 of 8 picks
Effective independence: 47%

Correlation breakdown:
  Same-lineup pairs:     4 pairs (ρ=0.40)
  Cross-game pairs:      8 pairs (ρ=0.04)
  Pitcher-target groups: 2 groups

Variance inflation: 2.1× vs independent picks

⚠ Consider adding 2 cross-game picks to raise N_eff above 5.
```

The correlation panel updates live. It is always visible when the Slip Builder is open. It is compact — three to five lines — and expands to full detail on operator tap.

---

## I. OVERSTACK PREVENTION

The system prevents inadvertent overstack through progressive visibility.

**Stage 1 — Queue warning** (before pick enters slip):
When a pick would create a stack ≥ 3 from the same team/game, a warning pill appears on the queue row: `⚠ Stack 3+`

**Stage 2 — Slip Builder warning** (when pick added to slip):
Slip Builder shows updated overstack indicator before confirming the add.

**Stage 3 — Checkpoint review** (at category review gate):
Category review checkpoint shows stack concentration explicitly. Operator must see it before finalizing.

**Stage 4 — Full slip review** (at execution summary):
Execution summary always includes the current overstack state. If HEAVY overstack, the state is shown in orange-red and requires explicit acknowledgement before `[Mark All as Submitted]` becomes active.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*
