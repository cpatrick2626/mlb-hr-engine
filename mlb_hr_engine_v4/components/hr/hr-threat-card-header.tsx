import React from 'react'
import type { EscalationTier } from './hr-threat-card'

interface HRThreatCardHeaderProps {
  playerName: string
  team: string
  hrThreatScore: number
  escalationTier: EscalationTier
}

type TierConfig = {
  badge: string
  badgeRing: string
  dotClass: string
  scoreClass: string
  scoreGlow: string | undefined
}

const TIER_CONFIG: Record<EscalationTier, TierConfig> = {
  CRITICAL: {
    badge: 'CRITICAL',
    badgeRing: 'bg-red-500/8 ring-1 ring-red-500/35',
    dotClass: 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.9)]',
    scoreClass: 'text-red-400',
    scoreGlow: '0 0 24px rgba(239,68,68,0.35)',
  },
  HIGH: {
    badge: 'HIGH ALERT',
    badgeRing: 'bg-amber-500/8 ring-1 ring-amber-500/30',
    dotClass: 'bg-amber-400 shadow-[0_0_6px_rgba(245,158,11,0.8)]',
    scoreClass: 'text-amber-400',
    scoreGlow: '0 0 20px rgba(245,158,11,0.28)',
  },
  MODERATE: {
    badge: 'MODERATE',
    badgeRing: 'bg-sky-500/8 ring-1 ring-sky-500/25',
    dotClass: 'bg-sky-400',
    scoreClass: 'text-sky-400',
    scoreGlow: undefined,
  },
  LOW: {
    badge: 'LOW',
    badgeRing: 'bg-zinc-800/50 ring-1 ring-zinc-700/30',
    dotClass: 'bg-zinc-600',
    scoreClass: 'text-zinc-500',
    scoreGlow: undefined,
  },
}

export function HRThreatCardHeader({
  playerName,
  team,
  hrThreatScore,
  escalationTier,
}: HRThreatCardHeaderProps) {
  const cfg = TIER_CONFIG[escalationTier]

  return (
    <div className="px-4 pt-5 pb-3">
      {/* Row 1: tier badge + threat score */}
      <div className="flex items-start justify-between">
        <div className={`flex items-center gap-1.5 px-2 py-[5px] rounded-[2px] ${cfg.badgeRing}`}>
          <span className={`block w-[5px] h-[5px] rounded-full flex-shrink-0 ${cfg.dotClass}`} />
          <span
            className={`text-[8.5px] font-mono tracking-[0.22em] uppercase ${cfg.scoreClass}`}
            style={{ opacity: 0.9 }}
          >
            {cfg.badge}
          </span>
        </div>

        <div className="text-right leading-none">
          <div
            className={`text-[46px] font-mono font-bold tabular-nums leading-none ${cfg.scoreClass}`}
            style={{ textShadow: cfg.scoreGlow }}
          >
            {hrThreatScore}
          </div>
          <div className="text-[7.5px] font-mono tracking-[0.24em] text-zinc-700 uppercase mt-[3px]">
            THREAT&nbsp;/&nbsp;100
          </div>
        </div>
      </div>

      {/* Row 2: player identity */}
      <div className="mt-3">
        <div
          className="font-mono font-semibold tracking-[0.06em] text-zinc-100 uppercase leading-tight"
          style={{ fontSize: '15px' }}
        >
          {playerName}
        </div>
        <div className="text-[9px] font-mono tracking-[0.18em] text-zinc-600 uppercase mt-1">
          {team}
        </div>
      </div>
    </div>
  )
}
