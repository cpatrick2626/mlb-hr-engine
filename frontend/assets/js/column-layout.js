/* Per-user column layout persistence hook — shared across all FSM rooms. */

const _LAYOUT_API = "https://mlb-hr-api.fly.dev/api/layout";

function useColumnLayout(layoutKey, defaultPref) {
  const [colPref, setColPref] = React.useState(defaultPref);
  // readyRef: true once the mount-load has resolved (prevents saving the default on first render)
  const readyRef = React.useRef(false);
  // skipRef: true for one cycle after a server/LS load (suppresses the echo-save)
  const skipRef = React.useRef(false);
  const timerRef = React.useRef(null);
  const lsKey = `hr_col_layout_${layoutKey}`;

  // Mount: load from Supabase; fall back to localStorage if logged-out or offline.
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      let loaded = null;

      if (window.__hrAuth?.authFetch) {
        try {
          const res = await window.__hrAuth.authFetch(`${_LAYOUT_API}/${layoutKey}`);
          if (!cancelled && res && !res._noAuth && res.ok) {
            const data = await res.json();
            if (data && data.layout) loaded = data.layout;
          }
        } catch (_) {}
      }

      if (cancelled) return;

      if (!loaded) {
        try {
          const saved = localStorage.getItem(lsKey);
          if (saved) loaded = JSON.parse(saved);
        } catch (_) {}
      }

      readyRef.current = true;
      if (loaded) {
        skipRef.current = true;
        setColPref(loaded);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // On colPref change: mirror to localStorage + debounced POST to Supabase.
  // Skipped until after mount-load resolves; skipped once after load to avoid echo.
  React.useEffect(() => {
    if (!readyRef.current) return;
    if (skipRef.current) { skipRef.current = false; return; }

    try { localStorage.setItem(lsKey, JSON.stringify(colPref)); } catch (_) {}

    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      if (!window.__hrAuth?.authFetch) return;
      try {
        await window.__hrAuth.authFetch(`${_LAYOUT_API}/${layoutKey}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(colPref),
        });
      } catch (_) {}
    }, 500);

    return () => clearTimeout(timerRef.current);
  }, [colPref]);

  // setColPref is the stable React state setter — call it directly, not via any callback.
  return [colPref, setColPref];
}

Object.assign(window, { useColumnLayout });
