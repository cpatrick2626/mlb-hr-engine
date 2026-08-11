// Injects ?v=<timestamp> into every .js script src in index.html.
// Runs as the Vercel build command — never modifies the committed file.
const fs = require('fs');
const v  = Date.now();
let html = fs.readFileSync('index.html', 'utf8');
html = html.replace(
  /(<script[^>]*\ssrc=")([^"]+\.js)(?:\?[^"]*)?"([^>]*>)/g,
  (m, pre, path, rest) => `${pre}${path}?v=${v}"${rest}`
);
fs.writeFileSync('index.html', html);
console.log(`Cache-bust: ?v=${v} injected into index.html`);
