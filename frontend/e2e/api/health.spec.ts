import { test, expect } from '@playwright/test';
import { API_BASE } from '../helpers/test-data';

test.describe('Health API', () => {
  test('GET /health/live returns alive status', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/v1/health/live`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe('alive');
  });

  test('GET /health/ready returns ready status with db info', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/v1/health/ready`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe('ready');
    expect(body.database).toBe('connected');
    expect(body.version).toBeTruthy();
  });

  test('health endpoints do not require authentication', async ({ request }) => {
    // No Authorization header — should still succeed
    const live = await request.get(`${API_BASE}/api/v1/health/live`);
    expect(live.ok()).toBeTruthy();

    const ready = await request.get(`${API_BASE}/api/v1/health/ready`);
    expect(ready.ok()).toBeTruthy();
  });
});
