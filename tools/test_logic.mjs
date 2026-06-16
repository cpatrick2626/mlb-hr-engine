import * as L from "../public/logic.js";
import { COLOR_THE_FLAG_COUNTRIES } from "../public/countries.js";
import { FLAG_BY_ID } from "../public/flags.js";

let fails = 0;
const ok = (cond, msg) => { if (!cond) { fails++; console.log("FAIL:", msg); } };

function act(state, pid, action) {
  const v = L.validateAction(state, pid, action);
  if (!v.ok) return { state, err: v.error };
  return { state: L.applyAction(state, pid, action), err: null };
}

const P = ["p-aaa", "p-bbb"];

// --- co-op full round ---
let s = L.setup(P);
ok(s.phase === "lobby", "starts in lobby");
ok(act(s, P[1], { type: "set_mode", mode: "coop" }).err, "non-host cannot set mode");
({ state: s } = act(s, P[0], { type: "set_name", name: "Chris" }));
({ state: s } = act(s, P[1], { type: "set_name", name: "Liam" }));
({ state: s } = act(s, P[0], { type: "set_mode", mode: "coop" }));
ok(s.phase === "playing", "coop playing after set_mode");
let flag = FLAG_BY_ID[s.order[0]];
// wrong color rejected
const wrongRegion = flag.regions[0];
const wrongColor = (wrongRegion.color + 1) % flag.palette.length;
ok(act(s, P[0], { type: "color", region: wrongRegion.id, color: wrongColor }).err, "wrong color rejected");
// both players fill alternately
flag.regions.forEach((r, i) => {
  const who = P[i % 2];
  const res = act(s, who, { type: "color", region: r.id, color: r.color });
  ok(!res.err, `coop fill ${r.id}: ${res.err}`);
  s = res.state;
});
ok(s.phase === "done", "coop round done at 100%");
ok(s.coopDone === 1, "coopDone incremented");
// duplicate region rejected after done? phase done blocks coloring
ok(act(s, P[0], { type: "color", region: flag.regions[0].id, color: flag.regions[0].color }).err, "color blocked when done");
// next flag with stale round rejected, correct accepted, double-send rejected
ok(act(s, P[0], { type: "next_flag", round: 99 }).err, "stale next_flag rejected");
const before = s.round;
({ state: s } = act(s, P[1], { type: "next_flag", round: s.round }));
ok(s.round === before + 1 && s.phase === "playing", "next flag advances");
ok(act(s, P[0], { type: "next_flag", round: before }).err, "duplicate next_flag rejected");

// --- versus ---
let v = L.setup(P);
({ state: v } = act(v, P[0], { type: "set_mode", mode: "versus" }));
flag = FLAG_BY_ID[v.order[0]];
// p0 races ahead; p1 colors one region on own board
const r0 = flag.regions[0];
({ state: v } = act(v, P[1], { type: "color", region: r0.id, color: r0.color }));
for (const r of flag.regions) {
  const res = act(v, P[0], { type: "color", region: r.id, color: r.color });
  ok(!res.err, `versus p0 fill ${r.id}: ${res.err}`);
  v = res.state;
}
ok(v.phase === "done" && v.winner === P[0], "first to finish wins");
ok(v.wins[P[0]] === 1, "win counted");
// opponent board masked in view
const view1 = L.viewFor(v, P[1]);
ok(Object.keys(view1.board).length === 1, "p1 sees only own board");
ok(view1.progress[P[0]] === 100, "p1 sees p0 progress %");
// loser cannot keep coloring
ok(act(v, P[1], { type: "color", region: flag.regions[1].id, color: flag.regions[1].color }).err, "coloring blocked after win");
// replay
({ state: v } = act(v, P[0], { type: "next_flag", round: v.round }));
ok(v.phase === "playing" && v.winner === null, "versus replay resets winner");

// state JSON-safe
ok(JSON.stringify(JSON.parse(JSON.stringify(v))) === JSON.stringify(v), "state JSON-safe");
ok(L.isGameOver(v).over === false, "engine game never ends");

// shared country database vs logic.js region/color parity
for (const f of COLOR_THE_FLAG_COUNTRIES) {
  for (const r of f.regions) {
    let check = L.setup(P);
    check.order = [f.id];
    check = L.applyAction(check, P[0], { type: "set_mode", mode: "coop" });
    const good = L.validateAction(check, P[0], { type: "color", region: r.id, color: r.color });
    const bad = L.validateAction(check, P[0], { type: "color", region: r.id, color: (r.color + 1) % f.palette.length });
    ok(good.ok, `logic.js accepts ${f.id}.${r.id}=${r.color}`);
    ok(!bad.ok, `logic.js rejects wrong color for ${f.id}.${r.id}`);
  }
}

console.log(fails === 0 ? "ALL TESTS PASS" : `${fails} FAILURES`);
process.exit(fails ? 1 : 0);
