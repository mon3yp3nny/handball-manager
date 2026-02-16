const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  // Warte bis Backend und Frontend laufen
  console.log('Warte auf die App...');
  
  // Versuche Verbindung zum Frontend
  let retries = 30;
  while (retries > 0) {
    try {
      await page.goto('http://localhost:5173/login', { timeout: 3000 });
      break;
    } catch {
      retries--;
      await new Promise(r => setTimeout(r, 1000));
    }
  }

  if (retries === 0) {
    console.log('Konnte keine Verbindung zur App herstellen');
    await browser.close();
    process.exit(1);
  }

  // Screenshot Login-Seite
  await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/login.png' });
  console.log('Login-Seite erfasst');

  // Login
  await page.fill('input[type="email"]', 'admin@handball.de');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);

  // Dashboard
  await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/dashboard.png' });
  console.log('Dashboard erfasst');

  // Teams
  await page.goto('http://localhost:5173/teams');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/teams.png' });
  console.log('Teams-Seite erfasst');

  // Spieler
  await page.goto('http://localhost:5173/players');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/players.png' });
  console.log('Spieler-Seite erfasst');

  // Spiele
  await page.goto('http://localhost:5173/games');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/games.png' });
  console.log('Spiele-Seite erfasst');

  // Kalender
  await page.goto('http://localhost:5173/calendar');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/helmut/.openclaw/workspace/handball-manager/screenshots/calendar.png' });
  console.log('Kalender erfasst');

  await browser.close();
  console.log('Alle Screenshots fertig!');
})();
