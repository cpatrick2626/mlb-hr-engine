/* HR Engine — Destination Picker
   Body-level portal for routing a pick: FD search, slip only, or both.
   Opened via window.__hrSlip.requestAdd(normalizedRow).
   Option 4 (FD + Confirm + New Slip) is rendered disabled — Phase C only. */
(() => {
  const DP_TIER_COLOR = {
    APEX: "#ff3344", ELITE: "#ff8a93", EDGE: "#1aff66",
    SIGNAL: "#3b6fff", WATCH: "#ffb020", COLD: "#6b7872",
  };

  const DP_FONT = { fontFamily: 'var(--font-display, "Barlow Condensed", sans-serif)' };

  function dpFdUrl(name) {
    const q = (name || "").trim();
    return q
      ? `https://sportsbook.fanduel.com/search?q=${encodeURIComponent(q)}`
      : "https://sportsbook.fanduel.com/baseball/mlb?tab=player-home-runs";
  }

  /* CRITICAL: window.open must be called synchronously inside the click handler,
     before any await, to avoid popup-blocker. Never await before this call.
     deepLink (bet-level, then event-level, resolved by caller) lands on the specific
     game; often absent — name search stays the fallback, clipboard copy always. */
  function dpOpenFD(name, deepLink) {
    window.open(deepLink || dpFdUrl(name), "_blank", "noopener");
    if (navigator.clipboard) navigator.clipboard.writeText(name).catch(() => {});
    dpToast(deepLink ? "Opened FanDuel event: " + name : "Opened FanDuel search: " + name);
  }

  function dpToast(msg) {
    let el = document.getElementById("dp-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "dp-toast";
      el.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a2030;border:1px solid #3b6fff;color:#e0e8ff;padding:10px 18px;border-radius:8px;font-size:13px;font-family:inherit;z-index:10001;pointer-events:none;transition:opacity .3s;white-space:nowrap;";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.opacity = "1";
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = "0"; }, 2800);
  }

  function dpIsAuthed() {
    return !!(window.__hrAuth && window.__hrAuth.authFetch);
  }

  function dpOpenAuth() {
    const btn = document.querySelector("#auth-root button");
    if (btn) btn.click();
  }

  // Imperative controller — setRow is assigned on every PickerPortal render.
  // React guarantees useState setters are stable references so this is safe.
  const _ctrl = { setRow: null };

  // Defined at IIFE scope so React never unmounts/remounts it between renders.
  function DpOptBtn({ onClick, color, border, disabled, children }) {
    const [hov, setHov] = React.useState(false);
    return (
      <button
        type="button"
        onClick={disabled ? undefined : onClick}
        onMouseEnter={() => !disabled && setHov(true)}
        onMouseLeave={() => setHov(false)}
        disabled={!!disabled}
        style={{
          ...DP_FONT,
          width: "100%",
          background: hov ? `${color}14` : "transparent",
          border: `1px solid ${hov && !disabled ? color : border}`,
          borderRadius: "5px",
          padding: "9px 14px",
          textAlign: "left",
          cursor: disabled ? "not-allowed" : "pointer",
          display: "flex",
          flexDirection: "column",
          gap: "2px",
          transition: "border-color .12s, background .12s",
          opacity: disabled ? 0.35 : 1,
        }}
      >
        {children}
      </button>
    );
  }

  function DestinationPicker({ row, onClose }) {
    const isMobile = window.innerWidth < 640;
    const tierC = DP_TIER_COLOR[row.tier] || "#6b7872";
    const name  = row.name || "—";
    const prob  = row.hrprob != null
      ? Number(row.hrprob).toFixed(1) + "%"
      : row.model_prob != null
        ? (Number(row.model_prob) * 100).toFixed(1) + "%"
        : "—";
    const authed = dpIsAuthed();
    // Deep-link priority: bet link → event link → null (dpOpenFD falls back to search)
    const fdLink = row.fd_bet_link || row.fd_event_link || null;

    // Option 1: FD only — no auth required
    const handleFDOnly = () => {
      dpOpenFD(name, fdLink);   // SYNC — popup-safe
      onClose();
    };

    // Option 2: Slip only — needs auth
    const handleSlipOnly = () => {
      if (!authed) { onClose(); dpOpenAuth(); return; }
      window.__hrSlip.addLeg(row);
      onClose();
    };

    // Option 3: FD + Slip — FD MUST open synchronously before any async op
    const handleFDAndSlip = () => {
      dpOpenFD(name, fdLink);   // SYNC — must be first; kept inside user gesture
      if (!authed) { onClose(); dpOpenAuth(); return; }
      window.__hrSlip.addLeg(row);   // async internally; fires, _notify updates surfaces
      onClose();
    };

    const opt2c = authed ? "#1aff66" : "#ffb020";
    const opt2b = authed ? "rgba(26,255,102,0.4)" : "rgba(255,176,32,0.4)";

    const titleSt = (c) => ({
      ...DP_FONT,
      fontSize: "12px", fontWeight: 800, letterSpacing: "0.1em",
      textTransform: "uppercase", color: c,
    });
    const descSt = {
      ...DP_FONT,
      fontSize: "10px", fontWeight: 400, letterSpacing: "0.03em",
      color: "rgba(224,232,255,0.55)",
    };

    return (
      <div
        style={{
          position: "fixed", inset: 0, zIndex: 9998,
          background: "rgba(0,0,0,0.65)",
          display: "flex",
          alignItems: isMobile ? "flex-end" : "center",
          justifyContent: "center",
        }}
        onClick={onClose}
      >
        <div
          style={{
            ...DP_FONT,
            width: isMobile ? "100%" : "360px",
            maxWidth: isMobile ? "100%" : "calc(100vw - 32px)",
            background: "var(--bg-raised, #1a2030)",
            border: "1px solid var(--border-2, rgba(59,111,255,0.3))",
            borderRadius: isMobile ? "12px 12px 0 0" : "8px",
            boxShadow: "0 8px 40px rgba(0,0,0,0.7)",
            overflow: "hidden",
          }}
          onClick={e => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-label="Select destination"
        >
          {/* Header: tier badge · player name · HR prob */}
          <div style={{
            padding: "12px 16px 10px",
            borderBottom: "1px solid rgba(59,111,255,0.2)",
            display: "flex", alignItems: "center", gap: "10px",
          }}>
            <span style={{
              ...DP_FONT, fontSize: "9px", fontWeight: 800, letterSpacing: "0.14em",
              textTransform: "uppercase", color: tierC,
              border: `1px solid ${tierC}55`, borderRadius: "3px", padding: "2px 7px", flexShrink: 0,
            }}>
              {row.tier || "—"}
            </span>
            <span style={{
              ...DP_FONT, fontSize: "14px", fontWeight: 800, letterSpacing: "0.06em",
              textTransform: "uppercase", color: "#e0e8ff",
              flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>
              {name}
            </span>
            <span style={{ ...DP_FONT, fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: tierC, flexShrink: 0 }}>
              {prob} HR
            </span>
          </div>

          <div style={{
            ...DP_FONT, fontSize: "9px", fontWeight: 800, letterSpacing: "0.2em",
            textTransform: "uppercase", color: "rgba(59,111,255,0.75)",
            padding: "9px 16px 4px",
          }}>
            SELECT DESTINATION
          </div>

          <div style={{ padding: "4px 12px 14px", display: "flex", flexDirection: "column", gap: "6px" }}>

            {/* Option 1 — FD only, works signed-out */}
            <DpOptBtn onClick={handleFDOnly} color="#3b6fff" border="rgba(59,111,255,0.45)">
              <span style={titleSt("#3b6fff")}>FD ONLY</span>
              <span style={descSt}>Opens FanDuel search — place manually.</span>
            </DpOptBtn>

            {/* Option 2 — slip only; amber noauth when signed-out */}
            <DpOptBtn onClick={handleSlipOnly} color={opt2c} border={opt2b}>
              <span style={titleSt(opt2c)}>
                {authed ? "ADD TO SLIP ONLY" : "⚿ ADD TO SLIP ONLY"}
              </span>
              <span style={descSt}>
                {authed ? "Adds this player to your active slip." : "Sign in to add to slip."}
              </span>
            </DpOptBtn>

            {/* Option 3 — FD + slip; amber noauth when signed-out; FD always opens */}
            <DpOptBtn onClick={handleFDAndSlip} color={opt2c} border={opt2b}>
              <span style={titleSt(opt2c)}>
                {authed ? "FD + ADD TO SLIP" : "⚿ FD + ADD TO SLIP"}
              </span>
              <span style={descSt}>
                {authed
                  ? "Opens FanDuel search and adds to slip."
                  : "Opens FanDuel search — sign in to add to slip."}
              </span>
            </DpOptBtn>

            {/* Option 4 — disabled; Phase C only */}
            <DpOptBtn color="#6b7872" border="rgba(107,120,114,0.25)" disabled>
              <span style={titleSt("#6b7872")}>FD + CONFIRM SLIP + START NEW</span>
              <span style={descSt} title="requires slip confirm flow — Phase C">Requires slip confirm flow — Phase C.</span>
            </DpOptBtn>

          </div>
        </div>
      </div>
    );
  }

  function PickerPortal() {
    const [row, setRow] = React.useState(null);
    _ctrl.setRow = setRow;   // stable ref; safe to assign in render body

    React.useEffect(() => {
      if (!row) return;
      const onKey = (e) => { if (e.key === "Escape") setRow(null); };
      document.addEventListener("keydown", onKey);
      return () => document.removeEventListener("keydown", onKey);
    }, [!!row]);

    if (!row) return null;
    return <DestinationPicker row={row} onClose={() => setRow(null)} />;
  }

  // Mount body-level portal (same pattern as slip-overlay-root in slip-btn.js)
  const portalEl = document.createElement("div");
  portalEl.id = "destination-picker-root";
  document.body.appendChild(portalEl);
  ReactDOM.createRoot(portalEl).render(<PickerPortal />);

  // Override the stub registered in slip-state.js with the real implementation.
  if (window.__hrSlip) {
    window.__hrSlip.requestAdd = function (row) {
      if (_ctrl.setRow) _ctrl.setRow(row);
    };
  }
})();
