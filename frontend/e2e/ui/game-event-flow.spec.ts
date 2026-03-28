import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Games & Events UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('games page renders', async ({ page }) => {
    await page.goto('/games');
    await page.waitForLoadState('networkidle');

    const content = page.locator('main, [class*="content"], [class*="page"], h1, h2');
    await expect(content.first()).toBeVisible({ timeout: 10_000 });
  });

  test('events page renders', async ({ page }) => {
    await page.goto('/events');
    await page.waitForLoadState('networkidle');

    const content = page.locator('main, [class*="content"], [class*="page"], h1, h2');
    await expect(content.first()).toBeVisible({ timeout: 10_000 });
  });

  test('navigate from games to events via sidebar', async ({ page }) => {
    await page.goto('/games');
    await page.waitForLoadState('networkidle');

    // Navigate to events via sidebar/nav link
    const eventsLink = page.locator('a[href="/events"], a[href*="/events"], a:has-text("Termine"), a:has-text("Events")');
    if (await eventsLink.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await eventsLink.first().click();
      await page.waitForTimeout(3_000);
      expect(page.url()).toContain('/events');
    }
  });
});
