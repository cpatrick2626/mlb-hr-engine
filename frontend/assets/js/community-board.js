/* HR Engine — Community Board + Profile.
   CommunityBoard: open read (no auth). CommunityProfile: signed-in only. */

const COMM_API = 'https://mlb-hr-api.fly.dev';

function commFmtDate(iso) {
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); }
  catch (_) { return ''; }
}

/* ---- SlipCard: one posted slip ---- */
function CommSlipCard({ post }) {
  const slip = post.slip || {};
  const legs = slip.legs || [];
  const dateStr = commFmtDate(post.posted_at);

  return (
    <div className="comm-slip">
      <div className="comm-slip__meta">
        {dateStr && <span className="comm-slip__date">{dateStr}</span>}
        {slip.ticket_type && <span className="comm-slip__type">{slip.ticket_type.replace(/_/g, ' ')}</span>}
        {slip.odds_american != null && (
          <span className="comm-slip__odds">{slip.odds_american > 0 ? '+' : ''}{slip.odds_american}</span>
        )}
      </div>
      <div className="comm-slip__legs">
        {legs.length === 0 && <div className="comm-slip__leg comm-slip__leg--empty">—</div>}
        {legs.map((leg, i) => (
          <div key={i} className="comm-slip__leg">
            <span className="comm-slip__leg-dot" />
            <span className="comm-slip__leg-name">{leg.player_name || '—'}</span>
            {leg.team && <span className="comm-slip__leg-team">{leg.team}</span>}
            {leg.tier && (
              <span className={`comm-slip__leg-tier comm-slip__leg-tier--${(leg.tier || '').toLowerCase()}`}>
                {leg.tier}
              </span>
            )}
            {leg.model_prob != null && (
              <span className="comm-slip__leg-prob">{(Number(leg.model_prob) * 100).toFixed(1)}%</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---- UserSlipBox: one box per community member ---- */
function CommUserBox({ user }) {
  const [showNum, setShowNum] = React.useState(false);
  const appNum = user.app_number != null ? `#${String(user.app_number).padStart(4, '0')}` : '';

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
        </div>
        <span className="comm-box__count">{user.posts.length} slip{user.posts.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="comm-box__slips">
        {user.posts.map(post => <CommSlipCard key={post.post_id} post={post} />)}
      </div>
    </div>
  );
}

/* ---- CommunityBoard: public board, no auth required ---- */
function CommunityBoard() {
  const [users, setUsers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    fetch(`${COMM_API}/api/community/posts`)
      .then(r => {
        if (!r.ok) throw new Error('Failed to load');
        return r.json();
      })
      .then(d => { setUsers(d.users || []); setLoading(false); })
      .catch(() => { setError('Could not load community board.'); setLoading(false); });
  }, []);

  if (loading) return (
    <div className="md-room" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 11, letterSpacing: '0.22em', color: 'var(--fg-3)', textTransform: 'uppercase' }}>Loading…</div>
    </div>
  );

  if (error) return (
    <div className="md-room" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--red-500)' }}>{error}</div>
    </div>
  );

  return (
    <div className="md-room comm-board">
      <div className="comm-board__head">
        <div className="comm-board__title">BET SLIPS</div>
        <div className="comm-board__meta">
          {users.length === 0
            ? 'No slips posted yet'
            : `${users.length} member${users.length !== 1 ? 's' : ''} · hover a username to reveal ID · submit a ticket to post`}
        </div>
      </div>
      {users.length === 0 ? (
        <div className="comm-board__empty">
          <div className="comm-board__empty-icon">◎</div>
          <div className="comm-board__empty-lbl">The board is empty</div>
          <div className="comm-board__empty-sub">Submit a ticket, then post it to community from the Ticket Command Slip.</div>
        </div>
      ) : (
        <div className="comm-board__grid">
          {users.map((u, i) => (
            <CommUserBox key={u.app_number != null ? u.app_number : i} user={u} />
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
    if (res.status === 409) { setSaveError('That username is already taken.'); return; }
    if (!res.ok) { setSaveError('Error saving. Try again.'); return; }
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
    <div className="md-room comm-profile" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 11, letterSpacing: '0.22em', color: 'var(--fg-3)', textTransform: 'uppercase' }}>Loading…</div>
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
        {saveOk && <div className="comm-profile__ok">Display name updated!</div>}
        <div className="comm-profile__hint">3–30 characters · letters, numbers, spaces, _ or −</div>
        {appNumLabel && (
          <div className="comm-profile__hint" style={{ marginTop: 4 }}>
            Your permanent ID ({appNumLabel}) never changes, even after renaming.
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { CommunityBoard, CommunityProfile });
