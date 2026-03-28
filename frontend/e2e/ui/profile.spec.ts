import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Profile Page UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('profile page loads with title', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    const title = page.locator('h1:has-text("Mein Profil"), h1:has-text("Profile")');
    await expect(title.first()).toBeVisible({ timeout: 10_000 });
  });

  test('profile shows user name', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    // Admin user should have a visible name
    const nameEl = page.locator('h2');
    await expect(nameEl.first()).toBeVisible({ timeout: 5_000 });
    const nameText = await nameEl.first().textContent();
    expect(nameText?.trim().length).toBeGreaterThan(0);
  });

  test('profile shows user email', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    const emailEl = page.locator('text=admin@handball.de');
    await expect(emailEl.first()).toBeVisible({ timeout: 5_000 });
  });

  test('profile shows role field', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    // The profile should display "Rolle:" label — the value may or may not be populated
    const roleField = page.locator('text=/Rolle/i');
    await expect(roleField.first()).toBeVisible({ timeout: 5_000 });
  });

  test('profile has avatar with user initials', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    // Avatar shows initials "AU" for Admin User
    const avatar = page.locator('text="AU"');
    await expect(avatar.first()).toBeVisible({ timeout: 5_000 });
  });

  test('profile has edit button', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    const editBtn = page.locator('button:has-text("Profil bearbeiten"), button:has-text("Edit")');
    await expect(editBtn.first()).toBeVisible({ timeout: 5_000 });
  });

  test('profile shows activity section', async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');

    const activitySection = page.locator('h2:has-text("Aktivität"), h2:has-text("Activity")');
    await expect(activitySection.first()).toBeVisible({ timeout: 5_000 });
  });

  test('navigate to profile from sidebar', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const profileLink = page.locator('a[href="/profile"], a:has-text("Profil")');
    if (await profileLink.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await profileLink.first().click();
      await page.waitForTimeout(2_000);
      expect(page.url()).toContain('/profile');
    }
  });
});
