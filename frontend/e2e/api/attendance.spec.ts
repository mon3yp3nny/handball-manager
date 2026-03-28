import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testTeamId: number;
let testEventId: number;
let testPlayerId: number;
let coachUserId: number;
let testPlayerUserId: number;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);

  const admin = new AuthenticatedClient(ctx, adminTokens);
  const coach = new AuthenticatedClient(ctx, coachTokens);

  const meRes = await coach.get('/api/v1/auth/me');
  const me = await meRes.json();
  coachUserId = me.id;

  // Create team with coach
  const teamRes = await admin.post('/api/v1/teams', {
    name: uniqueName('AttendTestTeam'),
    age_group: 'U15',
    coach_id: coachUserId,
  });
  const team = await teamRes.json();
  testTeamId = team.id;

  // Create a player user and add to team so attendance init works
  const email = `${uniqueName('attendplayer')}@test.de`;
  const userRes = await admin.post('/api/v1/users', {
    email,
    password: 'testpass123',
    first_name: 'Attend',
    last_name: 'Player',
    role: 'player',
  });
  const user = await userRes.json();
  testPlayerUserId = user.id;

  // Find the auto-created player profile and assign to team
  const playersRes = await admin.get('/api/v1/players');
  const players = await playersRes.json();
  const player = players.items.find((p: { user_id: number }) => p.user_id === user.id);
  if (player) {
    testPlayerId = player.id;
    // Add player to team
    await admin.post(`/api/v1/teams/${testTeamId}/players/${player.id}`);
  }

  // Create event for this team
  const start = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString();
  const end = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 90 * 60 * 1000).toISOString();
  const eventRes = await coach.post('/api/v1/events', {
    title: uniqueName('AttendTraining'),
    start_time: start,
    end_time: end,
    event_type: 'training',
    visibility: 'team',
    team_id: testTeamId,
  });
  const event = await eventRes.json();
  testEventId = event.id;

  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const coach = new AuthenticatedClient(ctx, coachTokens);
  const admin = new AuthenticatedClient(ctx, adminTokens);
  if (testEventId) await coach.delete(`/api/v1/events/${testEventId}`).catch(() => {});
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  if (testPlayerUserId) await admin.delete(`/api/v1/users/${testPlayerUserId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Attendance API', () => {
  test('list attendance', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/attendance');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('initialize event attendance creates pending records', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.post(`/api/v1/attendance/event/${testEventId}/initialize`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('message');
    expect(body).toHaveProperty('created');
  });

  test('get event attendance summary', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.get(`/api/v1/attendance/event/${testEventId}/summary`);
    expect(res.ok()).toBeTruthy();
    const summary = await res.json();
    expect(summary).toHaveProperty('event_id');
    expect(summary).toHaveProperty('total_players');
    expect(summary).toHaveProperty('present');
    expect(summary).toHaveProperty('absent');
    expect(summary).toHaveProperty('pending');
  });

  test('list attendance filtered by event_id', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/attendance', { event_id: String(testEventId) });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
  });

  test('get player attendance stats', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const playerId = testPlayerId;
    if (!playerId) {
      test.skip();
      return;
    }
    const res = await admin.get(`/api/v1/attendance/stats/player/${playerId}`);
    expect(res.ok()).toBeTruthy();
    const stats = await res.json();
    expect(stats).toHaveProperty('player_id');
    expect(stats).toHaveProperty('total');
    expect(stats).toHaveProperty('attendance_rate');
  });
});
