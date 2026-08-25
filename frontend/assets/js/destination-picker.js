/* HR Engine — Destination Picker
   Body-level portal for routing a pick: FD search, slip only, or both.
   Opened via window.__hrSlip.requestAdd(normalizedRow).
   Option 4 (FD + Confirm + New Slip) is rendered disabled — Phase C only. */
(() => {
  const DP_TIER_COLOR = {
    APEX: "#ff3344", ELITE: "#ff8a93", EDGE: "#1aff66",
    SIGNAL: "#3b6fff", WATCH: "#ffb020", COLD: "#6b7872",
  };

  /* TM score band colors — replicates TM_BANDS from full-slate-matrix.js */
  const DP_TM_BANDS = [
    { min: 60, color: "#4ade80" },
    { min: 50, color: "#86efac" },
    { min: 38, color: "#fbbf24" },
    { min: 25, color: "#f97316" },
    { min:  0, color: "#ef4444" },
  ];
  function dpTmColor(s) {
    if (s == null || !Number.isFinite(Number(s))) return "#6b7872";
    const n = Number(s);
    for (const b of DP_TM_BANDS) { if (n >= b.min) return b.color; }
    return "#ef4444";
  }

  const DP_FONT = { fontFamily: 'var(--font-display, "Barlow Condensed", sans-serif)' };

/* Normalize a display name for FD search URL only — strips generational suffixes
   (Jr./Sr./II/III/IV) and accent-folds to ASCII. Display name is never mutated. */
function fdSearchName(displayName) {
  return (displayName || "")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/,?\s*(Jr\.?|Sr\.?|II|III|IV)\s*$/i, "")
    .trim();
}

  function dpFdUrl(name) {
    const q = fdSearchName(name);
    return q
      ? `https://sportsbook.fanduel.com/search?q=${encodeURIComponent(q)}`
      : "https://sportsbook.fanduel.com/baseball/mlb?tab=player-home-runs";
  }

  /* FanDuel killed ?q= app pre-fill (confirmed 2026-08-25). Clipboard copy +
     manual paste is the only reliable mobile path now.
     execCommand('copy') runs synchronously inside the gesture and is more
     reliable on mobile browsers than the async Clipboard API, which can be
     cancelled mid-flight when window.open backgrounds the tab. Try it first;
     fall back to navigator.clipboard as a best-effort second attempt. */
  function dpCopyToClipboard(text) {
    let ok = false;
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.top = "-9999px";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      ok = document.execCommand("copy");
      document.body.removeChild(ta);
    } catch (_) {}
    if (!ok) {
      try { navigator.clipboard && navigator.clipboard.writeText(text); } catch (_) {}
    }
    return ok;
  }

  let _dpToastTimer = null;
  function dpShowToast(message) {
    let el = document.getElementById("dp-copy-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "dp-copy-toast";
      el.style.cssText = [
        "position:fixed", "left:50%", "bottom:24px", "transform:translateX(-50%)",
        "z-index:99999",
        "background:var(--bg-raised, #1a2030)",
        "border:1px solid rgba(26,255,102,0.5)",
        "color:#e0e8ff",
        "font-family:var(--font-display, \"Barlow Condensed\", sans-serif)",
        "font-size:12px", "font-weight:700", "letter-spacing:0.03em",
        "padding:10px 16px", "border-radius:6px",
        "box-shadow:0 8px 24px rgba(0,0,0,0.5)",
        "opacity:0", "transition:opacity .15s",
        "pointer-events:none", "max-width:calc(100vw - 32px)",
        "text-align:center", "white-space:nowrap", "overflow:hidden", "text-overflow:ellipsis",
      ].join(";");
      document.body.appendChild(el);
    }
    el.textContent = message;
    clearTimeout(_dpToastTimer);
    requestAnimationFrame(() => { el.style.opacity = "1"; });
    _dpToastTimer = setTimeout(() => { el.style.opacity = "0"; }, 2000);
  }

  /* CRITICAL: window.open must be called synchronously inside the click handler,
     before any await, to avoid popup-blocker. Never await before this call.
     Copy happens first, synchronously, so it lands before window.open can
     background the tab and cancel a pending async clipboard write. */
  function dpOpenFD(name) {
    const trimmed = (name || "").trim();
    if (trimmed) {
      dpCopyToClipboard(trimmed);
      dpShowToast(`✓ Copied ${trimmed} — paste in FanDuel search`);
    }
    const url = dpFdUrl(name);
    window.open(url, "_blank", "noopener");
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
  const _ctrl = { setRow: null, onParentClose: null };

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

    /* Five pick-card scores — read already-forwarded values, null-guarded. */
    const isJigLane   = row.board === 'jig' || !!(row.signal_snapshot && row.signal_snapshot.lane === 'jig');
    const tmLabel     = isJigLane ? 'JIG' : 'TM';
    const tmRaw       = isJigLane
      ? (row.jig_score != null && Number.isFinite(Number(row.jig_score)) ? Number(row.jig_score) : null)
      : (row.true_matchup_score != null && Number.isFinite(Number(row.true_matchup_score)) ? Number(row.true_matchup_score) : null);
    const tmDisplay   = tmRaw != null ? String(Math.round(tmRaw)) : "—";
    const tmColor     = dpTmColor(tmRaw);
    const sigRaw      = row.arsenal_edge_score != null && Number.isFinite(Number(row.arsenal_edge_score)) ? Number(row.arsenal_edge_score) : null;
    const sigDisplay  = sigRaw != null ? sigRaw.toFixed(1) : "—";
    const edgeRaw     = row.edge != null && Number.isFinite(Number(row.edge)) ? Number(row.edge) : null;
    const edgeDisplay = edgeRaw != null ? (edgeRaw >= 0 ? "+" : "") + (edgeRaw * 100).toFixed(1) + "pp" : "—";
    const edgeColor   = edgeRaw != null ? (edgeRaw >= 0 ? "#1aff66" : "#ffb020") : "#6b7872";
    const confRaw     = row.arsenal_edge_confidence != null && Number.isFinite(Number(row.arsenal_edge_confidence)) ? Number(row.arsenal_edge_confidence) : null;
    const confDisplay = confRaw != null ? Math.round(confRaw * 100) + "%" : "—";

    // Captured once at render; called after picker closes to also dismiss the parent card.
    const onParentClose = _ctrl.onParentClose;

    // Current slip players — read once at render (picker is ephemeral)
    const currentLegs = (window.__hrSlip ? window.__hrSlip.getState().legs : []);

    // Option 1: FD only — no auth required
    const handleFDOnly = () => {
      dpOpenFD(name);   // SYNC — popup-safe
      onClose();
      onParentClose && onParentClose();
    };

    // Option 2: Slip only — needs auth
    const handleSlipOnly = () => {
      if (!authed) { onClose(); onParentClose && onParentClose(); dpOpenAuth(); return; }
      window.__hrSlip.addLeg(row);
      onClose();
      onParentClose && onParentClose();
    };

    // Option 3: FD + Slip — FD MUST open synchronously before any async op
    const handleFDAndSlip = () => {
      dpOpenFD(name);   // SYNC — must be first; kept inside user gesture
      if (!authed) { onClose(); onParentClose && onParentClose(); dpOpenAuth(); return; }
      window.__hrSlip.addLeg(row);   // async internally; fires, _notify updates surfaces
      onClose();
      onParentClose && onParentClose();
    };

    // Option 4: FD + Add to Slip + Submit Slip — opens FD, adds leg, submits whole slip, auto-posts
    const handleFDAddSubmit = async () => {
      dpOpenFD(name);   // SYNC — must be first
      if (!authed) { onClose(); onParentClose && onParentClose(); dpOpenAuth(); return; }
      onClose();
      onParentClose && onParentClose();
      await window.__hrSlip.addLeg(row);
      const { ticketId } = window.__hrSlip.getState();
      if (!ticketId) return;
      try {
        const res = await window.__hrAuth.authFetch(
          "https://mlb-hr-api.fly.dev/api/tickets/complete",
          { method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticket_id: ticketId }) }
        );
        if (res.ok) {
          window.__hrAuth.authFetch("https://mlb-hr-api.fly.dev/api/community/posts", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticket_id: ticketId }),
          }).catch(() => {});
          window.__hrSlip.resetSlip();
        }
      } catch (_) {}
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
            padding: "15px 16px 13px",
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
              ...DP_FONT, fontSize: "22px", fontWeight: 900, letterSpacing: "0.03em", lineHeight: 1,
              textTransform: "uppercase", color: "#e0e8ff",
              flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>
              {name}
            </span>
            <span style={{ ...DP_FONT, fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: tierC, flexShrink: 0 }}>
              {prob} HR
            </span>
          </div>

          {/* Stacked score grid — column headers · preview row · selected-leg rows · totals row */}
          {(() => {
            /* Combined HR% — product of all finite leg decimals including preview.
               hrprob on legs is in % units (e.g. 14.2); divide by 100 for decimal.
               model_prob on the preview row is already 0–1 decimal. */
            const previewDec = Number.isFinite(Number(row.model_prob))
              ? Number(row.model_prob)
              : Number.isFinite(Number(row.hrprob))
                ? Number(row.hrprob) / 100
                : null;

            let product = previewDec;
            let partial = previewDec == null;

            for (const leg of currentLegs) {
              const p = Number.isFinite(Number(leg.hrprob)) ? Number(leg.hrprob) / 100 : null;
              if (p != null) { product = product == null ? p : product * p; }
              else partial = true;
            }

            const combinedHRDisplay = product != null
              ? (product * 100).toFixed(2) + "%" + (partial ? "*" : "")
              : "—";

            /* EV total: selected legs don't store edge, so "—" whenever any are present.
               Preview-only case (0 selected legs) shows preview edge if it exists. */
            const evTotalDisplay = (currentLegs.length === 0 && edgeRaw != null)
              ? edgeDisplay
              : "—";

            const NAME_W = 80;

            const colHdrSt = (laneColor) => ({
              ...DP_FONT, fontSize: "9px", fontWeight: 700, letterSpacing: "0.12em",
              textTransform: "uppercase", color: laneColor, whiteSpace: "nowrap",
            });
            const valSt = (color, fs) => ({
              ...DP_FONT, fontSize: fs || (isMobile ? "11px" : "12px"), fontWeight: 800,
              letterSpacing: "0.02em", lineHeight: 1, color,
            });
            const nameSt = (color) => ({
              ...DP_FONT, fontSize: "12px", fontWeight: 800, letterSpacing: "0.04em",
              textTransform: "uppercase", color: color || "rgba(224,232,255,0.9)",
              display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            });
            const subSt = (color) => ({
              ...DP_FONT, fontSize: "9px", fontWeight: 600, letterSpacing: "0.1em",
              textTransform: "uppercase", color: color || "rgba(224,232,255,0.55)",
              display: "block",
            });

            const cols = [
              { label: "TM/JIG", laneColor: "rgba(255,138,147,0.92)" },
              { label: "HR%",    laneColor: "rgba(59,111,255,0.88)"  },
              { label: "SIGNAL", laneColor: "rgba(59,111,255,0.88)"  },
              { label: "EDGE",   laneColor: "rgba(59,111,255,0.88)"  },
              { label: "CONF",   laneColor: "rgba(59,111,255,0.88)"  },
            ];

            return (
              <div style={{ borderBottom: "1px solid rgba(59,111,255,0.13)" }}>

                {/* Column header row */}
                <div style={{ display: "flex", alignItems: "center", padding: "5px 12px 2px" }}>
                  <div style={{ width: NAME_W, flexShrink: 0 }} />
                  {cols.map((c, i) => (
                    <div key={i} style={{ flex: 1, textAlign: "center" }}>
                      <span style={colHdrSt(c.laneColor)}>{c.label}</span>
                    </div>
                  ))}
                </div>

                {/* Preview batter row */}
                <div style={{
                  display: "flex", alignItems: "center",
                  padding: "4px 12px 5px",
                  background: "rgba(59,111,255,0.07)",
                  borderLeft: `3px solid ${tierC}`,
                }}>
                  <div style={{ width: NAME_W, flexShrink: 0, paddingRight: 4, overflow: "hidden" }}>
                    <span style={nameSt(tierC)}>{name}</span>
                    <span style={subSt()}>preview</span>
                  </div>
                  {[
                    { val: tmDisplay,   color: tmRaw   != null ? tmColor   : "#6b7872" },
                    { val: prob,         color: prob    !== "—" ? tierC     : "#6b7872" },
                    { val: sigDisplay,   color: sigRaw  != null ? tierC     : "#6b7872" },
                    { val: edgeDisplay,  color: edgeColor },
                    { val: confDisplay,  color: confRaw != null ? tierC     : "#6b7872" },
                  ].map((cell, i) => (
                    <div key={i} style={{ flex: 1, textAlign: "center" }}>
                      <span style={valSt(cell.color)}>{cell.val}</span>
                    </div>
                  ))}
                </div>

                {/* Selected leg rows — scores snapshotted at add time */}
                {currentLegs.map((leg, i) => {
                  const legHR = Number.isFinite(Number(leg.hrprob))
                    ? Number(leg.hrprob).toFixed(1) + "%"
                    : "—";
                  const legTierC       = DP_TIER_COLOR[leg.tier] || "#6b7872";
                  const legIsJig       = leg.board === 'jig';
                  const legTmRaw       = legIsJig
                    ? (leg.jig_score != null && Number.isFinite(Number(leg.jig_score)) ? Number(leg.jig_score) : null)
                    : (leg.true_matchup_score != null && Number.isFinite(Number(leg.true_matchup_score)) ? Number(leg.true_matchup_score) : null);
                  const legTmDisplay   = legTmRaw   != null ? String(Math.round(legTmRaw)) : "—";
                  const legTmColor     = dpTmColor(legTmRaw);
                  const legSigRaw      = leg.arsenal_edge_score != null && Number.isFinite(Number(leg.arsenal_edge_score)) ? Number(leg.arsenal_edge_score) : null;
                  const legSigDisplay  = legSigRaw  != null ? legSigRaw.toFixed(1) : "—";
                  const legEdgeRaw     = leg.edge != null && Number.isFinite(Number(leg.edge)) ? Number(leg.edge) : null;
                  const legEdgeDisplay = legEdgeRaw != null ? (legEdgeRaw >= 0 ? "+" : "") + (legEdgeRaw * 100).toFixed(1) + "pp" : "—";
                  const legEdgeColor   = legEdgeRaw != null ? (legEdgeRaw >= 0 ? "#1aff66" : "#ffb020") : "#6b7872";
                  const legConfRaw     = leg.arsenal_edge_confidence != null && Number.isFinite(Number(leg.arsenal_edge_confidence)) ? Number(leg.arsenal_edge_confidence) : null;
                  const legConfDisplay = legConfRaw != null ? Math.round(legConfRaw * 100) + "%" : "—";
                  return (
                    <div key={i} style={{
                      display: "flex", alignItems: "center",
                      padding: "4px 12px 4px",
                      borderTop: "1px solid rgba(59,111,255,0.08)",
                      borderLeft: `3px solid ${legTierC}55`,
                    }}>
                      <div style={{ width: NAME_W, flexShrink: 0, paddingRight: 4, overflow: "hidden" }}>
                        <span style={nameSt()}>{leg.name || "—"}</span>
                        {leg.tier && <span style={subSt(legTierC)}>{leg.tier}</span>}
                      </div>
                      {[
                        { val: legTmDisplay,   color: legTmRaw   != null ? legTmColor  : "#6b7872" },
                        { val: legHR,           color: legHR      !== "—"  ? legTierC   : "#6b7872" },
                        { val: legSigDisplay,   color: legSigRaw  != null  ? legTierC   : "#6b7872" },
                        { val: legEdgeDisplay,  color: legEdgeColor },
                        { val: legConfDisplay,  color: legConfRaw != null  ? legTierC   : "#6b7872" },
                      ].map((cell, j) => (
                        <div key={j} style={{ flex: 1, textAlign: "center" }}>
                          <span style={valSt(cell.color)}>{cell.val}</span>
                        </div>
                      ))}
                    </div>
                  );
                })}

                {/* Totals row — combined HR% product; EV only if no selected legs + preview has edge;
                    TM/Signal/Conf are non-aggregable across legs → "—" (never summed) */}
                <div style={{
                  display: "flex", alignItems: "center",
                  padding: "5px 12px 5px",
                  marginTop: "3px",
                  borderTop: "1px solid rgba(255,51,68,0.35)",
                  background: "rgba(255,51,68,0.05)",
                  borderLeft: "3px solid rgba(255,51,68,0.6)",
                }}>
                  <div style={{ width: NAME_W, flexShrink: 0, paddingRight: 4, overflow: "hidden" }}>
                    <span style={subSt("rgba(255,51,68,0.85)")}>TICKET</span>
                  </div>
                  {[
                    { val: "—",              color: "#6b7872",  fs: undefined },
                    { val: combinedHRDisplay, color: partial ? "#ffb020" : "#1aff66", fs: isMobile ? "10px" : "11px" },
                    { val: "—",              color: "#6b7872",  fs: undefined },
                    { val: evTotalDisplay,   color: evTotalDisplay !== "—" ? edgeColor : "#6b7872", fs: undefined },
                    { val: "—",              color: "#6b7872",  fs: undefined },
                  ].map((cell, i) => (
                    <div key={i} style={{ flex: 1, textAlign: "center" }}>
                      <span style={valSt(cell.color, cell.fs)}>{cell.val}</span>
                    </div>
                  ))}
                </div>

              </div>
            );
          })()}

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

            {/* Option 4 — FD + Add + Submit Slip (enabled; needs auth) */}
            <DpOptBtn onClick={handleFDAddSubmit} color={opt2c} border={opt2b} disabled={!authed}>
              <span style={titleSt(authed ? opt2c : "#6b7872")}>
                {authed ? "FD + ADD TO SLIP + SUBMIT SLIP" : "⚿ FD + ADD TO SLIP + SUBMIT SLIP"}
              </span>
              <span style={descSt}>
                {authed
                  ? "Opens FD, adds to slip, submits and auto-posts."
                  : "Sign in to use this option."}
              </span>
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
    window.__hrSlip.requestAdd = function (row, onParentClose) {
      _ctrl.onParentClose = onParentClose || null;
      if (_ctrl.setRow) _ctrl.setRow(row);
    };
  }
})();
