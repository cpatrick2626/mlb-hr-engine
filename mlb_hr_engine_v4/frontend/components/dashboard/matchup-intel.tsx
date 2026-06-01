export interface MatchupRow {
  batter: string
  batterTeam: string
  pitcher: string
  pitcherTeam: string
  hand: string
  hvyScore: number
  barrelPct: number
  pitcherHR9: number
  edge: 'FAVORABLE' | 'NEUTRAL' | 'UNFAVORABLE'
}

const edgePill: Record<string, { label: string; cls: string; bg: string }> = {
  FAVORABLE:   { label: 'FAVORABLE',   cls: 'text-emerald-300', bg: 'bg-emerald-500/[0.12]' },
  NEUTRAL:     { label: 'NEUTRAL',     cls: 'text-zinc-500',    bg: 'bg-white/[0.04]'       },
  UNFAVORABLE: { label: 'UNFAVORABLE', cls: 'text-red-300',     bg: 'bg-red-500/[0.08]'     },
}

function hvyColor(score: number): string {
  if (score >= 1.2) return 'text-emerald-400'
  if (score >= 1.0) return 'text-zinc-300'
  if (score >= 0.85) return 'text-zinc-500'
  return 'text-red-400/70'
}

function barrelHeat(pct: number): string {
  if (pct >= 12) return 'text-emerald-300'
  if (pct >= 10) return 'text-emerald-400'
  if (pct >= 8)  return 'text-teal-400'
  if (pct >= 6)  return 'text-sky-400/80'
  return 'text-zinc-600'
}

function hr9Heat(hr9: number): string {
  if (hr9 >= 1.6) return 'text-red-300'
  if (hr9 >= 1.3) return 'text-orange-400'
  if (hr9 >= 1.0) return 'text-amber-400'
  return 'text-zinc-600'
}

const COLS = ['BATTER', 'PITCHER', 'HAND', 'HVY', 'BREL%', 'HR/9', 'EDGE']

export function MatchupIntelPanel({ rows }: { rows: MatchupRow[] }) {
  return (
    <div className="p-2.5">
      {/* Header */}
      <div className="grid grid-cols-[1fr_1fr_32px_40px_40px_36px_92px] gap-x-2 pb-[5px] mb-[2px] border-b border-white/[0.07]">
        {COLS.map((h) => (
          <span key={h} className="text-[6.5px] font-mono tracking-[0.22em] text-zinc-700 uppercase leading-none">
            {h}
          </span>
        ))}
      </div>

      {rows.map((r, i) => {
        const ep = edgePill[r.edge]
        const isAlt = i % 2 === 1

        return (
          <div
            key={i}
            className={[
              'grid grid-cols-[1fr_1fr_32px_40px_40px_36px_92px] gap-x-2',
              'py-[7px] border-b border-white/[0.04] last:border-0 items-center',
              'transition-colors duration-100 hover:bg-white/[0.018]',
              isAlt ? 'bg-white/[0.008]' : '',
            ].join(' ')}
          >
            {/* Batter */}
            <div className="min-w-0">
              <div className="text-[9.5px] font-mono text-zinc-100 truncate leading-none">{r.batter}</div>
              <div className="text-[6px] font-mono text-zinc-700 mt-[2px] tracking-[0.12em] uppercase">{r.batterTeam}</div>
            </div>

            {/* Pitcher */}
            <div className="min-w-0">
              <div className="text-[9.5px] font-mono text-zinc-400 truncate leading-none">{r.pitcher}</div>
              <div className="text-[6px] font-mono text-zinc-700 mt-[2px] tracking-[0.12em] uppercase">{r.pitcherTeam}</div>
            </div>

            {/* Handedness */}
            <span className="text-[8px] font-mono text-zinc-600 tabular-nums">{r.hand}</span>

            {/* HVY score */}
            <span className={`text-[10px] font-mono font-semibold tabular-nums leading-none ${hvyColor(r.hvyScore)}`}>
              {r.hvyScore.toFixed(2)}
            </span>

            {/* Barrel */}
            <span className={`text-[9.5px] font-mono tabular-nums leading-none ${barrelHeat(r.barrelPct)}`}>
              {r.barrelPct.toFixed(1)}%
            </span>

            {/* HR/9 */}
            <span className={`text-[9.5px] font-mono tabular-nums leading-none ${hr9Heat(r.pitcherHR9)}`}>
              {r.pitcherHR9.toFixed(2)}
            </span>

            {/* Edge pill */}
            <div
              className={`inline-flex items-center justify-center px-[5px] py-[2px] rounded-[2px] ${ep.bg}`}
            >
              <span className={`text-[6.5px] font-mono tracking-[0.14em] uppercase leading-none ${ep.cls}`}>
                {ep.label}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
