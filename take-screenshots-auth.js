const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  const BASE_URL = 'http://localhost:3000';
  console.log('Starte mit Login...');

  try {
    // Zuerst einloggen
    await page.goto(`${BASE_URL}/login`, { timeout: 15000, waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    
    // Login ausfüllen
    await page.fill('input[type="email"]', 'admin@handball.de');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Warte auf Weiterleitung nach Login
    await page.waitForTimeout(3000);
    
    // 1. Dashboard (nach Login)
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/01-dashboard-logged-in.png', fullPage: false });
    console.log('✓ Dashboard (eingeloggt)');

    // 2. Teams
    await page.goto(`${BASE_URL}/teams`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/02-teams.png', fullPage: false });
    console.log('✓ Teams');

    // 3. Spieler
    await page.goto(`${BASE_URL}/players`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/03-players.png', fullPage: false });
    console.log('✓ Spieler');

    // 4. Spiele
    await page.goto(`${BASE_URL}/games`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/04-games.png', fullPage: false });
    console.log('✓ Spiele');

    // 5. Kalender
    await page.goto(`${BASE_URL}/calendar`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/05-calendar.png', fullPage: false });
    console.log('✓ Kalender');

    // 6. Mobile Ansicht (Login)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/login`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/06-mobile-login.png', fullPage: false });
    console.log('✓ Mobile Login');

    // 7. Mobile Dashboard
    await page.goto(`${BASE_URL}/`, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/07-mobile-dashboard.png', fullPage: false });
    console.log('✓ Mobile Dashboard');

    console.log('\n✅ Alle Screenshots fertig!');
  } catch (e) {
    console.log('Fehler:', e.message);
    console.log(e.stack);
  }

  await browser.close();
})();
