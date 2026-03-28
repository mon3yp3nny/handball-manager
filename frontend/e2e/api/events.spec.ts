import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testTeamId: number;
let coachUserId: number;
const createdEventIds: number[] = [];

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);

  const admin = new AuthenticatedClient(ctx, adminTokens);
  const coach = new AuthenticatedClient(ctx, coachTokens);

  const meRes = await coach.get('/api/v1/auth/me');
  const me = await meRes.json();
  coachUserId = me.id;

  const teamRes = await admin.post('/api/v1/teams', {
    name: uniqueName('EventTestTeam'),
    age_group: 'U15',
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
  for (const id of createdEventIds) {
    await coach.delete(`/api/v1/events/${id}`).catch(() => {});
  }
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Events API', () => {
  test('coach creates training event', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const start = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString();
    const end = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 90 * 60 * 1000).toISOString();
    const res = await coach.post('/api/v1/events', {
      title: uniqueName('Training'),
      description: 'Test training session',
      start_time: start,
      end_time: end,
      location: 'Trainingshalle',
      event_type: 'training',
      visibility: 'team',
      team_id: testTeamId,
    });
    expect(res.status()).toBe(201);
    const event = await res.json();
    expect(event.event_type).toBe('training');
    expect(event.team_id).toBe(testTeamId);
    createdEventIds.push(event.id);
  });

  test('coach creates meeting event', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const start = new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString();
    const end = new Date(Date.now() + 4 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString();
    const res = await coach.post('/api/v1/events', {
      title: uniqueName('Meeting'),
      description: 'Team meeting',
      start_time: start,
      end_time: end,
      event_type: 'other',
      visibility: 'club_wide',
    });
    expect(res.status()).toBe(201);
    const event = await res.json();
    createdEventIds.push(event.id);
  });

  test('list events returns paginated response', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/events');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('list events filtered by team_id', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.get('/api/v1/events', { team_id: String(testTeamId) });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    for (const event of body.items) {
      expect(event.team_id).toBe(testTeamId);
    }
  });

  test('list events with upcoming=true', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/events', { upcoming: 'true' });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
  });

  test('update event', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const eventId = createdEventIds[0];
    expect(eventId).toBeTruthy();
    const res = await coach.put(`/api/v1/events/${eventId}`, {
      title: 'Updated Training',
      location: 'Neue Halle',
    });
    expect(res.ok()).toBeTruthy();
    const event = await res.json();
    expect(event.title).toBe('Updated Training');
  });

  test('delete event', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    // Create throwaway
    const start = new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString();
    const end = new Date(Date.now() + 6 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString();
    const createRes = await coach.post('/api/v1/events', {
      title: 'ToDelete',
      start_time: start,
      end_time: end,
      event_type: 'other',
      visibility: 'team',
      team_id: testTeamId,
    });
    const event = await createRes.json();
    const res = await coach.delete(`/api/v1/events/${event.id}`);
    expect(res.status()).toBe(204);
  });

  test('calendar endpoint returns events', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/events/calendar/all', { days: '30' });
    expect(res.ok()).toBeTruthy();
    const events = await res.json();
    expect(Array.isArray(events)).toBeTruthy();
  });
});
