export const API_BASE = process.env.API_BASE_URL ?? 'https://handball-backend-218596927281.europe-west1.run.app';
export const APP_BASE = process.env.APP_BASE_URL ?? 'https://handball-frontend-218596927281.europe-west1.run.app';

export const ADMIN_CREDENTIALS = {
  email: 'admin@handball.de',
  password: 'admin123',
};

export const COACH_CREDENTIALS = {
  email: 'coach@handball.de',
  password: 'coach123',
};

export const PARENT_CREDENTIALS = {
  email: 'eltern@handball.de',
  password: 'parent123',
};

/** Generate a unique name using timestamp + random suffix */
export function uniqueName(prefix: string): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 6);
  return `${prefix}-${ts}-${rand}`;
}
