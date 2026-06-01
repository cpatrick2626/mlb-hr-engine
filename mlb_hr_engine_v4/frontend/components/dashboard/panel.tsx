import React from 'react'

type PanelStatus = 'ACTIVE' | 'STANDBY' | 'ALERT'
type PanelAccent = 'red' | 'amber' | 'sky' | 'none'

interface PanelProps {
  label: string
  zoneId?: string
  status?: PanelStatus
  accent?: PanelAccent
  children: React.ReactNode
  className?: string
}

// Status dot config
const statusDot: Record<PanelStatus, { cls: string; anim: string }> = {
  ACTIVE:  { cls: 'bg-emerald-500', anim: 'animate-pulse-beacon' },
  STANDBY: { cls: 'bg-zinc-600',    anim: '' },
  ALERT:   { cls: 'bg-red-500',     anim: 'animate-pulse-alert'  },
}

// Accent-driven box shadow (restrained — ambient, not neon)
const accentGlow: Record<PanelAccent, string> = {
  red:   '0 0 0 1px rgba(220,38,38,0.22), 0 0 32px rgba(220,38,38,0.06)',
  amber: '0 0 0 1px rgba(217,119,6,0.18), 0 0 24px rgba(217,119,6,0.04)',
  sky:   '0 0 0 1px rgba(14,165,233,0.16), 0 0 20px rgba(14,165,233,0.04)',
  none:  '0 0 0 1px rgba(255,255,255,0.07)',
}

// Accent corner bracket color
const accentBracket: Record<PanelAccent, { tl: string; br: string }> = {
  red:   { tl: 'rgba(220,38,38,0.45)', br: 'rgba(220,38,38,0.18)' },
  amber: { tl: 'rgba(217,119,6,0.35)', br: 'rgba(217,119,6,0.14)' },
  sky:   { tl: 'rgba(14,165,233,0.28)', br: 'rgba(14,165,233,0.12)' },
  none:  { tl: 'rgba(255,255,255,0.18)', br: 'rgba(255,255,255,0.07)' },
}

// Accent header top-line shimmer
const accentShimmer: Record<PanelAccent, string> = {
  red:   'linear-gradient(90deg, transparent 0%, rgba(220,38,38,0.15) 35%, rgba(220,38,38,0.28) 50%, rgba(220,38,38,0.15) 65%, transparent 100%)',
  amber: 'linear-gradient(90deg, transparent 0%, rgba(217,119,6,0.12) 35%, rgba(217,119,6,0.22) 50%, rgba(217,119,6,0.12) 65%, transparent 100%)',
  sky:   'linear-gradient(90deg, transparent 0%, rgba(14,165,233,0.10) 35%, rgba(14,165,233,0.18) 50%, rgba(14,165,233,0.10) 65%, transparent 100%)',
  none:  'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 35%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.05) 65%, transparent 100%)',
}

export function Panel({
  label,
  zoneId,
  status = 'ACTIVE',
  accent = 'none',
  children,
  className = '',
}: PanelProps) {
  const sd = statusDot[status]
  const brackets = accentBracket[accent]

  return (
    <div
      className={`relative bg-[#060C15] flex flex-col overflow-hidden rounded-[2px] ${className}`}
      style={{ boxShadow: accentGlow[accent] }}
    >
      {/* ── Corner brackets — tactical framing ── */}
      {/* Top-left */}
      <div
        aria-hidden
        className="pointer-events-none absolute top-0 left-0 w-[14px] h-[14px] z-20"
        style={{
          borderTop:  `1px solid ${brackets.tl}`,
          borderLeft: `1px solid ${brackets.tl}`,
        }}
      />
      {/* Top-right */}
      <div
        aria-hidden
        className="pointer-events-none absolute top-0 right-0 w-[14px] h-[14px] z-20"
        style={{
          borderTop:   `1px solid ${brackets.br}`,
          borderRight: `1px solid ${brackets.br}`,
        }}
      />
      {/* Bottom-left */}
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-0 w-[14px] h-[14px] z-20"
        style={{
          borderBottom: `1px solid ${brackets.br}`,
          borderLeft:   `1px solid ${brackets.br}`,
        }}
      />
      {/* Bottom-right */}
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 right-0 w-[14px] h-[14px] z-20"
        style={{
          borderBottom: `1px solid ${brackets.br}`,
          borderRight:  `1px solid ${brackets.br}`,
        }}
      />

      {/* ── Panel header ── */}
      <div
        className="relative z-10 flex items-center gap-2 px-3 py-[6px] border-b border-white/[0.06] shrink-0"
        style={{ background: 'linear-gradient(180deg, #04080F 0%, #060C16 100%)' }}
      >
        {/* Accent shimmer strip on header top edge */}
        <div
          aria-hidden
          className="pointer-events-none absolute top-0 left-0 right-0 h-[1px] z-10"
          style={{ background: accentShimmer[accent] }}
        />

        {/* Status dot */}
        <div
          className={`w-[6px] h-[6px] rounded-full shrink-0 ${sd.cls} ${sd.anim}`}
          style={status === 'ALERT'
            ? { boxShadow: '0 0 5px rgba(220,38,38,0.70)' }
            : status === 'ACTIVE'
            ? { boxShadow: '0 0 4px rgba(16,185,129,0.40)' }
            : undefined
          }
        />

        {/* Label */}
        <span className="text-[7.5px] font-mono tracking-[0.30em] text-zinc-600 uppercase flex-1 leading-none">
          {label}
        </span>

        {/* Zone ID chip */}
        {zoneId && (
          <span className="text-[6px] font-mono tracking-[0.18em] text-zinc-800 uppercase leading-none">
            {zoneId}
          </span>
        )}
      </div>

      {/* ── Inner glass gradient ── */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background: 'linear-gradient(180deg, rgba(255,255,255,0.010) 0%, rgba(255,255,255,0.003) 25%, transparent 60%)',
        }}
      />

      {/* ── Content ── */}
      <div className="relative z-10 flex-1 overflow-auto min-h-0">
        {children}
      </div>
    </div>
  )
}
