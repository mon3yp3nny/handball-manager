import { test, expect } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'https://handball-frontend-218596927281.europe-west1.run.app';

test.describe('User Account Lifecycle', () => {
  const testEmail = `test-${Date.now()}@example.com`;
  const testPassword = 'TestPass123!';
  const firstName = 'Test';
  const lastName = 'User';

  test.beforeEach(async ({ page }) => {
    // Clear any existing session
    await page.goto(`${BASE_URL}/login`);
    await page.evaluate(() => {
      localStorage.clear();
    });
  });

  test('complete user lifecycle: register → login → access profile → delete account', async ({ page }) => {
    // Step 1: Navigate to registration page
    await page.goto(`${BASE_URL}/login`);
    await page.click('text=Jetzt registrieren');
    
    // Verify we're on the registration page
    await expect(page).toHaveURL(/.*\/register/);
    await expect(page.getByText('Neues Konto erstellen')).toBeVisible();

    // Step 2: Fill registration form
    await page.fill('input#first_name', firstName);
    await page.fill('input#last_name', lastName);
    await page.fill('input#email', testEmail);
    await page.fill('input#phone', '+49 123 456789');
    await page.fill('input#password', testPassword);
    
    // Select role (Player)
    await page.getByLabel('Spieler').check();
    
    // Submit registration
    await page.click('button:has-text("Konto erstellen")');
    
    // Verify redirect to login page with success message
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.getByText('Registrierung erfolgreich!')).toBeVisible();

    // Step 3: Login with new credentials
    await page.fill('input#email', testEmail);
    await page.fill('input#password', testPassword);
    await page.click('button:has-text("Anmelden")');
    
    // Verify successful login and redirect to dashboard
    await expect(page).toHaveURL(/.*\//);
    await expect(page.getByText('Handball Manager')).toBeVisible();
    await expect(page.getByText(firstName)).toBeVisible();

    // Step 4: Navigate to profile page
    await page.click('text=Profil'); // Assuming there's a profile link
    await page.goto(`${BASE_URL}/profile`);
    
    // Verify profile page content
    await expect(page.getByText('Mein Profil')).toBeVisible();
    await expect(page.getByText(testEmail)).toBeVisible();
    await expect(page.getByText(firstName + ' ' + lastName)).toBeVisible();
    await expect(page.getByText('Spieler')).toBeVisible();

    // Step 5: Delete account
    await page.click('button:has-text("Konto löschen")');
    
    // Verify confirmation modal appears
    await expect(page.getByText('Bist du sicher')).toBeVisible();
    await expect(page.getByText('Diese Aktion kann nicht rückgängig')).toBeVisible();
    
    // Try without confirmation text (should be disabled)
    const deleteButton = page.getByText('Endgültig löschen');
    await expect(deleteButton).toBeDisabled();
    
    // Enter confirmation text
    await page.fill('input[placeholder="LÖSCHEN"]', 'LÖSCHEN');
    
    // Click delete button
    await deleteButton.click();
    
    // Verify success message
    await expect(page.getByText('Dein Konto wurde erfolgreich gelöscht')).toBeVisible();
    
    // Verify redirect to login page
    await expect(page).toHaveURL(/.*\/login/);

    // Step 6: Verify cannot login with deleted account
    await page.fill('input#email', testEmail);
    await page.fill('input#password', testPassword);
    await page.click('button:has-text("Anmelden")');
    
    // Should show error message
    await expect(page.getByText(/falsch|Fehler|nicht gefunden/)).toBeVisible();
  });

  test('register with existing email shows error', async ({ page }) => {
    // First, register a user
    const existingEmail = `existing-${Date.now()}@example.com`;
    
    await page.goto(`${BASE_URL}/register`);
    await page.fill('input#first_name', 'Existing');
    await page.fill('input#last_name', 'User');
    await page.fill('input#email', existingEmail);
    await page.fill('input#password', testPassword);
    await page.getByLabel('Spieler').check();
    await page.click('button:has-text("Konto erstellen")');
    
    await page.goto(`${BASE_URL}/login`);
    
    // Try to register with same email
    await page.goto(`${BASE_URL}/register`);
    await page.fill('input#first_name', 'Duplicate');
    await page.fill('input#last_name', 'User');
    await page.fill('input#email', existingEmail);
    await page.fill('input#password', testPassword);
    await page.getByLabel('Spieler').check();
    await page.click('button:has-text("Konto erstellen")');
    
    // Should show error
    await expect(page.getByText(/bereits|existiert|registered/)).toBeVisible();
  });

  test('login with wrong password shows error', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input#email', 'nonexistent@example.com');
    await page.fill('input#password', 'wrongpassword123');
    await page.click('button:has-text("Anmelden")');
    
    // Should show error
    await expect(page.getByText(/falsch|Fehler|Incorrect/)).toBeVisible();
  });

  test('access protected page without login redirects to login', async ({ page }) => {
    await page.goto(`${BASE_URL}/profile`);
    
    // Should redirect to login
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('cancel account deletion keeps user logged in', async ({ page }) => {
    // Register and login first
    const email = `cancel-${Date.now()}@example.com`;
    
    await page.goto(`${BASE_URL}/register`);
    await page.fill('input#first_name', 'Cancel');
    await page.fill('input#last_name', 'Test');
    await page.fill('input#email', email);
    await page.fill('input#password', testPassword);
    await page.getByLabel('Spieler').check();
    await page.click('button:has-text("Konto erstellen")');
    
    await page.fill('input#email', email);
    await page.fill('input#password', testPassword);
    await page.click('button:has-text("Anmelden")');
    
    await page.goto(`${BASE_URL}/profile`);
    
    // Click delete but cancel
    await page.click('button:has-text("Konto löschen")');
    await expect(page.getByText('Bist du sicher')).toBeVisible();
    await page.click('button:has-text("Abbrechen")');
    
    // Should still be on profile page
    await expect(page.getByText('Mein Profil')).toBeVisible();
    await expect(page.getByText(email)).toBeVisible();
  });
});

// API integration test for backend
test.describe('Backend API - User Lifecycle', () => {
  test('register endpoint creates user', async ({ request }) => {
    const email = `api-test-${Date.now()}@example.com`;
    
    const response = await request.post(`${BASE_URL}/api/v1/auth/register`, {
      data: {
        email,
        password: 'TestPass123!',
        first_name: 'API',
        last_name: 'Test',
        role: 'player'
      }
    });
    
    expect(response.status()).toBe(201);
    const body = await response.json();
    expect(body.email).toBe(email);
    expect(body.first_name).toBe('API');
  });

  test('login endpoint returns tokens', async ({ request }) => {
    // First register
    const email = `login-test-${Date.now()}@example.com`;
    const password = 'TestPass123!';
    
    await request.post(`${BASE_URL}/api/v1/auth/register`, {
      data: {
        email,
        password,
        first_name: 'Login',
        last_name: 'Test',
        role: 'player'
      }
    });
    
    // Then login
    const response = await request.post(`${BASE_URL}/api/v1/auth/login`, {
      form: {
        username: email,
        password
      }
    });
    
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.access_token).toBeDefined();
    expect(body.refresh_token).toBeDefined();
  });
});
