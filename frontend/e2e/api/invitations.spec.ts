import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
let testTeamId: number;
let coachUserId: number;
let createdInvitationId: number | undefined;

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
    name: uniqueName('InviteTestTeam'),
    age_group: 'U15',
    coach_id: coachUserId,
  });
  const team = await teamRes.json();
  testTeamId = team.id;

  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  if (createdInvitationId) {
    await admin.delete(`/api/v1/invitations/${createdInvitationId}`).catch(() => {});
  }
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Invitations API', () => {
  test('admin sends invitation', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const email = `${uniqueName('invite')}@test.de`;
    const res = await admin.post('/api/v1/invitations/send', {
      email,
      first_name: 'Invited',
      last_name: 'Player',
      role: 'player',
      team_id: testTeamId,
    });
    if (res.status() === 429) {
      test.skip(true, 'Invitation rate limit (10/hour) exceeded');
      return;
    }
    expect([200, 201]).toContain(res.status());
    const inv = await res.json();
    expect(inv.email).toBe(email);
    expect(inv.role).toBe('player');
    createdInvitationId = inv.id;
  });

  test('list sent invitations', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/invitations/sent');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
  });

  test('get team invitations', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get(`/api/v1/invitations/${testTeamId}/invitations`);
    expect(res.ok()).toBeTruthy();
    const invitations = await res.json();
    expect(Array.isArray(invitations)).toBeTruthy();
  });

  test('resend invitation', async ({ request }) => {
    if (!createdInvitationId) {
      test.skip(true, 'No invitation created (rate limited)');
      return;
    }
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.post(`/api/v1/invitations/resend/${createdInvitationId}`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('message');
  });

  test('revoke invitation (delete)', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const email = `${uniqueName('revoke')}@test.de`;
    const createRes = await admin.post('/api/v1/invitations/send', {
      email,
      first_name: 'Revoke',
      last_name: 'Test',
      role: 'player',
      team_id: testTeamId,
    });
    if (createRes.status() === 429) {
      test.skip(true, 'Invitation rate limit (10/hour) exceeded');
      return;
    }
    const inv = await createRes.json();
    const res = await admin.delete(`/api/v1/invitations/${inv.id}`);
    expect(res.status()).toBe(204);
  });
});
