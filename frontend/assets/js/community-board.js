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
  const [wager, setWager]                 = React.useState('');

  const slip       = post.slip || {};
  const legs       = slip.legs || [];
  const analysis   = slip.analysis || {};
  const grade      = analysis.grade || {};
  const combined   = analysis.combined || {};
  const honestRead = analysis.honest_read || {};
  const analyzed   = analysis.legs || [];
  const dateStr    = commFmtDate(post.posted_at);

  const hasGrade = grade.status === 'complete';
  const gradeColor = commGradeColor(grade.color);
  const evPct = combined.ev_pct;
  const evStr = evPct != null ? (evPct > 0 ? '+' : '') + evPct.toFixed(1) + '% EV' : null;

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

  // Wager + payout computation — guard every numeric op against null/NaN
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

  // Index analysis legs by leg_id for per-leg EV display
  const evByLegId = {};
  analyzed.forEach(al => { if (al.leg_id) evByLegId[al.leg_id] = al.ev_pct; });

  const pillSt = {
    fontSize: '9px', fontFamily: 'var(--font-display)', fontWeight: 800,
    letterSpacing: '0.1em', textTransform: 'uppercase', borderRadius: '3px',
    padding: '2px 6px', border: '1px solid', cursor: 'pointer',
  };

  return (
    <div className="comm-slip">
      {/* Meta row: date · type · odds · grade badge */}
      <div className="comm-slip__meta" style={{flexWrap:'wrap',gap:'4px'}}>
        {dateStr && <span className="comm-slip__date">{dateStr}</span>}
        {slip.ticket_type && <span className="comm-slip__type">{slip.ticket_type.replace(/_/g, ' ')}</span>}
        {slip.odds_american != null && (
          <span className="comm-slip__odds">{slip.odds_american > 0 ? '+' : ''}{slip.odds_american}</span>
        )}
        {hasGrade && (
          <span style={{
            marginLeft: 'auto', fontSize: '10px',
            fontFamily: 'var(--font-display)', fontWeight: 800, letterSpacing: '0.1em',
            color: gradeColor, border: `1px solid ${gradeColor}55`,
            borderRadius: '3px', padding: '2px 6px',
          }}>
            {grade.letter} · {evStr || grade.label}
          </span>
        )}
      </div>

      {/* Honest singles-better note */}
      {honestRead.singles_would_be_better && (
        <div style={{
          fontSize: '10px', padding: '4px 8px', margin: '4px 0',
          background: 'rgba(255,176,32,0.07)', borderLeft: '2px solid #ffb020',
          color: '#ffb020', fontFamily: 'var(--font-display)', letterSpacing: '0.04em',
        }}>
          Singles would be better — parlay EV {evStr}, best single +{(honestRead.best_single_ev_pct || 0).toFixed(1)}%
        </div>
      )}

      {/* Legs */}
      <div className="comm-slip__legs">
        {legs.length === 0 && <div className="comm-slip__leg comm-slip__leg--empty">—</div>}
        {legs.map((leg, i) => {
          const legEv = evByLegId[leg.leg_id];
          const hasLegEv = legEv != null;
          const legEvStr = hasLegEv ? (legEv > 0 ? '+' : '') + legEv.toFixed(1) + '%' : null;
          const legEvColor = hasLegEv
            ? commGradeColor(legEv > 0 ? 'green' : legEv < 0 ? 'red' : 'amber')
            : null;
          return (
            <div key={i} className="comm-slip__leg" style={{display:'flex',alignItems:'center',gap:'4px',flexWrap:'wrap'}}>
              <span className="comm-slip__leg-dot" />
              {/* Clickable batter name → opens card */}
              <button
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'inherit', fontFamily: 'inherit', fontSize: 'inherit',
                  fontWeight: 'inherit', letterSpacing: 'inherit', padding: 0,
                  textAlign: 'left', textDecoration: 'underline', textDecorationStyle: 'dotted',
                  textUnderlineOffset: '2px',
                }}
                onClick={() => onOpenCard && onOpenCard(commLegRow(leg))}
                title="View batter card"
              >
                {leg.player_name || '—'}
              </button>
              {leg.team && <span className="comm-slip__leg-team">{leg.team}</span>}
              {leg.tier && (
                <span className={`comm-slip__leg-tier comm-slip__leg-tier--${(leg.tier || '').toLowerCase()}`}>
                  {leg.tier}
                </span>
              )}
              {leg.model_prob != null && (
                <span className="comm-slip__leg-prob">{(Number(leg.model_prob) * 100).toFixed(1)}%</span>
              )}
              {hasLegEv && (
                <span style={{
                  fontSize: '9px', fontFamily: 'var(--font-mono)',
                  color: legEvColor, marginLeft: '1px',
                }}>
                  {legEvStr}
                </span>
              )}
              {/* Per-batter Pick button */}
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

      {/* Wager input + payout */}
      <div style={{display:'flex',gap:'6px',alignItems:'center',marginTop:'7px',flexWrap:'wrap'}}>
        <span style={{
          fontSize: '9px', fontFamily: 'var(--font-display)', fontWeight: 800,
          letterSpacing: '0.1em', color: 'rgba(224,232,255,0.4)', textTransform: 'uppercase',
        }}>WAGER</span>
        <span style={{fontSize:'10px',color:'rgba(224,232,255,0.45)',fontFamily:'var(--font-mono)'}}>$</span>
        <input
          type="number"
          min="0"
          step="1"
          value={wager}
          onChange={e => setWager(e.target.value)}
          placeholder="0"
          style={{
            width: '58px', background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(224,232,255,0.15)', borderRadius: '3px',
            color: 'rgba(224,232,255,0.85)', fontFamily: 'var(--font-mono)',
            fontSize: '11px', padding: '2px 5px', outline: 'none',
          }}
        />
        {payoutStr && (
          <span style={{
            fontSize: '10px', fontFamily: 'var(--font-mono)',
            color: hasOdds ? '#1aff66' : 'rgba(224,232,255,0.3)',
          }}>
            {payoutStr}
          </span>
        )}
      </div>

      {/* Slip-level actions: Copy Slip · Remove */}
      <div style={{display:'flex',gap:'6px',marginTop:'7px',alignItems:'center',flexWrap:'wrap'}}>
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
