/* HR Engine — Slip History (private, JWT-gated).
   Source: GET /api/my-tickets only. No other fetch, no backend change.
   Groups tickets by date descending. Derives per-leg badge + slip outcome. */

const SH_API = 'https://mlb-hr-api.fly.dev';

function shFmtDate(dateStr) {
  if (!dateStr || dateStr === 'unknown') return '—';
  try {
    return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    });
  } catch (_) { return dateStr; }
}

/* Derive per-leg badge from settlement_status + hr_result. Null-guarded. */
function shLegBadge(leg) {
  if (!leg) return 'PENDING';
  const status = leg.settlement_status || 'pending';
  if (status === 'void') return 'VOID';
  if (status === 'settled') {
    const r = leg.hr_result;
    if (r === 1) return 'HIT';
    if (r === 0) return 'MISS';
    return 'PENDING'; // settled but hr_result absent — guard
  }
  return 'PENDING';
}

/* Derive whole-slip outcome. VOID legs are neutral. */
function shSlipOutcome(legs) {
  if (!Array.isArray(legs) || legs.length === 0) return 'PENDING';
  const badges = legs.map(shLegBadge);
  const nonVoid = badges.filter(b => b !== 'VOID');
  if (nonVoid.length === 0) return 'VOID';
  if (nonVoid.includes('PENDING')) return 'PENDING';
  if (nonVoid.includes('MISS')) return 'LOSS';
  return 'WIN';
}

/* Group tickets by date (ticket.date), sorted descending. */
function shGroupByDate(tickets) {
  const map = {};
  for (const t of (tickets || [])) {
    const d = t.date || 'unknown';
    if (!map[d]) map[d] = [];
    map[d].push(t);
  }
  return Object.keys(map)
    .sort((a, b) => b.localeCompare(a))
    .map(date => ({ date, tickets: map[date] }));
}

function shBadgeColor(badge) {
  if (badge === 'HIT')     return '#1aff66';
  if (badge === 'MISS')    return '#ff3344';
  if (badge === 'PENDING') return '#ffb020';
  return '#8a9691';
}

function shOutcomeColor(outcome) {
  if (outcome === 'WIN')     return '#1aff66';
  if (outcome === 'LOSS')    return '#ff3344';
  if (outcome === 'PENDING') return '#ffb020';
  return '#8a9691';
}

function ShBadge({ label }) {
  const c = shBadgeColor(label);
  return (
    <span style={{
      fontSize: '9px', fontFamily: 'var(--font-display)', fontWeight: 800,
      letterSpacing: '0.12em', textTransform: 'uppercase',
      color: c, background: `${c}18`, border: `1px solid ${c}55`,
      borderRadius: '3px', padding: '2px 6px', flexShrink: 0,
    }}>
      {label}
    </span>
  );
}

function ShSlipCard({ ticket }) {
  const legs = Array.isArray(ticket.legs) ? ticket.legs : [];
  const outcome = shSlipOutcome(legs);
  const outcomeColor = shOutcomeColor(outcome);
  const ticketType = typeof ticket.ticket_type === 'string'
    ? ticket.ticket_type.replace(/_/g, ' ')
    : '';

  return (
    <div style={{
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid rgba(180,220,200,0.08)',
      borderLeft: `3px solid ${outcomeColor}35`,
      borderRadius: '5px',
      padding: '10px 12px',
      display: 'flex', flexDirection: 'column', gap: '6px',
    }}>
      {/* Slip header: outcome + meta */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <span style={{
          fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '15px',
          letterSpacing: '0.06em', color: outcomeColor,
        }}>
          {outcome}
        </span>
        {ticketType && (
          <span style={{
            fontSize: '10px', fontFamily: 'var(--font-display)', fontWeight: 700,
            letterSpacing: '0.1em', textTransform: 'uppercase',
            color: 'rgba(224,232,255,0.45)',
          }}>
            {ticketType}
          </span>
        )}
        {legs.length > 0 && (
          <span style={{
            fontSize: '10px', fontFamily: 'var(--font-display)', fontWeight: 700,
            letterSpacing: '0.1em', textTransform: 'uppercase',
            color: 'rgba(224,232,255,0.35)',
          }}>
            {legs.length}-LEG
          </span>
        )}
      </div>

      {/* Legs */}
      {legs.length === 0 ? (
        <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'rgba(224,232,255,0.3)' }}>
          No legs recorded
        </div>
      ) : legs.map((leg, i) => {
        const badge = shLegBadge(leg);
        const playerName = (leg && leg.player_name) ? leg.player_name : '—';
        const team = (leg && leg.team) ? leg.team : '';
        const pitcher = (leg && leg.pitcher) ? leg.pitcher : '';

        return (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap',
            padding: '5px 7px',
            background: 'rgba(255,255,255,0.025)',
            borderRadius: '3px',
          }}>
            <ShBadge label={badge} />
            <span style={{
              fontFamily: 'var(--font-display)', fontSize: '13px', fontWeight: 700,
              color: 'rgba(224,232,255,0.88)', letterSpacing: '0.02em',
            }}>
              {playerName}
            </span>
            {team && (
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'rgba(224,232,255,0.38)' }}>
                {team}
              </span>
            )}
            {pitcher && (
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'rgba(224,232,255,0.28)' }}>
                vs {pitcher}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ShDateRow({ date, tickets }) {
  const [open, setOpen] = React.useState(false);
  const outcomes = tickets.map(t => shSlipOutcome(Array.isArray(t.legs) ? t.legs : []));
  const wins    = outcomes.filter(o => o === 'WIN').length;
  const losses  = outcomes.filter(o => o === 'LOSS').length;
  const pending = outcomes.filter(o => o === 'PENDING').length;
  const voids   = outcomes.filter(o => o === 'VOID').length;

  const tally = [];
  if (wins > 0)    tally.push({ label: wins + 'W',       color: '#1aff66' });
  if (losses > 0)  tally.push({ label: losses + 'L',     color: '#ff3344' });
  if (pending > 0) tally.push({ label: pending + ' PEND', color: '#ffb020' });
  if (voids > 0)   tally.push({ label: voids + 'V',      color: '#8a9691' });

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          background: open ? 'rgba(155,89,245,0.07)' : 'var(--bg-raised, #0e1519)',
          border: '1px solid rgba(180,220,200,0.12)',
          borderRadius: open ? '6px 6px 0 0' : '6px',
          padding: '10px 14px',
          cursor: 'pointer', textAlign: 'left', width: '100%',
          transition: 'background 0.15s ease',
        }}
      >
        <span style={{
          fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '14px',
          letterSpacing: '0.06em', textTransform: 'uppercase',
          color: 'var(--fg-1, #f1f5f3)', flex: 1,
        }}>
          {shFmtDate(date)}
        </span>
        <span style={{
          fontSize: '11px', fontFamily: 'var(--font-display)', fontWeight: 700,
          letterSpacing: '0.08em', textTransform: 'uppercase',
          color: 'rgba(224,232,255,0.4)',
        }}>
          {tickets.length} slip{tickets.length !== 1 ? 's' : ''}
        </span>
        {tally.map((t, i) => (
          <span key={i} style={{
            fontSize: '10px', fontFamily: 'var(--font-display)', fontWeight: 700,
            letterSpacing: '0.1em', color: t.color,
          }}>
            {t.label}
          </span>
        ))}
        <span style={{ fontSize: '11px', color: 'rgba(224,232,255,0.3)', marginLeft: '2px' }}>
          {open ? '▾' : '▸'}
        </span>
      </button>

      {open && (
        <div style={{
          border: '1px solid rgba(180,220,200,0.12)',
          borderTop: 'none',
          borderRadius: '0 0 6px 6px',
          padding: '10px 12px',
          display: 'flex', flexDirection: 'column', gap: '8px',
          background: 'var(--bg-base, #0a1014)',
        }}>
          {tickets.map((t, i) => (
            <ShSlipCard key={t.ticket_id || i} ticket={t} />
          ))}
        </div>
      )}
    </div>
  );
}

function SlipHistory() {
  // null = auth loading, false = not signed in, object = signed in
  const [session, setSession] = React.useState(null);
  // null = tickets loading, array = loaded (possibly empty)
  const [tickets, setTickets] = React.useState(null);
  const [error, setError]     = React.useState(null); // 'noauth' | 'fetch' | null

  React.useEffect(() => {
    const sb = window.__hrAuth?.sb;
    if (!sb) { setSession(false); return; }
    sb.auth.getSession().then(({ data }) => setSession(data.session || false));
    const { data: { subscription } } = sb.auth.onAuthStateChange((_e, s) => setSession(s || false));
    return () => subscription.unsubscribe();
  }, []);

  React.useEffect(() => {
    if (session === null) return; // still resolving auth
    if (!session) { setTickets(null); setError(null); return; }
    let cancelled = false;
    setTickets(null);
    setError(null);
    (async () => {
      try {
        const res = await window.__hrAuth.authFetch(`${SH_API}/api/my-tickets`);
        if (cancelled) return;
        if (!res || res._noAuth) { setError('noauth'); return; }
        if (!res.ok) { setError('fetch'); return; }
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        setTickets(Array.isArray(data.tickets) ? data.tickets : []);
      } catch (_) {
        if (!cancelled) setError('fetch');
      }
    })();
    return () => { cancelled = true; };
  }, [session]);

  // Auth still loading
  if (session === null) {
    return (
      <div className="md-room sh-root" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 11, letterSpacing: '0.22em', color: 'var(--fg-3)', textTransform: 'uppercase' }}>Loading…</div>
      </div>
    );
  }

  // Not signed in
  if (!session || error === 'noauth') {
    return (
      <div className="md-room sh-root">
        <div className="sh-header">
          <div className="sh-title">SLIP HISTORY</div>
          <div className="sh-meta">Private — your slips only</div>
        </div>
        <div className="sh-gate">
          <div className="sh-gate__icon">◎</div>
          <div className="sh-gate__title">Sign in to view your history</div>
          <div className="sh-gate__sub">Your slip history is private and only visible to you.</div>
        </div>
      </div>
    );
  }

  // Network / API error
  if (error === 'fetch') {
    return (
      <div className="md-room sh-root">
        <div className="sh-header">
          <div className="sh-title">SLIP HISTORY</div>
        </div>
        <div className="sh-gate">
          <div className="sh-gate__icon">⚠</div>
          <div className="sh-gate__title">Could not load history</div>
          <div className="sh-gate__sub">Check your connection and refresh to retry.</div>
        </div>
      </div>
    );
  }

  // Tickets loading
  if (tickets === null) {
    return (
      <div className="md-room sh-root" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 11, letterSpacing: '0.22em', color: 'var(--fg-3)', textTransform: 'uppercase' }}>Loading history…</div>
      </div>
    );
  }

  const groups = shGroupByDate(tickets);

  return (
    <div className="md-room sh-root">
      <div className="sh-header">
        <div className="sh-title">SLIP HISTORY</div>
        <div className="sh-meta">
          {tickets.length === 0
            ? 'No slips on record'
            : `${tickets.length} slip${tickets.length !== 1 ? 's' : ''} across ${groups.length} date${groups.length !== 1 ? 's' : ''} · most recent first`}
        </div>
      </div>

      {tickets.length === 0 ? (
        <div className="sh-empty">
          <div className="sh-empty__icon">◎</div>
          <div className="sh-empty__title">No slips yet</div>
          <div className="sh-empty__sub">Slips submitted from Ticket Command will appear here.</div>
        </div>
      ) : (
        <div className="sh-list">
          {groups.map(({ date, tickets: dayTickets }) => (
            <ShDateRow key={date} date={date} tickets={dayTickets} />
          ))}
        </div>
      )}
    </div>
  );
}

Object.assign(window, { SlipHistory });
