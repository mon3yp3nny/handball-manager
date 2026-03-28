import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';

test.describe('Attendance UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('attendance page renders', async ({ page }) => {
    await page.goto('/attendance');
    await page.waitForLoadState('networkidle');

    const content = page.locator('main, [class*="content"], [class*="page"], h1, h2');
    await expect(content.first()).toBeVisible({ timeout: 10_000 });
  });

  test('attendance page shows relevant content', async ({ page }) => {
    await page.goto('/attendance');
    await page.waitForLoadState('networkidle');

    // Look for attendance-related text
    const attendanceText = page.locator('text=/Anwesenheit|Attendance|Status|Spieler/i');
    await expect(attendanceText.first()).toBeVisible({ timeout: 10_000 });
  });
});
