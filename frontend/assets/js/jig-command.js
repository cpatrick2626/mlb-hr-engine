/* HR Engine — JIG BUILDER lens.
   Shows the Full Slate Intelligence Matrix with a Save / Load builder bar on top. */

const JIG_BUILDS_API = "https://mlb-hr-api.fly.dev/api/builds";

function JigCommand({ engine, lens, appliedFilters, roomFilters, onApplyFilters, onOpenPlayer }) {
  // Phase A stopgap: prefer raw slate rows if exposed; otherwise use JIG-side rows.
  // Do not default JIG Builder to MAIN leaderboard rows.
  const rawRows =
    Array.isArray(window.SLATE_ROWS_RAW) ? window.SLATE_ROWS_RAW :
    Array.isArray(window.RAW_SLATE_ROWS) ? window.RAW_SLATE_ROWS :
    Array.isArray(window.LEADERBOARD_ROWS_RAW) ? window.LEADERBOARD_ROWS_RAW :
    null;
  const builderRows =
    rawRows ||
    (Array.isArray(window.LEADERBOARD_ROWS_JIG) ? window.LEADERBOARD_ROWS_JIG :
    // Last-resort degraded fallback only if raw/JIG rows are missing entirely.
    (Array.isArray(window.LEADERBOARD_ROWS) ? window.LEADERBOARD_ROWS : []));
  const [preset, setPreset] = React.useState("DEFAULT TACTICAL");
  const [feedback, setFeedback] = React.useState(null);
  const [builds, setBuilds] = React.useState([]);
  const [loadOpen, setLoadOpen] = React.useState(false);
  const [busy, setBusy] = React.useState(null);
  const feedbackTimer = React.useRef(null);

  React.useEffect(() => () => clearTimeout(feedbackTimer.current), []);

  const showFeedback = (text, kind = "success", timeout = 2800) => {
    clearTimeout(feedbackTimer.current);
    setFeedback({ text, kind });
    if (timeout) {
      feedbackTimer.current = setTimeout(() => setFeedback(null), timeout);
    }
  };

  const responseError = async (res, fallback) => {
    try {
      const data = await res.json();
      return data.detail || fallback;
    } catch (_) {
      return fallback;
    }
  };

  const noAuthFeedback = (action) => {
    setLoadOpen(false);
    showFeedback(`SIGN IN TO ${action} · FILTERS STAY ON THIS DEVICE`, "error", 5200);
  };

  const doSave = async () => {
    if (busy) return;
    const nameInput = window.prompt("Name this TCC build:", preset === "DEFAULT TACTICAL" ? "" : preset);
    if (nameInput === null) return;
    const name = nameInput.trim();
    if (!name) {
      showFeedback("BUILD NAME REQUIRED", "error");
      return;
    }
    if (!window.__hrAuth?.authFetch) {
      noAuthFeedback("SAVE BUILDS");
      return;
    }

    setBusy("save");
    setLoadOpen(false);
    showFeedback("SAVING BUILD", "neutral", 0);
    try {
      const res = await window.__hrAuth.authFetch(JIG_BUILDS_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          main_filters: roomFilters?.main || {},
          jig_filters: roomFilters?.jig || {},
        }),
      });
      if (res._noAuth) {
        noAuthFeedback("SAVE BUILDS");
        return;
      }
      if (!res.ok) {
        showFeedback(await responseError(res, `SAVE FAILED (${res.status})`), "error", 5200);
        return;
      }
      setPreset(name);
      showFeedback(`SAVED · ${name}`);
    } catch (_) {
      showFeedback("SAVE FAILED · CHECK CONNECTION", "error", 5200);
    } finally {
      setBusy(null);
    }
  };

  const doLoad = async () => {
    if (busy) return;
    if (loadOpen) {
      setLoadOpen(false);
      return;
    }
    if (!window.__hrAuth?.authFetch) {
      noAuthFeedback("LOAD BUILDS");
      return;
    }

    setBusy("load");
    showFeedback("LOADING BUILDS", "neutral", 0);
    try {
      const res = await window.__hrAuth.authFetch(JIG_BUILDS_API);
      if (res._noAuth) {
        noAuthFeedback("LOAD BUILDS");
        return;
      }
      if (!res.ok) {
        showFeedback(await responseError(res, `LOAD FAILED (${res.status})`), "error", 5200);
        return;
      }
      const data = await res.json();
      const savedBuilds = Array.isArray(data.builds) ? data.builds : [];
      setBuilds(savedBuilds);
      setLoadOpen(savedBuilds.length > 0);
      showFeedback(savedBuilds.length ? `${savedBuilds.length} BUILD${savedBuilds.length === 1 ? "" : "S"} READY` : "NO SAVED BUILDS", savedBuilds.length ? "neutral" : "error", savedBuilds.length ? 1800 : 3600);
    } catch (_) {
      showFeedback("LOAD FAILED · CHECK CONNECTION", "error", 5200);
    } finally {
      setBusy(null);
    }
  };

  const applyBuild = (build) => {
    const validFilterObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
    if (!build || !validFilterObject(build.main_filters) || !validFilterObject(build.jig_filters)) {
      showFeedback("BUILD FILTER DATA IS INVALID", "error", 5200);
      return;
    }
    const restoredMain = Object.keys(build.main_filters).length ? build.main_filters : null;
    const restoredJig = Object.keys(build.jig_filters).length ? build.jig_filters : null;
    onApplyFilters(restoredMain, "main");
    onApplyFilters(restoredJig, "jig");
    setPreset(build.name || "SAVED BUILD");
    setLoadOpen(false);
    showFeedback(`LOADED · ${build.name || "SAVED BUILD"}`);
  };

  return (
    <div className="md-room jig-room">
      <div className="jig-bar">
        <div className="jig-bar__id">
          <span className="jig-bar__title">JIG BUILDER</span>
          <span className="jig-bar__preset"><span className="jig-bar__k">BUILD</span> {preset}</span>
        </div>
        <div className="jig-bar__actions">
          {feedback && <span className={`jig-bar__flash jig-bar__flash--${feedback.kind}`} role="status" aria-live="polite">{feedback.kind === "success" ? "✓ " : ""}{feedback.text}</span>}
          <button className="hr-btn hr-btn--ghost" onClick={doSave} disabled={busy !== null}>{busy === "save" ? "SAVING…" : "SAVE BUILDER"}</button>
          <div className="jig-load">
            <button className="hr-btn hr-btn--ghost" onClick={doLoad} disabled={busy !== null} aria-expanded={loadOpen}>{busy === "load" ? "LOADING…" : "LOAD BUILDER"}</button>
            {loadOpen && (
              <div className="jig-load__menu" role="dialog" aria-label="Saved TCC builds">
                <div className="jig-load__head">
                  <span>SAVED BUILDS</span>
                  <button className="jig-load__close" onClick={() => setLoadOpen(false)} aria-label="Close saved builds">×</button>
                </div>
                <div className="jig-load__list">
                  {builds.map((build) => (
                    <button className="jig-load__item" key={build.build_id || build.name} onClick={() => applyBuild(build)}>
                      <span>{build.name}</span>
                      <span className="jig-load__apply">APPLY</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="jig-banner" role="status" aria-live="polite">
        <div className="jig-banner__title">JIG BUILDER · PHASE A WORKSPACE</div>
        <div className="jig-banner__sub">Current source: JIG scored slate rows. Raw unscored Builder feed is not exposed yet.</div>
      </div>
      <FullSlateMatrix rows={applyRoomFilters(builderRows, appliedFilters)} total={builderRows.length} onOpen={onOpenPlayer} builderMode={true} />
    </div>
  );
}

Object.assign(window, { JigCommand });
