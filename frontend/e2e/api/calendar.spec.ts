import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { COACH_CREDENTIALS, API_BASE } from '../helpers/test-data';

let coachTokens: Tokens;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
  await ctx.dispose();
});

test.describe('Calendar API', () => {
  test('coach can fetch their calendar token (idempotent)', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const first = await coach.get('/api/v1/calendar/me/token');
    expect(first.ok()).toBeTruthy();
    const a = await first.json();
    expect(a.token).toBeTruthy();
    expect(a.url).toContain('/api/v1/calendar/');
    expect(a.url).toMatch(/\.ics$/);

    const second = await coach.get('/api/v1/calendar/me/token');
    const b = await second.json();
    expect(b.token).toBe(a.token);
  });

  test('feed is bearerless and returns a valid VCALENDAR', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const { token } = await (await coach.get('/api/v1/calendar/me/token')).json();

    // No Authorization header — calendar apps don't send one.
    const res = await request.get(`${API_BASE}/api/v1/calendar/${token}.ics`);
    expect(res.ok()).toBeTruthy();
    expect(res.headers()['content-type']).toMatch(/text\/calendar/);
    const body = await res.text();
    expect(body.startsWith('BEGIN:VCALENDAR\r\n')).toBeTruthy();
    expect(body).toContain('VERSION:2.0');
    expect(body.trimEnd().endsWith('END:VCALENDAR')).toBeTruthy();
  });

  test('rotating the token invalidates the old one', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const oldToken = (await (await coach.get('/api/v1/calendar/me/token')).json()).token;

    const rot = await coach.post('/api/v1/calendar/me/token');
    expect(rot.ok()).toBeTruthy();
    const { token: newToken } = await rot.json();
    expect(newToken).not.toBe(oldToken);

    const bad = await request.get(`${API_BASE}/api/v1/calendar/${oldToken}.ics`);
    expect(bad.status()).toBe(404);

    const good = await request.get(`${API_BASE}/api/v1/calendar/${newToken}.ics`);
    expect(good.ok()).toBeTruthy();
  });

  test('unknown token returns 404 (does not leak validity)', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/v1/calendar/totally-bogus-token.ics`);
    expect(res.status()).toBe(404);
  });
});
