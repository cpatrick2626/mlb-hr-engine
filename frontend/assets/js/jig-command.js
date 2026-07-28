/* HR Engine — JIG BUILDER lens.
   Shows the Full Slate Intelligence Matrix with a Save / Load builder bar on top. */

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
  const { preset, feedback, builds, loadOpen, busy, setLoadOpen, doSave, doLoad, applyBuild } = useTccBuildSaver({ roomFilters, onApplyFilters });

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
      <FullSlateMatrix rows={applyRoomFilters(builderRows, appliedFilters)} total={builderRows.length} onOpen={onOpenPlayer} builderMode={true} isJigContext={true} />
    </div>
  );
}

Object.assign(window, { JigCommand });
