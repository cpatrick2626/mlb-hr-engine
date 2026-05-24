import React from 'react'

interface HRThreatCardMetricsProps {
  barrelPct: number
  hardHitPct: number
  pitchMatchupEdge: number
  weatherBoost: number
  pitcherVulnerability: number
}

function MicroBar({ fill, color, glow }: { fill: number; color: string; glow?: string }) {
  const pct = Math.min(100, Math.max(0, fill))
  return (
    <div className="mt-[6px] h-[2px] w-full bg-zinc-800/70 relative overflow-hidden rounded-full">
      <div
        className={`absolute inset-y-0 left-0 rounded-full ${color}`}
        style={{ width: `${pct}%`, boxShadow: glow }}
      />
    </div>
  )
}

function MetricCell({
  label,
  value,
  valueColor,
  subtext,
  subtextColor = 'text-zinc-700',
  bar,
}: {
  label: string
  value: string
  valueColor: string
  subtext?: string
  subtextColor?: string
  bar?: { fill: number; color: string; glow?: string }
}) {
  return (
    <div className="py-[9px]">
      <div className="text-[6.5px] font-mono tracking-[0.24em] text-zinc-700 uppercase mb-[4px] leading-none">
        {label}
      </div>
      <div className={`text-[12px] font-mono font-medium tabular-nums leading-none ${valueColor}`}>
        {value}
      </div>
      {bar && <MicroBar fill={bar.fill} color={bar.color} glow={bar.glow} />}
      {subtext && (
        <div className={`text-[6.5px] font-mono tracking-[0.14em] uppercase mt-[4px] leading-none ${subtextColor}`}>
          {subtext}
        </div>
      )}
    </div>
  )
}

function barrelColor(pct: number) {
  if (pct >= 12) return { text: 'text-emerald-300', bar: 'bg-emerald-400', glow: '0 0 6px rgba(52,211,153,0.65)' }
  if (pct >= 9)  return { text: 'text-emerald-400', bar: 'bg-emerald-500', glow: '0 0 5px rgba(16,185,129,0.55)' }
  if (pct >= 6)  return { text: 'text-teal-400',    bar: 'bg-teal-500',    glow: '0 0 4px rgba(20,184,166,0.40)' }
  return { text: 'text-zinc-500', bar: 'bg-zinc-600', glow: undefined }
}

function hardHitColor(pct: number) {
  if (pct >= 52) return 'text-amber-400'
  if (pct >= 44) return 'text-zinc-300'
  return 'text-zinc-500'
}

function edgeColor(e: number) {
  if (e >= 0.15) return 'text-emerald-400'
  if (e >= 0.05) return 'text-emerald-400/70'
  if (e <= -0.15) return 'text-red-400'
  if (e <= -0.05) return 'text-red-400/70'
  return 'text-zinc-500'
}

function edgeLabel(e: number): string {
  if (e >= 0.15) return 'STRONG EDGE'
  if (e >= 0.05) return 'EDGE'
  if (e <= -0.15) return 'UNFAVORABLE'
  if (e <= -0.05) return 'SLIGHT DEFICIT'
  return 'NEUTRAL'
}

function edgeValue(e: number): string {
  const pct = e * 100
  return pct >= 0 ? `+${pct.toFixed(1)}%` : `${pct.toFixed(1)}%`
}

function weatherColor(boost: number) {
  const delta = (boost - 1) * 100
  if (delta >= 5)  return { text: 'text-emerald-400', label: 'AMPLIFIED',  lc: 'text-emerald-400/60' }
  if (delta >= 2)  return { text: 'text-emerald-400/60', label: 'BOOSTED', lc: 'text-zinc-600' }
  if (delta <= -5) return { text: 'text-red-400',    label: 'SUPPRESSED',  lc: 'text-red-400/60' }
  if (delta <= -2) return { text: 'text-red-400/60', label: 'SLIGHT DRAG', lc: 'text-zinc-600' }
  return { text: 'text-zinc-500', label: 'NEUTRAL', lc: 'text-zinc-700' }
}

function weatherValue(boost: number): string {
  const delta = (boost - 1) * 100
  return delta >= 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`
}

function vulnColor(v: number) {
  if (v >= 70) return { text: 'text-red-300',   bar: 'bg-red-500',   glow: '0 0 7px rgba(220,38,38,0.55)',  label: 'VULNERABLE' }
  if (v >= 50) return { text: 'text-amber-400', bar: 'bg-amber-500', glow: '0 0 6px rgba(217,119,6,0.45)',  label: 'SOFT' }
  if (v >= 30) return { text: 'text-zinc-400',  bar: 'bg-zinc-500',  glow: undefined,                       label: 'MANAGEABLE' }
  return { text: 'text-zinc-600', bar: 'bg-zinc-700', glow: undefined, label: 'CONTAINED' }
}

export function HRThreatCardMetrics({
  barrelPct,
  hardHitPct,
  pitchMatchupEdge,
  weatherBoost,
  pitcherVulnerability,
}: HRThreatCardMetricsProps) {
  const bc = barrelColor(barrelPct)
  const vc = vulnColor(pitcherVulnerability)
  const wc = weatherColor(weatherBoost)

  return (
    <div className="px-4 pb-4">
      {/* Row 1 — barrel / hard hit / pitch edge */}
      <div className="grid grid-cols-3 gap-x-3 border-b border-zinc-800/50">
        <MetricCell
          label="BARREL %"
          value={`${barrelPct.toFixed(1)}%`}
          valueColor={bc.text}
          bar={{ fill: (barrelPct / 20) * 100, color: bc.bar, glow: bc.glow }}
        />
        <MetricCell
          label="HRD HIT %"
          value={`${hardHitPct.toFixed(1)}%`}
          valueColor={hardHitColor(hardHitPct)}
          bar={{ fill: (hardHitPct / 70) * 100, color: hardHitPct >= 50 ? 'bg-amber-500' : 'bg-zinc-600' }}
        />
        <MetricCell
          label="PITCH EDGE"
          value={edgeValue(pitchMatchupEdge)}
          valueColor={edgeColor(pitchMatchupEdge)}
          subtext={edgeLabel(pitchMatchupEdge)}
        />
      </div>

      {/* Row 2 — weather / pitcher vulnerability */}
      <div className="grid grid-cols-2 gap-x-4">
        <MetricCell
          label="WEATHER"
          value={weatherValue(weatherBoost)}
          valueColor={wc.text}
          subtext={wc.label}
          subtextColor={wc.lc}
        />
        <MetricCell
          label="PTCHR VULN"
          value={String(pitcherVulnerability)}
          valueColor={vc.text}
          bar={{ fill: pitcherVulnerability, color: vc.bar, glow: vc.glow }}
          subtext={vc.label}
        />
      </div>
    </div>
  )
}
