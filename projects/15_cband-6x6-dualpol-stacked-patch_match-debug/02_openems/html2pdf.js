// usage: node html2pdf.js in.html out.pdf [footer text]   (uses the preinstalled Playwright Chromium)
let pw;
try { pw = require('playwright'); } catch (e) {   // fall back to a global npm install
  const root = require('child_process').execSync('npm root -g').toString().trim();
  pw = require(require('path').join(root, 'playwright'));
}
const { chromium } = pw;
(async () => {
  const [inp, out, foot] = process.argv.slice(2);
  const label = foot || 'C-band 6x6 stacked-patch array: S11 analysis';
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + require('path').resolve(inp), { waitUntil: 'load' });
  await p.pdf({ path: out, format: 'A4', printBackground: true,
    margin: { top: '14mm', bottom: '16mm', left: '14mm', right: '14mm' },
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:7px;width:100%;text-align:center;color:#666">' + label + ' &middot; page <span class="pageNumber"></span> / <span class="totalPages"></span></div>' });
  await b.close();
})();
