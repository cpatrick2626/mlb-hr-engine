# Design Decisions — TASK-001 HR Threat Card

## Aesthetic Direction

**Cinematic Intelligence Terminal** — not a sportsbook, not a fantasy app. Feels like a covert analytics workstation. Sparse color, measured glow, monospace everywhere.

### Color language

| Signal | Color | Trigger |
|---|---|---|
| CRITICAL threat | `red-400` + ambient glow | escalationTier = CRITICAL |
| HIGH threat | `amber-400` + soft glow | escalationTier = HIGH |
| MODERATE | `sky-400` | escalationTier = MODERATE |
| LOW | `zinc-500` | escalationTier = LOW |
| Positive edge | `emerald-400` | pitchMatchupEdge, weatherBoost, etc. |
| Negative edge | `red-400` | inverse signals |
| Data labels | `zinc-700` | all metric labels |

Escalation drives the card's ambient glow via `box-shadow`. CRITICAL gets the loudest ring; LOW gets barely-visible ring. This is the only "decoration" — everything else is functional.

### Typography

- Monospace (`font-mono`) for all data values, labels, badges
- Uppercase tracking on all labels (`tracking-[0.22em]`)
- Threat score at 46px dominates — first read is always the score
- Player name at 15px, tight tracking — secondary read
- Labels at 7.5–8.5px — tertiary reference layer

### Layout

```
┌──────────────────────────────────┐
│ [2px accent strip — tier color]  │
│                                  │
│  ● CRITICAL              87      │
│                       THREAT/100 │
│                                  │
│  AARON JUDGE                     │
│  NYY · RF                        │
│ ─────────────────────────────── │
│  BARREL %  HRD HIT %  PITCH EDGE │
│  15.2%     57.3%      +28.0%     │
│  ━━━━━━━   ━━━━━━━━              │
│ ─────────────────────────────── │
│  WEATHER AMP    PTCHR VULN       │
│  +7.0%          74               │
│  AMPLIFIED      ━━━━━━  VULN     │
└──────────────────────────────────┘
```

Width: `max-w-[272px]` — compact enough for sidebar rail, spacious enough for density.

## Props decisions

### `pitchMatchupEdge` — normalized –1 to +1

The HVY Pitch Mix Modifier lives on [0.70, 1.40]. Component normalizes to ±1 scale for display symmetry:
`edge = (hvy – 1.0) / 0.40`

This keeps the UI unit-independent. Caller controls normalization.

### `weatherBoost` — multiplicative

Accepted as raw multiplicative factor (e.g. 1.08) matching engine output. Component converts to "+8%" for display. No transformation loss.

### `pitcherVulnerability` — 0–100 index

Not a direct engine output — caller maps pitcher factor to this scale. Suggested: `Math.round((pit_factor – 0.55) / (1.60 – 0.55) * 100)`. Kept separate from `pitchMatchupEdge` because they are different signals (HVY modifier = batter vs arsenal matchup; vuln = pitcher baseline HR rate vs league).

### `hrThreatScore` — 0–100 composite

Matches engine's composite score `(ev×0.4 + edge×0.35 + confidence×0.25)` rescaled to 0–100. Caller controls this mapping.

## Scanline overlay

Thin repeating CSS gradient at `opacity-[0.018]`. Adds tactile texture without visual noise. `pointer-events-none` + `z-10` ensures no interaction interference.

## Modularity

Three files per task spec. Header and metrics are individually importable for custom layouts. Main card re-exports types so consumers import from one location.
