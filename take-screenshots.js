const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

  const BASE_URL = 'http://localhost:3000';
  console.log('Mache Screenshots...');

  try {
    // Login-Seite
    await page.goto(`${BASE_URL}/login`, { timeout: 15000, waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/01-login.png', fullPage: false });
    console.log('✓ Login-Seite');

    // Dashboard
    await page.goto(`${BASE_URL}/`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/02-dashboard.png', fullPage: false });
    console.log('✓ Dashboard');

    // Teams
    await page.goto(`${BASE_URL}/teams`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/03-teams.png', fullPage: false });
    console.log('✓ Teams');

    // Spieler
    await page.goto(`${BASE_URL}/players`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/04-players.png', fullPage: false });
    console.log('✓ Spieler');

    // Spiele
    await page.goto(`${BASE_URL}/games`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/05-games.png', fullPage: false });
    console.log('✓ Spiele');

    // Kalender
    await page.goto(`${BASE_URL}/calendar`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/06-calendar.png', fullPage: false });
    console.log('✓ Kalender');

    console.log('\n✅ Alle Screenshots fertig in /screenshots/');
  } catch (e) {
    console.log('Fehler:', e.message);
  }

  await browser.close();
})();
