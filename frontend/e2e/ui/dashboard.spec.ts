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
    const sidebar = page.locator('nav, [role="navigation"], aside');
    await expect(sidebar.first()).toBeVisible({ timeout: 5_000 });

    // Sidebar should show app name and user info
    const branding = page.locator('text=/Handball Manager/i');
    await expect(branding.first()).toBeVisible({ timeout: 3_000 });
  });
});
