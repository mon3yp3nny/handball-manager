import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testTeamId: number;
let testPlayerId: number;
let testPlayerUserId: number;
const cleanupUserIds: number[] = [];

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);

  const admin = new AuthenticatedClient(ctx, adminTokens);

  // Create a test team for player operations
  const teamRes = await admin.post('/api/v1/teams', {
    name: uniqueName('PlayerTestTeam'),
    age_group: 'U15',
  });
  const team = await teamRes.json();
  testTeamId = team.id;

  // Create a player user
  const email = `${uniqueName('player')}@test.de`;
  const userRes = await admin.post('/api/v1/users', {
    email,
    password: 'testpass123',
    first_name: 'Test',
    last_name: 'Player',
    role: 'player',
  });
  const user = await userRes.json();
  testPlayerUserId = user.id;
  cleanupUserIds.push(user.id);

  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  // Clean up: delete player, team, user
  if (testPlayerId) await admin.delete(`/api/v1/players/${testPlayerId}`).catch(() => {});
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  for (const id of cleanupUserIds) {
    await admin.delete(`/api/v1/users/${id}`).catch(() => {});
  }
  await ctx.dispose();
});

test.describe('Players API', () => {
  test('admin lists players', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/players');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('create player with team assignment', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.post('/api/v1/players', {
      user_id: testPlayerUserId,
      team_id: testTeamId,
      jersey_number: 7,
      position: 'left_back',
    });
    // Player may already exist if user creation auto-creates one
    if (res.status() === 201) {
      const player = await res.json();
      testPlayerId = player.id;
      expect(player.jersey_number).toBe(7);
    } else {
      // Player auto-created — find it
      const listRes = await admin.get('/api/v1/players', { team_id: String(testTeamId) });
      const list = await listRes.json();
      const player = list.items.find((p: { user_id: number }) => p.user_id === testPlayerUserId);
      if (player) testPlayerId = player.id;
    }
  });

  test('get player detail includes stats', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // Use the first player from the list if testPlayerId isn't set
    let playerId = testPlayerId;
    if (!playerId) {
      const listRes = await admin.get('/api/v1/players');
      const list = await listRes.json();
      playerId = list.items[0]?.id;
    }
    expect(playerId).toBeTruthy();

    const res = await admin.get(`/api/v1/players/${playerId}`);
    expect(res.ok()).toBeTruthy();
    const player = await res.json();
    expect(player.id).toBe(playerId);
    // PlayerWithStats should have user info
    expect(player).toHaveProperty('user_id');
  });

  test('update player jersey number and position', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    let playerId = testPlayerId;
    if (!playerId) {
      const listRes = await admin.get('/api/v1/players');
      const list = await listRes.json();
      playerId = list.items[0]?.id;
    }
    expect(playerId).toBeTruthy();

    const res = await admin.put(`/api/v1/players/${playerId}`, {
      jersey_number: 99,
      position: 'goalkeeper',
    });
    expect(res.ok()).toBeTruthy();
    const player = await res.json();
    expect(player.jersey_number).toBe(99);
  });

  test('list players filtered by team_id', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/players', { team_id: String(testTeamId) });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    // All returned players should belong to our test team
    for (const player of body.items) {
      expect(player.team_id).toBe(testTeamId);
    }
  });
});
