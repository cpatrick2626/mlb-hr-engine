export type EscalationTier = 'CRITICAL' | 'HIGH' | 'MODERATE'

export interface EscalationEvent {
  id: string
  tier: EscalationTier
  player: string
  team: string
  signal: string
  value: string
  ts: string
}

const tierConfig: Record<
  EscalationTier,
  {
    code:        string
    labelColor:  string
    valueColor:  string
    borderColor: string
    borderWidth: string
    bg:          string
    dotClass:    string
    dotAnim:     string
  }
> = {
  CRITICAL: {
    code:        'C1',
    labelColor:  'text-red-300',
    valueColor:  'text-red-300',
    borderColor: 'border-l-red-500',
    borderWidth: 'border-l-[3px]',
    bg:          'bg-red-500/[0.08]',
    dotClass:    'bg-red-500',
    dotAnim:     'animate-pulse-alert',
  },
  HIGH: {
    code:        'H2',
    labelColor:  'text-amber-400',
    valueColor:  'text-amber-300',
    borderColor: 'border-l-amber-500',
    borderWidth: 'border-l-2',
    bg:          'bg-amber-500/[0.055]',
    dotClass:    'bg-amber-400',
    dotAnim:     'animate-pulse-beacon',
  },
  MODERATE: {
    code:        'M3',
    labelColor:  'text-sky-400',
    valueColor:  'text-sky-300',
    borderColor: 'border-l-sky-500',
    borderWidth: 'border-l-[1.5px]',
    bg:          'bg-sky-500/[0.04]',
    dotClass:    'bg-sky-500',
    dotAnim:     '',
  },
}

const STAGGER_CLASSES = [
  'stagger-1', 'stagger-2', 'stagger-3', 'stagger-4',
  'stagger-5', 'stagger-6', 'stagger-7', 'stagger-8',
]

export function EscalationFeed({ events }: { events: EscalationEvent[] }) {
  return (
    <div className="flex flex-col gap-[3px] p-1.5">
      {events.map((e, i) => {
        const cfg = tierConfig[e.tier]
        const stagger = STAGGER_CLASSES[Math.min(i, STAGGER_CLASSES.length - 1)]
        const seqNum = String(i + 1).padStart(3, '0')

        return (
          <div
            key={e.id}
            className={[
              cfg.borderWidth,
              cfg.borderColor,
              cfg.bg,
              'pl-2.5 pr-2 py-[7px] rounded-r-[2px]',
              'animate-enter-left',
              stagger,
            ].join(' ')}
          >
            {/* Header row: tier code + seq + timestamp */}
            <div className="flex items-center justify-between mb-[4px]">
              <div className="flex items-center gap-1.5">
                <div
                  className={`w-[4px] h-[4px] rounded-full shrink-0 ${cfg.dotClass} ${cfg.dotAnim}`}
                />
                <span className={`text-[6.5px] font-mono tracking-[0.28em] uppercase ${cfg.labelColor}`}>
                  {e.tier}
                </span>
                <span className="text-[6px] font-mono text-zinc-800">
                  /{seqNum}
                </span>
              </div>
              <span className="text-[6.5px] font-mono text-zinc-700 tabular-nums">
                {e.ts}
              </span>
            </div>

            {/* Player identity */}
            <div className="text-[10px] font-mono font-medium text-zinc-100 leading-none tracking-[0.04em]">
              {e.player}
            </div>
            <div className="text-[6.5px] font-mono text-zinc-600 mt-[2px] tracking-[0.14em] uppercase">
              {e.team}
            </div>

            {/* Signal + value */}
            <div className="flex items-end justify-between mt-[6px]">
              <span className="text-[7px] font-mono text-zinc-600 uppercase tracking-[0.16em] leading-none">
                {e.signal}
              </span>
              <span className={`text-[11px] font-mono font-semibold tabular-nums leading-none ${cfg.valueColor}`}>
                {e.value}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
