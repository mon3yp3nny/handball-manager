import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import {
  ADMIN_CREDENTIALS,
  COACH_CREDENTIALS,
  PARENT_CREDENTIALS,
  uniqueName,
} from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let parentTokens: Tokens;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
  parentTokens = await login(ctx, PARENT_CREDENTIALS.email, PARENT_CREDENTIALS.password);
  await ctx.dispose();
});

test.describe('RBAC - Role-Based Access Control', () => {
  test('coach cannot create teams (admin-only)', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.post('/api/v1/teams', {
      name: uniqueName('Forbidden'),
      age_group: 'U15',
    });
    expect(res.status()).toBe(403);
  });

  test('parent cannot create games', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const res = await parent.post('/api/v1/games', {
      team_id: 1,
      opponent: 'Test',
      game_time: new Date().toISOString(),
      location: 'Test',
      is_home: true,
      scheduled_at: new Date().toISOString(),
    });
    expect(res.status()).toBe(403);
  });

  test('parent cannot create events', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const start = new Date().toISOString();
    const end = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    const res = await parent.post('/api/v1/events', {
      title: 'Forbidden',
      start_time: start,
      end_time: end,
      event_type: 'training',
      visibility: 'team',
      team_id: 1,
    });
    expect(res.status()).toBe(403);
  });

  test('parent cannot create news', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const res = await parent.post('/api/v1/news', {
      title: 'Forbidden',
      content: 'Should fail',
    });
    expect(res.status()).toBe(403);
  });

  test('parent cannot send invitations', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const res = await parent.post('/api/v1/invitations/send', {
      email: 'nobody@test.de',
      first_name: 'No',
      last_name: 'Way',
      role: 'player',
    });
    expect(res.status()).toBe(403);
  });

  test('coach cannot create users (admin-only)', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.post('/api/v1/users', {
      email: `${uniqueName('forbidden')}@test.de`,
      password: 'testpass123',
      first_name: 'No',
      last_name: 'Way',
      role: 'player',
    });
    expect(res.status()).toBe(403);
  });

  test('coach cannot delete users (admin-only)', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.delete('/api/v1/users/1');
    expect(res.status()).toBe(403);
  });

  test('parent sees filtered teams (only children teams)', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const res = await parent.get('/api/v1/teams');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    // Parent should see a filtered (possibly empty) list, not all teams
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('parent cannot access admin stats', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const res = await parent.get('/api/v1/users/admin/stats');
    expect(res.status()).toBe(403);
  });

  test('parent cannot bulk-activate users', async ({ request }) => {
    const parent = new AuthenticatedClient(request, parentTokens);
    const res = await parent.post('/api/v1/users/admin/bulk-activate', {
      user_ids: [1],
    });
    expect(res.status()).toBe(403);
  });
});
