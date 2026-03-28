import { test, expect } from '@playwright/test';
import { authenticatedClient } from '../helpers/api-client';
import { PARENT_CREDENTIALS, ADMIN_CREDENTIALS, COACH_CREDENTIALS } from '../helpers/test-data';

test.describe('Parents API', () => {
  test('parent can list their children', async ({ request }) => {
    const client = await authenticatedClient(request, PARENT_CREDENTIALS.email, PARENT_CREDENTIALS.password);
    const res = await client.get('/api/v1/parents/children');
    expect(res.ok()).toBeTruthy();
    const children = await res.json();
    expect(Array.isArray(children)).toBeTruthy();
  });

  test('coach cannot list children (403)', async ({ request }) => {
    const client = await authenticatedClient(request, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
    const res = await client.get('/api/v1/parents/children');
    expect(res.status()).toBe(403);
  });

  test('admin can list children for a specific parent', async ({ request }) => {
    const adminClient = await authenticatedClient(request, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);

    // First get the parent user's ID
    const meRes = await (await authenticatedClient(request, PARENT_CREDENTIALS.email, PARENT_CREDENTIALS.password)).get('/api/v1/auth/me');
    const parentUser = await meRes.json();

    const res = await adminClient.get(`/api/v1/parents/${parentUser.id}/children`);
    expect(res.ok()).toBeTruthy();
    const children = await res.json();
    expect(Array.isArray(children)).toBeTruthy();
  });

  test('non-admin cannot use admin children endpoint (403 or 401)', async ({ request }) => {
    const client = await authenticatedClient(request, COACH_CREDENTIALS.email, COACH_CREDENTIALS.password);
    // Use a dummy parent_id — should fail with 403 before validating the ID
    const res = await client.get('/api/v1/parents/1/children');
    expect([401, 403]).toContain(res.status());
  });

  test('link non-existent player returns 404', async ({ request }) => {
    const client = await authenticatedClient(request, PARENT_CREDENTIALS.email, PARENT_CREDENTIALS.password);
    const res = await client.post('/api/v1/parents/children/999999');
    expect(res.status()).toBe(404);
  });

  test('get parents for non-existent player returns 404', async ({ request }) => {
    const client = await authenticatedClient(request, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
    const res = await client.get('/api/v1/parents/player/999999/parents');
    expect(res.status()).toBe(404);
  });
});
