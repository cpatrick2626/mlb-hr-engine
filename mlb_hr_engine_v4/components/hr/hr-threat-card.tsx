/**
 * HR Threat Card — root component
 *
 * Cinematic tactical HUD. Composes header + metrics subcomponents.
 * Zero external dependencies beyond React + Tailwind.
 *
 * Recommended fonts (add to your <head> or global CSS):
 *   JetBrains Mono — monospace data values
 *   Barlow Condensed — player name display
 */

import React from 'react'
import { HRThreatCardHeader } from './hr-threat-card-header'
import { HRThreatCardMetrics } from './hr-threat-card-metrics'

// ─── Types ────────────────────────────────────────────────────────────────────

export type EscalationTier = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'

export interface HRThreatCardProps {
  /** Display name */
  playerName: string
  /** Team + position, e.g. "NYY · RF" */
  team: string
  /** Composite threat score 0–100 */
  hrThreatScore: number
  /** Barrel rate percentage, e.g. 12.5 */
  barrelPct: number
  /** Hard-hit rate percentage, e.g. 48.2 */
  hardHitPct: number
  /**
   * Pitch matchup edge — normalized –1.0 to +1.0.
   * Positive = favorable matchup for batter.
   * Derived from HVY modifier: (hvy – 1.0) / 0.40
   */
  pitchMatchupEdge: number
  /** Multiplicative weather factor, e.g. 1.08 → displayed as +8% */
  weatherBoost: number
  /** Pitcher vulnerability index 0–100 (higher = more hittable) */
  pitcherVulnerability: number
  escalationTier: EscalationTier
  className?: string
}

// ─── Tier glow config ─────────────────────────────────────────────────────────

const tierGlow: Record<EscalationTier, string> = {
  CRITICAL: '0 0 0 1px rgba(239,68,68,0.28), 0 0 40px rgba(239,68,68,0.10), inset 0 1px 0 rgba(239,68,68,0.10)',
  HIGH:     '0 0 0 1px rgba(245,158,11,0.22), 0 0 32px rgba(245,158,11,0.08), inset 0 1px 0 rgba(245,158,11,0.08)',
  MODERATE: '0 0 0 1px rgba(56,189,248,0.16), 0 0 24px rgba(56,189,248,0.06), inset 0 1px 0 rgba(56,189,248,0.06)',
  LOW:      '0 0 0 1px rgba(255,255,255,0.06)',
}

const tierAccentBg: Record<EscalationTier, string> = {
  CRITICAL: 'bg-red-500',
  HIGH:     'bg-amber-400',
  MODERATE: 'bg-sky-400',
  LOW:      'bg-zinc-700',
}

// ─── Mock data ────────────────────────────────────────────────────────────────

export const mockHRThreatCardData: HRThreatCardProps = {
  playerName: 'Aaron Judge',
  team: 'NYY · RF',
  hrThreatScore: 87,
  barrelPct: 15.2,
  hardHitPct: 57.3,
  pitchMatchupEdge: 0.28,
  weatherBoost: 1.07,
  pitcherVulnerability: 74,
  escalationTier: 'CRITICAL',
}

// ─── Component ────────────────────────────────────────────────────────────────

export function HRThreatCard({
  playerName,
  team,
  hrThreatScore,
  barrelPct,
  hardHitPct,
  pitchMatchupEdge,
  weatherBoost,
  pitcherVulnerability,
  escalationTier,
  className = '',
}: HRThreatCardProps) {
  return (
    <div
      role="group"
      aria-label={`${playerName} HR threat card`}
      className={`relative w-full max-w-[272px] rounded-[3px] bg-[#07090e] overflow-hidden select-none ${className}`}
      style={{ boxShadow: tierGlow[escalationTier] }}
    >
      {/* Escalation accent strip */}
      <div className={`absolute top-0 left-0 right-0 h-[2px] ${tierAccentBg[escalationTier]} opacity-90`} />

      {/* Scanline texture overlay */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-10 opacity-[0.018]"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,1) 2px, rgba(255,255,255,1) 3px)',
        }}
      />

      <HRThreatCardHeader
        playerName={playerName}
        team={team}
        hrThreatScore={hrThreatScore}
        escalationTier={escalationTier}
      />

      <HRThreatCardMetrics
        barrelPct={barrelPct}
        hardHitPct={hardHitPct}
        pitchMatchupEdge={pitchMatchupEdge}
        weatherBoost={weatherBoost}
        pitcherVulnerability={pitcherVulnerability}
      />
    </div>
  )
}

export default HRThreatCard
