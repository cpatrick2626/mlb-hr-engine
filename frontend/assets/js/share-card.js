(function () {
  // Polyfill for browsers without native roundRect (pre-Chrome 99)
  if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
      r = Math.min(r, w / 2, h / 2);
      this.moveTo(x + r, y);
      this.lineTo(x + w - r, y);
      this.arcTo(x + w, y, x + w, y + r, r);
      this.lineTo(x + w, y + h - r);
      this.arcTo(x + w, y + h, x + w - r, y + h, r);
      this.lineTo(x + r, y + h);
      this.arcTo(x, y + h, x, y + h - r, r);
      this.lineTo(x, y + r);
      this.arcTo(x, y, x + r, y, r);
      this.closePath();
    };
  }

  var TIER_COLORS = {
    APEX:   '#ff3344',
    ELITE:  '#ff8a93',
    EDGE:   '#1aff66',
    SIGNAL: '#3b6fff',
    WATCH:  '#ffb020',
    COLD:   '#6b7872',
  };

  function _draw(ctx, row, W, H) {
    var tier = (row.tier || 'COLD').toUpperCase();
    var tc   = TIER_COLORS[tier] || '#6b7872';

    // --- background void ---
    ctx.fillStyle = '#04070a';
    ctx.fillRect(0, 0, W, H);

    // --- tier color strip at top ---
    ctx.fillStyle = tc;
    ctx.fillRect(0, 0, W, 4);

    // --- inner card panel ---
    ctx.beginPath();
    ctx.roundRect(12, 14, W - 24, H - 26, 6);
    ctx.fillStyle = '#0a1014';
    ctx.fill();

    // --- tier badge pill (top-left) ---
    ctx.beginPath();
    ctx.roundRect(20, 24, 86, 24, 4);
    ctx.fillStyle = tc + '28';
    ctx.fill();
    ctx.beginPath();
    ctx.roundRect(20, 24, 86, 24, 4);
    ctx.strokeStyle = tc + 'aa';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = tc;
    ctx.font = '700 13px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(tier, 32, 40);

    // --- HR PROB hero (top-right) ---
    var hrProb = row.hrprob != null ? row.hrprob.toFixed(1) + '%' : '—';
    ctx.fillStyle = '#1aff66';
    ctx.font = '800 40px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(hrProb, W - 18, 54);
    ctx.fillStyle = '#4a6660';
    ctx.font = '600 9px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.fillText('HR PROB', W - 18, 66);

    // --- player name ---
    ctx.fillStyle = '#f1f5f3';
    ctx.font = '800 26px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText((row.name || '').toUpperCase(), 20, 74);

    // --- team · vs pitcher meta ---
    var metaParts = [row.teamAbbr || null, row.pitcher_name ? 'vs ' + row.pitcher_name : null].filter(Boolean);
    ctx.fillStyle = '#6a8078';
    ctx.font = '600 11px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.fillText(metaParts.join(' · ').toUpperCase(), 20, 90);

    // --- divider ---
    ctx.beginPath();
    ctx.moveTo(20, 102); ctx.lineTo(W - 20, 102);
    ctx.strokeStyle = 'rgba(180,220,200,0.10)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // --- stats grid: 4 columns ---
    var stats = [
      { k: 'BARREL%',    v: row.barrel    != null ? row.barrel.toFixed(1) + '%'             : '—', c: '#1aff66' },
      { k: 'HARD HIT%',  v: row.hh        != null ? row.hh.toFixed(1) + '%'                 : '—', c: '#1aff66' },
      { k: 'xSLG',       v: row.xslg      != null ? row.xslg.toFixed(3)                     : '—', c: '#00d9ff' },
      { k: 'MODEL PROB', v: row.model_prob != null ? (row.model_prob * 100).toFixed(1) + '%' : '—', c: '#1aff66' },
    ];
    var colW = (W - 40) / stats.length;
    stats.forEach(function (s, i) {
      var x = 20 + i * colW;
      ctx.fillStyle = '#4a6660';
      ctx.font = '600 8px "Barlow Condensed", "Arial Narrow", sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(s.k, x + 6, 118);
      ctx.fillStyle = s.c;
      ctx.font = '700 20px "Barlow Condensed", "Arial Narrow", sans-serif';
      ctx.fillText(s.v, x + 6, 136);
    });

    // --- divider ---
    ctx.beginPath();
    ctx.moveTo(20, 150); ctx.lineTo(W - 20, 150);
    ctx.strokeStyle = 'rgba(180,220,200,0.10)';
    ctx.stroke();

    // --- arsenal edge row ---
    var edgeLabel = (row.arsenal_edge_label && row.arsenal_edge_label !== 'DATA GAP')
      ? row.arsenal_edge_label : null;
    var keyPitch  = row.arsenal_edge_key_pitch || null;
    var edgeStr   = [edgeLabel, keyPitch].filter(Boolean).join(' · ') || '—';

    ctx.fillStyle = '#4a6660';
    ctx.font = '600 8px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('ARSENAL EDGE', 20, 166);

    ctx.fillStyle = '#00d9ff';
    ctx.font = '700 15px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.fillText(edgeStr.toUpperCase().slice(0, 64), 20, 182);

    // --- EV / Edge (right) if line posted ---
    var evParts = [];
    if (row.edge   != null) evParts.push('EDGE ' + (row.edge   >= 0 ? '+' : '') + (row.edge * 100).toFixed(1) + 'pp');
    if (row.ev_pct != null) evParts.push('EV '   + (row.ev_pct >= 0 ? '+' : '') + row.ev_pct.toFixed(1) + '%');
    if (evParts.length) {
      ctx.fillStyle = (row.edge != null && row.edge > 0) ? '#1aff66' : '#ff3344';
      ctx.font = '700 12px "Barlow Condensed", "Arial Narrow", sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(evParts.join(' · '), W - 20, 182);
    }

    // --- footer ---
    ctx.beginPath();
    ctx.moveTo(20, H - 28); ctx.lineTo(W - 20, H - 28);
    ctx.strokeStyle = 'rgba(180,220,200,0.07)';
    ctx.stroke();

    ctx.fillStyle = '#2a3a36';
    ctx.font = '600 9px "Barlow Condensed", "Arial Narrow", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('HR ENGINE', 20, H - 14);
    ctx.textAlign = 'right';
    ctx.fillText(
      new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      W - 20, H - 14
    );
  }

  window.fsmShareCard = function (row) {
    var W = 600, H = 220;
    var canvas = document.createElement('canvas');
    canvas.width  = W * 2;  // 2× for retina
    canvas.height = H * 2;
    var ctx = canvas.getContext('2d');
    ctx.scale(2, 2);

    document.fonts.ready.then(function () {
      _draw(ctx, row, W, H);
      canvas.toBlob(function (blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = (row.name || 'player').replace(/\s+/g, '-').toLowerCase() + '-hr-card.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      }, 'image/png');
    });
  };
})();
