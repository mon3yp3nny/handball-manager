import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
  await ctx.dispose();
});

test.describe('Dashboard widgets API (#129)', () => {
  test('admin gets payload with both keys', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/dashboard/widgets');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('next_match');
    expect(body).toHaveProperty('upcoming_birthdays');
    expect(Array.isArray(body.upcoming_birthdays)).toBeTruthy();
  });

  test('coach payload is RBAC-scoped (200 with same shape)', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.get('/api/v1/dashboard/widgets');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('next_match');
    expect(body).toHaveProperty('upcoming_birthdays');
  });

  test('next_match (if present) carries expected fields', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const { next_match } = await (await admin.get('/api/v1/dashboard/widgets')).json();
    if (next_match) {
      expect(typeof next_match.id).toBe('number');
      expect(typeof next_match.opponent).toBe('string');
      expect(next_match.scheduled_at).toBeTruthy();
    }
  });

  test('birthday entries cap at 7 days out', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const body = await (await admin.get('/api/v1/dashboard/widgets')).json();
    for (const b of body.upcoming_birthdays) {
      expect(b.days_until).toBeGreaterThanOrEqual(0);
      expect(b.days_until).toBeLessThanOrEqual(7);
    }
  });
});
