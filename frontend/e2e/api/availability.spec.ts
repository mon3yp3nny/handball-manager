import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testPlayerId: number;
let testTeamId: number;
let testUserId: number;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
  const admin = new AuthenticatedClient(ctx, adminTokens);
  const coach = new AuthenticatedClient(ctx, coachTokens);

  const me = await (await coach.get('/api/v1/auth/me')).json();
  const team = await (
    await admin.post('/api/v1/teams', {
      name: uniqueName('AvailTeam'),
      age_group: 'U15',
      coach_id: me.id,
    })
  ).json();
  testTeamId = team.id;

  const email = `${uniqueName('availplayer')}@test.de`;
  const u = await (
    await admin.post('/api/v1/users', {
      email,
      password: 'testpass123',
      first_name: 'Avail',
      last_name: 'Player',
      role: 'player',
    })
  ).json();
  testUserId = u.id;

  const list = await (await admin.get('/api/v1/players')).json();
  const p = (list.items as { user_id: number; id: number }[]).find(
    (x) => x.user_id === u.id,
  );
  if (p) {
    testPlayerId = p.id;
    await admin.post(`/api/v1/teams/${testTeamId}/players/${p.id}`);
  }
  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  if (testUserId) await admin.delete(`/api/v1/users/${testUserId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Player availability API (#136)', () => {
  test('admin creates + lists availability windows', async ({ request }) => {
    test.skip(!testPlayerId, 'player setup failed');
    const admin = new AuthenticatedClient(request, adminTokens);
    const today = new Date();
    const inOneDay = new Date(today.getTime() + 86_400_000).toISOString().slice(0, 10);
    const inFiveDays = new Date(today.getTime() + 5 * 86_400_000).toISOString().slice(0, 10);

    const res = await admin.post(`/api/v1/players/${testPlayerId}/availability`, {
      from_date: inOneDay,
      to_date: inFiveDays,
      reason: 'holiday',
      note: 'Schulausflug',
    });
    expect(res.status()).toBe(201);
    const created = await res.json();
    expect(created.reason).toBe('holiday');
    expect(typeof created.id).toBe('number');

    const list = await (await admin.get(`/api/v1/players/${testPlayerId}/availability`)).json();
    expect(list.length).toBeGreaterThanOrEqual(1);
    expect(list[0]).toHaveProperty('from_date');
  });

  test('inverted date range is rejected', async ({ request }) => {
    test.skip(!testPlayerId, 'player setup failed');
    const admin = new AuthenticatedClient(request, adminTokens);
    const today = new Date();
    const inOneDay = new Date(today.getTime() + 86_400_000).toISOString().slice(0, 10);
    const inFiveDays = new Date(today.getTime() + 5 * 86_400_000).toISOString().slice(0, 10);
    const res = await admin.post(`/api/v1/players/${testPlayerId}/availability`, {
      from_date: inFiveDays,
      to_date: inOneDay,
      reason: 'other',
    });
    expect([400, 422]).toContain(res.status());
  });
});
