import { test, expect } from '@playwright/test';
import { loginAsAdmin } from '../helpers/ui-helpers';
import { uniqueName } from '../helpers/test-data';

test.describe('Team Management UI', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('teams page lists teams', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    const teamElements = page.locator('[class*="card"], [class*="team"], tr, [data-testid*="team"]');
    await expect(teamElements.first()).toBeVisible({ timeout: 10_000 });
  });

  test('create new team button exists', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    const createBtn = page.locator('button:has-text("Neue Mannschaft"), button:has-text("Mannschaft erstellen"), button:has-text("New Team"), a:has-text("Neue Mannschaft")');
    await expect(createBtn.first()).toBeVisible({ timeout: 5_000 });
  });

  test('create team flow', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    const createBtn = page.locator('button:has-text("Neue Mannschaft"), button:has-text("Mannschaft erstellen"), button:has-text("New Team"), a:has-text("Neue Mannschaft")');
    await createBtn.first().click();
    await page.waitForTimeout(1_000);

    const teamName = uniqueName('UITeam');
    const nameInput = page.locator('input[name="name"], input[placeholder*="Name"], input[placeholder*="name"]');
    if (await nameInput.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await nameInput.first().fill(teamName);

      const ageGroupInput = page.locator('input[name="age_group"], select[name="age_group"], input[placeholder*="Alter"]');
      if (await ageGroupInput.first().isVisible({ timeout: 1_000 }).catch(() => false)) {
        const tagName = await ageGroupInput.first().evaluate((el) => el.tagName);
        if (tagName === 'SELECT') {
          await ageGroupInput.first().selectOption({ index: 1 });
        } else {
          await ageGroupInput.first().fill('U15');
        }
      }

      const submitBtn = page.locator('button[type="submit"], button:has-text("Erstellen"), button:has-text("Speichern"), button:has-text("Create")');
      await submitBtn.first().click();
      await page.waitForTimeout(2_000);
    }
  });

  test('click team navigates to detail', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    const teamLink = page.locator('a[href*="/teams/"], [class*="card"] a, [data-testid*="team"]').first();
    if (await teamLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await teamLink.click();
      await page.waitForTimeout(2_000);
      expect(page.url()).toMatch(/\/teams\/\d+/);
    }
  });
});
