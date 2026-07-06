(() => {
  const SUPABASE_URL = 'https://cuhkisxjaknusppgladb.supabase.co';
  const SUPABASE_ANON_KEY =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1aGtpc3hqYWtudXNwcGdsYWRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAyODY5ODgsImV4cCI6MjA5NTg2Mjk4OH0.F4sPxTaSCmtOWhFlKC5TvjevyHlo4gj8XEyXrxAW8WE';

  const API = 'https://mlb-hr-api.fly.dev';

  const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  window.__hrAuth = {
    sb,
    getToken: async () => (await sb.auth.getSession()).data.session?.access_token,
    // Token-aware fetch — attach Bearer header if logged in, else return {ok:false,_noAuth:true}
    authFetch: async (url, opts = {}) => {
      const token = await window.__hrAuth.getToken();
      if (!token) return { ok: false, _noAuth: true };
      return fetch(url, {
        ...opts,
        headers: { ...(opts.headers || {}), 'Authorization': `Bearer ${token}` },
      });
    },
  };

  const S = {
    widget: {
      position: 'relative',
      fontFamily: 'var(--font-display, "Barlow Condensed", sans-serif)',
    },
    btnSignIn: {
      background: 'linear-gradient(160deg, rgba(26,255,102,0.05), rgba(180,220,200,0.02))',
      border: '1px solid rgba(26,255,102,0.40)',
      color: 'var(--fg-1, #f1f5f3)',
      fontFamily: 'inherit',
      fontWeight: 800,
      fontSize: '12px',
      letterSpacing: '0.20em',
      textTransform: 'uppercase',
      padding: '10px 32px',
      borderRadius: '5px',
      cursor: 'pointer',
      transition: 'border-color .2s, color .2s, box-shadow .2s',
      boxShadow: '0 0 0 1px rgba(26,255,102,0.12), 0 0 24px rgba(26,255,102,0.07)',
      whiteSpace: 'nowrap',
    },
    btnSigned: {
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      background: 'transparent',
      border: '1px solid rgba(26,255,102,0.22)',
      color: 'var(--green-500, #1aff66)',
      fontFamily: 'inherit',
      fontWeight: 700,
      fontSize: '10px',
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      padding: '6px 12px',
      borderRadius: '4px',
      cursor: 'pointer',
      maxWidth: '200px',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
    },
    dot: {
      display: 'inline-block',
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      background: 'var(--green-500, #1aff66)',
      boxShadow: '0 0 6px var(--green-500, #1aff66)',
      flexShrink: 0,
    },
    dropdown: {
      position: 'absolute',
      top: 'calc(100% + 6px)',
      right: 0,
      background: 'var(--bg-raised, #0e1519)',
      border: '1px solid rgba(180,220,200,0.16)',
      borderRadius: '6px',
      padding: '10px 12px',
      minWidth: '200px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      zIndex: 500,
    },
    dropEmail: {
      fontSize: '11px',
      color: 'var(--fg-3, #8a9691)',
      letterSpacing: '0.04em',
      marginBottom: '10px',
      wordBreak: 'break-all',
    },
    modal: {
      position: 'absolute',
      top: 'calc(100% + 6px)',
      right: 0,
      background: 'var(--bg-raised, #0e1519)',
      border: '1px solid rgba(180,220,200,0.16)',
      borderRadius: '6px',
      padding: '16px',
      width: '260px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      zIndex: 500,
    },
    modalTitle: {
      fontWeight: 800,
      fontSize: '11px',
      letterSpacing: '0.18em',
      textTransform: 'uppercase',
      color: 'var(--fg-1, #f1f5f3)',
      marginBottom: '14px',
    },
    input: {
      display: 'block',
      width: '100%',
      background: 'var(--bg-elevated, #131b21)',
      border: '1px solid rgba(180,220,200,0.16)',
      borderRadius: '4px',
      color: 'var(--fg-1, #f1f5f3)',
      fontFamily: 'var(--font-mono, monospace)',
      fontSize: '12px',
      padding: '7px 10px',
      marginBottom: '8px',
      outline: 'none',
      boxSizing: 'border-box',
    },
    error: {
      fontSize: '11px',
      color: 'var(--red-500, #ff3344)',
      letterSpacing: '0.04em',
      marginBottom: '8px',
      lineHeight: 1.4,
    },
    btnRow: {
      display: 'flex',
      gap: '8px',
      marginTop: '4px',
    },
    btnPrimary: {
      flex: 1,
      background: 'var(--green-500, #1aff66)',
      border: 'none',
      borderRadius: '4px',
      color: '#04140a',
      fontFamily: 'var(--font-display, inherit)',
      fontWeight: 800,
      fontSize: '10px',
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      padding: '7px 0',
      cursor: 'pointer',
    },
    btnSecondary: {
      flex: 1,
      background: 'transparent',
      border: '1px solid rgba(180,220,200,0.22)',
      borderRadius: '4px',
      color: 'var(--fg-2, #b8c2c0)',
      fontFamily: 'var(--font-display, inherit)',
      fontWeight: 700,
      fontSize: '10px',
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      padding: '7px 0',
      cursor: 'pointer',
    },
    btnSignOut: {
      width: '100%',
      background: 'transparent',
      border: '1px solid rgba(255,51,68,0.22)',
      borderRadius: '4px',
      color: 'var(--red-500, #ff3344)',
      fontFamily: 'var(--font-display, inherit)',
      fontWeight: 700,
      fontSize: '10px',
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      padding: '6px 0',
      cursor: 'pointer',
    },
    confirm: {
      textAlign: 'center',
      padding: '4px 0',
    },
    confirmIcon: {
      fontSize: '28px',
      marginBottom: '10px',
    },
    confirmTitle: {
      fontWeight: 800,
      fontSize: '12px',
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      color: 'var(--fg-1, #f1f5f3)',
      marginBottom: '8px',
    },
    confirmText: {
      fontSize: '11px',
      color: 'var(--fg-3, #8a9691)',
      lineHeight: 1.5,
      marginBottom: '14px',
    },
    linkBtn: {
      background: 'none',
      border: 'none',
      color: 'var(--fg-3, #8a9691)',
      fontFamily: 'var(--font-display, inherit)',
      fontSize: '10px',
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
      cursor: 'pointer',
      padding: 0,
    },
    btnNeedsBeta: {
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      background: 'transparent',
      border: '1px solid rgba(255,170,0,0.35)',
      color: '#ffaa00',
      fontFamily: 'var(--font-display, "Barlow Condensed", sans-serif)',
      fontWeight: 700,
      fontSize: '10px',
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      padding: '6px 12px',
      borderRadius: '4px',
      cursor: 'pointer',
      whiteSpace: 'nowrap',
    },
    dotAmber: {
      display: 'inline-block',
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      background: '#ffaa00',
      boxShadow: '0 0 6px rgba(255,170,0,0.7)',
      flexShrink: 0,
    },
    successMsg: {
      fontSize: '12px',
      color: 'var(--green-500, #1aff66)',
      letterSpacing: '0.08em',
      textAlign: 'center',
      padding: '12px 0 4px',
    },
  };

  function AuthWidget() {
    const [open, setOpen] = React.useState(false);
    const [session, setSession] = React.useState(null);
    const [mode, setMode] = React.useState('idle'); // 'idle' | 'pending_confirm'
    const [email, setEmail] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [error, setError] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [isBeta, setIsBeta] = React.useState(null); // null=checking|unknown, true=beta, false=needs-redeem
    const [redeemCode, setRedeemCode] = React.useState('');
    const [redeemError, setRedeemError] = React.useState('');
    const [redeemLoading, setRedeemLoading] = React.useState(false);
    const [redeemSuccess, setRedeemSuccess] = React.useState(false);

    React.useEffect(() => {
      sb.auth.getSession().then(({ data }) => setSession(data.session));
      const { data: { subscription } } = sb.auth.onAuthStateChange((_event, sess) => {
        setSession(sess);
        if (sess) { setMode('idle'); setOpen(false); }
      });
      return () => subscription.unsubscribe();
    }, []);

    // Close modal on outside click
    React.useEffect(() => {
      if (!open) return;
      const handler = () => setOpen(false);
      document.addEventListener('click', handler);
      return () => document.removeEventListener('click', handler);
    }, [open]);

    // Check beta status whenever session changes
    React.useEffect(() => {
      if (!session) { setIsBeta(null); return; }
      let cancelled = false;
      (async () => {
        try {
          const res = await window.__hrAuth.authFetch(`${API}/api/runs`);
          if (cancelled) return;
          if (res._noAuth) { setIsBeta(null); return; }
          setIsBeta(res.status === 200);
        } catch (_) {
          if (!cancelled) setIsBeta(true); // network error: don't block
        }
      })();
      return () => { cancelled = true; };
    }, [session]);

    const handleSignIn = async () => {
      setError(''); setLoading(true);
      const { error: err } = await sb.auth.signInWithPassword({ email, password });
      setLoading(false);
      if (err) setError(err.message);
    };

    const handleSignUp = async () => {
      setError(''); setLoading(true);
      const { error: err } = await sb.auth.signUp({ email, password });
      setLoading(false);
      if (err) { setError(err.message); } else { setMode('pending_confirm'); }
    };

    const handleSignOut = async () => {
      await sb.auth.signOut();
      setOpen(false);
    };

    const handleRedeem = async () => {
      if (!redeemCode.trim()) { setRedeemError('Enter an invite code.'); return; }
      setRedeemError(''); setRedeemLoading(true);
      const res = await window.__hrAuth.authFetch(`${API}/api/invite/redeem`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: redeemCode.trim().toUpperCase() }),
      });
      setRedeemLoading(false);
      if (!res || res._noAuth) { setRedeemError('Not signed in.'); return; }
      if (res.ok) {
        setRedeemSuccess(true);
        setIsBeta(true);
        setTimeout(() => { setOpen(false); setRedeemSuccess(false); setRedeemCode(''); }, 1800);
      } else {
        const data = await res.json().catch(() => ({}));
        setRedeemError(data.detail || 'Invalid or already-used invite code.');
      }
    };

    if (session && isBeta === false) {
      return (
        <div style={S.widget} onClick={e => e.stopPropagation()}>
          <button style={S.btnNeedsBeta} onClick={() => setOpen(o => !o)}>
            <span style={S.dotAmber} />
            Invite Required
          </button>
          {open && (
            <div style={S.modal}>
              <div style={S.modalTitle}>Beta Access</div>
              {redeemSuccess ? (
                <div style={S.successMsg}>✓ Access unlocked!</div>
              ) : (
                <>
                  <div style={{...S.dropEmail, marginBottom: '12px'}}>{session.user.email}</div>
                  <input
                    style={S.input}
                    type="text"
                    placeholder="INVITE CODE"
                    value={redeemCode}
                    onChange={e => setRedeemCode(e.target.value.toUpperCase())}
                    onKeyDown={e => e.key === 'Enter' && handleRedeem()}
                    autoCapitalize="characters"
                  />
                  {redeemError && <div style={S.error}>{redeemError}</div>}
                  <div style={S.btnRow}>
                    <button style={S.btnPrimary} onClick={handleRedeem} disabled={redeemLoading}>
                      {redeemLoading ? '…' : 'Redeem'}
                    </button>
                    <button style={S.btnSecondary} onClick={handleSignOut}>
                      Sign Out
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      );
    }

    if (session) {
      return (
        <div style={S.widget} onClick={e => e.stopPropagation()}>
          <button style={S.btnSigned} onClick={() => setOpen(o => !o)}>
            <span style={S.dot} />
            {session.user.email}
          </button>
          {open && (
            <div style={S.dropdown}>
              <div style={S.dropEmail}>{session.user.email}</div>
              <button style={S.btnSignOut} onClick={handleSignOut}>Sign Out</button>
            </div>
          )}
        </div>
      );
    }

    return (
      <div style={S.widget} onClick={e => e.stopPropagation()}>
        <button
          style={S.btnSignIn}
          onClick={() => { setOpen(o => !o); setError(''); setMode('idle'); }}
        >
          Sign In
        </button>
        {open && (
          <div style={S.modal}>
            {mode === 'pending_confirm' ? (
              <div style={S.confirm}>
                <div style={S.confirmIcon}>✉</div>
                <div style={S.confirmTitle}>Check your email</div>
                <div style={S.confirmText}>
                  Confirm your account via the link we sent, then sign in below.
                </div>
                <button style={S.linkBtn} onClick={() => setMode('idle')}>← Back to sign in</button>
              </div>
            ) : (
              <>
                <div style={S.modalTitle}>HR Engine Access</div>
                <input
                  style={S.input}
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoComplete="email"
                />
                <input
                  style={S.input}
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                  onKeyDown={e => e.key === 'Enter' && handleSignIn()}
                />
                {error && <div style={S.error}>{error}</div>}
                <div style={S.btnRow}>
                  <button style={S.btnPrimary} onClick={handleSignIn} disabled={loading}>
                    {loading ? '…' : 'Sign In'}
                  </button>
                  <button style={S.btnSecondary} onClick={handleSignUp} disabled={loading}>
                    Sign Up
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  let mounted = false;
  function mountAuth() {
    if (mounted) return;
    const mountEl = document.getElementById('auth-root');
    if (!mountEl) return;
    mounted = true;
    ReactDOM.createRoot(mountEl).render(<AuthWidget />);
  }

  // Mount immediately if #auth-root already exists (static HTML path),
  // otherwise wait for it to appear (React-rendered topbar path).
  mountAuth();
  if (!mounted) {
    const obs = new MutationObserver(() => {
      mountAuth();
      if (mounted) obs.disconnect();
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }
})();
