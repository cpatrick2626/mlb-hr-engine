export interface ThreatRankRow {
  rank: number
  player: string
  team: string
  pos: string
  threatScore: number
  modelProb: number
  evPct: number
  edgePct: number
  barrelPct: number
  tier: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'
}

const tierPip: Record<string, { cls: string; glow: string | undefined }> = {
  CRITICAL: { cls: 'bg-red-500',   glow: '0 0 6px rgba(220,38,38,0.80)'   },
  HIGH:     { cls: 'bg-amber-400', glow: '0 0 5px rgba(217,119,6,0.65)'   },
  MODERATE: { cls: 'bg-sky-400',   glow: '0 0 4px rgba(14,165,233,0.55)'  },
  LOW:      { cls: 'bg-zinc-700',  glow: undefined                         },
}

function barrelHeat(pct: number): string {
  if (pct >= 12) return 'text-emerald-300'
  if (pct >= 10) return 'text-emerald-400'
  if (pct >= 8)  return 'text-teal-400'
  if (pct >= 6)  return 'text-sky-400/80'
  return 'text-zinc-600'
}

function probHeat(p: number): string {
  if (p >= 0.22) return 'text-red-300'
  if (p >= 0.18) return 'text-amber-400'
  if (p >= 0.13) return 'text-sky-400'
  return 'text-zinc-400'
}

function evHeat(ev: number): string {
  if (ev >= 10) return 'text-emerald-300'
  if (ev >= 6)  return 'text-emerald-400'
  if (ev >= 3)  return 'text-teal-400'
  return 'text-zinc-600'
}

function scoreSize(rank: number): string {
  if (rank <= 3) return 'text-[12px] font-bold text-white'
  return 'text-[11px] font-semibold text-zinc-200'
}

const COLS = ['#', 'PLAYER', 'POS', 'SCORE', 'P(HR)', 'EV%', 'EDGE', 'BREL%']

export function ThreatRankingsTable({ rows }: { rows: ThreatRankRow[] }) {
  return (
    <div className="p-2.5">
      {/* Header */}
      <div className="grid grid-cols-[20px_1fr_26px_42px_38px_36px_40px_40px] gap-x-2 pb-[5px] mb-[3px] border-b border-white/[0.07]">
        {COLS.map((c) => (
          <span key={c} className="text-[6.5px] font-mono tracking-[0.22em] text-zinc-700 uppercase leading-none">
            {c}
          </span>
        ))}
      </div>

      {rows.map((r, i) => {
        const pip = tierPip[r.tier]
        const isTop = r.rank <= 3

        return (
          <div
            key={r.rank}
            className={[
              'grid grid-cols-[20px_1fr_26px_42px_38px_36px_40px_40px] gap-x-2',
              'py-[6px] border-b border-white/[0.04] last:border-0 items-center',
              'transition-colors duration-100',
              isTop ? 'hover:bg-white/[0.025]' : 'hover:bg-white/[0.015]',
            ].join(' ')}
          >
            {/* Rank */}
            <span className={`text-[7.5px] font-mono tabular-nums leading-none ${isTop ? 'text-zinc-500' : 'text-zinc-700'}`}>
              #{String(r.rank).padStart(2, '0')}
            </span>

            {/* Player + tier pip */}
            <div className="flex items-center gap-1.5 min-w-0">
              <div
                className={`w-[3px] h-[15px] rounded-full shrink-0 ${pip.cls}`}
                style={pip.glow ? { boxShadow: pip.glow } : undefined}
              />
              <div className="min-w-0">
                <div className={`text-[9.5px] font-mono truncate leading-none ${isTop ? 'text-zinc-100' : 'text-zinc-300'}`}>
                  {r.player}
                </div>
                <div className="text-[6px] font-mono text-zinc-700 mt-[2px] tracking-[0.12em] uppercase">
                  {r.team}
                </div>
              </div>
            </div>

            {/* Position */}
            <span className="text-[7.5px] font-mono text-zinc-600">{r.pos}</span>

            {/* Threat score */}
            <span className={`tabular-nums leading-none ${scoreSize(r.rank)}`}>
              {r.threatScore}
            </span>

            {/* Model prob */}
            <span className={`text-[9.5px] font-mono tabular-nums leading-none ${probHeat(r.modelProb)}`}>
              {(r.modelProb * 100).toFixed(1)}%
            </span>

            {/* EV */}
            <span className={`text-[9.5px] font-mono tabular-nums leading-none ${evHeat(r.evPct)}`}>
              {r.evPct > 0 ? '+' : ''}{r.evPct.toFixed(1)}
            </span>

            {/* Edge */}
            <span className="text-[9.5px] font-mono text-sky-400/80 tabular-nums leading-none">
              {r.edgePct.toFixed(1)}%
            </span>

            {/* Barrel */}
            <span className={`text-[9.5px] font-mono tabular-nums leading-none ${barrelHeat(r.barrelPct)}`}>
              {r.barrelPct.toFixed(1)}%
            </span>
          </div>
        )
      })}
    </div>
  )
}
