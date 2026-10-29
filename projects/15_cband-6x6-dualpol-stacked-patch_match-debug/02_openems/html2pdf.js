// usage: node html2pdf.js in.html out.pdf   (uses the preinstalled Playwright Chromium)
const { chromium } = require('playwright');
(async () => {
  const [inp, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + require('path').resolve(inp), { waitUntil: 'load' });
  await p.pdf({ path: out, format: 'A4', printBackground: true,
    margin: { top: '14mm', bottom: '16mm', left: '14mm', right: '14mm' },
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:7px;width:100%;text-align:center;color:#666">C-band 6x6 stacked-patch array: S11 analysis &middot; page <span class="pageNumber"></span> / <span class="totalPages"></span></div>' });
  await b.close();
})();
