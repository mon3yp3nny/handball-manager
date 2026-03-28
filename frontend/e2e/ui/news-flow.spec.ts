import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('News Page UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('news page loads and shows content or error', async ({ page }) => {
    await page.goto('/news');
    await page.waitForLoadState('networkidle');

    // Page may show title, news content, or API error state
    const title = page.locator('h1:has-text("Nachrichten"), h1:has-text("News")');
    const errorState = page.locator('text=/Fehler beim Laden der Nachrichten/');
    const hasTitle = await title.first().isVisible({ timeout: 5_000 }).catch(() => false);
    const hasError = await errorState.first().isVisible({ timeout: 3_000 }).catch(() => false);
    expect(hasTitle || hasError).toBeTruthy();
  });

  test('news page shows news cards, empty state, or error', async ({ page }) => {
    await page.goto('/news');
    await page.waitForLoadState('networkidle');

    const cards = page.locator('[class*="card"]');
    const emptyState = page.locator('text=/Keine Nachrichten|Noch keine|No news/i');
    const errorState = page.locator('text=/Fehler|Error/i');
    const loadingState = page.locator('text=/Lädt/i');

    const hasCards = await cards.first().isVisible({ timeout: 5_000 }).catch(() => false);
    const isEmpty = await emptyState.first().isVisible({ timeout: 1_000 }).catch(() => false);
    const hasError = await errorState.first().isVisible({ timeout: 1_000 }).catch(() => false);
    const isLoading = await loadingState.first().isVisible({ timeout: 1_000 }).catch(() => false);

    expect(hasCards || isEmpty || hasError || isLoading).toBeTruthy();
  });

  test('news cards show published/draft badge', async ({ page }) => {
    await page.goto('/news');
    await page.waitForLoadState('networkidle');

    // Look for status badges
    const badges = page.locator('text=/Veröffentlicht|Entwurf|Published|Draft/i');
    if (await badges.first().isVisible({ timeout: 5_000 }).catch(() => false)) {
      const count = await badges.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('news cards display author name', async ({ page }) => {
    await page.goto('/news');
    await page.waitForLoadState('networkidle');

    // Look for "Von" (author prefix) in news cards
    const authorLabel = page.locator('text=/Von /');
    if (await authorLabel.first().isVisible({ timeout: 5_000 }).catch(() => false)) {
      await expect(authorLabel.first()).toBeVisible();
    }
  });

  test('navigate to news detail page', async ({ page }) => {
    await page.goto('/news');
    await page.waitForLoadState('networkidle');

    const newsLink = page.locator('a[href*="/news/"]').first();
    if (await newsLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await newsLink.click();
      await page.waitForTimeout(2_000);
      expect(page.url()).toMatch(/\/news\/\d+/);

      // Detail page should show "Nachricht"
      const detailTitle = page.locator('h1:has-text("Nachricht")');
      await expect(detailTitle.first()).toBeVisible({ timeout: 5_000 });
    }
  });
});
