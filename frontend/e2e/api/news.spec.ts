import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testTeamId: number;
let coachUserId: number;
const createdNewsIds: number[] = [];

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
    name: uniqueName('NewsTestTeam'),
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
  for (const id of createdNewsIds) {
    await coach.delete(`/api/v1/news/${id}`).catch(() => {});
  }
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('News API', () => {
  test('coach creates news draft', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.post('/api/v1/news', {
      title: uniqueName('Draft'),
      content: 'This is a draft news article.',
      team_id: testTeamId,
      is_published: false,
    });
    expect(res.status()).toBe(201);
    const news = await res.json();
    expect(news.is_published).toBe(false);
    expect(news.title).toContain('Draft');
    createdNewsIds.push(news.id);
  });

  test('coach creates and publishes news', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.post('/api/v1/news', {
      title: uniqueName('Published'),
      content: 'Published news content.',
      team_id: testTeamId,
      is_published: true,
    });
    expect(res.status()).toBe(201);
    const news = await res.json();
    expect(news.is_published).toBe(true);
    createdNewsIds.push(news.id);
  });

  test('list news returns paginated response', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/news');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('list news with only_published=true excludes drafts', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/news', { only_published: 'true' });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    for (const news of body.items) {
      expect(news.is_published).toBe(true);
    }
  });

  test('publish news via PATCH', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const draftId = createdNewsIds[0]; // the draft
    expect(draftId).toBeTruthy();
    const res = await coach.patch(`/api/v1/news/${draftId}/publish`, {
      is_published: true,
    });
    expect(res.ok()).toBeTruthy();
    const news = await res.json();
    expect(news.is_published).toBe(true);
  });

  test('update news content', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const newsId = createdNewsIds[0];
    expect(newsId).toBeTruthy();
    const res = await coach.put(`/api/v1/news/${newsId}`, {
      title: 'Updated Title',
      content: 'Updated content.',
    });
    expect(res.ok()).toBeTruthy();
    const news = await res.json();
    expect(news.title).toBe('Updated Title');
  });

  test('get news by ID', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const newsId = createdNewsIds[0];
    expect(newsId).toBeTruthy();
    const res = await admin.get(`/api/v1/news/${newsId}`);
    expect(res.ok()).toBeTruthy();
    const news = await res.json();
    expect(news.id).toBe(newsId);
  });

  test('delete news', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const createRes = await coach.post('/api/v1/news', {
      title: 'ToDelete',
      content: 'Temp.',
      team_id: testTeamId,
    });
    const news = await createRes.json();
    const res = await coach.delete(`/api/v1/news/${news.id}`);
    expect(res.status()).toBe(204);
  });
});
