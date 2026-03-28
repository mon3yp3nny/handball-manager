import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('404 Not Found Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('shows 404 for unknown route', async ({ page }) => {
    await page.goto('/this-page-does-not-exist');
    await page.waitForLoadState('networkidle');

    const heading = page.locator('text="404"');
    await expect(heading.first()).toBeVisible({ timeout: 5_000 });
  });

  test('shows "Seite nicht gefunden" message', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await page.waitForLoadState('networkidle');

    const message = page.locator('text="Seite nicht gefunden"');
    await expect(message.first()).toBeVisible({ timeout: 5_000 });
  });

  test('has link back to home', async ({ page }) => {
    await page.goto('/nonexistent-route');
    await page.waitForLoadState('networkidle');

    const homeLink = page.locator('a:has-text("Zurück zur Startseite"), a[href="/"]');
    await expect(homeLink.first()).toBeVisible({ timeout: 5_000 });
  });

  test('clicking home link navigates to dashboard', async ({ page }) => {
    await page.goto('/nonexistent-route');
    await page.waitForLoadState('networkidle');

    const homeLink = page.locator('a:has-text("Zurück zur Startseite"), a[href="/"]');
    if (await homeLink.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await homeLink.first().click();
      await page.waitForTimeout(2_000);
      // Should navigate to root/dashboard
      expect(page.url()).not.toContain('nonexistent');
    }
  });
});
