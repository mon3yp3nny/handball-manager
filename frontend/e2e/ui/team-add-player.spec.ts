import { test, expect, request as pwRequest } from '@playwright/test';
import { login, AuthenticatedClient, Tokens } from '../helpers/api-client';
import { loginAsAdmin } from '../helpers/ui-helpers';
import { ADMIN_CREDENTIALS, uniqueName } from '../helpers/test-data';

let adminTokens: Tokens;
let testTeamId: number;

test.beforeAll(async () => {
  const ctx = await pwRequest.newContext();
  adminTokens = await login(ctx, ADMIN_CREDENTIALS.email, ADMIN_CREDENTIALS.password);
  const admin = new AuthenticatedClient(ctx, adminTokens);

  // Create a test team
  const teamRes = await admin.post('/api/v1/teams', {
    name: uniqueName('AddPlayerTeam'),
    age_group: 'U15',
  });
  const team = await teamRes.json();
  testTeamId = team.id;

  await ctx.dispose();
});

test.afterAll(async () => {
  const ctx = await pwRequest.newContext();
  const admin = new AuthenticatedClient(ctx, adminTokens);
  if (testTeamId) await admin.delete(`/api/v1/teams/${testTeamId}`).catch(() => {});
  await ctx.dispose();
});

test.describe('Team Add Player Flow', () => {
  test('team detail page shows "Spieler hinzufügen" button for admin', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`/teams/${testTeamId}`);
    await page.waitForLoadState('networkidle');

    const addButton = page.locator('button:has-text("Spieler hinzufügen")');
    await expect(addButton).toBeVisible({ timeout: 10_000 });
  });

  test('clicking "Spieler hinzufügen" shows search panel', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`/teams/${testTeamId}`);
    await page.waitForLoadState('networkidle');

    // Click the add player button
    const addButton = page.locator('button:has-text("Spieler hinzufügen")');
    await addButton.click();

    // Should show search input
    const searchInput = page.locator('input[placeholder*="Spieler suchen"]');
    await expect(searchInput).toBeVisible({ timeout: 5_000 });

    // Button should now say "Abbrechen"
    const cancelButton = page.locator('button:has-text("Abbrechen")');
    await expect(cancelButton).toBeVisible();
  });

  test('cancel hides the search panel', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(`/teams/${testTeamId}`);
    await page.waitForLoadState('networkidle');

    // Open
    await page.locator('button:has-text("Spieler hinzufügen")').click();
    const searchInput = page.locator('input[placeholder*="Spieler suchen"]');
    await expect(searchInput).toBeVisible({ timeout: 5_000 });

    // Cancel
    await page.locator('button:has-text("Abbrechen")').click();
    await expect(searchInput).not.toBeVisible({ timeout: 3_000 });
  });

  test('add player to team via API and verify on page', async ({ page, request }) => {
    const admin = new AuthenticatedClient(request, adminTokens);

    // Create a player user
    const email = `${uniqueName('uiplayer')}@test.de`;
    const userRes = await admin.post('/api/v1/users', {
      email,
      password: 'testpass123',
      first_name: 'UITest',
      last_name: 'Player',
      role: 'player',
    });
    const user = await userRes.json();

    // Find auto-created player and add to team via API
    const playersRes = await admin.get('/api/v1/players');
    const players = await playersRes.json();
    const player = players.items.find((p: { user_id: number }) => p.user_id === user.id);
    expect(player).toBeTruthy();

    const addRes = await admin.post(`/api/v1/teams/${testTeamId}/players/${player.id}`);
    expect(addRes.ok()).toBeTruthy();

    // Now verify in the UI
    await loginAsAdmin(page);
    await page.goto(`/teams/${testTeamId}`);
    await page.waitForLoadState('networkidle');
    // Wait for data to render
    await page.waitForTimeout(3_000);

    // Player should appear in the roster — check for first name or full name
    const playerText = await page.textContent('body');
    expect(playerText).toContain('UITest');

    // Clean up
    await admin.delete(`/api/v1/teams/${testTeamId}/players/${player.id}`).catch(() => {});
    await admin.delete(`/api/v1/users/${user.id}`).catch(() => {});
  });
});
