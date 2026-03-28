import { test, expect } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { API_BASE, ADMIN_CREDENTIALS } from '../helpers/test-data';

test.describe('Auth API', () => {
  test('login with valid credentials returns tokens', async ({ request }) => {
    const tokens = await login(request, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
    expect(tokens.access_token).toBeTruthy();
    expect(tokens.refresh_token).toBeTruthy();
  });

  test('login with wrong password returns 401 or 429', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/v1/auth/login`, {
      form: { username: ADMIN_CREDENTIALS.email, password: 'wrongpassword' },
    });
    // May be rate-limited (429) from previous login calls
    expect([401, 429]).toContain(res.status());
  });

  test('login with non-existent email returns 401 or 429', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/v1/auth/login`, {
      form: { username: 'nobody@example.com', password: 'whatever' },
    });
    expect([401, 429]).toContain(res.status());
  });

  test('token refresh with valid refresh token returns new tokens', async ({ request }) => {
    const tokens = await login(request, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
    // FastAPI expects refresh_token as query param since it's a plain str parameter
    const res = await request.post(`${API_BASE}/api/v1/auth/refresh?refresh_token=${encodeURIComponent(tokens.refresh_token)}`);
    expect(res.ok()).toBeTruthy();
    const newTokens = await res.json();
    expect(newTokens.access_token).toBeTruthy();
    expect(newTokens.refresh_token).toBeTruthy();
  });

  test('token refresh with invalid token returns error', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/v1/auth/refresh?refresh_token=invalid-token`);
    expect(res.ok()).toBeFalsy();
  });

  test('GET /auth/me with valid token returns user info', async ({ request }) => {
    const tokens = await login(request, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
    const client = new AuthenticatedClient(request, tokens);
    const res = await client.get('/api/v1/auth/me');
    expect(res.ok()).toBeTruthy();
    const user = await res.json();
    expect(user.email).toBe(ADMIN_CREDENTIALS.email);
    expect(user.role).toBe('admin');
    expect(user.id).toBeTruthy();
    expect(user.first_name).toBeTruthy();
  });

  test('GET /auth/me with invalid token returns 401', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/v1/auth/me`, {
      headers: { Authorization: 'Bearer invalid-token' },
    });
    expect(res.status()).toBe(401);
  });
});
