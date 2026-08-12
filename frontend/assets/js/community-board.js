/* HR Engine — Community Board + Profile.
   Pass 2: grade/EV/confidence display; Remove (owner-only, confirm-before);
   clickable batter names → card; Copy Slip (loads into builder); per-batter Pick.
   CommunityBoard: open read (no auth). CommunityProfile: signed-in only. */

const COMM_API = 'https://mlb-hr-api.fly.dev';

function commFmtDate(iso) {
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); }
  catch (_) { return ''; }
}

function commGradeColor(colorStr) {
  if (colorStr === 'green') return '#1aff66';
  if (colorStr === 'red')   return '#ff3344';
  if (colorStr === 'amber') return '#ffb020';
  return '#9aa0ac';
}

/* Maps grade subfields → plain-language verdict. Always returns { text, color }. */
function commVerdictLine({ hasEv, evPct, numLegs, singlesBetter }) {
  if (!hasEv) return { text: "Odds pending — can't grade EV yet.", color: 'rgba(224,232,255,0.28)' };
  if (evPct > 0) {
    if (numLegs === 1) return { text: 'Strong — +EV single, worth a look.', color: 'rgba(26,255,102,0.6)' };
    if (singlesBetter) return { text: `Positive EV — ${numLegs}-leg parlay, but singles score higher.`, color: 'rgba(255,176,32,0.6)' };
    return { text: `Solid — ${numLegs}-leg parlay, positive EV.`, color: 'rgba(26,255,102,0.6)' };
  }
  if (singlesBetter) return { text: `Weak — ${numLegs}-leg parlay, −EV, singles are better.`, color: 'rgba(255,51,68,0.6)' };
  const legPart = numLegs > 1 ? `${numLegs}-leg, ` : '';
  return { text: `Weak — ${legPart}negative EV.`, color: 'rgba(255,51,68,0.6)' };
}

/* Build a normalized slip-state row from a community leg record. */
function commLegRow(leg) {
  return {
    player_id: leg.player_id,
    name:      leg.player_name,
    teamAbbr:  leg.team,
    team:      leg.team,
    model_prob: leg.model_prob,
    tier:       leg.tier || 'EDGE',
    board:      'community',
    hrprob:     leg.model_prob != null ? parseFloat((leg.model_prob * 100).toFixed(1)) : null,
  };
}

/* ---- SlipCard: one posted slip ---- */
function CommSlipCard({ post, onRemove, onOpenCard }) {
  const [confirmRemove, setConfirmRemove] = React.useState(false);
  const [removing, setRemoving]           = React.useState(false);
  const persistedStake = (typeof (post.slip || {}).stake === 'number' && isFinite((post.slip || {}).stake))
    ? (post.slip || {}).stake : null;
  const [wager, setWager]     = React.useState(persistedStake != null ? String(persistedStake) : '');
  const [saving, setSaving]   = React.useState(false);
  const [savedOk, setSavedOk] = React.useState(false);

  const slip       = post.slip || {};
  const legs       = slip.legs || [];
  const analysis   = slip.analysis || {};
  const grade      = analysis.grade || {};
  const combined   = analysis.combined || {};
  const confidence = analysis.confidence || {};
  const honestRead = analysis.honest_read || {};
  const analyzed   = analysis.legs || [];
  const dateStr    = commFmtDate(post.posted_at);

  // --- Safe grade display (grade is an OBJECT — render only string subfields) ---
  const gradeLetter  = typeof grade.letter === 'string' && grade.letter ? grade.letter : null;
  const gradeLabel   = typeof grade.label  === 'string' && grade.label  ? grade.label  : 'PENDING';
  const gradeDisplay = gradeLetter || gradeLabel;
  const gradeColor   = commGradeColor(typeof grade.color === 'string' ? grade.color : null);

  // --- Safe combined EV% (combined is an OBJECT — guard numeric ops) ---
  const evPct     = combined.ev_pct;
  const hasEv     = typeof evPct === 'number' && isFinite(evPct);
  const evStr     = hasEv ? (evPct > 0 ? '+' : '') + evPct.toFixed(1) + '%' : null;
  const evDisplay = evStr ? evStr + ' EV' : 'EV pending';
  const evColor   = hasEv ? commGradeColor(evPct > 0 ? 'green' : evPct < 0 ? 'red' : 'amber') : 'rgba(224,232,255,0.35)';

  // --- Safe combined probability ---
  const combinedProb = combined.probability;
  const probDisplay  = typeof combinedProb === 'number' && isFinite(combinedProb)
    ? (combinedProb * 100).toFixed(2) + '%'
    : null;

  // --- Safe confidence (confidence is an OBJECT — render only string subfields) ---
  const confLabel   = typeof confidence.label === 'string' ? confidence.label : '';
  // confidence.reasons is an ARRAY — join to string, never render directly
  const confReasons = Array.isArray(confidence.reasons) ? confidence.reasons.join(' · ') : '';

  // --- Singles better flag (explicit true check — null means not evaluated) ---
  const singlesBetter = honestRead.singles_would_be_better === true;

  // Board + ticket info
  const ticketType = typeof slip.ticket_type === 'string' ? slip.ticket_type.replace(/_/g, ' ') : '';
  const numLegs    = legs.length;

  const verdict = commVerdictLine({ hasEv, evPct, numLegs, singlesBetter });

  const handleCopySlip = () => {
    if (!window.__hrSlip) return;
    if (!window.__hrAuth?.authFetch) {
      const btn = document.querySelector('#auth-root button');
      if (btn) btn.click();
      return;
    }
    legs.forEach(leg => window.__hrSlip.addLeg(commLegRow(leg)));
  };

  const handlePickLeg = (leg) => {
    if (!window.__hrSlip) return;
    window.__hrSlip.requestAdd(commLegRow(leg));
  };

  const handleRemove = async () => {
    if (!onRemove || !window.__hrAuth?.authFetch) return;
    setRemoving(true);
    try {
      const res = await window.__hrAuth.authFetch(
        `${COMM_API}/api/community/posts/${post.post_id}`,
        { method: 'DELETE' }
      );
      if (res.ok) onRemove(post.post_id);
    } catch (_) {}
    setRemoving(false);
    setConfirmRemove(false);
  };

  const isOwner  = !!onRemove;
  const ticketId = slip.ticket_id;

  const saveWager = async () => {
    if (!isOwner || !ticketId || !window.__hrAuth?.authFetch) return;
    const stakeVal = wager === '' ? null : parseFloat(wager);
    if (stakeVal !== null && (!isFinite(stakeVal) || stakeVal < 0)) return;
    setSaving(true);
    try {
      await window.__hrAuth.authFetch(`${COMM_API}/api/tickets/${ticketId}/stake`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stake: stakeVal }),
      });
      setSavedOk(true);
      setTimeout(() => setSavedOk(false), 2000);
    } catch (_) {}
    setSaving(false);
  };

  // Wager + payout — guard every numeric op
  const americanOdds = slip.odds_american;
  const hasOdds = typeof americanOdds === 'number' && isFinite(americanOdds) && americanOdds !== 0;
  const wagerNum = parseFloat(wager);
  const hasWager = isFinite(wagerNum) && wagerNum > 0;
  let payoutStr = null;
  if (hasWager) {
    if (!hasOdds) {
      payoutStr = 'payout pending — no odds';
    } else {
      const decimal = americanOdds > 0
        ? (americanOdds / 100) + 1
        : (100 / Math.abs(americanOdds)) + 1;
      const profit = (decimal - 1) * wagerNum;
      const totalReturn = decimal * wagerNum;
      payoutStr = '+$' + profit.toFixed(2) + ' profit ($' + totalReturn.toFixed(2) + ' return)';
    }
  }

  // Index analysis legs by leg_id — only store when ev_pct is a real number
  const evByLegId = {};
  analyzed.forEach(al => {
    if (al.leg_id && typeof al.ev_pct === 'number' && isFinite(al.ev_pct)) {
      evByLegId[al.leg_id] = al.ev_pct;
    }
  });

  const tierColor = (tier) => {
    if (tier === 'ELITE') return '#1aff66';
    if (tier === 'PRIME') return '#4fc8ff';
    if (tier === 'CORE')  return '#ffb020';
    return 'rgba(224,232,255,0.4)';
  };

  const pillSt = {
    fontSize: '9px', fontFamily: 'var(--font-display)', fontWeight: 800,
    letterSpacing: '0.1em', textTransform: 'uppercase', borderRadius: '3px',
    padding: '2px 6px', border: '1px solid', cursor: 'pointer',
  };

  return (
    <div className="comm-slip">

      {/* ── GRADE VERDICT HEADLINE ── */}
      <div style={{
        borderLeft: `3px solid ${gradeColor}`,
        background: `${gradeColor}0a`,
        borderRadius: '0 5px 5px 0',
        padding: '10px 12px',
        marginBottom: '8px',
      }}>
        {/* Row 1: grade · EV · parlay prob · date */}
        <div style={{display:'flex',alignItems:'baseline',gap:'10px',flexWrap:'wrap'}}>
          <span style={{
            fontFamily: 'var(--font-display)', fontWeight: 900,
            fontSize: '22px', letterSpacing: '0.04em',
            color: gradeColor, lineHeight: 1,
          }}>
            {gradeDisplay}
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '13px',
            color: evColor, fontWeight: 700,
          }}>
            {evDisplay}
          </span>
          {probDisplay && (
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: '11px',
              color: 'rgba(224,232,255,0.5)',
            }}>
              {probDisplay} prob
            </span>
          )}
          {dateStr && (
            <span style={{
              marginLeft: 'auto', fontFamily: 'var(--font-mono)',
              fontSize: '10px', color: 'rgba(224,232,255,0.3)',
            }}>
              {dateStr}
            </span>
          )}
        </div>
        {/* Row 2: confidence · legs count · ticket type · odds */}
        <div style={{
          display:'flex', gap:'8px', flexWrap:'wrap', alignItems:'center',
          marginTop: '5px',
        }}>
          {confLabel && (
            <span style={{
              fontSize: '10px', fontFamily: 'var(--font-display)', fontWeight: 700,
              letterSpacing: '0.12em', color: 'rgba(224,232,255,0.5)',
              textTransform: 'uppercase',
            }}>
              {confLabel} CONFIDENCE
            </span>
          )}
          {numLegs > 0 && (
            <span style={{
              fontSize: '10px', fontFamily: 'var(--font-display)', fontWeight: 700,
              letterSpacing: '0.1em', color: 'rgba(224,232,255,0.35)',
              textTransform: 'uppercase',
            }}>
              {numLegs}-LEG
            </span>
          )}
          {ticketType && (
            <span style={{
              fontSize: '10px', fontFamily: 'var(--font-display)', fontWeight: 700,
              letterSpacing: '0.1em', color: 'rgba(224,232,255,0.35)',
              textTransform: 'uppercase',
            }}>
              {ticketType}
            </span>
          )}
          {typeof americanOdds === 'number' && isFinite(americanOdds) && (
            <span style={{
              fontSize: '10px', fontFamily: 'var(--font-mono)',
              color: 'rgba(224,232,255,0.4)',
            }}>
              {americanOdds > 0 ? '+' : ''}{americanOdds}
            </span>
          )}
        </div>
        {/* Row 3: confidence reasons (array joined to string — never rendered as array) */}
        {confReasons && (
          <div style={{
            marginTop: '4px', fontSize: '9px', fontFamily: 'var(--font-mono)',
            color: 'rgba(224,232,255,0.28)', letterSpacing: '0.03em',
          }}>
            {confReasons}
          </div>
        )}
        {/* Row 4: plain-language verdict */}
        <div style={{
          marginTop: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)',
          color: verdict.color, letterSpacing: '0.02em',
        }}>
          {verdict.text}
        </div>
      </div>

      {/* ── SINGLES BETTER FLAG (only when explicitly true — not when null) ── */}
      {singlesBetter && (
        <div style={{
          fontSize: '11px', padding: '6px 10px', marginBottom: '8px',
          background: 'rgba(255,176,32,0.07)', border: '1px solid rgba(255,176,32,0.28)',
          borderRadius: '4px', color: '#ffb020',
          fontFamily: 'var(--font-display)', fontWeight: 700, letterSpacing: '0.06em',
          textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px',
        }}>
          <span>&#9888;</span>
          <span>SINGLES WOULD BE BETTER</span>
          {typeof honestRead.best_single_ev_pct === 'number' && isFinite(honestRead.best_single_ev_pct) && (
            <span style={{
              marginLeft: 'auto', fontSize: '10px',
              fontFamily: 'var(--font-mono)', fontWeight: 400,
            }}>
              best single +{honestRead.best_single_ev_pct.toFixed(1)}%
            </span>
          )}
        </div>
      )}

      {/* ── LEGS ── */}
      <div style={{display:'flex',flexDirection:'column',gap:'4px'}}>
        {legs.length === 0 && (
          <div style={{
            padding: '8px', fontSize: '11px',
            color: 'rgba(224,232,255,0.3)', fontFamily: 'var(--font-mono)',
          }}>—</div>
        )}
        {legs.map((leg, i) => {
          const legEv    = evByLegId[leg.leg_id];
          const hasLegEv = typeof legEv === 'number' && isFinite(legEv);
          const legEvStr = hasLegEv ? (legEv > 0 ? '+' : '') + legEv.toFixed(1) + '%' : null;
          const legEvColor = hasLegEv
            ? commGradeColor(legEv > 0 ? 'green' : legEv < 0 ? 'red' : 'amber')
            : null;
          const legTier = typeof leg.tier === 'string' && leg.tier ? leg.tier : 'EDGE';
          const tc = tierColor(legTier);
          const hrPct = typeof leg.model_prob === 'number' && isFinite(leg.model_prob)
            ? (leg.model_prob * 100).toFixed(1) + '%'
            : null;

          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap',
              padding: '7px 8px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '4px',
              borderLeft: `2px solid ${tc}44`,
            }}>
              {/* Tier badge */}
              <span style={{
                fontSize: '9px', fontFamily: 'var(--font-display)', fontWeight: 800,
                letterSpacing: '0.1em', color: tc,
                background: `${tc}12`, border: `1px solid ${tc}40`,
                borderRadius: '3px', padding: '2px 5px', flexShrink: 0,
              }}>
                {legTier}
              </span>
              {/* Clickable batter name */}
              <button
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'rgba(224,232,255,0.9)',
                  fontFamily: 'var(--font-display)', fontSize: '13px',
                  fontWeight: 700, letterSpacing: '0.02em', padding: 0,
                  textAlign: 'left', textDecoration: 'underline',
                  textDecorationStyle: 'dotted', textUnderlineOffset: '2px',
                  flexShrink: 0,
                }}
                onClick={() => onOpenCard && onOpenCard(commLegRow(leg))}
                title="View batter card"
              >
                {leg.player_name || '—'}
              </button>
              {/* Team */}
              {leg.team && (
                <span style={{
                  fontSize: '10px', color: 'rgba(224,232,255,0.38)',
                  fontFamily: 'var(--font-mono)', flexShrink: 0,
                }}>
                  {leg.team}
                </span>
              )}
              {/* HR% */}
              {hrPct && (
                <span style={{
                  fontSize: '11px', fontFamily: 'var(--font-mono)',
                  color: 'rgba(224,232,255,0.6)', fontWeight: 600,
                }}>
                  {hrPct} HR
                </span>
              )}
              {/* Per-leg EV (only when it's a real number) */}
              {hasLegEv && (
                <span style={{
                  fontSize: '10px', fontFamily: 'var(--font-mono)',
                  color: legEvColor, fontWeight: 700,
                }}>
                  {legEvStr} EV
                </span>
              )}
              {/* PICK button */}
              <button
                onClick={() => handlePickLeg(leg)}
                style={{
                  ...pillSt, marginLeft: 'auto', flexShrink: 0,
                  color: '#1aff66', borderColor: 'rgba(26,255,102,0.4)',
                  background: 'none',
                }}
                title="Add this player to your slip"
              >
                PICK
              </button>
            </div>
          );
        })}
      </div>

      {/* ── WAGER / PAYOUT ── */}
      <div style={{
        display:'flex', gap:'8px', alignItems:'center',
        marginTop: '10px', padding: '7px 8px',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '4px', flexWrap: 'wrap',
      }}>
        <span style={{
          fontSize: '9px', fontFamily: 'var(--font-display)', fontWeight: 800,
          letterSpacing: '0.12em', color: 'rgba(224,232,255,0.38)', textTransform: 'uppercase',
        }}>WAGER</span>
        {isOwner ? (
          <>
            <span style={{fontSize:'11px',color:'rgba(224,232,255,0.4)',fontFamily:'var(--font-mono)'}}>$</span>
            <input
              type="number"
              min="0"
              step="1"
              value={wager}
              onChange={e => { setWager(e.target.value); setSavedOk(false); }}
              onBlur={saveWager}
              placeholder="0"
              style={{
                width: '64px', background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(224,232,255,0.15)', borderRadius: '3px',
                color: 'rgba(224,232,255,0.85)', fontFamily: 'var(--font-mono)',
                fontSize: '12px', padding: '3px 6px', outline: 'none',
              }}
            />
            {saving && <span style={{fontSize:'9px',color:'rgba(224,232,255,0.35)',fontFamily:'var(--font-mono)'}}>saving…</span>}
            {savedOk && <span style={{fontSize:'9px',color:'#1aff66',fontFamily:'var(--font-mono)'}}>✓</span>}
          </>
        ) : (
          <span style={{fontSize:'12px',fontFamily:'var(--font-mono)',color:'rgba(224,232,255,0.55)'}}>
            {hasWager ? '$' + wagerNum.toFixed(2) : '—'}
          </span>
        )}
        {payoutStr && (
          <span style={{
            fontSize: '11px', fontFamily: 'var(--font-mono)',
            color: hasOdds ? '#1aff66' : 'rgba(224,232,255,0.3)',
          }}>
            {payoutStr}
          </span>
        )}
      </div>

      {/* ── ACTIONS: Copy Slip · Remove ── */}
      <div style={{display:'flex',gap:'6px',marginTop:'8px',alignItems:'center',flexWrap:'wrap'}}>
        {legs.length > 0 && (
          <button
            onClick={handleCopySlip}
            style={{
              ...pillSt, color: '#3b6fff', borderColor: 'rgba(59,111,255,0.4)',
              background: 'none',
            }}
            title="Load all players into your active slip builder"
          >
            COPY SLIP
          </button>
        )}
        {onRemove && !confirmRemove && (
          <button
            onClick={() => setConfirmRemove(true)}
            style={{
              ...pillSt, marginLeft: 'auto', color: '#ff3344',
              borderColor: 'rgba(255,51,68,0.35)', background: 'none',
            }}
            title="Remove this post from community"
          >
            REMOVE
          </button>
        )}
        {onRemove && confirmRemove && (
          <>
            <span style={{
              marginLeft: 'auto', fontSize: '9px',
              color: 'rgba(224,232,255,0.55)', fontFamily: 'var(--font-display)',
            }}>
              Remove post?
            </span>
            <button
              onClick={handleRemove} disabled={removing}
              style={{
                ...pillSt, color: '#ff3344', borderColor: '#ff3344',
                background: 'rgba(255,51,68,0.1)', cursor: removing ? 'wait' : 'pointer',
              }}
            >
              {removing ? '…' : 'CONFIRM'}
            </button>
            <button
              onClick={() => setConfirmRemove(false)}
              style={{
                ...pillSt, color: 'rgba(224,232,255,0.5)',
                borderColor: 'rgba(224,232,255,0.2)', background: 'none',
              }}
            >
              CANCEL
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* ---- UserSlipBox: one box per community member ---- */
function CommUserBox({ user, myAppNumber, onRemovePost, onOpenCard }) {
  const [showNum, setShowNum] = React.useState(false);
  const appNum  = user.app_number != null ? `#${String(user.app_number).padStart(4, '0')}` : '';
  const isOwner = myAppNumber != null && user.app_number === myAppNumber;

  return (
    <div className="comm-box">
      <div className="comm-box__header">
        <div
          className="comm-box__username"
          onMouseEnter={() => setShowNum(true)}
          onMouseLeave={() => setShowNum(false)}
        >
          <span className="comm-box__uname-text">{user.username || 'Anonymous'}</span>
          {showNum && appNum && <span className="comm-box__appnum">{appNum}</span>}
          {isOwner && (
            <span style={{
              fontSize: '9px', color: 'rgba(26,255,102,0.65)', marginLeft: '5px',
              fontFamily: 'var(--font-display)', letterSpacing: '0.08em',
            }}>
              YOU
            </span>
          )}
        </div>
        <span className="comm-box__count">{user.posts.length} slip{user.posts.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="comm-box__slips">
        {user.posts.map(post => (
          <CommSlipCard
            key={post.post_id}
            post={post}
            onRemove={isOwner ? (postId) => onRemovePost(user.app_number, postId) : null}
            onOpenCard={onOpenCard}
          />
        ))}
      </div>
    </div>
  );
}

/* ---- CommunityBoard: public board, no auth required ---- */
function CommunityBoard() {
  const [users, setUsers]           = React.useState([]);
  const [loading, setLoading]       = React.useState(true);
  const [error, setError]           = React.useState(null);
  const [myAppNumber, setMyAppNumber] = React.useState(null);
  const [cardRow, setCardRow]       = React.useState(null);

  React.useEffect(() => {
    fetch(`${COMM_API}/api/community/posts`)
      .then(r => {
        if (!r.ok) throw new Error('Failed to load');
        return r.json();
      })
      .then(d => { setUsers(d.users || []); setLoading(false); })
      .catch(() => { setError('Could not load community board.'); setLoading(false); });
  }, []);

  // Optional: fetch current user's app_number so Remove shows on their posts
  React.useEffect(() => {
    if (!window.__hrAuth?.authFetch) return;
    window.__hrAuth.authFetch(`${COMM_API}/api/profile`)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d?.profile?.app_number != null) setMyAppNumber(d.profile.app_number); })
      .catch(() => {});
  }, []);

  const handleRemovePost = (appNumber, postId) => {
    setUsers(prev =>
      prev
        .map(u =>
          u.app_number === appNumber
            ? { ...u, posts: u.posts.filter(p => p.post_id !== postId) }
            : u
        )
        .filter(u => u.posts.length > 0)
    );
  };

  if (loading) return (
    <div className="md-room" style={{display:'flex',alignItems:'center',justifyContent:'center',minHeight:200}}>
      <div style={{fontFamily:'var(--font-display)',fontWeight:700,fontSize:11,letterSpacing:'0.22em',color:'var(--fg-3)',textTransform:'uppercase'}}>Loading…</div>
    </div>
  );

  if (error) return (
    <div className="md-room" style={{display:'flex',alignItems:'center',justifyContent:'center',minHeight:200}}>
      <div style={{fontFamily:'var(--font-mono)',fontSize:12,color:'var(--red-500)'}}>{error}</div>
    </div>
  );

  return (
    <div className="md-room comm-board">
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

      <div className="comm-board__head">
        <div className="comm-board__title">BET SLIPS</div>
        <div className="comm-board__meta">
          {users.length === 0
            ? 'No slips posted yet'
            : `${users.length} member${users.length !== 1 ? 's' : ''} · hover username to reveal ID · submit a ticket to auto-post`}
        </div>
      </div>
      {users.length === 0 ? (
        <div className="comm-board__empty">
          <div className="comm-board__empty-icon">◎</div>
          <div className="comm-board__empty-lbl">The board is empty</div>
          <div className="comm-board__empty-sub">Submit a ticket from Ticket Command — it auto-posts to community.</div>
        </div>
      ) : (
        <div className="comm-board__grid">
          {users.map((u, i) => (
            <CommUserBox
              key={u.app_number != null ? u.app_number : i}
              user={u}
              myAppNumber={myAppNumber}
              onRemovePost={handleRemovePost}
              onOpenCard={(row) => setCardRow(row)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ---- CommunityProfile: edit username, view app_number (signed-in only) ---- */
function CommunityProfile() {
  const [session, setSession]     = React.useState(null);
  const [profile, setProfile]     = React.useState(null);
  const [loading, setLoading]     = React.useState(true);
  const [username, setUsername]   = React.useState('');
  const [saving, setSaving]       = React.useState(false);
  const [saveError, setSaveError] = React.useState('');
  const [saveOk, setSaveOk]       = React.useState(false);

  React.useEffect(() => {
    const sb = window.__hrAuth?.sb;
    if (!sb) { setLoading(false); return; }
    sb.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: { subscription } } = sb.auth.onAuthStateChange((_e, s) => setSession(s));
    return () => subscription.unsubscribe();
  }, []);

  React.useEffect(() => {
    if (!session) { setLoading(false); return; }
    setLoading(true);
    window.__hrAuth.authFetch(`${COMM_API}/api/profile`)
      .then(r => r.json())
      .then(d => {
        setProfile(d.profile || null);
        setUsername(d.profile?.username || '');
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [session]);

  const handleSave = async () => {
    setSaveError(''); setSaveOk(false); setSaving(true);
    const res = await window.__hrAuth.authFetch(`${COMM_API}/api/profile/username`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    }).catch(() => null);
    setSaving(false);
    if (!res || res._noAuth) { setSaveError('Sign in to edit your profile.'); return; }
    if (res.status === 409)  { setSaveError('That username is already taken.'); return; }
    if (!res.ok)             { setSaveError('Error saving. Try again.'); return; }
    const d = await res.json().catch(() => ({}));
    if (d.profile) { setProfile(d.profile); setUsername(d.profile.username || username); }
    setSaveOk(true);
    setTimeout(() => setSaveOk(false), 2500);
  };

  const appNumLabel = profile?.app_number != null ? `#${String(profile.app_number).padStart(4, '0')}` : '';

  if (!session) return (
    <div className="md-room comm-profile">
      <div className="comm-profile__empty">Sign in to view and edit your profile.</div>
    </div>
  );

  if (loading) return (
    <div className="md-room comm-profile" style={{display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div style={{fontFamily:'var(--font-display)',fontWeight:700,fontSize:11,letterSpacing:'0.22em',color:'var(--fg-3)',textTransform:'uppercase'}}>Loading…</div>
    </div>
  );

  return (
    <div className="md-room comm-profile">
      <div className="comm-profile__head">
        <div className="comm-profile__title">YOUR PROFILE</div>
        {appNumLabel && (
          <div className="comm-profile__idrow">
            <span className="comm-profile__id-lbl">Permanent ID</span>
            <span className="comm-profile__id">{appNumLabel}</span>
          </div>
        )}
      </div>
      <div className="comm-profile__form">
        <div className="comm-profile__fieldlbl">Display Name</div>
        <div className="comm-profile__inputrow">
          <input
            className="comm-profile__input"
            type="text"
            value={username}
            onChange={e => { setUsername(e.target.value); setSaveOk(false); setSaveError(''); }}
            maxLength={30}
            placeholder="3–30 chars: letters, numbers, _ or −"
            onKeyDown={e => e.key === 'Enter' && handleSave()}
          />
          <button
            className="comm-profile__savebtn"
            onClick={handleSave}
            disabled={saving || username.trim().length < 3}
          >
            {saving ? '…' : saveOk ? '✓ Saved' : 'Save'}
          </button>
        </div>
        {saveError && <div className="comm-profile__err">{saveError}</div>}
        {saveOk    && <div className="comm-profile__ok">Display name updated!</div>}
        <div className="comm-profile__hint">3–30 characters · letters, numbers, spaces, _ or −</div>
        {appNumLabel && (
          <div className="comm-profile__hint" style={{marginTop:4}}>
            Your permanent ID ({appNumLabel}) never changes, even after renaming.
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { CommunityBoard, CommunityProfile });
