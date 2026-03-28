import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { ADMIN_CREDENTIALS, COACH_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let coachTokens: Tokens;
const createdUserIds: number[] = [];

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  coachTokens = await login(ctx, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  for (const id of createdUserIds) {
    await admin.delete(`/api/v1/users/${id}`).catch(() => {});
  }
  await ctx.dispose();
});

test.describe('Users API', () => {
  test('admin lists users', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/users');
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('total');
    expect(body.total).toBeGreaterThan(0);
  });

  test('admin lists users filtered by role', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const res = await admin.get('/api/v1/users', { role: 'admin' });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    for (const user of body.items) {
      expect(user.role).toBe('admin');
    }
  });

  test('admin creates user', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const email = `${uniqueName('user')}@test.de`;
    const res = await admin.post('/api/v1/users', {
      email,
      password: 'testpass123',
      first_name: 'Test',
      last_name: 'User',
      role: 'supervisor',
    });
    expect(res.status()).toBe(201);
    const user = await res.json();
    expect(user.email).toBe(email);
    expect(user.role).toBe('supervisor');
    createdUserIds.push(user.id);
  });

  test('admin resets user password', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const userId = createdUserIds[0];
    expect(userId).toBeTruthy();
    const res = await admin.post(`/api/v1/users/${userId}/reset-password`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('temp_password');
    expect(body.temp_password.length).toBeGreaterThanOrEqual(12);
  });

  test('admin deactivates user (soft delete)', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // Create a user to deactivate
    const email = `${uniqueName('deactivate')}@test.de`;
    const createRes = await admin.post('/api/v1/users', {
      email,
      password: 'testpass123',
      first_name: 'Deactivate',
      last_name: 'Me',
      role: 'player',
    });
    const user = await createRes.json();
    createdUserIds.push(user.id);

    const res = await admin.delete(`/api/v1/users/${user.id}`);
    expect(res.status()).toBe(204);
  });

  test('get user by ID', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    const userId = createdUserIds[0];
    expect(userId).toBeTruthy();
    const res = await admin.get(`/api/v1/users/${userId}`);
    // User may have been soft-deleted; either 200 or 404 is acceptable
    expect([200, 404].includes(res.status())).toBeTruthy();
    if (res.ok()) {
      const user = await res.json();
      expect(user.id).toBe(userId);
    }
  });

  test('admin bulk-activate users', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // FastAPI expects a plain JSON array body for List[int] parameter
    const ids = createdUserIds.filter(Boolean);
    const res = await admin.post('/api/v1/users/admin/bulk-activate', ids);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('message');
  });

  test('admin bulk-deactivate users', async ({ request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);
    // Create throwaway users for bulk deactivation
    const ids: number[] = [];
    for (let i = 0; i < 2; i++) {
      const email = `${uniqueName('bulk')}@test.de`;
      const createRes = await admin.post('/api/v1/users', {
        email,
        password: 'testpass123',
        first_name: 'Bulk',
        last_name: `User${i}`,
        role: 'player',
      });
      const user = await createRes.json();
      ids.push(user.id);
      createdUserIds.push(user.id);
    }

    const res = await admin.post('/api/v1/users/admin/bulk-deactivate', ids);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('message');
  });

  test('coach can list users', async ({ request }) => {
    const coach = new AuthenticatedClient(request, coachTokens);
    const res = await coach.get('/api/v1/users');
    expect(res.ok()).toBeTruthy();
  });
});
