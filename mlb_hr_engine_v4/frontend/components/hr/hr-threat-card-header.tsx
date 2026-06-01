import React from 'react'
import type { EscalationTier } from './hr-threat-card'

interface HRThreatCardHeaderProps {
  playerName: string
  team: string
  hrThreatScore: number
  escalationTier: EscalationTier
}

type TierConfig = {
  badge:       string
  badgeRing:   string
  dotClass:    string
  dotAnim:     string
  scoreClass:  string
  scoreGlow:   string | undefined
  accentBar:   string
}

const TIER_CONFIG: Record<EscalationTier, TierConfig> = {
  CRITICAL: {
    badge:      'CRITICAL',
    badgeRing:  'bg-red-500/[0.09] ring-1 ring-red-500/40',
    dotClass:   'bg-red-500',
    dotAnim:    'animate-pulse-alert',
    scoreClass: 'text-red-400',
    scoreGlow:  '0 0 32px rgba(220,38,38,0.45)',
    accentBar:  'bg-red-500',
  },
  HIGH: {
    badge:      'HIGH ALERT',
    badgeRing:  'bg-amber-500/[0.08] ring-1 ring-amber-500/32',
    dotClass:   'bg-amber-400',
    dotAnim:    'animate-pulse-beacon',
    scoreClass: 'text-amber-400',
    scoreGlow:  '0 0 26px rgba(217,119,6,0.38)',
    accentBar:  'bg-amber-400',
  },
  MODERATE: {
    badge:      'MODERATE',
    badgeRing:  'bg-sky-500/[0.07] ring-1 ring-sky-500/26',
    dotClass:   'bg-sky-400',
    dotAnim:    '',
    scoreClass: 'text-sky-400',
    scoreGlow:  '0 0 18px rgba(14,165,233,0.28)',
    accentBar:  'bg-sky-500',
  },
  LOW: {
    badge:      'LOW',
    badgeRing:  'bg-zinc-800/50 ring-1 ring-zinc-700/30',
    dotClass:   'bg-zinc-600',
    dotAnim:    '',
    scoreClass: 'text-zinc-500',
    scoreGlow:  undefined,
    accentBar:  'bg-zinc-700',
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
    <div className="px-4 pt-5 pb-[10px]">
      {/* Row 1: tier badge (left) + threat score (right) */}
      <div className="flex items-start justify-between">
        {/* Tier badge */}
        <div className={`flex items-center gap-[6px] px-[7px] py-[5px] rounded-[2px] ${cfg.badgeRing}`}>
          <span className={`block w-[5px] h-[5px] rounded-full shrink-0 ${cfg.dotClass} ${cfg.dotAnim}`} />
          <span className={`text-[7.5px] font-mono tracking-[0.24em] uppercase ${cfg.scoreClass}`}>
            {cfg.badge}
          </span>
        </div>

        {/* Threat score — the dominant number */}
        <div className="text-right leading-none">
          <div
            className={`font-mono font-bold tabular-nums leading-none ${cfg.scoreClass}`}
            style={{
              fontSize: '52px',
              lineHeight: 1,
              textShadow: cfg.scoreGlow,
            }}
          >
            {hrThreatScore}
          </div>
          <div className="text-[6.5px] font-mono tracking-[0.28em] text-zinc-700 uppercase mt-[4px]">
            THREAT&nbsp;·&nbsp;100
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="w-full h-px bg-white/[0.06] mt-[10px] mb-[8px]" />

      {/* Row 2: player identity */}
      <div>
        <div
          className="font-display font-semibold tracking-[0.08em] text-zinc-100 uppercase leading-tight"
          style={{ fontSize: '16px' }}
        >
          {playerName}
        </div>
        <div className="text-[8px] font-mono tracking-[0.20em] text-zinc-600 uppercase mt-[3px]">
          {team}
        </div>
      </div>
    </div>
  )
}
