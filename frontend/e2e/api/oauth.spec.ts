import { test, expect } from '@playwright/test';
import { API_BASE } from '../helpers/test-data';

test.describe('OAuth API', () => {
  test('POST /oauth/google with invalid token returns error', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/v1/oauth/google`, {
      data: { token: 'invalid-google-token' },
    });
    // Should reject the invalid token — 400 or 401
    expect(res.ok()).toBeFalsy();
    expect([400, 401, 422]).toContain(res.status());
  });

  test('POST /oauth/apple with invalid token returns error', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/v1/oauth/apple`, {
      data: { token: 'invalid-apple-token' },
    });
    expect(res.ok()).toBeFalsy();
    expect([400, 401, 422]).toContain(res.status());
  });

  test('POST /oauth/set-role without auth returns 401', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/v1/oauth/set-role`, {
      data: { role: 'player' },
    });
    expect(res.status()).toBe(401);
  });
});
