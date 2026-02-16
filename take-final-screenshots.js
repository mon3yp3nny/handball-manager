const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

  const BASE_URL = 'http://localhost:3000';
  const SCREENSHOTS_DIR = '/Users/helmut/.openclaw/workspace/handball-manager/screenshots';
  
  console.log('Mache Screenshots der aktuellen Features...');

  try {
    // 1. Login mit OAuth Buttons
    await page.goto(`${BASE_URL}/login`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/oauth-login.png` });
    console.log('✓ OAuth Login-Seite');

    // 2. Dashboard als Admin
    await page.goto(`${BASE_URL}/`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/dashboard-admin.png` });
    console.log('✓ Dashboard (Admin)');

    // 3. Teams Seite
    await page.goto(`${BASE_URL}/teams`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/teams-page.png` });
    console.log('✓ Teams Seite');

    // 4. Spieler Seite (Coach Ansicht)
    await page.goto(`${BASE_URL}/players`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/players-coach.png` });
    console.log('✓ Spieler (Coach Ansicht)');

    // 5. Spiele
    await page.goto(`${BASE_URL}/games`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/games-page.png` });
    console.log('✓ Spiele Seite');

    // 6. Kalender
    await page.goto(`${BASE_URL}/calendar`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/calendar-view.png` });
    console.log('✓ Kalender');

    // 7. Mobile Ansicht
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/login`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/mobile-oauth.png` });
    console.log('✓ Mobile Login');

    // 8. Mobile Dashboard
    await page.goto(`${BASE_URL}/`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/mobile-dashboard.png` });
    console.log('✓ Mobile Dashboard');

    console.log('\n✅ Alle Screenshots fertig!');
  } catch (e) {
    console.log('Fehler:', e.message);
  }

  await browser.close();
})();
