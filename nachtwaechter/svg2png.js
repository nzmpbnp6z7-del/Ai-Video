// Rendert SVG-Dateien mit Chromium (Playwright) zu transparenten PNGs.
// Aufruf: node svg2png.js jobs.json   (jobs: [{svg, png, w, h}, ...])
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  for (const j of jobs) {
    await page.setViewportSize({ width: j.w, height: j.h });
    const svg = fs.readFileSync(j.svg, 'utf8');
    await page.setContent(
      `<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await page.screenshot({ path: j.png, omitBackground: true,
      clip: { x: 0, y: 0, width: j.w, height: j.h } });
  }
  await browser.close();
})();
