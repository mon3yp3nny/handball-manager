import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Calendar Page UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('calendar page loads with title', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    const title = page.locator('h1:has-text("Kalender"), h1:has-text("Calendar")');
    await expect(title.first()).toBeVisible({ timeout: 10_000 });
  });

  test('calendar shows current month and year', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    // The calendar should display the current month name in German
    const monthNames = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
      'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
    const currentMonth = monthNames[new Date().getMonth()];
    const currentYear = new Date().getFullYear().toString();

    const monthHeader = page.locator(`text=/${currentMonth}.*${currentYear}/i`);
    await expect(monthHeader.first()).toBeVisible({ timeout: 5_000 });
  });

  test('calendar shows weekday headers', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    // German weekday abbreviations
    const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
    let found = 0;
    for (const day of weekDays) {
      const el = page.locator(`text="${day}"`);
      if (await el.first().isVisible({ timeout: 1_000 }).catch(() => false)) {
        found++;
      }
    }
    expect(found).toBeGreaterThanOrEqual(5);
  });

  test('calendar has navigation arrows', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    // Previous and next month buttons
    const prevBtn = page.locator('button:has-text("←")');
    const nextBtn = page.locator('button:has-text("→")');

    await expect(prevBtn).toBeVisible({ timeout: 5_000 });
    await expect(nextBtn).toBeVisible({ timeout: 5_000 });
  });

  test('navigate to next month', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    // Get current month text
    const monthHeader = page.locator('h2').first();
    const currentText = await monthHeader.textContent();

    // Click next month
    const nextBtn = page.locator('button:has-text("→")');
    await nextBtn.click();
    await page.waitForTimeout(500);

    // Month should have changed
    const newText = await monthHeader.textContent();
    expect(newText).not.toBe(currentText);
  });

  test('navigate to previous month', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    const monthHeader = page.locator('h2').first();
    const currentText = await monthHeader.textContent();

    const prevBtn = page.locator('button:has-text("←")');
    await prevBtn.click();
    await page.waitForTimeout(500);

    const newText = await monthHeader.textContent();
    expect(newText).not.toBe(currentText);
  });

  test('calendar has "Neuer Termin" button', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    const newEventBtn = page.locator('button:has-text("Neuer Termin"), button:has-text("New Event")');
    await expect(newEventBtn.first()).toBeVisible({ timeout: 5_000 });
  });

  test('today is highlighted in the calendar', async ({ page }) => {
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');

    // Today should have a ring/highlight class
    const todayCell = page.locator('[class*="ring-2"], [class*="ring-primary"]');
    await expect(todayCell.first()).toBeVisible({ timeout: 5_000 });
  });
});
