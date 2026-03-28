import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testTeamId: number;
let coachUserId: number;
const createdGameIds: number[] = [];

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);

  const admin = new AuthenticatedClient(ctx, adminTokens);
  const coach = new AuthenticatedClient(ctx, coachTokens);

  // Get coach user ID
  const meRes = await coach.get('/api/v1/auth/me');
  const me = await meRes.json();
  coachUserId = me.id;

  // Create a team assigned to this coach
  const teamRes = await admin.post('/api/v1/teams', {
    name: uniqueName('GameTestTeam'),
    age_group: 'U17',
    coach_id: coachUserId,
  });
  const team = await teamRes.json();
  testTeamId = team.id;

  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const coach = new AuthenticatedClient(ctx, coachTokens);
  const admin = new AuthenticatedClient(ctx, adminTokens);
  for (const id of createdGameIds) {
    await coach.delete(`/api/v1/games/${id}`).catch(() => {});
  }
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Games API', () => {
  test('coach creates a game', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const scheduledAt = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString();
    const res = await coach.post('/api/v1/games', {
      team_id: testTeamId,
      opponent: uniqueName('Opponent'),
      game_time: scheduledAt,
      location: 'Sporthalle Test',
      is_home: true,
      scheduled_at: scheduledAt,
    });
    expect(res.status()).toBe(201);
    const game = await res.json();
    expect(game.team_id).toBe(testTeamId);
    expect(game.location).toBe('Sporthalle Test');
    createdGameIds.push(game.id);
  });

  test('list games returns paginated response', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/games');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('list games filtered by team_id', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.get('/api/v1/games', { team_id: String(testTeamId) });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    for (const game of body.items) {
      expect(game.team_id).toBe(testTeamId);
    }
  });

  test('list games with upcoming=true', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/games', { upcoming: 'true' });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
  });

  test('update game details', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const gameId = createdGameIds[0];
    expect(gameId).toBeTruthy();
    const res = await coach.put(`/api/v1/games/${gameId}`, {
      opponent: 'Updated Opponent',
      location: 'Neue Halle',
    });
    expect(res.ok()).toBeTruthy();
    const game = await res.json();
    expect(game.opponent).toBe('Updated Opponent');
  });

  test('update game result', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const gameId = createdGameIds[0];
    expect(gameId).toBeTruthy();
    const res = await coach.patch(`/api/v1/games/${gameId}/result`, {
      home_score: 28,
      away_score: 24,
      status: 'completed',
    });
    expect(res.ok()).toBeTruthy();
    const game = await res.json();
    expect(game.home_score).toBe(28);
    expect(game.away_score).toBe(24);
  });

  test('delete game', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    // Create a throwaway game
    const scheduledAt = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString();
    const createRes = await coach.post('/api/v1/games', {
      team_id: testTeamId,
      opponent: 'ToDelete',
      game_time: scheduledAt,
      location: 'Anywhere',
      is_home: false,
      scheduled_at: scheduledAt,
    });
    const game = await createRes.json();
    const res = await coach.delete(`/api/v1/games/${game.id}`);
    expect(res.status()).toBe(204);
  });

  test('calendar upcoming endpoint returns games', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/games/calendar/upcoming', { days: '30' });
    expect(res.ok()).toBeTruthy();
    const games = await res.json();
    expect(Array.isArray(games)).toBeTruthy();
  });
});
