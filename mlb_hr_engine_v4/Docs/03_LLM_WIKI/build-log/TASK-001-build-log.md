# Build Log — TASK-001 HR Threat Card

## Summary

Built three React/TypeScript/Tailwind components implementing the HR Threat Card UI primitive.

## Files Created

| File | Role |
|---|---|
| `components/hr/hr-threat-card.tsx` | Root card — composes header + metrics, owns prop types, exports mock data |
| `components/hr/hr-threat-card-header.tsx` | Player identity + escalation badge + threat score display |
| `components/hr/hr-threat-card-metrics.tsx` | 5-metric grid — barrel%, hard hit%, pitch edge, weather, pitcher vuln |

## Prop Interface

```ts
interface HRThreatCardProps {
  playerName: string
  team: string
  hrThreatScore: number        // 0–100 composite
  barrelPct: number            // e.g. 12.5
  hardHitPct: number           // e.g. 48.2
  pitchMatchupEdge: number     // –1.0 to +1.0 (derived: (hvy – 1.0) / 0.40)
  weatherBoost: number         // multiplicative, e.g. 1.08
  pitcherVulnerability: number // 0–100
  escalationTier: EscalationTier // 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'
  className?: string
}
```

## Design Decisions

See `Docs/09_DECISIONS/TASK-001-threat-card-decisions.md`.

## Usage

```tsx
import { HRThreatCard, mockHRThreatCardData } from './components/hr/hr-threat-card'

// Mock data example
<HRThreatCard {...mockHRThreatCardData} />

// Live data
<HRThreatCard
  playerName={pick.name}
  team={`${pick.team} · ${pick.position}`}
  hrThreatScore={Math.round(pick.composite_score * 100)}
  barrelPct={pick.barrel_rate * 100}
  hardHitPct={pick.hard_hit_pct * 100}
  pitchMatchupEdge={(pick.hvy_modifier - 1.0) / 0.40}
  weatherBoost={pick.weather_factor}
  pitcherVulnerability={Math.round(pick.pitcher_vuln_index)}
  escalationTier={deriveEscalationTier(pick.composite_score)}
/>
```

## Escalation Tier Mapping (suggested)

```ts
function deriveEscalationTier(compositeScore: number): EscalationTier {
  if (compositeScore >= 0.80) return 'CRITICAL'
  if (compositeScore >= 0.60) return 'HIGH'
  if (compositeScore >= 0.40) return 'MODERATE'
  return 'LOW'
}
```
