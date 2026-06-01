'use client'

import { useState } from 'react'
import { CommandHeader } from '@/components/dashboard/command-header'
import type { WorkspaceId } from '@/components/dashboard/command-header'
import { EscalationFeed } from '@/components/dashboard/escalation-feed'
import type { EscalationEvent } from '@/components/dashboard/escalation-feed'
import { MatchupIntelPanel } from '@/components/dashboard/matchup-intel'
import type { MatchupRow } from '@/components/dashboard/matchup-intel'
import { Panel } from '@/components/dashboard/panel'
import { PitcherVulnerabilityPanel } from '@/components/dashboard/pitcher-vulnerability'
import type { PitcherVulnRow } from '@/components/dashboard/pitcher-vulnerability'
import { ThreatRankingsTable } from '@/components/dashboard/threat-rankings'
import type { ThreatRankRow } from '@/components/dashboard/threat-rankings'
import { HRThreatCard } from '@/components/hr/hr-threat-card'
import type { HRThreatCardProps } from '@/components/hr/hr-threat-card'

// ─── Mock Data — MAIN workspace ───────────────────────────────────────────────

const MOCK_THREATS: HRThreatCardProps[] = [
  { playerName: 'Aaron Judge',    team: 'NYY · RF', hrThreatScore: 87, barrelPct: 15.2, hardHitPct: 57.3, pitchMatchupEdge: 0.28, weatherBoost: 1.07, pitcherVulnerability: 74, escalationTier: 'CRITICAL' },
  { playerName: 'Shohei Ohtani',  team: 'LAD · DH', hrThreatScore: 82, barrelPct: 13.8, hardHitPct: 54.1, pitchMatchupEdge: 0.21, weatherBoost: 1.03, pitcherVulnerability: 81, escalationTier: 'CRITICAL' },
  { playerName: 'Yordan Alvarez', team: 'HOU · LF', hrThreatScore: 76, barrelPct: 12.4, hardHitPct: 52.7, pitchMatchupEdge: 0.14, weatherBoost: 1.05, pitcherVulnerability: 68, escalationTier: 'HIGH'     },
  { playerName: 'Pete Alonso',    team: 'NYM · 1B', hrThreatScore: 71, barrelPct: 10.9, hardHitPct: 48.2, pitchMatchupEdge: 0.18, weatherBoost: 1.04, pitcherVulnerability: 72, escalationTier: 'HIGH'     },
]

const MOCK_ESCALATIONS: EscalationEvent[] = [
  { id: 'e1', tier: 'CRITICAL', player: 'Aaron Judge',      team: 'NYY', signal: 'Barrel Rate',  value: '15.2%', ts: '09:41' },
  { id: 'e2', tier: 'CRITICAL', player: 'Shohei Ohtani',    team: 'LAD', signal: 'Pitcher HR/9', value: '1.84',  ts: '09:38' },
  { id: 'e3', tier: 'HIGH',     player: 'Yordan Alvarez',   team: 'HOU', signal: 'Wind + Park',  value: '+11%',  ts: '09:35' },
  { id: 'e4', tier: 'HIGH',     player: 'Pete Alonso',      team: 'NYM', signal: 'Platoon Edge', value: 'R vs L',ts: '09:32' },
  { id: 'e5', tier: 'HIGH',     player: 'Kyle Schwarber',   team: 'PHI', signal: 'EV% Edge',     value: '+8.4%', ts: '09:30' },
  { id: 'e6', tier: 'MODERATE', player: 'Matt Olson',       team: 'ATL', signal: 'FB% Surge',    value: '42.1%', ts: '09:27' },
  { id: 'e7', tier: 'MODERATE', player: 'Marcell Ozuna',    team: 'ATL', signal: 'Park Factor',  value: '1.14',  ts: '09:24' },
  { id: 'e8', tier: 'MODERATE', player: 'Gunnar Henderson', team: 'BAL', signal: 'xSLG Spike',   value: '.618',  ts: '09:21' },
]

const MOCK_MATCHUPS: MatchupRow[] = [
  { batter: 'Aaron Judge',    batterTeam: 'NYY', pitcher: 'Jose Berrios',   pitcherTeam: 'TOR', hand: 'R/R', hvyScore: 1.28, barrelPct: 15.2, pitcherHR9: 1.62, edge: 'FAVORABLE'   },
  { batter: 'Shohei Ohtani',  batterTeam: 'LAD', pitcher: 'Kyle Gibson',    pitcherTeam: 'STL', hand: 'L/R', hvyScore: 1.31, barrelPct: 13.8, pitcherHR9: 1.84, edge: 'FAVORABLE'   },
  { batter: 'Yordan Alvarez', batterTeam: 'HOU', pitcher: 'Chris Bassitt',  pitcherTeam: 'TOR', hand: 'L/R', hvyScore: 1.14, barrelPct: 12.4, pitcherHR9: 1.41, edge: 'FAVORABLE'   },
  { batter: 'Pete Alonso',    batterTeam: 'NYM', pitcher: 'Zack Wheeler',   pitcherTeam: 'PHI', hand: 'R/R', hvyScore: 0.97, barrelPct: 10.9, pitcherHR9: 0.88, edge: 'NEUTRAL'     },
  { batter: 'Kyle Schwarber', batterTeam: 'PHI', pitcher: 'David Peterson', pitcherTeam: 'NYM', hand: 'L/L', hvyScore: 0.91, barrelPct: 11.3, pitcherHR9: 1.22, edge: 'NEUTRAL'     },
  { batter: 'Matt Olson',     batterTeam: 'ATL', pitcher: 'Max Scherzer',   pitcherTeam: 'TEX', hand: 'L/R', hvyScore: 0.83, barrelPct:  9.7, pitcherHR9: 0.71, edge: 'UNFAVORABLE' },
]

const MOCK_PITCHERS: PitcherVulnRow[] = [
  { name: 'Kyle Gibson',    team: 'STL', opp: 'LAD', vulnIndex: 88, hr9: 1.84, fbPct: 38.2, kPct: 14.1, tier: 'EXPLOITABLE' },
  { name: 'Jose Berrios',   team: 'TOR', opp: 'NYY', vulnIndex: 74, hr9: 1.62, fbPct: 34.7, kPct: 19.8, tier: 'EXPLOITABLE' },
  { name: 'Chris Bassitt',  team: 'TOR', opp: 'HOU', vulnIndex: 61, hr9: 1.41, fbPct: 33.1, kPct: 22.4, tier: 'ELEVATED'    },
  { name: 'David Peterson', team: 'NYM', opp: 'PHI', vulnIndex: 54, hr9: 1.22, fbPct: 31.8, kPct: 24.7, tier: 'ELEVATED'    },
  { name: 'Zack Wheeler',   team: 'PHI', opp: 'NYM', vulnIndex: 31, hr9: 0.88, fbPct: 28.4, kPct: 31.2, tier: 'STANDARD'    },
]

const MOCK_RANKINGS: ThreatRankRow[] = [
  { rank:  1, player: 'Aaron Judge',      team: 'NYY', pos: 'RF', threatScore: 87, modelProb: 0.241, evPct: 11.2, edgePct: 8.4, barrelPct: 15.2, tier: 'CRITICAL' },
  { rank:  2, player: 'Shohei Ohtani',    team: 'LAD', pos: 'DH', threatScore: 82, modelProb: 0.218, evPct:  9.7, edgePct: 7.1, barrelPct: 13.8, tier: 'CRITICAL' },
  { rank:  3, player: 'Yordan Alvarez',   team: 'HOU', pos: 'LF', threatScore: 76, modelProb: 0.196, evPct:  7.8, edgePct: 6.3, barrelPct: 12.4, tier: 'HIGH'     },
  { rank:  4, player: 'Pete Alonso',      team: 'NYM', pos: '1B', threatScore: 71, modelProb: 0.184, evPct:  6.4, edgePct: 5.2, barrelPct: 10.9, tier: 'HIGH'     },
  { rank:  5, player: 'Kyle Schwarber',   team: 'PHI', pos: 'LF', threatScore: 68, modelProb: 0.179, evPct:  5.9, edgePct: 4.8, barrelPct: 11.3, tier: 'HIGH'     },
  { rank:  6, player: 'Gunnar Henderson', team: 'BAL', pos: 'SS', threatScore: 63, modelProb: 0.164, evPct:  4.7, edgePct: 3.9, barrelPct: 10.1, tier: 'HIGH'     },
  { rank:  7, player: 'Matt Olson',       team: 'ATL', pos: '1B', threatScore: 61, modelProb: 0.158, evPct:  4.2, edgePct: 3.4, barrelPct:  9.7, tier: 'MODERATE' },
  { rank:  8, player: 'Marcell Ozuna',    team: 'ATL', pos: 'LF', threatScore: 57, modelProb: 0.149, evPct:  3.8, edgePct: 3.1, barrelPct:  9.2, tier: 'MODERATE' },
  { rank:  9, player: 'Adolis Garcia',    team: 'TEX', pos: 'RF', threatScore: 54, modelProb: 0.141, evPct:  3.4, edgePct: 2.8, barrelPct:  8.8, tier: 'MODERATE' },
  { rank: 10, player: 'Cal Raleigh',      team: 'SEA', pos: 'C',  threatScore: 51, modelProb: 0.134, evPct:  3.1, edgePct: 2.5, barrelPct:  9.4, tier: 'MODERATE' },
]

// ─── Mock Data — JIG workspace ────────────────────────────────────────────────

const JIG_ESCALATIONS: EscalationEvent[] = [
  { id: 'j1', tier: 'CRITICAL', player: 'Aaron Judge',    team: 'NYY', signal: 'JIG Confidence', value: '94.1%', ts: '09:40' },
  { id: 'j2', tier: 'CRITICAL', player: 'Shohei Ohtani',  team: 'LAD', signal: 'EV Threshold',   value: '+12.4', ts: '09:37' },
  { id: 'j3', tier: 'HIGH',     player: 'Yordan Alvarez', team: 'HOU', signal: 'Edge Qualifier',  value: '+7.8%', ts: '09:34' },
  { id: 'j4', tier: 'HIGH',     player: 'Pete Alonso',    team: 'NYM', signal: 'Barrel Qualify',  value: '10.9%', ts: '09:31' },
  { id: 'j5', tier: 'MODERATE', player: 'Matt Olson',     team: 'ATL', signal: 'FB% Signal',      value: '42.1%', ts: '09:28' },
]

const JIG_RANKINGS: ThreatRankRow[] = [
  { rank: 1, player: 'Aaron Judge',    team: 'NYY', pos: 'RF', threatScore: 91, modelProb: 0.258, evPct: 12.1, edgePct: 9.2, barrelPct: 15.2, tier: 'CRITICAL' },
  { rank: 2, player: 'Shohei Ohtani',  team: 'LAD', pos: 'DH', threatScore: 86, modelProb: 0.231, evPct: 10.4, edgePct: 7.8, barrelPct: 13.8, tier: 'CRITICAL' },
  { rank: 3, player: 'Yordan Alvarez', team: 'HOU', pos: 'LF', threatScore: 79, modelProb: 0.208, evPct:  8.1, edgePct: 6.6, barrelPct: 12.4, tier: 'HIGH'     },
  { rank: 4, player: 'Pete Alonso',    team: 'NYM', pos: '1B', threatScore: 74, modelProb: 0.192, evPct:  6.8, edgePct: 5.5, barrelPct: 10.9, tier: 'HIGH'     },
  { rank: 5, player: 'Kyle Schwarber', team: 'PHI', pos: 'LF', threatScore: 69, modelProb: 0.183, evPct:  6.1, edgePct: 4.9, barrelPct: 11.3, tier: 'HIGH'     },
  { rank: 6, player: 'Matt Olson',     team: 'ATL', pos: '1B', threatScore: 62, modelProb: 0.162, evPct:  4.3, edgePct: 3.5, barrelPct:  9.7, tier: 'MODERATE' },
]

const JIG_MATCHUPS: MatchupRow[] = [
  { batter: 'Aaron Judge',    batterTeam: 'NYY', pitcher: 'Jose Berrios',   pitcherTeam: 'TOR', hand: 'R/R', hvyScore: 1.34, barrelPct: 15.2, pitcherHR9: 1.62, edge: 'FAVORABLE'   },
  { batter: 'Shohei Ohtani',  batterTeam: 'LAD', pitcher: 'Kyle Gibson',    pitcherTeam: 'STL', hand: 'L/R', hvyScore: 1.38, barrelPct: 13.8, pitcherHR9: 1.84, edge: 'FAVORABLE'   },
  { batter: 'Yordan Alvarez', batterTeam: 'HOU', pitcher: 'Chris Bassitt',  pitcherTeam: 'TOR', hand: 'L/R', hvyScore: 1.18, barrelPct: 12.4, pitcherHR9: 1.41, edge: 'FAVORABLE'   },
  { batter: 'Pete Alonso',    batterTeam: 'NYM', pitcher: 'Zack Wheeler',   pitcherTeam: 'PHI', hand: 'R/R', hvyScore: 1.02, barrelPct: 10.9, pitcherHR9: 0.88, edge: 'NEUTRAL'     },
  { batter: 'Matt Olson',     batterTeam: 'ATL', pitcher: 'Max Scherzer',   pitcherTeam: 'TEX', hand: 'L/R', hvyScore: 0.79, barrelPct:  9.7, pitcherHR9: 0.71, edge: 'UNFAVORABLE' },
]

// ─── Standby workspace ────────────────────────────────────────────────────────

const STANDBY_LABELS: Record<WorkspaceId, { title: string; desc: string }> = {
  main:        { title: 'MAIN',        desc: 'Primary threat zone and escalation feed.' },
  jig:         { title: 'JIG',         desc: 'Joint intelligence grid — alternative pick engine.' },
  strategy:    { title: 'STRATEGY',    desc: 'Advanced parlay construction and portfolio sizing.' },
  hits:        { title: 'HITS',        desc: 'Settlement validation and live result tracking.' },
  performance: { title: 'PERFORMANCE', desc: 'Backtest analytics, calibration, and Brier scoring.' },
  ops:         { title: 'OPS',         desc: 'Room 26 — daily operations, CLV, drift monitoring.' },
}

function StandbyWorkspace({ workspace }: { workspace: WorkspaceId }) {
  const info = STANDBY_LABELS[workspace]
  return (
    <div className="flex-1 min-h-0 flex items-center justify-center">
      <div className="text-center">
        <div className="text-[7px] font-mono tracking-[0.36em] text-zinc-700 uppercase mb-3">
          WORKSPACE · {info.title}
        </div>
        <div className="text-[11px] font-mono text-zinc-600 max-w-[320px] leading-relaxed">
          {info.desc}
        </div>
        <div className="mt-6 text-[6.5px] font-mono tracking-[0.28em] text-zinc-800 uppercase">
          STANDBY — NO ACTIVE FEED
        </div>
      </div>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

const GRID = 'flex-1 min-h-0 grid grid-cols-12 grid-rows-2 gap-[6px] p-[6px]'

export default function DashboardPage() {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>('main')

  return (
    <div className="h-screen flex flex-col bg-[#030508] overflow-hidden">
      <CommandHeader
        date="Saturday, May 23 2026"
        slateCount={87}
        activeThreats={14}
        systemStatus="OPERATIONAL"
        activeWorkspace={activeWorkspace}
        onWorkspaceChange={setActiveWorkspace}
      />

      {/* ── MAIN workspace ── */}
      {activeWorkspace === 'main' && (
        <div className={GRID}>
          <Panel label="Escalation Feed"        zoneId="ESC-01" status="ALERT"  accent="red"   className="col-start-1 col-span-2 row-start-1 row-span-2">
            <EscalationFeed events={MOCK_ESCALATIONS} />
          </Panel>
          <Panel label="Primary HR Threat Zone" zoneId="THR-01" status="ACTIVE"               className="col-start-3 col-span-6 row-start-1">
            <div className="flex gap-[6px] p-[6px] overflow-x-auto h-full items-start">
              {MOCK_THREATS.map((t, i) => <HRThreatCard key={i} {...t} className="shrink-0" />)}
            </div>
          </Panel>
          <Panel label="Pitcher Vulnerability"  zoneId="VUL-01" status="ACTIVE" accent="amber" className="col-start-9 col-span-4 row-start-1">
            <PitcherVulnerabilityPanel rows={MOCK_PITCHERS} />
          </Panel>
          <Panel label="Matchup Intelligence"   zoneId="MTH-01" status="ACTIVE" accent="sky"   className="col-start-3 col-span-6 row-start-2">
            <MatchupIntelPanel rows={MOCK_MATCHUPS} />
          </Panel>
          <Panel label="Threat Rankings"        zoneId="RNK-01" status="ACTIVE"               className="col-start-9 col-span-4 row-start-2">
            <ThreatRankingsTable rows={MOCK_RANKINGS} />
          </Panel>
        </div>
      )}

      {/* ── JIG workspace — distinct layout, JIG-filtered intelligence ── */}
      {activeWorkspace === 'jig' && (
        <div className={GRID}>
          <Panel label="JIG Signal Feed"        zoneId="JIG-ESC" status="ALERT"  accent="red"   className="col-start-1 col-span-2 row-start-1 row-span-2">
            <EscalationFeed events={JIG_ESCALATIONS} />
          </Panel>
          <Panel label="JIG — Qualified Picks"  zoneId="JIG-RNK" status="ACTIVE"               className="col-start-3 col-span-5 row-start-1 row-span-2">
            <ThreatRankingsTable rows={JIG_RANKINGS} />
          </Panel>
          <Panel label="JIG Matchup Matrix"     zoneId="JIG-MTH" status="ACTIVE" accent="sky"   className="col-start-8 col-span-5 row-start-1">
            <MatchupIntelPanel rows={JIG_MATCHUPS} />
          </Panel>
          <Panel label="JIG — Engine Status"    zoneId="JIG-SYS" status="STANDBY"              className="col-start-8 col-span-5 row-start-2">
            <div className="p-4 flex flex-col gap-3">
              {[
                { label: 'Poisson model',      value: 'ACTIVE',    ok: true  },
                { label: 'Platt calibration',  value: 'ACTIVE',    ok: true  },
                { label: 'Elite reg. ceiling', value: 'ENABLED',   ok: true  },
                { label: 'Context guard',      value: 'ENABLED',   ok: true  },
                { label: 'CLV feed',           value: 'NO DATA',   ok: false },
                { label: 'Settlement',         value: 'n=324',     ok: true  },
                { label: 'Drift monitor',      value: 'STABLE',    ok: true  },
                { label: 'Barrel threshold',   value: '≥8%',       ok: true  },
              ].map(({ label, value, ok }) => (
                <div key={label} className="flex items-center justify-between border-b border-white/[0.04] pb-[6px] last:border-0">
                  <span className="text-[8px] font-mono tracking-[0.16em] text-zinc-600 uppercase">{label}</span>
                  <span className={`text-[9px] font-mono font-semibold tracking-[0.12em] ${ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      )}

      {/* ── All other workspaces — standby ── */}
      {activeWorkspace !== 'main' && activeWorkspace !== 'jig' && (
        <StandbyWorkspace workspace={activeWorkspace} />
      )}
    </div>
  )
}
