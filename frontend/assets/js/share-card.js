(function () {
  if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
      r = Math.min(r, w / 2, h / 2);
      this.moveTo(x + r, y); this.lineTo(x + w - r, y);
      this.arcTo(x + w, y, x + w, y + r, r); this.lineTo(x + w, y + h - r);
      this.arcTo(x + w, y + h, x + w - r, y + h, r); this.lineTo(x + r, y + h);
      this.arcTo(x, y + h, x, y + h - r, r); this.lineTo(x, y + r);
      this.arcTo(x, y, x + r, y, r); this.closePath();
    };
  }

  var TC = { APEX:'#ff3344', ELITE:'#ff8a93', EDGE:'#1aff66', SIGNAL:'#3b6fff', WATCH:'#ffb020', COLD:'#6b7872' };
  var P  = {
    void:'#04070a', panel:'#0a1014', cell:'#0d1519',
    fg1:'#f4f8f6', fg2:'#c8d2cf', fg3:'#93a09b',
    green:'#1aff66', red:'#ff3344', cyan:'#00d9ff', amber:'#ffb020'
  };

  var CARD_CACHE = new Map();

  // ── format helpers ─────────────────────────────────────────────────
  function pct(n)  { return n != null ? n.toFixed(1) + '%' : '—'; }
  function fmtD(n) { if (n == null) return '—'; return n < 1 ? '.' + String(Math.round(n*1000)).padStart(3,'0') : n.toFixed(3); }
  function f1(n)   { return n != null ? n.toFixed(1) : '—'; }

  function hexRgba(hex, a) {
    var h = hex.replace('#','');
    if (h.length === 3) h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2];
    return 'rgba('+parseInt(h.slice(0,2),16)+','+parseInt(h.slice(2,4),16)+','+parseInt(h.slice(4,6),16)+','+a+')';
  }

  function vColor(v, hi, lo) {
    if (v == null) return P.fg2;
    return v >= hi ? P.green : v >= lo ? P.amber : P.fg2;
  }

  function pillColor(pill) {
    return pill==='EXPLOIT'?P.green : pill==='HUNT'?P.amber : pill==='AVOID'?P.red : P.fg3;
  }

  // ── canvas draw helpers ────────────────────────────────────────────
  function hdr(ctx, label, x, y, W) {
    ctx.fillStyle = P.fg3;
    ctx.font = '700 8.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.letterSpacing = '0.12em';
    ctx.fillText('◈ ' + label, x, y);
    var tw = ctx.measureText('◈ ' + label).width + 8;
    ctx.beginPath(); ctx.moveTo(x + tw, y - 4); ctx.lineTo(W - x, y - 4);
    ctx.strokeStyle = 'rgba(180,220,200,0.14)'; ctx.lineWidth = 1; ctx.stroke();
    ctx.letterSpacing = '0';
  }

  function divider(ctx, x1, x2, y, a) {
    ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y);
    ctx.strokeStyle = 'rgba(180,220,200,' + (a||0.10) + ')';
    ctx.lineWidth = 1; ctx.stroke();
  }

  function statCell(ctx, k, v, color, x, y, w, h) {
    ctx.beginPath(); ctx.roundRect(x+1, y+1, w-2, h-2, 4);
    ctx.fillStyle = P.cell; ctx.fill();
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(k, x+6, y+13);
    ctx.fillStyle = color;
    ctx.font = '700 15px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText(v, x+6, y+27);
  }

  // ── main draw ─────────────────────────────────────────────────────
  function _draw(ctx, row, detail, W, H) {
    var PAD = 18;
    var tier = (row.tier || 'COLD').toUpperCase();
    var tc   = TC[tier] || P.fg3;

    // Background + tier strip
    ctx.fillStyle = P.void; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = tc; ctx.fillRect(0, 0, W, 4);

    // Card panel
    ctx.beginPath(); ctx.roundRect(10, 12, W-20, H-22, 7);
    ctx.fillStyle = P.panel; ctx.fill();

    var cy = 20;

    // Extract detail sections
    var sc     = (detail && detail.statcast)    || {};
    var splits = (detail && detail.splits)      || {};
    var disc   = (detail && detail.discipline)  || {};
    var ars    = (detail && detail.arsenal)     || {};
    var ptch   = (detail && detail.pitcher)     || {};
    var env    = (detail && detail.environment) || {};
    var ppRows = (detail && detail.pitch_profile && Array.isArray(detail.pitch_profile.rows))
                 ? detail.pitch_profile.rows : [];
    var verdict = (detail && detail.pitch_mix_verdict) || null;

    // ── HEADER ────────────────────────────────────────────────────
    // Tier badge
    ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
    var tlw = ctx.measureText(tier).width;
    var tbw = tlw + 16;
    ctx.beginPath(); ctx.roundRect(PAD, cy, tbw, 20, 4);
    ctx.fillStyle = hexRgba(tc, 0.18); ctx.fill();
    ctx.beginPath(); ctx.roundRect(PAD, cy, tbw, 20, 4);
    ctx.strokeStyle = hexRgba(tc, 0.7); ctx.lineWidth = 1; ctx.stroke();
    ctx.fillStyle = tc; ctx.textAlign = 'left';
    ctx.fillText(tier, PAD+8, cy+13);

    // HR PROB hero (right)
    var hrProb = row.hrprob != null ? row.hrprob.toFixed(1) + '%' : '—';
    ctx.fillStyle = P.green;
    ctx.font = '800 34px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'right'; ctx.fillText(hrProb, W-PAD, cy+30);
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText('HR PROB', W-PAD, cy+40);

    // EV / edge
    var evParts = [];
    if (row.edge   != null) evParts.push('EDGE '+(row.edge>=0?'+':'')+(row.edge*100).toFixed(1)+'pp');
    if (row.ev_pct != null) evParts.push('EV '+(row.ev_pct>=0?'+':'')+row.ev_pct.toFixed(1)+'%');
    if (evParts.length) {
      ctx.fillStyle = (row.edge != null && row.edge > 0) ? P.green : P.red;
      ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'right'; ctx.fillText(evParts.join(' · '), W-PAD, cy+52);
    }

    cy += 6;
    // Player name
    ctx.fillStyle = P.fg1;
    ctx.font = '800 22px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText((row.name || '').toUpperCase(), PAD, cy+26);
    cy += 30;

    // Meta line
    var batSide = row.bats || row.batter_side || '?';
    var pHand   = row.pitcher_hand || '?';
    var meta = [row.teamAbbr, 'BATS '+batSide, row.pitcher_name ? 'vs '+row.pitcher_name.toUpperCase()+' ('+pHand+'HP)' : null].filter(Boolean).join('  ·  ');
    ctx.fillStyle = P.fg3;
    ctx.font = '600 9.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left'; ctx.fillText(meta, PAD, cy+10);
    cy += 18;

    divider(ctx, PAD, W-PAD, cy); cy += 12;

    // ── POWER PROFILE ─────────────────────────────────────────────
    hdr(ctx, 'POWER PROFILE · STATCAST', PAD, cy+9, W); cy += 16;

    // 16 stats, 4 cols × 4 rows
    var STATS = [
      { k:'BARREL%',  v: sc.barrel!=null ? pct(sc.barrel) : (row.barrel!=null ? pct(row.barrel) : '—'),   c: vColor(sc.barrel||row.barrel, 15, 8)  },
      { k:'HARD HIT%',v: sc.hh!=null     ? pct(sc.hh)     : (row.hh!=null     ? pct(row.hh)     : '—'),   c: vColor(sc.hh||row.hh,         50,38)  },
      { k:'MAX EV',   v: sc.maxev!=null   ? f1(sc.maxev)+'mph' : '—',                                       c: vColor(sc.maxev,115,108)               },
      { k:'AVG EV',   v: sc.ev!=null      ? f1(sc.ev)+'mph'    : '—',                                       c: vColor(sc.ev,   93, 88)                },
      { k:'xSLG',     v: sc.xslg!=null   ? fmtD(sc.xslg) : (row.xslg!=null ? fmtD(row.xslg) : '—'),      c: vColor(sc.xslg||row.xslg,.600,.480)    },
      { k:'xISO',     v: sc.xiso!=null   ? fmtD(sc.xiso) : (row.xiso!=null ? fmtD(row.xiso) : '—'),      c: vColor(sc.xiso||row.xiso,.280,.200)    },
      { k:'wOBA',     v: fmtD(sc.woba),                                                                     c: vColor(sc.woba, .400,.320)             },
      { k:'LAUNCH°',  v: sc.la!=null      ? f1(sc.la)+'°' : '—',                                           c: (sc.la>=18&&sc.la<=28)?P.green:P.fg2  },
      { k:'PULL-AIR%',v: pct(sc.pullair),                                                                    c: vColor(sc.pullair,26,16)               },
      { k:'SWEET%',   v: pct(sc.sweet),                                                                      c: vColor(sc.sweet,  35,25)               },
      { k:'SQ-UP%',   v: disc.squp!=null  ? pct(disc.squp)  : '—',                                         c: vColor(disc.squp, 35,22)               },
      { k:'BB%',      v: disc.bbpct!=null ? pct(disc.bbpct) : '—',                                         c: vColor(disc.bbpct,12, 7)               },
      { k:'SLG vRHP', v: fmtD(splits.actual_slg_vs_rhp),                                                    c: vColor(splits.actual_slg_vs_rhp,.580,.450) },
      { k:'SLG vLHP', v: fmtD(splits.actual_slg_vs_lhp),                                                    c: vColor(splits.actual_slg_vs_lhp,.580,.450) },
      { k:'PLATOON',  v: splits.handedness_edge_label || '—',                                               c: P.cyan                                  },
      { k:'PULL%',    v: pct(splits.pull),                                                                   c: P.fg2                                   },
    ];

    var COLS = 4, CW = (W - PAD*2) / COLS, RH = 40;
    for (var i = 0; i < STATS.length; i++) {
      statCell(ctx, STATS[i].k, STATS[i].v, STATS[i].c,
               PAD + (i%COLS)*CW, cy + Math.floor(i/COLS)*RH, CW, RH);
    }
    cy += 4 * RH + 8;

    divider(ctx, PAD, W-PAD, cy); cy += 12;

    // ── ARSENAL EDGE INTEL ────────────────────────────────────────
    hdr(ctx, 'ARSENAL EDGE INTEL · PITCHER PITCH-MIX MATCHUP', PAD, cy+9, W); cy += 16;

    var arsLabel = (ars.arsenal_edge_label && ars.arsenal_edge_label !== 'DATA GAP')
                   ? ars.arsenal_edge_label
                   : ((row.arsenal_edge_label && row.arsenal_edge_label !== 'DATA GAP') ? row.arsenal_edge_label : null);
    var arsKey   = ars.arsenal_edge_key_pitch  || row.arsenal_edge_key_pitch  || null;
    var arsScore = ars.arsenal_edge_score      != null ? ars.arsenal_edge_score  : (row.arsenal_edge_score  != null ? row.arsenal_edge_score  : null);
    var arsConf  = ars.arsenal_edge_confidence != null ? ars.arsenal_edge_confidence : (row.arsenal_edge_confidence != null ? row.arsenal_edge_confidence : null);
    var vcColor  = arsLabel==='MISMATCH'||arsLabel==='EXPLOIT' ? P.green
                 : arsLabel==='LEAN'||arsLabel==='FAVORABLE'   ? P.amber : P.fg3;

    var vx = PAD;

    // Verdict pill
    if (arsLabel) {
      ctx.font = '800 9px "Barlow Condensed","Arial Narrow",sans-serif';
      var vpw = ctx.measureText(arsLabel).width + 14;
      ctx.beginPath(); ctx.roundRect(vx, cy, vpw, 18, 4);
      ctx.fillStyle = hexRgba(vcColor, 0.18); ctx.fill();
      ctx.beginPath(); ctx.roundRect(vx, cy, vpw, 18, 4);
      ctx.strokeStyle = hexRgba(vcColor, 0.7); ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle = vcColor; ctx.textAlign = 'left';
      ctx.fillText(arsLabel, vx+7, cy+13);
      vx += vpw + 10;
    }

    if (arsScore != null) {
      ctx.fillStyle = P.fg3; ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif'; ctx.textAlign = 'left';
      ctx.fillText('SCORE', vx, cy+8);
      ctx.fillStyle = vcColor; ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(Number(arsScore).toFixed(1), vx, cy+18);
      vx += 46;
    }
    if (arsConf != null) {
      ctx.fillStyle = P.fg3; ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText('CONF', vx, cy+8);
      ctx.fillStyle = P.fg2; ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(Math.round(Number(arsConf)*100)+'%', vx, cy+18);
      vx += 46;
    }
    if (arsKey) {
      ctx.fillStyle = P.fg3; ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText('KEY PITCH', vx, cy+8);
      ctx.fillStyle = P.cyan; ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(arsKey, vx, cy+18);
    }

    // Pitch mix verdict (right side)
    if (verdict) {
      var vtC = verdict==='DEPLOY'?P.green : verdict==='HUNT'?P.amber : verdict==='AVOID'?P.red : P.fg3;
      ctx.fillStyle = P.fg3; ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif'; ctx.textAlign = 'right';
      ctx.fillText('PITCH MIX VERDICT', W-PAD, cy+8);
      ctx.fillStyle = vtC; ctx.font = '800 13px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(verdict, W-PAD, cy+18);
    }
    cy += 24;

    // Per-pitch rows
    var livePP = ppRows.filter(function(r) { var av=r.availability||{}; return av.pill==='Live'||av.xwoba==='Live'; });
    var hasThin = ppRows.some(function(r) { return r.pill_thin_sample; });

    // Column header row
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    var COL = { type: PAD, bar: PAD+46, xw: W-PAD-72, pill: W-PAD-20 };
    ctx.fillText('PITCH', COL.type, cy+8);
    ctx.fillText('DAMAGE SIGNAL', COL.bar, cy+8);
    ctx.fillText('xwOBA', COL.xw-6, cy+8);
    ctx.fillStyle = P.fg3; ctx.textAlign = 'right';
    ctx.fillText('SIGNAL', W-PAD, cy+8);
    cy += 11;

    if (livePP.length === 0) {
      ctx.fillStyle = P.amber;
      ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('Arsenal detail data unavailable — open batter card to load', PAD, cy+12);
      cy += 18;
    } else {
      livePP.slice(0, 6).forEach(function(pr) {
        var av     = pr.availability || {};
        var pill   = (!pr.pill_thin_sample && av.pill==='Live') ? (pr.pill || 'NEUT') : '—';
        var xw     = (av.xwoba==='Live' && pr.xwoba!=null) ? fmtD(pr.xwoba) : '—';
        var barPct = (!pr.pill_thin_sample && av.damage==='Live') ? Math.min(100, pr.damage||0) : 0;
        var pc     = pillColor(pill);
        var thin   = pr.pill_thin_sample ? ' ⚠' : '';
        var barW   = COL.xw - COL.bar - 10;

        // Pitch label
        ctx.fillStyle = P.fg2;
        ctx.font = '700 9.5px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText((pr.pitch_type || '?')+thin, COL.type, cy+12);

        // Bar track
        ctx.beginPath(); ctx.roundRect(COL.bar, cy+5, barW, 5, 2);
        ctx.fillStyle = 'rgba(180,220,200,0.12)'; ctx.fill();
        if (barPct > 0) {
          ctx.beginPath(); ctx.roundRect(COL.bar, cy+5, barW*barPct/100, 5, 2);
          ctx.fillStyle = pc; ctx.fill();
        }

        // xwOBA
        ctx.fillStyle = P.fg1;
        ctx.font = '600 9.5px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(xw, COL.xw+30, cy+12);

        // Pill signal label
        ctx.fillStyle = pc;
        ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(pill, W-PAD, cy+12);

        cy += 20;
      });
    }

    if (hasThin) {
      ctx.fillStyle = P.amber;
      ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('⚠ thin sample (<10 PA) — treat EXPLOIT/AVOID with caution', PAD, cy+7);
      cy += 12;
    }

    cy += 4;
    divider(ctx, PAD, W-PAD, cy); cy += 12;

    // ── MATCHUP STACK ─────────────────────────────────────────────
    hdr(ctx, 'MATCHUP · ENVIRONMENT · MODEL', PAD, cy+9, W); cy += 16;

    var MATCH = [
      { k:'PITCHER VULN', v: ptch.pitcherVuln||row.pitcherVuln||'—',                                     c: (ptch.pitcherVuln==='TARGET'||row.pitcherVuln==='TARGET') ? P.red : P.fg2 },
      { k:'HR/9',         v: ptch.pitcher_hr9!=null ? Number(ptch.pitcher_hr9).toFixed(2) : '—',          c: vColor(ptch.pitcher_hr9, 2.2, 1.4)                                       },
      { k:'ENV /10',      v: env.hr_environment_0_10!=null ? Number(env.hr_environment_0_10).toFixed(1) : '—', c: vColor(env.hr_environment_0_10, 7, 5)                            },
      { k:'PARK×',        v: env.hrFactor!=null ? Number(env.hrFactor).toFixed(3) : '—',                  c: (env.hrFactor||0)>=1.05 ? P.green : P.fg2                               },
      { k:'PITCH VERDICT',v: verdict || '—',                                                               c: verdict==='DEPLOY'?P.green:verdict==='HUNT'?P.amber:P.fg2               },
      { k:'MODEL PROB',   v: row.model_prob!=null ? (row.model_prob*100).toFixed(1)+'%' : '—',            c: P.green                                                                  },
    ];
    var MW = (W-PAD*2)/MATCH.length;
    MATCH.forEach(function(m, idx) {
      var mx = PAD + idx*MW;
      ctx.fillStyle = P.fg3;
      ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left'; ctx.fillText(m.k, mx, cy+9);
      ctx.fillStyle = m.c;
      ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(m.v, mx, cy+22);
    });
    cy += 32;

    // ── FOOTER ────────────────────────────────────────────────────
    divider(ctx, PAD, W-PAD, H-20, 0.07);
    ctx.fillStyle = P.fg3;
    ctx.font = '600 8px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';  ctx.fillText('HR ENGINE · FULL INTEL CARD', PAD, H-8);
    ctx.textAlign = 'right'; ctx.fillText(new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}), W-PAD, H-8);
  }

  // ── fetch batter-detail for share card ────────────────────────────
  function _fetchDetail(row, cb) {
    var batterId = row.id;
    if (!batterId) { cb(null); return; }
    var key = batterId + ':' + (row.pitcher_id||'') + ':' + (row.game_pk||'');
    if (CARD_CACHE.has(key)) { cb(CARD_CACHE.get(key)); return; }
    var p = new URLSearchParams();
    p.set('batter_id', batterId);
    if (row.pitcher_id) p.set('pitcher_id', row.pitcher_id);
    if (row.game_pk)    p.set('game_pk',    row.game_pk);
    var url = 'https://mlb-hr-api.fly.dev/api/batter-detail?' + p;
    var doFetch = (window.__hrAuth && typeof window.__hrAuth.authFetch === 'function')
      ? function(u) { return window.__hrAuth.authFetch(u); }
      : function(u) { return fetch(u); };
    doFetch(url)
      .then(function(r) { return r.json(); })
      .then(function(d) { CARD_CACHE.set(key, d); cb(d); })
      .catch(function()  { cb(null); });
  }

  // ── render + download ─────────────────────────────────────────────
  function _render(row, detail) {
    var ppRows = (detail && detail.pitch_profile && Array.isArray(detail.pitch_profile.rows))
      ? detail.pitch_profile.rows.filter(function(r) { var av=r.availability||{}; return av.pill==='Live'||av.xwoba==='Live'; })
      : [];
    var hasThin = (detail && detail.pitch_profile && Array.isArray(detail.pitch_profile.rows))
      ? detail.pitch_profile.rows.some(function(r) { return r.pill_thin_sample; }) : false;

    var W = 680;
    // Height: header + stats + arsenal section + matchup + footer
    var pitchH = ppRows.length === 0 ? 18 : Math.min(ppRows.length, 6) * 20;
    var H = 22   // top
          + 62   // header block (badges + name + meta)
          + 18   // divider area
          + 16   // stat section hdr
          + 4*40 // 4 stat rows
          + 18   // divider area
          + 16   // arsenal hdr
          + 24   // verdict row
          + 11   // pitch col headers
          + pitchH
          + (hasThin ? 12 : 0)
          + 18   // divider area
          + 16   // matchup hdr
          + 40   // matchup row
          + 28;  // footer

    var canvas = document.createElement('canvas');
    canvas.width  = W * 2;
    canvas.height = H * 2;
    var ctx = canvas.getContext('2d');
    ctx.scale(2, 2);

    document.fonts.ready.then(function () {
      _draw(ctx, row, detail, W, H);
      canvas.toBlob(function (blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = (row.name || 'player').replace(/\s+/g, '-').toLowerCase() + '-hr-intel.png';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      }, 'image/png');
    });
  }

  window.fsmShareCard = function (row) {
    _fetchDetail(row, function (detail) { _render(row, detail); });
  };
})();
