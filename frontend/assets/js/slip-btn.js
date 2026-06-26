/* HR Engine — Persistent Slip Button + Global Overlay Host
   Mounts a "SLIP · N" button into #slip-btn-root in the top bar whenever the
   shared ticket has >=1 leg. Also hosts the TicketCommandSlip overlay globally
   so any surface can open it via window.__hrSlip.openSlip(). */
(() => {
  /* ---- subscribe hook (same pattern as useSlipState in hr-threat-zone.js) ---- */
  function useSlipState() {
    const [state, setState] = React.useState(() => window.__hrSlip.getState());
    React.useEffect(() => {
      return window.__hrSlip.subscribe(() => setState(window.__hrSlip.getState()));
    }, []);
    return state;
  }

  /* ---- button styles — matches auth.js "signed" chip aesthetic ---- */
  const S = {
    btn: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      background: 'transparent',
      border: '1px solid rgba(26,255,102,0.35)',
      color: 'var(--green-500, #1aff66)',
      fontFamily: 'var(--font-display, "Barlow Condensed", sans-serif)',
      fontWeight: 800,
      fontSize: '10px',
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      padding: '5px 10px',
      borderRadius: '4px',
      cursor: 'pointer',
      whiteSpace: 'nowrap',
      transition: 'border-color .15s, background .15s',
    },
    dot: {
      display: 'inline-block',
      width: '5px',
      height: '5px',
      borderRadius: '50%',
      background: 'var(--green-500, #1aff66)',
      boxShadow: '0 0 5px var(--green-500, #1aff66)',
      flexShrink: 0,
      animation: 'hr-pulse 1.8s cubic-bezier(.65,0,.35,1) infinite',
    },
  };

  /* ---- SlipButton: top-bar chip, visible only when legs >= 1 ---- */
  function SlipButton() {
    const { legs } = useSlipState();
    if (legs.length === 0) return null;
    return (
      <button
        style={S.btn}
        onClick={() => window.__hrSlip.openSlip()}
        onMouseEnter={e => {
          e.currentTarget.style.background = 'rgba(26,255,102,0.08)';
          e.currentTarget.style.borderColor = 'rgba(26,255,102,0.6)';
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.borderColor = 'rgba(26,255,102,0.35)';
        }}
      >
        <span style={S.dot} />
        SLIP · {legs.length}
      </button>
    );
  }

  /* ---- SlipOverlayHost: renders TicketCommandSlip when isOpen is true ---- */
  function SlipOverlayHost() {
    const { legs, ticketId, isOpen } = useSlipState();
    if (!isOpen || !window.TicketCommandSlip) return null;
    return React.createElement(window.TicketCommandSlip, {
      legs,
      ticketId,
      onClose:     () => window.__hrSlip.closeSlip(),
      onRemoveLeg: (n) => window.__hrSlip.removeLeg(n),
    });
  }

  /* ---- Mount SlipButton into #slip-btn-root (MutationObserver pattern, same as auth.js) ---- */
  let btnMounted = false;
  function mountSlipBtn() {
    if (btnMounted) return;
    const el = document.getElementById('slip-btn-root');
    if (!el) return;
    btnMounted = true;
    ReactDOM.createRoot(el).render(<SlipButton />);
  }

  mountSlipBtn();
  if (!btnMounted) {
    const obs = new MutationObserver(() => {
      mountSlipBtn();
      if (btnMounted) obs.disconnect();
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  /* ---- Mount SlipOverlayHost into a permanent body-level div ---- */
  const hostEl = document.createElement('div');
  hostEl.id = 'slip-overlay-root';
  document.body.appendChild(hostEl);
  ReactDOM.createRoot(hostEl).render(<SlipOverlayHost />);
})();
