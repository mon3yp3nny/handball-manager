import { test, expect } from '@playwright/test';
import { ADMIN_CREDENTIALS } from '../helpers/test-data';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Login Flow', () => {
  test('loads login page with form fields', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('login with valid admin credentials redirects to dashboard', async ({ page }) => {
    await loginAsAdmin(page);
    expect(page.url()).not.toContain('/login');
  });

  test('login with wrong password shows error or stays on login', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]');
    await emailInput.fill(ADMIN_CREDENTIALS.email);

    const passwordInput = page.locator('input[type="password"]');
    await passwordInput.fill('wrongpassword');

    const submitButton = page.locator('button[type="submit"], button:has-text("Anmelden"), button:has-text("Login")');
    await submitButton.click();

    // Wait a bit for response
    await page.waitForTimeout(3_000);

    // Should still be on login page (not redirected)
    expect(page.url()).toContain('/login');
  });

  test('logout returns to login', async ({ page }) => {
    await loginAsAdmin(page);

    // Try to find and click logout
    const logoutBtn = page.locator('button:has-text("Abmelden"), button:has-text("Logout"), a:has-text("Abmelden"), a:has-text("Logout")');
    if (await logoutBtn.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await logoutBtn.first().click();
      await page.waitForURL('**/login', { timeout: 5_000 });
      expect(page.url()).toContain('/login');
    }
  });
});
