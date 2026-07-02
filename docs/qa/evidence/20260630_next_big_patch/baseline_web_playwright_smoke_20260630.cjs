const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const base = 'http://127.0.0.1:8123/index.html';
const outDir = process.env.MTR_SCREEN_DIR;
const logs = [];
const markers = [
  'MTR_PLAYER_SKIN_SAFE_FALLBACK',
  'MTR_PLAYER_SKIN_SAFE_FALLBACK_MISSING',
  'MTR_LEGACY_PLAYER_EQUIPMENT_OVERLAY_SUPPRESSED',
  'themed_platform_missing',
  'latest_themed_platform_asset_pending',
  'asset missing',
  'WebGL context lost',
  'MTR_GAMEPLAY_START_GATE_WAIT',
  'MTR_POSE_MISSING',
];
async function waitFrame(page, ms = 9000) { await page.waitForTimeout(ms); }
async function snap(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  return file;
}
async function setupPage(browser, url) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  page.on('console', msg => logs.push({ type: msg.type(), text: msg.text(), url }));
  page.on('pageerror', err => logs.push({ type: 'pageerror', text: err.message, url }));
  await page.goto(url, { waitUntil: 'load', timeout: 60000 });
  return page;
}
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  let page = await setupPage(browser, base);
  await waitFrame(page, 15000);
  results.push({ name: 'main_menu', screenshot: await snap(page, 'ui_01_main_menu') });
  await page.mouse.click(429, 282);
  await waitFrame(page, 6000);
  results.push({ name: 'start_name_submenu', screenshot: await snap(page, 'ui_02_start_name_submenu') });
  await page.mouse.click(640, 434);
  await waitFrame(page, 3000);
  results.push({ name: 'enter_name_button_after_click', screenshot: await snap(page, 'ui_03_enter_name_after_click') });
  await page.close();
  const uiStates = [ ['achievements', `${base}?mtr_dev=1&mtr_state=achievements`] ];
  for (const [name, url] of uiStates) {
    page = await setupPage(browser, url);
    await waitFrame(page, 9000);
    results.push({ name, screenshot: await snap(page, `ui_state_${name}`) });
    await page.close();
  }
  for (let level = 1; level <= 15; level++) {
    const url = `${base}?mtr_dev=1&mtr_autostart=1&mtr_level=${level}&mtr_qa_bonuses=1`;
    page = await setupPage(browser, url);
    await waitFrame(page, 12000);
    results.push({ name: `level_${level}`, screenshot: await snap(page, `level_${String(level).padStart(2,'0')}_baseline_autostart`) });
    await page.close();
  }
  await browser.close();
  const flagged = logs.filter(l => markers.some(m => l.text.includes(m)) || l.type === 'error' || l.type === 'pageerror');
  const report = { generatedAt: new Date().toISOString(), base, resultCount: results.length, results, logCount: logs.length, flaggedCount: flagged.length, flagged, logs: logs.slice(-2500) };
  fs.writeFileSync(path.join(outDir, '..', 'baseline_web_playwright_smoke_20260630.json'), JSON.stringify(report, null, 2), 'utf8');
  console.log(JSON.stringify({ resultCount: results.length, logCount: logs.length, flaggedCount: flagged.length, outDir }, null, 2));
})().catch(err => { console.error(err); process.exit(1); });
