/* HR Engine — Ticket Command Slip
   Pass 2: real grade/EV/confidence displayed; auto-post on submit; stale-slip fixed;
   clickable View Card per leg. Never computes grade — displays backend values only. */

const TC_API = 'https://mlb-hr-api.fly.dev';
const TC_FD_URL = 'https://sportsbook.fanduel.com/baseball';

const TC_SEND_SVG   = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/></svg>';
const TC_FAN_SVG    = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l10 10-10 10L2 12z"/></svg>';
const TC_TAG_SVG    = '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M3 11V4h7l11 11-7 7z"/><circle cx="7.5" cy="7.5" r="1.6" fill="currentColor"/></svg>';
const TC_EXT_SVG    = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 5h10v10M19 5L9 15M15 13v6H5V9h6"/></svg>';
const TC_BULB_SVG   = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 1 4 10.5c-.7.6-1 1.2-1 2.5H9c0-1.3-.3-1.9-1-2.5A6 6 0 0 1 12 3z"/></svg>';
const TC_SHIELD_SVG = '<svg viewBox="0 0 24 28" width="40" height="46" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M12 2l9 3.5v8C21 20 17 24.5 12 26 7 24.5 3 20 3 13.5v-8z" fill="rgba(26,255,102,.08)"/><path d="M8 14l3 3 5-6" stroke-width="2" stroke-linecap="round"/></svg>';

function tcFmt(v) {
  return v != null ? Number(v).toFixed(1) + '%' : '—';
}

function tcGradeColor(colorStr) {
  if (colorStr === 'green') return '#1aff66';
  if (colorStr === 'red')   return '#ff3344';
  if (colorStr === 'amber') return '#ffb020';
  return 'var(--fg-2, #e0e8ff)';
}

function tcConfColor(label) {
  if (label === 'HIGH')   return '#1aff66';
  if (label === 'LOW')    return '#ff3344';
  if (label === 'MEDIUM') return '#ffb020';
  return 'var(--fg-3, #9aa0ac)';
}

/* ---- Leg card ---- */
function TcLegCard({ leg, onRemove, onViewCard, analysisLeg }) {
  const prob   = tcFmt(leg.hrprob);
  const barrel = tcFmt(leg.barrel);
  const hh     = tcFmt(leg.hh);
  const tier   = leg.tier || '—';
  const tierCls = tier === 'APEX' ? 'tcs-tier--apex'
    : tier === 'ELITE' ? 'tcs-tier--elite'
    : tier === 'EDGE'  ? 'tcs-tier--edge'
    : 'tcs-tier--other';

  const evPct = analysisLeg?.ev_pct;
  const evStr = evPct != null ? (evPct > 0 ? '+' : '') + evPct.toFixed(1) + '%' : null;
  const evColor = evPct != null ? tcGradeColor(evPct > 0 ? 'green' : evPct < 0 ? 'red' : 'amber') : null;
  const isPending = analysisLeg?.status === 'pending';

  return (
    <div className="tcs-leg">
      <div className="tcs-leg__top">
        <div className="tcs-leg__num">{leg.n}</div>
        <div className="tcs-leg__id">
          <div className="tcs-leg__name">{leg.name || '—'}</div>
          {leg.teamAbbr && (
            <div className="tcs-leg__meta">
              <span className="tcs-leg__team">{leg.teamAbbr}</span>
            </div>
          )}
          {leg.pitcher_name && (
            <div className="tcs-leg__matchup">vs {leg.pitcher_name}</div>
          )}
        </div>
        <div className="tcs-leg__actions">
          <a className="tcs-btn tcs-btn--fan"
             href={TC_FD_URL} target="_blank" rel="noopener noreferrer">
            <span dangerouslySetInnerHTML={{__html: TC_FAN_SVG}} /> FANDUEL
            <span dangerouslySetInnerHTML={{__html: TC_EXT_SVG}} />
          </a>
          <button className="tcs-btn" onClick={() => onViewCard && onViewCard(leg)}>
            View Card
          </button>
          <button className="tcs-linkbtn" onClick={() => onRemove(leg.n)}>Remove</button>
        </div>
      </div>

      <div className="tcs-leg__stats">
        <div className="tcs-leg__stat">
          <div className="tcs-sk">HR Prob</div>
          <div className="tcs-sv tcs-pos">{prob}</div>
        </div>
        <div className="tcs-leg__stat">
          <div className="tcs-sk">Tier</div>
          <div className={`tcs-tier ${tierCls}`}>{tier}</div>
        </div>
        <div className="tcs-leg__stat">
          <div className="tcs-sk">Barrel %</div>
          <div className="tcs-sv">{barrel}</div>
        </div>
        <div className="tcs-leg__stat">
          <div className="tcs-sk">Hard-Hit %</div>
          <div className="tcs-sv">{hh}</div>
        </div>
        {analysisLeg && (
          <div className="tcs-leg__stat">
            <div className="tcs-sk">EV</div>
            <div className="tcs-sv tcs-mono" style={{color: evColor || undefined}}>
              {isPending ? 'pending' : evStr || '—'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Summary strip — real grade values from backend analysis ---- */
function TcSumStrip({ legs, stake, analysis }) {
  const n          = legs.length;
  const grade      = analysis?.grade;
  const combined   = analysis?.combined;
  const confidence = analysis?.confidence;

  const gradeLabel = grade?.letter || '—';
  const gradeColor = grade?.color ? tcGradeColor(grade.color) : undefined;
  const probStr = combined?.probability != null
    ? (combined.probability * 100).toFixed(1) + '%' : '—';
  const evPct   = combined?.ev_pct;
  const evStr   = evPct != null ? (evPct > 0 ? '+' : '') + evPct.toFixed(1) + '%' : '—';
  const evColor = evPct != null ? tcGradeColor(evPct > 0 ? 'green' : evPct < 0 ? 'red' : 'amber') : undefined;
  const confLabel = confidence?.label || '—';
  const confColor = tcConfColor(confLabel);

  return (
    <div className="tcs-sumstrip">
      <div className="tcs-sumcell">
        <div className="tcs-sv tcs-sv--legs">{n}</div>
        <div className="tcs-sk">Legs</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Grade</div>
        <div className="tcs-sv" style={{color: gradeColor}}>{gradeLabel}</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Combined Prob</div>
        <div className="tcs-sv tcs-mono">{probStr}</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Combined EV</div>
        <div className="tcs-sv tcs-mono" style={{color: evColor}}>{evStr}</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Confidence</div>
        <div className="tcs-sv" style={{fontSize:'15px', color: confColor}}>{confLabel}</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Stake</div>
        <div className="tcs-sv tcs-mono">${parseFloat(stake || 0).toFixed(2)}</div>
      </div>
    </div>
  );
}

/* ---- Honest analysis panel — replaces Engine + Grade preview panels ---- */
function TcAnalysisPanel({ analysis }) {
  if (!analysis) {
    return (
      <div className="tcs-panel">
        <div className="tcs-panel__hd">
          <h2 className="tcs-panel__title">Ticket Analysis</h2>
        </div>
        <div className="tcs-panel__bd">
          <div className="tcs-pv-block">
            <div className="tcs-pv-block__title" style={{color:'var(--tcs-ink3)'}}>Loading analysis…</div>
          </div>
        </div>
      </div>
    );
  }

  const grade      = analysis.grade || {};
  const combined   = analysis.combined || {};
  const confidence = analysis.confidence || {};
  const honestRead = analysis.honest_read || {};
  const analyzed   = analysis.legs || [];

  const gradeColor = tcGradeColor(grade.color);
  const probPct = combined.probability != null
    ? (combined.probability * 100).toFixed(1) + '%' : '—';
  const evPct = combined.ev_pct;
  const evStr = evPct != null ? (evPct > 0 ? '+' : '') + evPct.toFixed(2) + '%' : '—';
  const evColor = evPct != null ? tcGradeColor(evPct > 0 ? 'green' : evPct < 0 ? 'red' : 'amber') : undefined;

  return (
    <div className="tcs-panel">
      <div className="tcs-panel__hd">
        <h2 className="tcs-panel__title">Ticket Analysis</h2>
        {grade.status === 'complete' && (
          <span style={{
            fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '11px',
            letterSpacing: '0.1em', textTransform: 'uppercase',
            color: gradeColor, border: `1px solid ${gradeColor}55`,
            borderRadius: '3px', padding: '2px 7px', marginLeft: 'auto',
          }}>
            {grade.letter} · {grade.label}
          </span>
        )}
      </div>
      <div className="tcs-panel__bd">

        {/* Grade stats row */}
        <div style={{display:'flex',gap:'16px',flexWrap:'wrap',marginBottom:'10px'}}>
          <div>
            <div className="tcs-sk">Combined Prob</div>
            <div className="tcs-sv tcs-mono">{probPct}</div>
          </div>
          <div>
            <div className="tcs-sk">Combined EV</div>
            <div className="tcs-sv tcs-mono" style={{color: evColor}}>{evStr}</div>
          </div>
          <div>
            <div className="tcs-sk">Confidence</div>
            <div className="tcs-sv" style={{color: tcConfColor(confidence.label)}}>
              {confidence.label || '—'}
            </div>
          </div>
        </div>

        {/* Honest singles-better note */}
        {honestRead.singles_would_be_better && (
          <div className="tcs-pv-block" style={{borderLeft:'2px solid #ffb020',paddingLeft:'8px',marginBottom:'10px'}}>
            <div className="tcs-pv-block__title" style={{color:'#ffb020'}}>Singles Would Be Better</div>
            <div className="tcs-pv-block__body">
              Parlay EV: {evStr} · Best single: +{(honestRead.best_single_ev_pct || 0).toFixed(1)}%.
              Consider a straight bet on your strongest leg instead.
            </div>
          </div>
        )}

        {/* Per-leg EV breakdown */}
        {analyzed.length > 0 && (
          <div className="tcs-pv-block">
            <div className="tcs-pv-block__title" style={{marginBottom:'4px'}}>Per-Leg EV</div>
            {analyzed.map((al, i) => {
              const legEv = al.ev_pct;
              const legEvStr = legEv != null ? (legEv > 0 ? '+' : '') + legEv.toFixed(1) + '%' : '—';
              const legEvColor = legEv != null ? tcGradeColor(legEv > 0 ? 'green' : legEv < 0 ? 'red' : 'amber') : undefined;
              const pending = al.status === 'pending';
              return (
                <div key={al.leg_id || i} style={{
                  display:'flex', justifyContent:'space-between',
                  padding:'3px 0', fontSize:'11px',
                  borderBottom:'1px solid rgba(59,111,255,0.1)',
                }}>
                  <span style={{color:'var(--tcs-ink3)'}}>{al.player_name || `Leg ${i + 1}`}</span>
                  <span className="tcs-mono" style={{color: pending ? 'var(--tcs-ink3)' : legEvColor}}>
                    {pending ? 'pending odds' : legEvStr}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* Low-confidence reasons */}
        {(confidence.reasons || []).length > 0 && (
          <div style={{fontSize:'10px',color:'var(--tcs-ink3)',marginTop:'6px',fontFamily:'var(--font-mono)'}}>
            Low confidence: {confidence.reasons.join(', ')}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Recommendations panel — shows singles-better call-to-action or EV summary ---- */
function TcRecsPanel({ analysis }) {
  const honestRead = analysis?.honest_read;
  const grade      = analysis?.grade;
  const evPct      = analysis?.combined?.ev_pct;

  return (
    <div className="tcs-panel">
      <div className="tcs-panel__hd">
        <span style={{color:'var(--tcs-gold)'}} dangerouslySetInnerHTML={{__html: TC_BULB_SVG}} />
        <h2 className="tcs-panel__title">Engine Recommendations</h2>
      </div>
      <div className="tcs-panel__bd">
        {!analysis ? (
          <div className="tcs-pv-block">
            <div className="tcs-pv-block__title" style={{color:'var(--tcs-ink3)'}}>Loading…</div>
          </div>
        ) : honestRead?.singles_would_be_better ? (
          <div className="tcs-pv-block" style={{borderLeft:'2px solid #ffb020',paddingLeft:'8px'}}>
            <div className="tcs-pv-block__title" style={{color:'#ffb020'}}>Consider a Single</div>
            <div className="tcs-pv-block__body">
              This parlay grades <strong style={{color: tcGradeColor(grade?.color)}}>{grade?.letter || '—'} ({grade?.label || '—'})</strong>.
              Best single EV: +{(honestRead.best_single_ev_pct || 0).toFixed(1)}% outperforms the combined ticket.
              Pull your strongest pick as a straight bet.
            </div>
          </div>
        ) : evPct != null && evPct > 0 ? (
          <div className="tcs-pv-block">
            <div className="tcs-pv-block__title" style={{color:'#1aff66'}}>Positive EV Ticket</div>
            <div className="tcs-pv-block__body">
              This ticket grades <strong style={{color: tcGradeColor(grade?.color)}}>{grade?.letter}</strong> with {evPct > 0 ? '+' : ''}{evPct.toFixed(1)}% combined EV.
              Review per-leg data above before deploying.
            </div>
          </div>
        ) : (
          <div className="tcs-pv-block">
            <div className="tcs-pv-block__title">
              {grade?.letter ? `Grade: ${grade.letter} (${grade.label})` : 'Review above'}
            </div>
            <div className="tcs-pv-block__body">
              Review per-leg data and EV breakdown before deploying.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Summary report ---- */
function TcReportPanel({ legs }) {
  const n = legs.length;
  const names = legs.map(l => l.name || '—').join(', ');
  return (
    <div className="tcs-panel">
      <div className="tcs-panel__hd">
        <h2 className="tcs-panel__title">Ticket Summary Report</h2>
      </div>
      <div className="tcs-panel__bd">
        <div className="tcs-report">
          <div className="tcs-report__shield" dangerouslySetInnerHTML={{__html: TC_SHIELD_SVG}} />
          <div className="tcs-report__body">
            <p>{n}-leg HR ticket: {names}. Per-leg barrel%, hard-hit%, HR probability, tier, and EV are live above.</p>
            <div className="tcs-report__blk"><b>Strengths:</b> Per-leg stats available above (barrel %, hard-hit %, tier).</div>
            <div className="tcs-report__blk"><b>Risks:</b> Multi-leg variance increases with each added leg.</div>
            <div className="tcs-report__blk"><b>Overall:</b> Review the grade and EV analysis before deploying.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- Deploy bar ---- */
function TcDeployBar({ legs, ticketId, stake, setStake, onSubmit, submitState, mode }) {
  const n = legs.length;
  const slipType = `${n}-LEG POWER`;
  const disabled = submitState === 'loading' || submitState === 'done' || !ticketId || n === 0;
  const isMobile = mode === 'mobile';

  const stepStake = (delta) => {
    setStake(s => Math.max(0, (parseFloat(s) || 0) + delta).toFixed(2));
  };

  const submitLabel = submitState === 'loading' ? 'Submitting…'
    : submitState === 'done'   ? '✓ Submitted'
    : submitState === 'error'  ? 'Error — Retry'
    : submitState === 'noauth' ? 'Sign In First'
    : isMobile ? 'Submit →'
    : 'Submit Slip ';

  if (isMobile) {
    return (
      <div className="tcs-m-deploy">
        <div className="tcs-m-deploy__top">
          <div className="tcs-m-deploy__lbl">
            <span className="tcs-deploy-icon" dangerouslySetInnerHTML={{__html: TC_SEND_SVG}} />
            Deployment
          </div>
        </div>
        <div className="tcs-m-deploy__row">
          <div className="tcs-m-deploy__meta"><div className="tcs-dk">Stake</div></div>
          <div className="tcs-stepper">
            <span className="tcs-stepper__pre">$</span>
            <input className="tcs-stepper__input" value={stake} inputMode="decimal"
              onChange={e => setStake(e.target.value)} />
            <button className="tcs-stepper__btn" onClick={() => stepStake(-1)}>−</button>
            <button className="tcs-stepper__btn" onClick={() => stepStake(1)}>＋</button>
          </div>
          <div className="tcs-m-deploy__meta" style={{marginLeft:'auto'}}>
            <div className="tcs-dk">Slip</div>
            <div className="tcs-dv" style={{fontSize:'12px'}}>{slipType}</div>
          </div>
          <div className="tcs-m-deploy__meta">
            <div className="tcs-dk">Book</div>
            <div className="tcs-dv" style={{color:'var(--tcs-fan)',fontSize:'12px'}}>
              <span dangerouslySetInnerHTML={{__html: TC_FAN_SVG}} /> FD
            </div>
          </div>
        </div>
        <div className="tcs-m-deploy__btns">
          <a className="tcs-btn tcs-btn--lg tcs-btn--fan"
             href={TC_FD_URL} target="_blank" rel="noopener noreferrer"
             style={{flex:1,justifyContent:'center',display:'flex'}}>
            Open FanDuel <span dangerouslySetInnerHTML={{__html: TC_EXT_SVG}} />
          </a>
          <button className="tcs-btn tcs-btn--lg tcs-btn--primary"
            onClick={onSubmit} disabled={disabled}
            style={{flex:'1.3',justifyContent:'center',display:'flex',gap:'6px'}}>
            {submitLabel}
            {submitState === 'idle' && <span dangerouslySetInnerHTML={{__html: TC_SEND_SVG}} />}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="tcs-deploybar">
      <div className="tcs-deploybar__inner">
        <div className="tcs-deploy-tag">
          <span className="tcs-deploy-tag__ic" dangerouslySetInnerHTML={{__html: TC_SEND_SVG}} />
          Deployment Panel
        </div>
        <div className="tcs-deploy-field">
          <div className="tcs-dk">Stake Amount</div>
          <div className="tcs-stepper">
            <span className="tcs-stepper__pre">$</span>
            <input className="tcs-stepper__input" value={stake} inputMode="decimal"
              onChange={e => setStake(e.target.value)} />
            <button className="tcs-stepper__btn" onClick={() => stepStake(-1)}>−</button>
            <button className="tcs-stepper__btn" onClick={() => stepStake(1)}>＋</button>
          </div>
        </div>
        <div className="tcs-deploy-field">
          <div className="tcs-dk">Slip Type</div>
          <div className="tcs-dv">{slipType}</div>
        </div>
        <div className="tcs-deploy-field">
          <div className="tcs-dk">Sportsbook</div>
          <div className="tcs-dv tcs-dv--fan">
            <span dangerouslySetInnerHTML={{__html: TC_FAN_SVG}} /> FANDUEL
          </div>
        </div>
        <div className="tcs-deploy-actions">
          <div className="tcs-deploy-action-col">
            <a className="tcs-btn tcs-btn--lg tcs-btn--fan"
               href={TC_FD_URL} target="_blank" rel="noopener noreferrer">
              Open FanDuel Slip <span dangerouslySetInnerHTML={{__html: TC_EXT_SVG}} />
            </a>
            <div className="tcs-deploy-note">Review in FanDuel and place your bet.</div>
          </div>
          <div className="tcs-deploy-action-col">
            <button className="tcs-btn tcs-btn--lg tcs-btn--primary"
              onClick={onSubmit} disabled={disabled}>
              {submitLabel}
              {submitState === 'idle' && <span dangerouslySetInnerHTML={{__html: TC_SEND_SVG}} />}
            </button>
            <div className="tcs-deploy-note">Auto-posts to community on submit.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- Main overlay component ---- */
function TicketCommandSlip({ legs, ticketId, onClose, onRemoveLeg }) {
  const [stake, setStake]             = React.useState('5.00');
  const [submitState, setSubmitState] = React.useState('idle');
  const [analysis, setAnalysis]       = React.useState(null);
  const [cardRow, setCardRow]         = React.useState(null);

  // Fetch analysis whenever ticketId is available
  React.useEffect(() => {
    if (!ticketId || !window.__hrAuth?.authFetch) return;
    let cancelled = false;
    window.__hrAuth.authFetch(`${TC_API}/api/tickets/${ticketId}/analysis`)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!cancelled && d?.analysis) setAnalysis(d.analysis); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [ticketId]);

  const handleSubmit = async () => {
    if (!ticketId || legs.length === 0) return;
    if (!window.__hrAuth?.authFetch) { setSubmitState('noauth'); return; }
    setSubmitState('loading');
    try {
      const res = await window.__hrAuth.authFetch(
        `${TC_API}/api/tickets/complete`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticket_id: ticketId, stake: parseFloat(stake) || null }),
        }
      );
      if (res._noAuth) { setSubmitState('noauth'); return; }
      if (!res.ok)     { setSubmitState('error');  return; }
      const data = await res.json();
      // Auto-post to community for signed-in users (fire-and-forget)
      window.__hrAuth.authFetch(`${TC_API}/api/community/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_id: ticketId }),
      }).catch(() => {});
      // Consume reset_slip: clear state immediately, then close
      if (data.reset_slip) window.__hrSlip.resetSlip();
      onClose();
    } catch (_) {
      setSubmitState('error');
    }
  };

  const handleClose = () => {
    window.__hrSlip.resetSlip();
    onClose();
  };

  const handleViewCard = (leg) => {
    setCardRow({ id: leg.id, name: leg.name, teamAbbr: leg.teamAbbr, pitcher_name: leg.pitcher_name });
  };

  const n = legs.length;

  // Index analyzed legs by player_name for EV display in TcLegCard
  const analysisLegByName = {};
  (analysis?.legs || []).forEach(al => {
    if (al.player_name) analysisLegByName[al.player_name] = al;
  });

  const overlay = (
    <div className="tcs-overlay" role="dialog" aria-label="Ticket Command Slip">

      {/* Batter card modal */}
      {cardRow && window.BatterDetailCard && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 10010,
          background: 'rgba(0,0,0,0.78)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }} onClick={() => setCardRow(null)}>
          <div style={{maxWidth:'900px',width:'100%',maxHeight:'90vh',overflow:'auto',borderRadius:'10px'}}
               onClick={e => e.stopPropagation()}>
            {React.createElement(window.BatterDetailCard, { row: cardRow, onClose: () => setCardRow(null) })}
          </div>
        </div>
      )}

      {/* ===== PC LAYOUT ===== */}
      <div className="tcs-pc">
        <div className="tcs-wrap">
          <header className="tcs-header">
            <div className="tcs-logo">
              <span dangerouslySetInnerHTML={{__html: TC_TAG_SVG}} />
            </div>
            <div className="tcs-title-block">
              <h1 className="tcs-title">TICKET COMMAND</h1>
              <div className="tcs-sub">HR DEPLOYMENT SLIP</div>
            </div>
            <div className="tcs-header-acts">
              <div className="tcs-status-row">
                <span className="tcs-live"><i className="tcs-live-dot" />Live</span>
              </div>
              <button className="tcs-close-btn" onClick={onClose} title="Close">✕</button>
            </div>
          </header>

          <TcSumStrip legs={legs} stake={stake} analysis={analysis} />

          <div className="tcs-grid">
            <div className="tcs-col">
              <div className="tcs-ticket-hd">
                <h2 className="tcs-ticket-h2">
                  Your Ticket <span>({n} Leg{n !== 1 ? 's' : ''})</span>
                </h2>
                <button className="tcs-btn tcs-btn--ghostblue" disabled title="Return to board to add players">
                  + Add Player
                </button>
              </div>

              {n === 0 ? (
                <div className="tcs-empty">No legs in ticket. Add players from the board.</div>
              ) : (
                legs.map(leg => (
                  <TcLegCard key={leg.n} leg={leg} onRemove={onRemoveLeg}
                    onViewCard={handleViewCard}
                    analysisLeg={analysisLegByName[leg.name]} />
                ))
              )}

              <div className="tcs-addrow" onClick={onClose}>
                <div className="tcs-addrow__t">＋ Add Another Player</div>
                <div className="tcs-addrow__s">Return to board and use + on any HR Threat card.</div>
              </div>

              <TcRecsPanel analysis={analysis} />
            </div>

            <div className="tcs-col">
              <TcAnalysisPanel analysis={analysis} />
              <TcReportPanel legs={legs} />
            </div>
          </div>
        </div>

        <TcDeployBar legs={legs} ticketId={ticketId} stake={stake} setStake={setStake}
          onSubmit={handleSubmit} submitState={submitState} mode="pc" />
      </div>

      {/* ===== MOBILE LAYOUT ===== */}
      <div className="tcs-mobile">
        <div className="tcs-m-header">
          <div className="tcs-logo tcs-logo--sm">
            <span dangerouslySetInnerHTML={{__html: TC_TAG_SVG}} />
          </div>
          <div className="tcs-title-block">
            <h1 className="tcs-title tcs-title--sm">TICKET COMMAND</h1>
            <div className="tcs-sub tcs-sub--sm">HR DEPLOYMENT SLIP</div>
          </div>
          <span className="tcs-live tcs-live--sm"><i className="tcs-live-dot" />Live</span>
          <button className="tcs-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="tcs-m-scroll">
          {/* Mobile summary grid — real grade values */}
          {(() => {
            const grade    = analysis?.grade;
            const combined = analysis?.combined;
            const conf     = analysis?.confidence;
            const gc       = grade?.color ? tcGradeColor(grade.color) : undefined;
            const probStr  = combined?.probability != null ? (combined.probability * 100).toFixed(1) + '%' : '—';
            const evPct    = combined?.ev_pct;
            const evStr    = evPct != null ? (evPct > 0 ? '+' : '') + evPct.toFixed(1) + '%' : '—';
            const ec       = evPct != null ? tcGradeColor(evPct > 0 ? 'green' : evPct < 0 ? 'red' : 'amber') : undefined;
            const confLabel = conf?.label || '—';
            return (
              <div className="tcs-m-sumgrid">
                <div className="tcs-m-sumcell">
                  <div className="tcs-sk">Legs</div>
                  <div className="tcs-sv tcs-sv--num">{n}</div>
                </div>
                <div className="tcs-m-sumcell">
                  <div className="tcs-sk">Grade</div>
                  <div className="tcs-sv" style={{color: gc}}>{grade?.letter || '—'}</div>
                </div>
                <div className="tcs-m-sumcell">
                  <div className="tcs-sk">Combined Prob</div>
                  <div className="tcs-sv tcs-mono">{probStr}</div>
                </div>
                <div className="tcs-m-sumcell">
                  <div className="tcs-sk">Combined EV</div>
                  <div className="tcs-sv tcs-mono" style={{color: ec}}>{evStr}</div>
                </div>
                <div className="tcs-m-sumcell">
                  <div className="tcs-sk">Confidence</div>
                  <div className="tcs-sv" style={{fontSize:'14px',color:tcConfColor(confLabel)}}>{confLabel}</div>
                </div>
                <div className="tcs-m-sumcell">
                  <div className="tcs-sk">Stake</div>
                  <div className="tcs-sv tcs-mono">${parseFloat(stake || 0).toFixed(2)}</div>
                </div>
              </div>
            );
          })()}

          <div className="tcs-m-secttl">
            <h2 className="tcs-m-h2">Your Ticket <span>({n})</span></h2>
            <button className="tcs-btn tcs-btn--ghostblue tcs-btn--sm" onClick={onClose}>+ Add</button>
          </div>

          {n === 0 ? (
            <div className="tcs-empty">No legs. Add from board.</div>
          ) : (
            legs.map(leg => (
              <TcLegCard key={leg.n} leg={leg} onRemove={onRemoveLeg}
                onViewCard={handleViewCard}
                analysisLeg={analysisLegByName[leg.name]} />
            ))
          )}

          <div className="tcs-addrow" onClick={onClose}>
            <div className="tcs-addrow__t">＋ Add Another Player</div>
            <div className="tcs-addrow__s">Return to board and use + on any HR Threat card.</div>
          </div>

          <TcAnalysisPanel analysis={analysis} />
          <TcReportPanel legs={legs} />
          <TcRecsPanel analysis={analysis} />
        </div>

        <TcDeployBar legs={legs} ticketId={ticketId} stake={stake} setStake={setStake}
          onSubmit={handleSubmit} submitState={submitState} mode="mobile" />
      </div>
    </div>
  );

  return ReactDOM.createPortal(overlay, document.body);
}

window.TicketCommandSlip = TicketCommandSlip;
