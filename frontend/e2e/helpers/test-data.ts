export const API_BASE = process.env.API_BASE_URL ?? 'https://handball-backend-218596927281.europe-west1.run.app';
export const APP_BASE = process.env.APP_BASE_URL ?? 'https://handball-frontend-218596927281.europe-west1.run.app';

// Accounts seeded on the deployment. Admin comes from setup_data.py /
// reset_db.py; the coach + parent are approved accounts from the
// season-storyline seed (seed_storyline.py). All storyline accounts share
// the Saison2627! password.
export const ADMIN_CREDENTIALS = {
  email: 'admin@handball.local',
  password: 'Admin123!',
};

export const COACH_CREDENTIALS = {
  email: 'stefan.brandt@tvf.de',
  password: 'Saison2627!',
};

export const PARENT_CREDENTIALS = {
  email: 'ralf.mertens@tvf.de',
  password: 'Saison2627!',
};

/** Generate a unique name using timestamp + random suffix */
export function uniqueName(prefix: string): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 6);
  return `${prefix}-${ts}-${rand}`;
}
