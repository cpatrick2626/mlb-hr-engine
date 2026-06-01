import React from 'react'
import { HRThreatCardHeader } from './hr-threat-card-header'
import { HRThreatCardMetrics } from './hr-threat-card-metrics'

// ─── Types ────────────────────────────────────────────────────────────────────

export type EscalationTier = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'

export interface HRThreatCardProps {
  playerName: string
  team: string
  hrThreatScore: number
  barrelPct: number
  hardHitPct: number
  pitchMatchupEdge: number
  weatherBoost: number
  pitcherVulnerability: number
  escalationTier: EscalationTier
  className?: string
}

// ─── Tier glow — ambient depth, not neon ─────────────────────────────────────

const tierGlow: Record<EscalationTier, string> = {
  CRITICAL: '0 0 0 1px rgba(220,38,38,0.32), 0 0 48px rgba(220,38,38,0.12), 0 0 12px rgba(220,38,38,0.08), inset 0 1px 0 rgba(220,38,38,0.12)',
  HIGH:     '0 0 0 1px rgba(217,119,6,0.26), 0 0 36px rgba(217,119,6,0.09), inset 0 1px 0 rgba(217,119,6,0.10)',
  MODERATE: '0 0 0 1px rgba(14,165,233,0.20), 0 0 26px rgba(14,165,233,0.06), inset 0 1px 0 rgba(14,165,233,0.07)',
  LOW:      '0 0 0 1px rgba(255,255,255,0.08)',
}

const tierAccentTop: Record<EscalationTier, string> = {
  CRITICAL: 'bg-red-500',
  HIGH:     'bg-amber-400',
  MODERATE: 'bg-sky-400',
  LOW:      'bg-zinc-700',
}

const tierCornerBracket: Record<EscalationTier, string> = {
  CRITICAL: 'rgba(220,38,38,0.40)',
  HIGH:     'rgba(217,119,6,0.32)',
  MODERATE: 'rgba(14,165,233,0.26)',
  LOW:      'rgba(255,255,255,0.14)',
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
  const bracketColor = tierCornerBracket[escalationTier]

  return (
    <div
      role="group"
      aria-label={`${playerName} HR threat card`}
      className={`relative w-full max-w-[272px] rounded-[2px] bg-[#060C15] overflow-hidden select-none ${className}`}
      style={{ boxShadow: tierGlow[escalationTier] }}
    >
      {/* Top accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-[2px] ${tierAccentTop[escalationTier]}`}
           style={{ opacity: 0.85 }} />

      {/* Corner brackets — tactical framing */}
      <div aria-hidden className="pointer-events-none absolute top-0 left-0 w-[12px] h-[12px] z-20"
           style={{ borderTop: `1px solid ${bracketColor}`, borderLeft: `1px solid ${bracketColor}` }} />
      <div aria-hidden className="pointer-events-none absolute top-0 right-0 w-[12px] h-[12px] z-20"
           style={{ borderTop: `1px solid ${bracketColor}`, borderRight: `1px solid ${bracketColor}` }} />
      <div aria-hidden className="pointer-events-none absolute bottom-0 left-0 w-[12px] h-[12px] z-20"
           style={{ borderBottom: `1px solid rgba(255,255,255,0.07)`, borderLeft: `1px solid rgba(255,255,255,0.07)` }} />
      <div aria-hidden className="pointer-events-none absolute bottom-0 right-0 w-[12px] h-[12px] z-20"
           style={{ borderBottom: `1px solid rgba(255,255,255,0.07)`, borderRight: `1px solid rgba(255,255,255,0.07)` }} />

      {/* Scanline texture */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-10"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255,255,255,1) 3px, rgba(255,255,255,1) 4px)',
          opacity: 0.020,
        }}
      />

      {/* Inner glass gradient */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background: 'linear-gradient(180deg, rgba(255,255,255,0.012) 0%, rgba(255,255,255,0.003) 30%, transparent 65%)',
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
