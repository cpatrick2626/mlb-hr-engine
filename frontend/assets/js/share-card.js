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
  var P = {
    void:'#04070a', panel:'#0a1014', cell:'#0d1519',
    fg1:'#f4f8f6', fg2:'#c8d2cf', fg3:'#93a09b',
    green:'#1aff66', red:'#ff3344', cyan:'#00d9ff', amber:'#ffb020'
  };

  var CARD_CACHE = new Map();

  // ── format helpers ─────────────────────────────────────────────────
  function f3d(n) {
    if (n == null) return '—';
    var v = Number(n);
    return v < 1 ? '.' + String(Math.round(v * 1000)).padStart(3, '0') : v.toFixed(3);
  }
  function f1(n)  { return n != null ? Number(n).toFixed(1) : '—'; }
  function f2(n)  { return n != null ? Number(n).toFixed(2) : '—'; }
  function fp1(n) { return n != null ? Number(n).toFixed(1) + '%' : '—'; }

  var PITCH_NAMES = {
    FF:'4-Seam', SI:'Sinker', FC:'Cutter', SL:'Slider', CU:'Curve', CH:'Change',
    FS:'Splitter', KC:'K-Curve', ST:'Sweeper', SV:'Slurve', KN:'Knuckle',
    FO:'Fork', CS:'Slow Curve', FA:'Fastball', EP:'Eephus', SC:'Screwball'
  };
  function pitchName(code) { return PITCH_NAMES[code] || code || '?'; }

  function hexRgba(hex, a) {
    var h = hex.replace('#', '');
    if (h.length === 3) h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2];
    return 'rgba('+parseInt(h.slice(0,2),16)+','+parseInt(h.slice(2,4),16)+','+parseInt(h.slice(4,6),16)+','+a+')';
  }

  function vColor(v, hi, lo) {
    if (v == null) return P.fg2;
    return v >= hi ? P.green : (lo != null && v >= lo ? P.amber : P.fg2);
  }

  // ── canvas primitives ──────────────────────────────────────────────
  function divider(ctx, x1, x2, y, a) {
    ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y);
    ctx.strokeStyle = 'rgba(180,220,200,' + (a || 0.10) + ')';
    ctx.lineWidth = 1; ctx.stroke();
  }

  function fillBar(ctx, x, y, w, h, frac, color) {
    ctx.beginPath(); ctx.roundRect(x, y, w, h, 2);
    ctx.fillStyle = 'rgba(180,220,200,0.10)'; ctx.fill();
    if (frac > 0) {
      ctx.beginPath(); ctx.roundRect(x, y, w * Math.min(1, frac), h, 2);
      ctx.fillStyle = color || P.green; ctx.fill();
    }
  }

  function chip(ctx, k, v, color, x, y, w, h) {
    ctx.beginPath(); ctx.roundRect(x + 1, y + 1, w - 2, h - 2, 3);
    ctx.fillStyle = P.cell; ctx.fill();
    ctx.fillStyle = P.fg3;
    ctx.font = '600 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(k, x + 5, y + 11);
    ctx.fillStyle = color || P.fg1;
    ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText(String(v), x + 5, y + 25);
  }

  function sectionHdr(ctx, label, PAD, cy, W) {
    ctx.fillStyle = P.fg3;
    ctx.font = '700 8px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.letterSpacing = '0.12em';
    ctx.fillText('◈ ' + label, PAD, cy + 9);
    var tw = ctx.measureText('◈ ' + label).width + 8;
    ctx.beginPath(); ctx.moveTo(PAD + tw, cy + 5); ctx.lineTo(W - PAD, cy + 5);
    ctx.strokeStyle = 'rgba(180,220,200,0.14)'; ctx.lineWidth = 1; ctx.stroke();
    ctx.letterSpacing = '0';
    return cy + 16;
  }

  // Draw a small stat block (label top, value bottom) — used for edge stack items
  function statBlock(ctx, k, v, color, x, y, w, h) {
    ctx.beginPath(); ctx.roundRect(x + 1, y + 1, w - 2, h - 2, 3);
    ctx.fillStyle = P.cell; ctx.fill();
    ctx.fillStyle = P.fg3;
    ctx.font = '600 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(k, x + 5, y + 11);
    ctx.fillStyle = color || P.fg2;
    ctx.font = '700 11px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText(String(v), x + 5, y + 25);
  }

  // ── MAIN DRAW (returns actual height used) ──────────────────────────
  function _draw(ctx, row, detail, W, bgH) {
    var PAD = 18;
    var IW  = W - PAD * 2;
    var tier = (row.tier || 'COLD').toUpperCase();
    var tc   = TC[tier] || P.fg3;

    // -- Derive from detail --
    var arsenal      = detail ? (detail.arsenal || []) : [];
    var pitchStats   = detail ? (detail.pitch_stats || {}) : {};
    var bvp          = detail ? (detail.batter_vs_pitches || {}) : {};
    var h2h          = detail && detail.h2h && detail.h2h.pa ? detail.h2h : null;
    var pitcherRecent = detail && Array.isArray(detail.pitcher_recent) ? detail.pitcher_recent : [];
    var batterRecent  = detail && Array.isArray(detail.batter_recent)
                        ? detail.batter_recent.filter(function(g) { return (g.pa || 0) >= 1; })
                        : [];
    var dataYear     = detail ? (detail.data_year || null) : null;
    var isPriorYear  = dataYear != null && dataYear !== new Date().getFullYear();

    var arsorted = arsenal.slice().sort(function(a, b) { return (b.usage || 0) - (a.usage || 0); });
    var bvpRows  = arsorted.filter(function(p) { var b = bvp[p.code]; return b && b.pa > 0; });
    var hasBvp   = bvpRows.length > 0;
    var anyBvpSmall = bvpRows.some(function(p) { return bvp[p.code].pa < 10; });
    var anyArsSmall = arsorted.some(function(p) { var pa = (pitchStats[p.code] || {}).pa; return pa != null && pa < 10; });

    // -- Derived row values --
    var keyPitch    = row.arsenal_edge_key_pitch || null;
    var edgeLabel   = row.arsenal_edge_label || '—';
    var edgeDisp    = ({ WATCH: 'LEAN', 'LIVE EDGE': 'FAVORABLE' })[edgeLabel] || edgeLabel;
    var isGap       = row.arsenal_edge_score == null || edgeLabel === 'DATA GAP';
    var score       = row.arsenal_edge_score;
    var confidence  = row.arsenal_edge_confidence;
    var batterSide  = row.bats || '';
    var pitcherHand = row.pitcher_hand || '';
    var batHand     = batterSide === 'S' ? (pitcherHand === 'L' ? 'R' : 'L') : batterSide;

    var vcColor = (edgeDisp === 'MISMATCH' || edgeDisp === 'EXPLOIT' || edgeDisp === 'FAVORABLE')
                  ? P.green : edgeDisp === 'LEAN' ? P.amber : P.fg3;

    var aeiHr9    = row.pitcher_hr9 != null ? Number(row.pitcher_hr9) : null;
    var aeiPTier  = aeiHr9 != null ? (aeiHr9 >= 1.45 ? 'HITTABLE' : aeiHr9 >= 1.05 ? 'AVERAGE' : 'STINGY') : '—';
    var aeiPTierC = aeiPTier === 'HITTABLE' ? P.green : aeiPTier === 'AVERAGE' ? P.amber : aeiPTier === 'STINGY' ? P.red : P.fg3;

    var h2hPct   = h2h ? (((h2h.hr || 0) / h2h.pa) * 100).toFixed(1) + '%' : '—';
    var h2hTrust = !h2h ? 'NO DATA' : h2h.pa < 10 ? 'VERY LOW' : h2h.pa < 30 ? 'LOW' : 'MODERATE';
    var h2hSigLbl = !h2h ? 'NO DATA' : h2h.pa < 10 ? 'THIN' : (h2h.hr > 0 ? 'PLUS' : 'THIN');
    var h2hSigC  = h2hSigLbl === 'PLUS' ? P.green : P.fg3;

    var exploitLbl = isGap ? '—' : score >= 8 ? 'PRIME' : score >= 6 ? 'PLUS' : score >= 4 ? 'EVEN' : 'FLAT';
    var exploitC   = isGap ? P.fg3 : score >= 6 ? P.green : score >= 4 ? P.amber : P.fg3;

    var barrelBand = (function() {
      var b = row.barrel;
      if (b == null) return { label: '—', color: P.fg3 };
      if (b >= 10) return { label: 'PRIME', color: P.green };
      if (b >= 7)  return { label: 'PLUS',  color: P.green };
      if (b >= 4)  return { label: 'EVEN',  color: P.amber };
      if (b >= 2)  return { label: 'THIN',  color: P.fg3 };
      return { label: 'FLAT', color: P.fg3 };
    })();

    var hhBand = row.hh == null ? { label: '—', color: P.fg3 }
               : row.hh >= 45 ? { label: 'PLUS', color: P.green }
               : row.hh >= 38 ? { label: 'EVEN', color: P.amber }
               : { label: 'THIN', color: P.fg3 };

    var modelTierColor = TC[row.tier] || P.fg3;

    var iso = row.iso != null ? row.iso
            : (row.slg != null && row.avg != null ? +(Number(row.slg) - Number(row.avg)).toFixed(3) : null);

    var pLast = (row.pitcher_name || 'TBD').replace('…', '').split(' ').slice(-1)[0];
    var bLast = (row.name || '').replace('…', '').split(' ').slice(-1)[0];

    // ── BACKGROUND ────────────────────────────────────────────────────
    ctx.fillStyle = P.void;
    ctx.fillRect(0, 0, W, bgH || 6000);
    ctx.fillStyle = tc;
    ctx.fillRect(0, 0, W, 4);

    var cy = 14;

    // ── HEADER ────────────────────────────────────────────────────────
    // Tier badge
    ctx.font = '700 8px "Barlow Condensed","Arial Narrow",sans-serif';
    var tlw = ctx.measureText(tier).width;
    var tbw = tlw + 14;
    ctx.beginPath(); ctx.roundRect(PAD, cy, tbw, 18, 3);
    ctx.fillStyle = hexRgba(tc, 0.18); ctx.fill();
    ctx.beginPath(); ctx.roundRect(PAD, cy, tbw, 18, 3);
    ctx.strokeStyle = hexRgba(tc, 0.7); ctx.lineWidth = 1; ctx.stroke();
    ctx.fillStyle = tc; ctx.textAlign = 'left';
    ctx.fillText(tier, PAD + 7, cy + 12);

    // HR PROB (right)
    var hrProb = row.hrprob != null ? Number(row.hrprob).toFixed(1) + '%' : '—';
    ctx.fillStyle = P.green;
    ctx.font = '800 30px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(hrProb, W - PAD, cy + 28);
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('MODEL HR PROB', W - PAD, cy + 38);

    // EV line
    var evParts = [];
    if (row.edge != null)   evParts.push('EDGE ' + (row.edge >= 0 ? '+' : '') + (row.edge * 100).toFixed(1) + 'pp');
    if (row.ev_pct != null) evParts.push('EV ' + (row.ev_pct >= 0 ? '+' : '') + Number(row.ev_pct).toFixed(1) + '%');
    if (evParts.length) {
      ctx.fillStyle = (row.edge != null && row.edge > 0) ? P.green : P.red;
      ctx.font = '700 8px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(evParts.join(' · '), W - PAD, cy + 49);
    }

    cy += 4;
    ctx.fillStyle = P.fg1;
    ctx.font = '800 22px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText((row.name || '').toUpperCase(), PAD, cy + 24);
    cy += 28;

    var metaParts = [row.teamAbbr, 'BATS ' + (batterSide || '?')];
    if (row.pitcher_name) metaParts.push('vs ' + row.pitcher_name.toUpperCase() + ' (' + (pitcherHand || '?') + 'HP)');
    ctx.fillStyle = P.fg3;
    ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(metaParts.filter(Boolean).join('  ·  '), PAD, cy + 10);
    cy += 18;

    divider(ctx, PAD, W - PAD, cy); cy += 10;

    // ══════════════════════════════════════════════════════════════════
    // PANEL 1 — PITCHER ARSENAL
    // ══════════════════════════════════════════════════════════════════
    cy = sectionHdr(ctx, 'PITCHER ARSENAL', PAD, cy, W);

    // Pitcher identity
    ctx.fillStyle = P.fg1;
    ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText((row.pitcher_name || 'TBD').toUpperCase(), PAD, cy + 13);

    ctx.fillStyle = P.fg3;
    ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
    var hr9Str = aeiHr9 != null ? aeiHr9.toFixed(2) : '—';
    var hr9Line = (pitcherHand || '?') + 'HP  ·  SEASON HR/9: ' + hr9Str + '  ';
    ctx.fillText(hr9Line, PAD, cy + 25);
    var hr9LineW = ctx.measureText(hr9Line).width;
    ctx.fillStyle = aeiPTierC;
    ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText('(' + aeiPTier + ')', PAD + hr9LineW, cy + 25);

    if (isPriorYear) {
      ctx.fillStyle = P.amber;
      ctx.font = '700 8px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText('⚠ ' + dataYear + ' DATA — PRIOR SEASON', PAD, cy + 36);
      cy += 12;
    }
    cy += 34;

    // Pitcher stat chips: ERA WHIP K% BB% BARREL% HH%
    var CH = 34, CW6 = IW / 6;
    var pChips = [
      ['ERA',     row.pitcher_era            != null ? Number(row.pitcher_era).toFixed(2)                  : '—', P.fg1],
      ['WHIP',    row.pitcher_whip           != null ? Number(row.pitcher_whip).toFixed(2)                 : '—', P.fg1],
      ['K%',      row.pitcher_k_pct          != null ? Number(row.pitcher_k_pct).toFixed(1)                : '—', vColor(row.pitcher_k_pct, 27, 20)],
      ['BB%',     row.pitcher_bb_pct         != null ? Number(row.pitcher_bb_pct).toFixed(1)               : '—', P.fg1],
      ['BARREL%', row.pitcher_barrel_allowed != null ? (Number(row.pitcher_barrel_allowed)*100).toFixed(1) : '—', P.fg1],
      ['HH%',     row.pitcher_hh_allowed     != null ? (Number(row.pitcher_hh_allowed)*100).toFixed(1)    : '—', P.fg1],
    ];
    pChips.forEach(function(c, i) { chip(ctx, c[0], c[1], c[2], PAD + i * CW6, cy, CW6, CH); });
    cy += CH + 10;

    // Arsenal table caption
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(pLast.toUpperCase() + ' ARSENAL VS ' + (batHand || '?') + 'HB', PAD, cy + 8);
    cy += 12;

    // Arsenal table column widths (sum must ≤ IW)
    // PITCH | USAGE (bar+%) | VELO | WHIFF% | HR/PA | K% | HH% | PA
    var AC = [88, 140, 62, 68, 68, 58, 58, 44]; // 588 total, IW≈724 — some right margin is fine

    // Column headers
    var AH = ['PITCH', 'USAGE', 'VELO', 'WHIFF%', 'HR/PA', 'K%', 'HH%', 'PA'];
    ctx.fillStyle = P.fg3;
    ctx.font = '600 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
    var axOff = PAD;
    AH.forEach(function(h, i) {
      ctx.textAlign = i === 0 ? 'left' : 'right';
      ctx.fillText(h, axOff + (i === 0 ? 0 : AC[i]), cy + 7);
      axOff += AC[i];
    });
    cy += 10;
    divider(ctx, PAD, PAD + AC.reduce(function(s,v){return s+v;},0), cy, 0.07);
    cy += 3;

    if (arsorted.length === 0) {
      ctx.fillStyle = P.amber;
      ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('No arsenal data available', PAD, cy + 12);
      cy += 18;
    } else {
      arsorted.forEach(function(p) {
        var ps     = pitchStats[p.code] || {};
        var isKey  = p.code === keyPitch;
        var velo   = p.velo != null ? Number(p.velo).toFixed(0)
                   : ps.avg_speed != null ? Number(ps.avg_speed).toFixed(0) : '—';
        var whiff  = p.whiff != null ? Number(p.whiff).toFixed(0) + '%' : '—';
        var hrPa   = ps.hr_rate != null ? (Number(ps.hr_rate)*100).toFixed(1) + '%'
                   : (ps.hr != null && ps.pa != null && ps.pa >= 10) ? (ps.hr/ps.pa*100).toFixed(1) + '%' : '—';
        var kPct   = ps.k_pct   != null ? (Number(ps.k_pct)*100).toFixed(0) + '%' : '—';
        var hhPct  = ps.display_hh != null ? (Number(ps.display_hh)*100).toFixed(0) + '%' : '—';
        var paVal  = ps.pa != null ? ps.pa : null;
        var paSmall = paVal != null && paVal < 10;
        var usage  = p.usage != null ? Number(p.usage) : 0;

        if (isKey) {
          ctx.beginPath(); ctx.roundRect(PAD, cy, IW, 18, 2);
          ctx.fillStyle = hexRgba(P.cyan, 0.08); ctx.fill();
        }

        var ax = PAD;

        // PITCH col
        ctx.textAlign = 'left';
        ctx.fillStyle = isKey ? P.cyan : P.fg2;
        ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.fillText(p.code, ax, cy + 12);
        if (isKey) {
          ctx.fillStyle = P.cyan;
          ctx.font = '700 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
          ctx.fillText('HUNT', ax + 26, cy + 8);
          ctx.fillText('THIS', ax + 26, cy + 15);
        }
        ax += AC[0];

        // USAGE bar + label
        var barW = AC[1] - 32;
        fillBar(ctx, ax, cy + 7, barW, 4, usage / 100, isKey ? P.cyan : P.fg3);
        ctx.fillStyle = P.fg2;
        ctx.font = '600 8.5px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(usage > 0 ? usage.toFixed(0) + '%' : '—', ax + AC[1] - 2, cy + 13);
        ax += AC[1];

        // Numeric cols
        var numVals = [
          [velo,  P.fg2],
          [whiff, P.fg2],
          [hrPa,  hrPa !== '—' && parseFloat(hrPa) >= 3 ? P.green : P.fg2],
          [kPct,  P.fg2],
          [hhPct, P.fg2],
          [paVal != null ? String(paVal) + (paSmall ? '*' : '') : '—', paSmall ? P.amber : P.fg3],
        ];
        numVals.forEach(function(item, vi) {
          ctx.fillStyle = item[1];
          ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(item[0], ax + AC[vi + 2], cy + 12);
          ax += AC[vi + 2];
        });

        cy += 19;
      });
    }

    if (anyArsSmall) {
      ctx.fillStyle = P.amber;
      ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('* <10 PA — small sample, treat with caution', PAD, cy + 7);
      cy += 12;
    }

    cy += 8;
    divider(ctx, PAD, W - PAD, cy); cy += 10;

    // ══════════════════════════════════════════════════════════════════
    // PANEL 2 — ARSENAL EDGE VERDICT
    // ══════════════════════════════════════════════════════════════════
    cy = sectionHdr(ctx, 'ARSENAL EDGE VERDICT', PAD, cy, W);

    // Arsenal edge pill + score + confidence + key pitch
    ctx.font = '800 9px "Barlow Condensed","Arial Narrow",sans-serif';
    var pillLabel = 'ARSENAL EDGE: ' + edgeDisp;
    var pillW = ctx.measureText(pillLabel).width + 16;
    ctx.beginPath(); ctx.roundRect(PAD, cy, pillW, 20, 3);
    ctx.fillStyle = hexRgba(vcColor, 0.15); ctx.fill();
    ctx.beginPath(); ctx.roundRect(PAD, cy, pillW, 20, 3);
    ctx.strokeStyle = hexRgba(vcColor, 0.6); ctx.lineWidth = 1; ctx.stroke();
    // label text
    ctx.textAlign = 'left';
    ctx.fillStyle = P.fg3;
    var aePrefix = 'ARSENAL EDGE: ';
    var aePrefixW = ctx.measureText(aePrefix).width;
    ctx.fillText(aePrefix, PAD + 8, cy + 14);
    ctx.fillStyle = vcColor;
    ctx.fillText(edgeDisp, PAD + 8 + aePrefixW, cy + 14);

    // score / confidence / key pitch
    var ex = PAD + pillW + 14;
    var miniItems = [
      ['EDGE SCORE',  isGap ? '—' : Number(score).toFixed(1),                          vcColor],
      ['CONFIDENCE',  confidence != null ? Math.round(Number(confidence)*100) + '%' : '—', P.fg2],
      ['KEY PITCH',   keyPitch ? pitchName(keyPitch) : '—',                             P.cyan],
    ];
    miniItems.forEach(function(item) {
      ctx.fillStyle = P.fg3;
      ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(item[0], ex, cy + 7);
      ctx.fillStyle = item[2];
      ctx.font = '700 12px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(item[1], ex, cy + 19);
      ex += 78;
    });
    cy += 26;

    // ── H2H HR SIGNAL ──
    ctx.fillStyle = P.fg3;
    ctx.font = '700 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.letterSpacing = '0.1em';
    ctx.fillText('H2H HR SIGNAL', PAD, cy + 9);
    ctx.letterSpacing = '0';

    ctx.fillStyle = h2h ? P.green : P.fg3;
    ctx.font = '800 22px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(h2hPct, W - PAD, cy + 14);
    cy += 16;

    fillBar(ctx, PAD, cy, IW, 5, h2h && h2h.pa > 0 ? Math.min(1, ((h2h.hr || 0) / h2h.pa) * 4) : 0.01, P.green);
    cy += 9;

    // H2H stats row
    var h2hStats = [
      ['PA',  h2h ? h2h.pa : '—'],
      ['HR',  h2h ? (h2h.hr || 0) : '—'],
      ['BA',  h2h ? (h2h.avg || '—') : '—'],
      ['SLG', h2h ? (h2h.slg || '—') : '—'],
      ['OPS', h2h ? (h2h.ops || '—') : '—'],
    ];
    var hcw = IW / h2hStats.length;
    h2hStats.forEach(function(item, i) {
      var hx = PAD + i * hcw;
      ctx.beginPath(); ctx.roundRect(hx + 1, cy + 1, hcw - 2, 27, 2);
      ctx.fillStyle = P.cell; ctx.fill();
      ctx.fillStyle = P.fg3;
      ctx.font = '600 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(item[0], hx + 4, cy + 11);
      ctx.fillStyle = P.fg1;
      ctx.font = '700 12px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.fillText(String(item[1]), hx + 4, cy + 24);
    });
    cy += 31;

    ctx.fillStyle = P.fg3;
    ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(h2h ? h2h.pa + ' PA' + (h2h.pa < 10 ? ' — NOT PREDICTIVE' : '') : 'NO CAREER H2H ON RECORD', PAD, cy + 8);
    ctx.textAlign = 'right';
    ctx.fillText(h2hTrust, W - PAD, cy + 8);
    cy += 14;

    divider(ctx, PAD, W - PAD, cy, 0.07); cy += 8;

    // ── OVERALL EXPLOIT CONFIDENCE ──
    ctx.fillStyle = P.fg3;
    ctx.font = '700 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.letterSpacing = '0.1em';
    ctx.fillText('OVERALL EXPLOIT CONFIDENCE', PAD, cy + 8);
    ctx.letterSpacing = '0';
    ctx.fillStyle = P.green;
    ctx.font = '700 18px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(confidence != null ? Math.round(Number(confidence)*100) + '%' : '—', W - PAD, cy + 12);
    cy += 15;
    fillBar(ctx, PAD, cy, IW, 4, confidence != null ? Math.min(1, Number(confidence)) : 0, P.green);
    cy += 10;

    divider(ctx, PAD, W - PAD, cy, 0.07); cy += 8;

    // ── MODEL HR PROB ──
    ctx.fillStyle = P.fg3;
    ctx.font = '700 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.letterSpacing = '0.1em';
    ctx.fillText('MODEL HR PROB', PAD, cy + 8);
    ctx.letterSpacing = '0';
    ctx.fillStyle = P.green;
    ctx.font = '700 18px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(row.hrprob != null ? Number(row.hrprob).toFixed(1) + '%' : '—', W - PAD, cy + 12);
    cy += 16;
    fillBar(ctx, PAD, cy, IW, 4, row.hrprob != null ? Math.min(1, Number(row.hrprob) / 30) : 0, P.green);
    cy += 8;
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('KEY PITCH: ' + (keyPitch ? pitchName(keyPitch) : '—') + '  ·  HR ODDS: ' + (row.odds || '—'), PAD, cy + 8);
    cy += 14;

    divider(ctx, PAD, W - PAD, cy, 0.07); cy += 8;

    // ── EDGE STACK ──
    ctx.fillStyle = P.fg3;
    ctx.font = '700 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.letterSpacing = '0.1em';
    ctx.fillText('EDGE STACK', PAD, cy + 8);
    ctx.letterSpacing = '0';
    cy += 12;

    var stackItems = [
      ['H2H',          h2hSigLbl,        h2hSigC],
      ['PITCH EXPLOIT', exploitLbl,       exploitC],
      ['BARREL PATH',  barrelBand.label, barrelBand.color],
      ['HH POWER',     hhBand.label,     hhBand.color],
      ['MODEL TIER',   row.tier || '—',  modelTierColor],
    ];
    var sw = IW / stackItems.length;
    stackItems.forEach(function(item, i) {
      statBlock(ctx, item[0], item[1], item[2], PAD + i * sw, cy, sw, 34);
    });
    cy += 40;

    divider(ctx, PAD, W - PAD, cy); cy += 10;

    // ══════════════════════════════════════════════════════════════════
    // PANEL 3 — BATTER DAMAGE PROFILE
    // ══════════════════════════════════════════════════════════════════
    cy = sectionHdr(ctx, 'BATTER DAMAGE PROFILE', PAD, cy, W);

    // Batter identity
    ctx.fillStyle = P.fg1;
    ctx.font = '700 13px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText((row.name || '').toUpperCase(), PAD, cy + 13);

    var bmeta = 'BATS ' + (batterSide || '?') + '  ·  ' + (row.teamAbbr || '');
    ctx.fillStyle = P.fg3;
    ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText(bmeta + '  ·  THREAT TIER: ', PAD, cy + 25);
    var bmetaW = ctx.measureText(bmeta + '  ·  THREAT TIER: ').width;
    ctx.fillStyle = tc;
    ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.fillText(tier, PAD + bmetaW, cy + 25);
    cy += 34;

    // Batter stat chips: AVG xISO HR K% BARREL% EV xwOBA
    var CW7 = IW / 7;
    var bChips = [
      ['AVG',     f3d(row.avg),                                  P.fg1],
      ['xISO',    f3d(iso),                                      vColor(iso, 0.28, 0.20)],
      ['HR',      row.hr != null ? String(row.hr) : '—',        P.fg1],
      ['K%',      row.kpct != null ? f1(row.kpct) : '—',       P.fg1],
      ['BARREL%', row.barrel != null ? f1(row.barrel) : '—',   vColor(row.barrel, 10, 6)],
      ['EV',      row.ev != null ? f1(row.ev) : '—',            vColor(row.ev, 93, 88)],
      ['xwOBA',   f3d(row.xwoba),                                vColor(row.xwoba, 0.40, 0.32)],
    ];
    bChips.forEach(function(c, i) { chip(ctx, c[0], c[1], c[2], PAD + i * CW7, cy, CW7, CH); });
    cy += CH + 10;

    // BvP table caption
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(bLast.toUpperCase() + ' VS ' + (pitcherHand || '?') + 'HP — BY PITCH TYPE', PAD, cy + 8);
    cy += 12;

    // BvP column widths: PITCH | PA | BA | SLG | ISO | HR | HR% | K%
    var BC = [90, 38, 48, 48, 48, 34, 44, 40]; // 390 — narrower so small canvas doesn't crowd

    var BH = ['PITCH', 'PA', 'BA', 'SLG', 'ISO', 'HR', 'HR%', 'K%'];
    ctx.fillStyle = P.fg3;
    ctx.font = '600 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
    var bxOff = PAD;
    BH.forEach(function(h, i) {
      ctx.textAlign = i === 0 ? 'left' : 'right';
      ctx.fillText(h, bxOff + (i === 0 ? 0 : BC[i]), cy + 7);
      bxOff += BC[i];
    });
    cy += 10;
    divider(ctx, PAD, PAD + BC.reduce(function(s,v){return s+v;},0), cy, 0.07);
    cy += 3;

    if (!hasBvp) {
      ctx.fillStyle = P.fg3;
      ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('No pitch-type data on record', PAD, cy + 12);
      cy += 18;
    } else {
      bvpRows.forEach(function(p) {
        var b      = bvp[p.code];
        var isKey  = p.code === keyPitch;
        var small  = b.pa < 10;
        var ba     = b.ba  != null ? Number(b.ba)  : null;
        var slg    = b.slg != null ? Number(b.slg) : null;
        var biso   = (ba != null && slg != null) ? +(slg - ba) : null;
        var kpctV  = b.k_pct != null ? Number(b.k_pct) * 100 : null;
        var hrPctV = (b.hr != null && b.pa >= 10) ? (b.hr / b.pa * 100) : null;

        function hc(v, hi, lo) { return v == null ? P.fg2 : v >= hi ? P.green : v >= lo ? P.amber : P.fg2; }

        if (isKey) {
          ctx.beginPath(); ctx.roundRect(PAD, cy, IW, 18, 2);
          ctx.fillStyle = hexRgba(P.cyan, 0.08); ctx.fill();
        }

        var bx = PAD;

        // PITCH
        ctx.textAlign = 'left';
        ctx.fillStyle = isKey ? P.cyan : (small ? P.fg3 : P.fg2);
        ctx.font = '700 9px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.fillText(pitchName(p.code) + (small ? ' ·' : ''), bx, cy + 12);
        bx += BC[0];

        var bvpVals = [
          [b.pa  != null ? String(b.pa) + (small ? '*' : '') : '—', small ? P.amber : P.fg2],
          [ba    != null ? ba.toFixed(3)                           : '—', hc(ba,  0.320, 0.275)],
          [slg   != null ? slg.toFixed(3)                          : '—', hc(slg, 0.520, 0.430)],
          [biso  != null ? biso.toFixed(3)                         : '—', hc(biso, 0.250, 0.200)],
          [b.hr  != null ? String(b.hr)                            : '—', (b.hr || 0) > 0 ? P.green : P.fg2],
          [hrPctV != null ? hrPctV.toFixed(1) + '%'                : '—', hc(hrPctV, 8, 5)],
          [kpctV  != null ? kpctV.toFixed(0) + '%'                 : '—', P.fg2],
        ];
        bvpVals.forEach(function(item, vi) {
          ctx.fillStyle = item[1];
          ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(item[0], bx + BC[vi + 1], cy + 12);
          bx += BC[vi + 1];
        });

        cy += 19;
      });
    }

    if (anyBvpSmall) {
      ctx.fillStyle = P.amber;
      ctx.font = '600 7px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('· <10 PA — small sample, treat with caution', PAD, cy + 7);
      cy += 12;
    }

    cy += 8;
    divider(ctx, PAD, W - PAD, cy); cy += 10;

    // ══════════════════════════════════════════════════════════════════
    // RECENT FORM
    // ══════════════════════════════════════════════════════════════════
    cy = sectionHdr(ctx, 'RECENT FORM', PAD, cy, W);

    var halfW  = Math.floor((IW - 10) / 2);
    var leftX  = PAD;
    var rightX = PAD + halfW + 10;

    // Sub-captions
    ctx.fillStyle = P.fg3;
    ctx.font = '700 7px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.letterSpacing = '0.08em';
    ctx.textAlign = 'left';
    ctx.fillText('LAST 5 STARTS — ' + (row.pitcher_name || 'PITCHER').toUpperCase(), leftX,  cy + 8);
    ctx.fillText('LAST 5 APPEARANCES — ' + (row.name || 'BATTER').toUpperCase(),       rightX, cy + 8);
    ctx.letterSpacing = '0';
    cy += 12;

    // Pitcher table: DATE | HR | K | IP | BB
    var P5W = [halfW - 28*4, 28, 28, 28, 28];
    var P5H = ['DATE', 'HR', 'K', 'IP', 'BB'];
    // Batter table: DATE | HR | AVG | SLG | PA
    var B5W = [halfW - 34*4, 34, 34, 34, 28];
    var B5H = ['DATE', 'HR', 'AVG', 'SLG', 'PA'];

    function drawTblHdr(x, heads, widths) {
      ctx.fillStyle = P.fg3;
      ctx.font = '600 6.5px "Barlow Condensed","Arial Narrow",sans-serif';
      var cx = x;
      heads.forEach(function(h, i) {
        ctx.textAlign = i === 0 ? 'left' : 'right';
        ctx.fillText(h, cx + (i === 0 ? 0 : widths[i]), cy + 7);
        cx += widths[i];
      });
    }
    drawTblHdr(leftX,  P5H, P5W);
    drawTblHdr(rightX, B5H, B5W);
    cy += 10;
    divider(ctx, leftX,  leftX  + halfW, cy, 0.07);
    divider(ctx, rightX, rightX + halfW, cy, 0.07);
    cy += 3;

    var maxRows = Math.max(pitcherRecent.length, batterRecent.length, 1);
    for (var ri = 0; ri < Math.min(maxRows, 5); ri++) {
      var ps5 = pitcherRecent[ri];
      var bs5 = batterRecent[ri];

      // Pitcher row
      if (ps5) {
        var pcx = leftX;
        ctx.fillStyle = P.fg2;
        ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(ps5.date || '—', pcx, cy + 12);
        pcx += P5W[0];
        var pVals = [
          [ps5.hr != null ? String(ps5.hr) : '—', (ps5.hr || 0) >= 2 ? P.green : (ps5.hr || 0) >= 1 ? P.amber : P.fg2],
          [ps5.k  != null ? String(ps5.k)  : '—', P.fg2],
          [ps5.ip != null && Number.isFinite(Number(ps5.ip)) ? Number(ps5.ip).toFixed(1) : '—', P.fg2],
          [ps5.bb != null ? String(ps5.bb) : '—', P.fg2],
        ];
        pVals.forEach(function(v, vi) {
          ctx.fillStyle = v[1];
          ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(v[0], pcx + P5W[vi + 1], cy + 12);
          pcx += P5W[vi + 1];
        });
      }

      // Batter row
      if (bs5) {
        var bcx = rightX;
        ctx.fillStyle = P.fg2;
        ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(bs5.date || '—', bcx, cy + 12);
        bcx += B5W[0];
        var bVals = [
          [bs5.hr  != null ? String(bs5.hr) : '—', (bs5.hr || 0) >= 1 ? P.green : P.fg2],
          [bs5.avg != null ? Number(bs5.avg).toFixed(3) : '—', bs5.avg != null && Number(bs5.avg) >= 0.280 ? P.green : P.fg2],
          [bs5.slg != null ? Number(bs5.slg).toFixed(3) : '—', bs5.slg != null && Number(bs5.slg) >= 0.450 ? P.green : P.fg2],
          [bs5.pa  != null ? String(bs5.pa)  : '—', P.fg2],
        ];
        bVals.forEach(function(v, vi) {
          ctx.fillStyle = v[1];
          ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(v[0], bcx + B5W[vi + 1], cy + 12);
          bcx += B5W[vi + 1];
        });
      }

      cy += 19;
    }

    if (pitcherRecent.length === 0 && batterRecent.length === 0) {
      ctx.fillStyle = P.fg3;
      ctx.font = '600 9px "Barlow Condensed","Arial Narrow",sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('No recent game data available', leftX, cy + 12);
      cy += 18;
    }

    cy += 8;
    divider(ctx, PAD, W - PAD, cy, 0.07); cy += 2;

    // ── FOOTER ────────────────────────────────────────────────────────
    ctx.fillStyle = P.fg3;
    ctx.font = '600 7.5px "Barlow Condensed","Arial Narrow",sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('HR ENGINE · ARSENAL EDGE INTEL · FULL INTEL CARD', PAD, cy + 10);
    ctx.textAlign = 'right';
    ctx.fillText(new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }), W - PAD, cy + 10);
    cy += 18;

    return cy;
  }

  // ── fetch pitcher-detail (same endpoint as AEI modal) ──────────────
  function _fetchDetail(row, cb) {
    var pitcherId  = row.pitcher_id;
    var batterId   = row.id;
    var batterSide = row.bats || '';
    var pitcherHand = row.pitcher_hand || '';
    if (!pitcherId) { cb(null); return; }
    var key = pitcherId + ':' + batterId + ':' + batterSide;
    if (CARD_CACHE.has(key)) { cb(CARD_CACHE.get(key)); return; }
    var url = 'https://mlb-hr-api.fly.dev/api/pitcher-detail'
            + '?pitcher_id='   + encodeURIComponent(pitcherId)
            + '&batter_id='    + encodeURIComponent(batterId || 0)
            + '&batter_side='  + encodeURIComponent(batterSide)
            + '&pitcher_hand=' + encodeURIComponent(pitcherHand);
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
    var W = 760;

    // Measure pass — draw to throwaway canvas to get actual height
    var mc = document.createElement('canvas');
    mc.width = W * 2; mc.height = 6000;
    var mCtx = mc.getContext('2d');
    mCtx.scale(2, 2);
    var H = _draw(mCtx, row, detail, W, 6000) + 14;

    // Real pass — exact canvas height
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
