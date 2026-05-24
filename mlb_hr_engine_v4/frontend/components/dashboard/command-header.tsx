'use client'

export type WorkspaceId = 'main' | 'jig' | 'strategy' | 'hits' | 'performance' | 'ops'

interface WorkspaceTab {
  id: WorkspaceId
  label: string
  sub: string
  isPrimary?: boolean
}

const WORKSPACES: WorkspaceTab[] = [
  { id: 'main',        label: 'MAIN',        sub: 'THREAT ZONE',    isPrimary: true },
  { id: 'jig',         label: 'JIG',         sub: 'INTELLIGENCE',   isPrimary: true },
  { id: 'strategy',    label: 'STRATEGY',    sub: 'ADVANCED'  },
  { id: 'hits',        label: 'HITS',        sub: 'VALIDATION' },
  { id: 'performance', label: 'PERFORMANCE', sub: 'ANALYTICS' },
  { id: 'ops',         label: 'OPS',         sub: 'ROOM 26'   },
]

interface CommandHeaderProps {
  date: string
  slateCount: number
  activeThreats: number
  systemStatus: 'OPERATIONAL' | 'DEGRADED' | 'OFFLINE'
  activeWorkspace?: WorkspaceId
  onWorkspaceChange?: (ws: WorkspaceId) => void
}

const statusConfig = {
  OPERATIONAL: {
    dot:   'animate-pulse-live',
    color: 'text-emerald-400',
    bg:    'bg-emerald-500',
  },
  DEGRADED: {
    dot:   'animate-pulse-beacon',
    color: 'text-amber-400',
    bg:    'bg-amber-400',
  },
  OFFLINE: {
    dot:   'animate-pulse-alert',
    color: 'text-red-400',
    bg:    'bg-red-500',
  },
}

export function CommandHeader({
  date,
  slateCount,
  activeThreats,
  systemStatus,
  activeWorkspace = 'main',
  onWorkspaceChange,
}: CommandHeaderProps) {
  const sc = statusConfig[systemStatus]

  return (
    <header
      className="shrink-0 border-b border-white/[0.06]"
      style={{ background: 'linear-gradient(180deg, #060D18 0%, #050A12 100%)' }}
    >
      {/* ── Row 1: System identity + operational vitals ── */}
      <div className="flex items-center justify-between px-5 py-2 border-b border-white/[0.04]">

        {/* Left — System identity */}
        <div className="flex items-center gap-6">
          <div>
            <div className="text-[6.5px] font-mono tracking-[0.38em] text-zinc-700 uppercase leading-none mb-[3px]">
              MLB · HOME RUN ENGINE · TACTICAL
            </div>
            <div
              className="font-display text-[17px] font-semibold tracking-[0.14em] text-zinc-100 uppercase leading-none"
              style={{ letterSpacing: '0.12em' }}
            >
              TACTICAL ASSESSMENT
            </div>
            <div className="text-[6.5px] font-mono tracking-[0.20em] text-zinc-700 uppercase leading-none mt-[4px]">
              POISSON · PLATT CAL · BARREL-KELLY · CONTEXT GUARD · v4
            </div>
          </div>

          {/* Separator */}
          <div className="w-px h-9 bg-white/[0.06]" />

          {/* Date */}
          <div>
            <div className="text-[6px] font-mono tracking-[0.26em] text-zinc-700 uppercase leading-none mb-1">
              SLATE DATE
            </div>
            <div className="text-[11px] font-mono tracking-[0.06em] text-zinc-300 leading-none">
              {date}
            </div>
          </div>
        </div>

        {/* Right — Operational vitals */}
        <div className="flex items-center gap-5">
          <VitalChip label="ASSESSED" value={String(slateCount)} />

          <div
            className="flex flex-col items-end px-3 py-1 rounded-[2px]"
            style={{ background: 'rgba(217,119,6,0.08)', boxShadow: '0 0 0 1px rgba(217,119,6,0.18)' }}
          >
            <span className="text-[6px] font-mono tracking-[0.26em] text-amber-600 uppercase leading-none mb-[3px]">
              ACTIVE THREATS
            </span>
            <span className="text-[15px] font-mono font-bold tabular-nums text-amber-400 leading-none">
              {activeThreats}
            </span>
          </div>

          {/* Separator */}
          <div className="w-px h-9 bg-white/[0.06]" />

          {/* System status */}
          <div className="flex items-center gap-2">
            <div
              className={`w-[7px] h-[7px] rounded-full shrink-0 ${sc.bg} ${sc.dot}`}
            />
            <div>
              <div className="text-[6px] font-mono tracking-[0.26em] text-zinc-700 uppercase leading-none mb-[3px]">
                SYSTEM STATUS
              </div>
              <div className={`text-[9px] font-mono tracking-[0.16em] uppercase leading-none ${sc.color}`}>
                {systemStatus}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Row 2: Workspace tab strip ── */}
      <div className="flex items-stretch">
        {WORKSPACES.map((ws) => {
          const isActive = ws.id === activeWorkspace

          return (
            <button
              key={ws.id}
              onClick={() => onWorkspaceChange?.(ws.id)}
              className={[
                'relative flex flex-col justify-center px-4 py-[7px] text-left',
                'transition-colors duration-150',
                ws.isPrimary ? 'min-w-[72px]' : 'min-w-[64px]',
                isActive
                  ? ws.isPrimary
                    ? 'tab-indicator tab-indicator-primary bg-white/[0.04]'
                    : 'tab-indicator bg-white/[0.03]'
                  : 'hover:bg-white/[0.02]',
              ].join(' ')}
            >
              <span
                className={[
                  'text-[8.5px] font-mono tracking-[0.20em] leading-none font-semibold',
                  isActive
                    ? ws.isPrimary ? 'text-zinc-100' : 'text-zinc-200'
                    : 'text-zinc-600 group-hover:text-zinc-400',
                ].join(' ')}
              >
                {ws.label}
              </span>
              <span
                className={[
                  'text-[5.5px] font-mono tracking-[0.22em] uppercase leading-none mt-[4px]',
                  isActive ? 'text-zinc-600' : 'text-zinc-800',
                ].join(' ')}
              >
                {ws.sub}
              </span>
            </button>
          )
        })}

        {/* Spacer + feed status indicators */}
        <div className="ml-auto flex items-center gap-5 px-5 border-l border-white/[0.04]">
          <FeedIndicator color="emerald" label="LIVE DATA" />
          <FeedIndicator color="sky"     label="ODDS FEED" />
          <FeedIndicator color="zinc"    label="STATCAST" dim />
        </div>
      </div>
    </header>
  )
}

function VitalChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-end">
      <span className="text-[6px] font-mono tracking-[0.26em] text-zinc-700 uppercase leading-none mb-[3px]">
        {label}
      </span>
      <span className="text-[15px] font-mono font-semibold tabular-nums text-zinc-300 leading-none">
        {value}
      </span>
    </div>
  )
}

function FeedIndicator({
  color,
  label,
  dim = false,
}: {
  color: 'emerald' | 'sky' | 'zinc'
  label: string
  dim?: boolean
}) {
  const dotColor = {
    emerald: 'bg-emerald-500',
    sky:     'bg-sky-500',
    zinc:    'bg-zinc-700',
  }[color]

  const dotAnim = color === 'emerald' ? 'animate-pulse-live'
                : color === 'sky'     ? 'animate-pulse-beacon'
                : ''

  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-[5px] h-[5px] rounded-full shrink-0 ${dotColor} ${dotAnim}`} />
      <span
        className={`text-[6px] font-mono tracking-[0.22em] uppercase ${dim ? 'text-zinc-800' : 'text-zinc-700'}`}
      >
        {label}
      </span>
    </div>
  )
}
