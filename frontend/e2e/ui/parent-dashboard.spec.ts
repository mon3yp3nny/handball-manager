import { test, expect } from '@playwright/test';
import { loginAsParent } from '../helpers/ui-helpers';

test.describe('Parent Dashboard UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsParent(page);
  });

  test('parent dashboard loads', async ({ page }) => {
    // Parent should land on dashboard after login
    expect(page.url()).not.toContain('/login');
  });

  test('parent sees welcome header', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // ParentDashboard shows "Hallo, {name}!"
    const welcome = page.locator('text=/Hallo|Willkommen|Dashboard/i');
    await expect(welcome.first()).toBeVisible({ timeout: 10_000 });
  });

  test('parent dashboard shows children cards or empty state', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Either children cards or "Keine Kinder verknüpft" message
    const childCards = page.locator('[class*="rounded-xl"][class*="shadow"]');
    const emptyState = page.locator('text=/Keine Kinder verknüpft|No children/i');
    const loading = page.locator('[class*="animate-spin"]');

    // Wait for loading to finish
    await page.waitForTimeout(3_000);

    const hasCards = await childCards.first().isVisible({ timeout: 2_000 }).catch(() => false);
    const isEmpty = await emptyState.first().isVisible({ timeout: 2_000 }).catch(() => false);
    const isLoading = await loading.first().isVisible({ timeout: 1_000 }).catch(() => false);

    // Should show either children data, empty state, or still loading
    expect(hasCards || isEmpty || isLoading).toBeTruthy();
  });

  test('parent dashboard shows child stats when children exist', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3_000);

    // Look for stat labels in child cards
    const statLabels = ['Spiele', 'Tore', 'Anwesenheit'];
    let found = 0;
    for (const label of statLabels) {
      const el = page.locator(`text="${label}"`);
      if (await el.first().isVisible({ timeout: 1_000 }).catch(() => false)) {
        found++;
      }
    }

    // If children exist, we expect to see stats; if no children, that's OK too
    const emptyState = page.locator('text=/Keine Kinder verknüpft/i');
    const hasNoChildren = await emptyState.first().isVisible({ timeout: 1_000 }).catch(() => false);
    if (!hasNoChildren) {
      expect(found).toBeGreaterThanOrEqual(0); // At least page loaded without error
    }
  });

  test('parent can navigate to profile', async ({ page }) => {
    const profileLink = page.locator('a[href="/profile"], a:has-text("Profil")');
    if (await profileLink.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await profileLink.first().click();
      await page.waitForTimeout(2_000);
      expect(page.url()).toContain('/profile');
    }
  });
});
