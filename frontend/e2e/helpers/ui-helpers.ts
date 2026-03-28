import type { Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, PARENT_CREDENTIALS } from './test-data';

const AUTH_STATE_DIR = path.join(process.cwd(), 'e2e', '.auth-states');

function authStatePath(role: string): string {
  return path.join(AUTH_STATE_DIR, `${role}.json`);
}

/**
 * Login as a specific role via the UI. Uses cached storage state to avoid hitting
 * the 5/min rate limit on the login endpoint.
 */
async function loginAs(page: Page, email: string, password: string, role: string): Promise<void> {
  const statePath = authStatePath(role);

  // Try to reuse cached auth state
  if (fs.existsSync(statePath)) {
    try {
      const state = JSON.parse(fs.readFileSync(statePath, 'utf-8'));
      await page.context().addCookies(state.cookies || []);
      if (state.origins?.[0]?.localStorage?.length) {
        await page.goto('/login');
        for (const item of state.origins[0].localStorage) {
          await page.evaluate(([k, v]) => localStorage.setItem(k, v), [item.name, item.value]);
        }
        await page.goto('/');
        await page.waitForTimeout(2_000);
        if (!page.url().includes('/login')) {
          return; // Successfully reused auth state
        }
      }
    } catch {
      // Fall through to fresh login
    }
  }

  // Fresh login
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]');
  await emailInput.fill(email);

  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.fill(password);

  const submitButton = page.locator('button[type="submit"], button:has-text("Anmelden"), button:has-text("Login")');
  await submitButton.click();

  try {
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15_000 });
  } catch {
    // Rate limited — wait and retry
    await page.waitForTimeout(10_000);
    await submitButton.click();
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15_000 });
  }

  // Save auth state for reuse
  try {
    if (!fs.existsSync(AUTH_STATE_DIR)) {
      fs.mkdirSync(AUTH_STATE_DIR, { recursive: true });
    }
    const state = await page.context().storageState();
    fs.writeFileSync(statePath, JSON.stringify(state));
  } catch {
    // Non-critical
  }
}

/** Login as admin via the UI */
export async function loginAsAdmin(page: Page): Promise<void> {
  await loginAs(page, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password, 'admin');
}

/** Login as coach via the UI */
export async function loginAsCoach(page: Page): Promise<void> {
  await loginAs(page, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password, 'coach');
}

/** Login as parent via the UI */
export async function loginAsParent(page: Page): Promise<void> {
  await loginAs(page, PARENT_CREDENTIALS.email, PARENT_CREDENTIALS.password, 'parent');
}
