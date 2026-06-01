/* HR Engine — Live data loader.
   Fetches from FastAPI at mlb-hr-api.fly.dev/api/slate.
   Falls back to empty arrays if API is unavailable. */

window.LEADERBOARD_ROWS = [];
window.SLATE_GAMES = [];
window._dataLoaded = false;

(async function loadSlateData() {
  try {
    const res = await fetch("https://mlb-hr-api.fly.dev/api/slate");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    window.LEADERBOARD_ROWS = data.leaderboard_rows || [];
    window.SLATE_GAMES = data.slate_games || [];
    window._dataLoaded = true;
    // Dispatch event so React components can re-render with live data
    window.dispatchEvent(new CustomEvent("hrEngineDataLoaded", { detail: data }));
  } catch (err) {
    console.warn("HR Engine: failed to load live data, using empty slate.", err);
    window.LEADERBOARD_ROWS = [];
    window.SLATE_GAMES = [];
    window._dataLoaded = false;
    window.dispatchEvent(new CustomEvent("hrEngineDataLoaded", { detail: {} }));
  }
})();
