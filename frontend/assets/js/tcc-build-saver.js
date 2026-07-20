/* Shared TCC build persistence for MAIN and JIG surfaces. */

const TCC_BUILDS_API = "https://mlb-hr-api.fly.dev/api/builds";

function useTccBuildSaver({ roomFilters, onApplyFilters, initialPreset = "DEFAULT TACTICAL" }) {
  const [preset, setPreset] = React.useState(initialPreset);
  const [feedback, setFeedback] = React.useState(null);
  const [builds, setBuilds] = React.useState([]);
  const [loadOpen, setLoadOpen] = React.useState(false);
  const [busy, setBusy] = React.useState(null);
  const feedbackTimer = React.useRef(null);

  React.useEffect(() => () => clearTimeout(feedbackTimer.current), []);

  const showFeedback = (text, kind = "success", timeout = 2800) => {
    clearTimeout(feedbackTimer.current);
    setFeedback({ text, kind });
    if (timeout) feedbackTimer.current = setTimeout(() => setFeedback(null), timeout);
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
      const res = await window.__hrAuth.authFetch(TCC_BUILDS_API, {
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
      const res = await window.__hrAuth.authFetch(TCC_BUILDS_API);
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

  return { preset, feedback, builds, loadOpen, busy, setLoadOpen, doSave, doLoad, applyBuild };
}

Object.assign(window, { useTccBuildSaver });
