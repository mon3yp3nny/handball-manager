import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAsCoach, loginAsParent } from '../helpers/ui-helpers';

test.describe('Navigation & Role-Based UI', () => {
  test.describe('Admin navigation', () => {
    test('admin sees sidebar with user info', async ({ page }) => {
      await loginAsAdmin(page);

      const sidebar = page.locator('aside, nav').first();
      await expect(sidebar).toBeVisible({ timeout: 5_000 });

      // Page should contain admin user info
      const content = await page.content();
      expect(content).toMatch(/Admin|Handball Manager/i);
    });

    test('admin can access teams page', async ({ page }) => {
      await loginAsAdmin(page);
      await page.goto('/teams');
      await page.waitForLoadState('networkidle');

      expect(page.url()).toContain('/teams');
      // Should not be redirected away
      expect(page.url()).not.toContain('/login');
    });

    test('admin can access all entity pages', async ({ page }) => {
      await loginAsAdmin(page);

      const pages = ['/teams', '/players', '/games', '/events', '/news', '/attendance', '/calendar', '/profile'];
      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');
        expect(page.url()).toContain(pagePath);
        expect(page.url()).not.toContain('/login');
      }
    });
  });

  test.describe('Coach navigation', () => {
    test('coach can access dashboard', async ({ page }) => {
      await loginAsCoach(page);

      expect(page.url()).not.toContain('/login');
    });

    test('coach sees sidebar with user info', async ({ page }) => {
      await loginAsCoach(page);

      const sidebar = page.locator('aside, nav').first();
      await expect(sidebar).toBeVisible({ timeout: 5_000 });

      const content = await page.content();
      expect(content).toMatch(/Coach|Handball Manager/i);
    });

    test('coach can access teams page', async ({ page }) => {
      await loginAsCoach(page);
      await page.goto('/teams');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/teams');
    });
  });

  test.describe('Parent navigation', () => {
    test('parent can access dashboard', async ({ page }) => {
      await loginAsParent(page);

      expect(page.url()).not.toContain('/login');
    });

    test('parent sees navigation', async ({ page }) => {
      await loginAsParent(page);

      const nav = page.locator('nav, [role="navigation"], aside');
      await expect(nav.first()).toBeVisible({ timeout: 5_000 });
    });

    test('parent can view profile page', async ({ page }) => {
      await loginAsParent(page);
      await page.goto('/profile');
      await page.waitForLoadState('networkidle');

      const title = page.locator('h1:has-text("Mein Profil"), h1:has-text("Profile")');
      await expect(title.first()).toBeVisible({ timeout: 5_000 });
    });
  });

  test.describe('Protected routes', () => {
    test('unauthenticated user is redirected to login', async ({ page }) => {
      // Clear any existing auth state
      await page.goto('/login');
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });

      await page.goto('/teams');
      await page.waitForTimeout(3_000);

      expect(page.url()).toContain('/login');
    });

    test('unauthenticated user cannot access profile', async ({ page }) => {
      await page.goto('/login');
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });

      await page.goto('/profile');
      await page.waitForTimeout(3_000);

      expect(page.url()).toContain('/login');
    });
  });

  test.describe('Cross-page navigation', () => {
    test('sidebar navigation works across pages', async ({ page }) => {
      await loginAsAdmin(page);

      // Navigate through multiple pages via sidebar
      const routes = [
        { text: 'Mannschaften', path: '/teams' },
        { text: 'Spieler', path: '/players' },
        { text: 'Spiele', path: '/games' },
        { text: 'Termine', path: '/events' },
      ];

      for (const route of routes) {
        const link = page.locator(`a:has-text("${route.text}"), a[href="${route.path}"]`);
        if (await link.first().isVisible({ timeout: 2_000 }).catch(() => false)) {
          await link.first().click();
          await page.waitForTimeout(1_500);
          expect(page.url()).toContain(route.path);
        }
      }
    });
  });
});
