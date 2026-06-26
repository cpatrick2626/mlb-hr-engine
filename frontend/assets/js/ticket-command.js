/* HR Engine — Ticket Command Slip
   Full-screen overlay: PC two-column layout + mobile single-column.
   LIVE: legs list (name/team/tier/hrProb/barrel/hh/pitcher), stake input, submit.
   PREVIEW (engine pending): combined prob, grade, confidence, recommendations, payout.
   Never computes combinedProb or grade — those are clearly labeled placeholders. */

const TC_API = 'https://mlb-hr-api.fly.dev';
const TC_FD_URL = 'https://sportsbook.fanduel.com/baseball';

/* ---- icons (inline SVG strings rendered via dangerouslySetInnerHTML) ---- */
const TC_SEND_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/></svg>';
const TC_FAN_SVG  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l10 10-10 10L2 12z"/></svg>';
const TC_TAG_SVG  = '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M3 11V4h7l11 11-7 7z"/><circle cx="7.5" cy="7.5" r="1.6" fill="currentColor"/></svg>';
const TC_EXT_SVG  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 5h10v10M19 5L9 15M15 13v6H5V9h6"/></svg>';
const TC_BULB_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 1 4 10.5c-.7.6-1 1.2-1 2.5H9c0-1.3-.3-1.9-1-2.5A6 6 0 0 1 12 3z"/></svg>';
const TC_SHIELD_SVG = '<svg viewBox="0 0 24 28" width="40" height="46" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M12 2l9 3.5v8C21 20 17 24.5 12 26 7 24.5 3 20 3 13.5v-8z" fill="rgba(26,255,102,.08)"/><path d="M8 14l3 3 5-6" stroke-width="2" stroke-linecap="round"/></svg>';

function tcFmt(v) {
  return v != null ? Number(v).toFixed(1) + '%' : '—';
}

function TcPreviewTag() {
  return <span className="tcs-pv-tag">SAMPLE</span>;
}

/* ---- Leg card ---- */
function TcLegCard({ leg, onRemove }) {
  const prob    = tcFmt(leg.hrprob);
  const barrel  = tcFmt(leg.barrel);
  const hh      = tcFmt(leg.hh);
  const tier    = leg.tier || '—';
  const tierCls = tier === 'APEX' ? 'tcs-tier--apex'
    : tier === 'ELITE' ? 'tcs-tier--elite'
    : tier === 'EDGE'  ? 'tcs-tier--edge'
    : 'tcs-tier--other';

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
          <button className="tcs-btn" disabled title="Player card view coming soon">View Card</button>
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
      </div>
    </div>
  );
}

/* ---- Summary strip ---- */
function TcSumStrip({ legs, stake }) {
  const n = legs.length;
  return (
    <div className="tcs-sumstrip">
      <div className="tcs-sumcell">
        <div className="tcs-sv tcs-sv--legs">{n}</div>
        <div className="tcs-sk">Legs</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Grade</div>
        <div className="tcs-sv tcs-pos">—</div>
        <TcPreviewTag />
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Combined Prob</div>
        <div className="tcs-sv tcs-pos tcs-mono">—</div>
        <TcPreviewTag />
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Confidence</div>
        <div className="tcs-sv tcs-warn" style={{fontSize:'15px'}}>—</div>
        <TcPreviewTag />
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Stake</div>
        <div className="tcs-sv tcs-mono">${parseFloat(stake || 0).toFixed(2)}</div>
      </div>
      <div className="tcs-sumcell">
        <div className="tcs-sk">Potential Return</div>
        <div className="tcs-sv tcs-pos tcs-mono">—</div>
        <TcPreviewTag />
      </div>
    </div>
  );
}

/* ---- Preview panels (engine / grade / recs) ---- */
function TcEnginePanel() {
  return (
    <div className="tcs-panel">
      <div className="tcs-panel__hd">
        <h2 className="tcs-panel__title">Ticket Probability Engine</h2>
        <TcPreviewTag />
      </div>
      <div className="tcs-panel__bd">
        <div className="tcs-pv-block">
          <div className="tcs-pv-block__title">Engine Pending</div>
          <div className="tcs-pv-block__body">
            Correlation-adjusted combined probability, adjustment factors, and confidence score appear here after the probability engine build. Raw per-leg probabilities are available above.
          </div>
        </div>
      </div>
    </div>
  );
}

function TcGradePanel() {
  return (
    <div className="tcs-panel">
      <div className="tcs-panel__hd">
        <h2 className="tcs-panel__title">Ticket Grade Breakdown</h2>
        <TcPreviewTag />
      </div>
      <div className="tcs-panel__bd">
        <div className="tcs-pv-block">
          <div className="tcs-pv-block__title">Grade Pending</div>
          <div className="tcs-pv-block__body">
            Overall grade, per-category scores (probability, tiers, matchup, park, certainty, risk), and grade circle appear here after the grade engine build.
          </div>
        </div>
      </div>
    </div>
  );
}

function TcRecsPanel() {
  return (
    <div className="tcs-panel">
      <div className="tcs-panel__hd">
        <span style={{color:'var(--tcs-gold)'}} dangerouslySetInnerHTML={{__html: TC_BULB_SVG}} />
        <h2 className="tcs-panel__title">Engine Recommendations</h2>
        <TcPreviewTag />
      </div>
      <div className="tcs-panel__bd">
        <div className="tcs-pv-block">
          <div className="tcs-pv-block__title">Recommendations Pending</div>
          <div className="tcs-pv-block__body">
            Upgrade suggestions, add candidates, and risk advisories appear here after the recommendation engine build.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- Summary report (real legs, no computed scores) ---- */
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
            <p>{n}-leg HR ticket: {names}. Per-leg barrel%, hard-hit%, HR probability, and tier are live above. Probability engine, grade, and qualitative analysis are engine-pending.</p>
            <div className="tcs-report__blk"><b>Strengths:</b> Per-leg stats available above (barrel %, hard-hit %, tier).</div>
            <div className="tcs-report__blk"><b>Risks:</b> Multi-leg variance increases with each added leg.</div>
            <div className="tcs-report__blk"><b>Overall:</b> Review per-leg data above before deploying.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- Deploy bar (shared between PC footer + mobile) ---- */
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
    : `Submit Slip `;

  if (isMobile) {
    return (
      <div className="tcs-m-deploy">
        <div className="tcs-m-deploy__top">
          <div className="tcs-m-deploy__lbl">
            <span className="tcs-deploy-icon" dangerouslySetInnerHTML={{__html: TC_SEND_SVG}} />
            Deployment
          </div>
          <div className="tcs-m-deploy__ret">
            <div className="tcs-sv tcs-pos">—</div>
            <div className="tcs-mono" style={{fontSize:'9px',color:'var(--tcs-ink3)'}}>Pot. Return</div>
            <TcPreviewTag />
          </div>
        </div>
        <div className="tcs-m-deploy__row">
          <div className="tcs-m-deploy__meta">
            <div className="tcs-dk">Stake</div>
          </div>
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
        <div className="tcs-deploy-field">
          <div className="tcs-dk">Potential Return</div>
          <div className="tcs-dv tcs-pos">—</div>
          <TcPreviewTag />
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
            <div className="tcs-deploy-note">Ticket marked as submitted in Supabase.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- Main overlay component ---- */
function TicketCommandSlip({ legs, ticketId, onClose, onRemoveLeg }) {
  const [stake, setStake]           = React.useState('5.00');
  const [submitState, setSubmitState] = React.useState('idle');

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
          body: JSON.stringify({
            ticket_id: ticketId,
            stake: parseFloat(stake) || null,
          }),
        }
      );
      if (res._noAuth) { setSubmitState('noauth'); return; }
      if (!res.ok)     { setSubmitState('error');  return; }
      setSubmitState('done');
    } catch (_) {
      setSubmitState('error');
    }
  };

  const n = legs.length;

  const overlay = (
    <div className="tcs-overlay" role="dialog" aria-label="Ticket Command Slip">

      {/* ===== PC LAYOUT ===== */}
      <div className="tcs-pc">
        <div className="tcs-wrap">

          {/* Header */}
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

          {/* Summary strip */}
          <TcSumStrip legs={legs} stake={stake} />

          {/* Two-column grid */}
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
                  <TcLegCard key={leg.n} leg={leg} onRemove={onRemoveLeg} />
                ))
              )}

              <div className="tcs-addrow" onClick={onClose}>
                <div className="tcs-addrow__t">＋ Add Another Player</div>
                <div className="tcs-addrow__s">Return to board and use + on any HR Threat card.</div>
              </div>

              <TcRecsPanel />
            </div>

            <div className="tcs-col">
              <TcEnginePanel />
              <TcGradePanel />
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
          {/* Mobile 3×2 summary grid */}
          <div className="tcs-m-sumgrid">
            <div className="tcs-m-sumcell">
              <div className="tcs-sk">Legs</div>
              <div className="tcs-sv tcs-sv--num">{n}</div>
            </div>
            <div className="tcs-m-sumcell">
              <div className="tcs-sk">Grade</div>
              <div className="tcs-sv tcs-pos">—</div>
              <span className="tcs-m-pvmini">SAMPLE</span>
            </div>
            <div className="tcs-m-sumcell">
              <div className="tcs-sk">Combined Prob</div>
              <div className="tcs-sv tcs-pos tcs-mono">—</div>
              <span className="tcs-m-pvmini">SAMPLE</span>
            </div>
            <div className="tcs-m-sumcell">
              <div className="tcs-sk">Confidence</div>
              <div className="tcs-sv tcs-warn" style={{fontSize:'14px'}}>—</div>
              <span className="tcs-m-pvmini">SAMPLE</span>
            </div>
            <div className="tcs-m-sumcell">
              <div className="tcs-sk">Stake</div>
              <div className="tcs-sv tcs-mono">${parseFloat(stake||0).toFixed(2)}</div>
            </div>
            <div className="tcs-m-sumcell">
              <div className="tcs-sk">Return</div>
              <div className="tcs-sv tcs-pos tcs-mono">—</div>
              <span className="tcs-m-pvmini">SAMPLE</span>
            </div>
          </div>

          <div className="tcs-m-secttl">
            <h2 className="tcs-m-h2">Your Ticket <span>({n})</span></h2>
            <button className="tcs-btn tcs-btn--ghostblue tcs-btn--sm" onClick={onClose}>+ Add</button>
          </div>

          {n === 0 ? (
            <div className="tcs-empty">No legs. Add from board.</div>
          ) : (
            legs.map(leg => (
              <TcLegCard key={leg.n} leg={leg} onRemove={onRemoveLeg} />
            ))
          )}

          <div className="tcs-addrow" onClick={onClose}>
            <div className="tcs-addrow__t">＋ Add Another Player</div>
            <div className="tcs-addrow__s">Return to board and use + on any HR Threat card.</div>
          </div>

          <TcEnginePanel />
          <TcGradePanel />
          <TcReportPanel legs={legs} />
          <TcRecsPanel />
        </div>

        <TcDeployBar legs={legs} ticketId={ticketId} stake={stake} setStake={setStake}
          onSubmit={handleSubmit} submitState={submitState} mode="mobile" />
      </div>
    </div>
  );

  return ReactDOM.createPortal(overlay, document.body);
}

window.TicketCommandSlip = TicketCommandSlip;
