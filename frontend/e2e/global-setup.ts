import { request } from '@playwright/test';
import { login, clearTokenCache } from './helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, PARENT_CREDENTIALS } from './helpers/test-data';

/**
 * Global setup: pre-authenticates all demo accounts so individual test files
 * don't hit the 5/min login rate limit. Reuses cached tokens if available.
 */
export default async function globalSetup() {
  const ctx = await request.newContext();

  try {
    // login() uses disk cache internally — only hits the API if not cached
    await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
    await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
    await login(ctx, PARENT_CREDENTIALS.email, PARENT_CREDENTIALS.password);
  } catch (e) {
    // If rate limited, clear cache and warn — tests using cached tokens may still work
    console.warn('Global setup login warning:', (e as Error).message);
    console.warn('Tests will attempt to use previously cached tokens.');
  }

  await ctx.dispose();
}
