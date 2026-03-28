import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Player Detail Page UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('navigate to player detail from players list', async ({ page }) => {
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);
      expect(page.url()).toMatch(/\/players\/\d+/);
    }
  });

  test('player detail shows player name', async ({ page }) => {
    // First find a player ID from the list
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);

      // Player name should be in an h1
      const nameEl = page.locator('h1');
      await expect(nameEl.first()).toBeVisible({ timeout: 5_000 });
      const name = await nameEl.first().textContent();
      expect(name?.trim().length).toBeGreaterThan(0);
    }
  });

  test('player detail shows profile information section', async ({ page }) => {
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);

      const profileSection = page.locator('h2:has-text("Profilinformationen"), h2:has-text("Profile")');
      await expect(profileSection.first()).toBeVisible({ timeout: 5_000 });
    }
  });

  test('player detail shows statistics section', async ({ page }) => {
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);

      const statsSection = page.locator('h2:has-text("Statistiken"), h2:has-text("Statistics")');
      await expect(statsSection.first()).toBeVisible({ timeout: 5_000 });
    }
  });

  test('player detail shows stat values (Spiele, Tore, Assists)', async ({ page }) => {
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);

      const statLabels = ['Spiele', 'Tore', 'Assists'];
      let found = 0;
      for (const label of statLabels) {
        const el = page.locator(`text="${label}"`);
        if (await el.first().isVisible({ timeout: 1_000 }).catch(() => false)) {
          found++;
        }
      }
      expect(found).toBeGreaterThanOrEqual(2);
    }
  });

  test('player detail has back link to players list', async ({ page }) => {
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);

      // Back arrow link
      const backLink = page.locator('a[href="/players"]');
      await expect(backLink.first()).toBeVisible({ timeout: 5_000 });
    }
  });

  test('admin sees edit button on player detail', async ({ page }) => {
    await page.goto('/players');
    await page.waitForLoadState('networkidle');

    const playerLink = page.locator('a[href*="/players/"]').first();
    if (await playerLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await playerLink.click();
      await page.waitForTimeout(2_000);

      const editBtn = page.locator('a:has-text("Bearbeiten"), button:has-text("Bearbeiten")');
      await expect(editBtn.first()).toBeVisible({ timeout: 5_000 });
    }
  });
});
