import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
const createdTeamIds: number[] = [];

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  for (const id of createdTeamIds) {
    await admin.delete(`/api/v1/teams/${id}`).catch(() => {});
  }
  await ctx.dispose();
});

test.describe('Teams API', () => {
  test('admin lists teams', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/teams');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
    expect(Array.isArray(body.items)).toBeTruthy();
  });

  test('admin creates team', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const name = uniqueName('Team');
    const res = await admin.post('/api/v1/teams', {
      name,
      age_group: 'U15',
    });
    expect(res.status()).toBe(201);
    const team = await res.json();
    expect(team.name).toBe(name);
    expect(team.age_group).toBe('U15');
    expect(team.id).toBeTruthy();
    createdTeamIds.push(team.id);
  });

  test('admin creates team with coach_id', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // Get a coach user ID
    const usersRes = await admin.get('/api/v1/users', { role: 'coach' });
    const users = await usersRes.json();
    const coachUser = users.items[0];
    expect(coachUser).toBeTruthy();

    const name = uniqueName('CoachTeam');
    const res = await admin.post('/api/v1/teams', {
      name,
      age_group: 'U17',
      coach_id: coachUser.id,
    });
    expect(res.status()).toBe(201);
    const team = await res.json();
    expect(team.coach_id).toBe(coachUser.id);
    createdTeamIds.push(team.id);
  });

  test('get team by ID includes players array', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // Use first created team
    const teamId = createdTeamIds[0];
    expect(teamId).toBeTruthy();
    const res = await admin.get(`/api/v1/teams/${teamId}`);
    expect(res.ok()).toBeTruthy();
    const team = await res.json();
    expect(team.id).toBe(teamId);
    expect(Array.isArray(team.players)).toBeTruthy();
  });

  test('admin updates team name', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const teamId = createdTeamIds[0];
    const newName = uniqueName('Updated');
    const res = await admin.put(`/api/v1/teams/${teamId}`, { name: newName });
    expect(res.ok()).toBeTruthy();
    const team = await res.json();
    expect(team.name).toBe(newName);
  });

  test('admin deletes team', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // Create a throwaway team to delete
    const createRes = await admin.post('/api/v1/teams', {
      name: uniqueName('ToDelete'),
      age_group: 'U12',
    });
    const team = await createRes.json();
    const res = await admin.delete(`/api/v1/teams/${team.id}`);
    expect(res.status()).toBe(204);
  });

  test('add player to team and remove', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);

    // Create a player user
    const email = `${uniqueName('addremove')}@test.de`;
    const userRes = await admin.post('/api/v1/users', {
      email,
      password: 'testpass123',
      first_name: 'AddRemove',
      last_name: 'Player',
      role: 'player',
    });
    const user = await userRes.json();

    // Find auto-created player profile
    const playersRes = await admin.get('/api/v1/players');
    const players = await playersRes.json();
    const player = players.items.find((p: { user_id: number }) => p.user_id === user.id);
    expect(player).toBeTruthy();

    // Add player to team
    const teamId = createdTeamIds[0];
    expect(teamId).toBeTruthy();
    const addRes = await admin.post(`/api/v1/teams/${teamId}/players/${player.id}`);
    expect(addRes.ok()).toBeTruthy();

    // Verify player is on team
    const teamRes = await admin.get(`/api/v1/teams/${teamId}`);
    const team = await teamRes.json();
    expect(team.players.some((p: { id: number }) => p.id === player.id)).toBeTruthy();

    // Remove player from team
    const removeRes = await admin.delete(`/api/v1/teams/${teamId}/players/${player.id}`);
    expect(removeRes.ok()).toBeTruthy();

    // Clean up user
    await admin.delete(`/api/v1/users/${user.id}`).catch(() => {});
  });

  test('coach cannot create teams (admin-only)', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.post('/api/v1/teams', {
      name: uniqueName('CoachTeam'),
      age_group: 'U15',
    });
    expect(res.status()).toBe(403);
  });
});
