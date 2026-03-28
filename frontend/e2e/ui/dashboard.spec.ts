import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('dashboard page loads after login', async ({ page }) => {
    const url = page.url();
    expect(url).not.toContain('/login');
  });

  test('shows upcoming games or events section', async ({ page }) => {
    // Look for "Spiele", "Termine", "Kommende", or similar dashboard sections
    const section = page.locator('text=/Spiel|Termin|Kommend|Game|Event|Dashboard/i');
    await expect(section.first()).toBeVisible({ timeout: 10_000 });
  });

  test('navigation has menu items', async ({ page }) => {
    const nav = page.locator('nav, [role="navigation"], aside');
    await expect(nav.first()).toBeVisible({ timeout: 5_000 });

    // Check for key menu items
    const menuTexts = ['Mannschaften', 'Spieler', 'Spiele', 'Termine', 'Nachrichten', 'Teams', 'Players', 'Dashboard'];
    let found = 0;
    for (const text of menuTexts) {
      const link = page.locator(`a:has-text("${text}"), [role="menuitem"]:has-text("${text}")`);
      if (await link.first().isVisible({ timeout: 1_000 }).catch(() => false)) {
        found++;
      }
    }
    expect(found).toBeGreaterThan(2);
  });
});
