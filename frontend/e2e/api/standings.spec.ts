import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let testTeamId: number;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  const admin = new AuthenticatedClient(ctx, adminTokens);

  const team = await (
    await admin.post('/api/v1/teams', {
      name: uniqueName('StandingsTeam'),
      age_group: 'U17',
    })
  ).json();
  testTeamId = team.id;
  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Team standings API (#128)', () => {
  test('empty team has zeroed summary', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get(`/api/v1/teams/${testTeamId}/standings`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.team_id).toBe(testTeamId);
    expect(body.summary.played).toBe(0);
    expect(body.summary.points).toBe(0);
    expect(body.per_opponent).toEqual([]);
  });

  test('payload shape includes summary + per_opponent', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const body = await (await admin.get(`/api/v1/teams/${testTeamId}/standings`)).json();
    expect(body).toHaveProperty('summary');
    expect(body.summary).toEqual(
      expect.objectContaining({
        played: expect.any(Number),
        wins: expect.any(Number),
        draws: expect.any(Number),
        losses: expect.any(Number),
        goals_for: expect.any(Number),
        goals_against: expect.any(Number),
        goal_difference: expect.any(Number),
        points: expect.any(Number),
      }),
    );
    expect(Array.isArray(body.per_opponent)).toBeTruthy();
  });

  test('returns 404 for unknown team', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/teams/999999/standings');
    expect(res.status()).toBe(404);
  });
});
