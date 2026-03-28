import { defineConfig, devices } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL ?? 'https://handball-backend-218596927281.europe-west1.run.app';
const APP_BASE = process.env.APP_BASE_URL ?? 'https://handball-frontend-218596927281.europe-west1.run.app';

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'html',
  timeout: 30_000,
  use: {
    baseURL: APP_BASE,
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'api',
      testDir: './e2e/api',
      use: {
        baseURL: API_BASE,
      },
    },
    {
      name: 'ui',
      testDir: './e2e/ui',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: APP_BASE,
      },
    },
  ],
});
