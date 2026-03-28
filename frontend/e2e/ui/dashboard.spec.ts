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

  test('sidebar is visible with app branding', async ({ page }) => {
    // Sidebar should be visible and contain "Handball Manager" text
    const sidebar = page.locator('aside, nav').first();
    await expect(sidebar).toBeVisible({ timeout: 5_000 });

    // Check for branding or user info within the page
    const content = await page.content();
    expect(content).toContain('Handball Manager');
  });
});
