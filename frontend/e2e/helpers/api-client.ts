import { APIRequestContext } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { API_BASE } from './test-data';

export interface Tokens {
  access_token: string;
  refresh_token: string;
}

const CACHE_DIR = path.join(process.cwd(), 'e2e', '.token-cache');

function getCachePath(email: string): string {
  return path.join(CACHE_DIR, `${email.replace(/[@.]/g, '_')}.json`);
}

function isTokenExpired(accessToken: string): boolean {
  try {
    const payload = JSON.parse(
      Buffer.from(accessToken.split('.')[1], 'base64').toString('utf-8'),
    );
    return typeof payload.exp !== 'number' || payload.exp * 1000 < Date.now() + 60_000;
  } catch {
    return true;
  }
}

function readCachedTokens(email: string): Tokens | null {
  try {
    const data = fs.readFileSync(getCachePath(email), 'utf-8');
    const tokens: Tokens = JSON.parse(data);
    if (isTokenExpired(tokens.access_token)) return null;
    return tokens;
  } catch {
    return null;
  }
}

function writeCachedTokens(email: string, tokens: Tokens): void {
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
  }
  fs.writeFileSync(getCachePath(email), JSON.stringify(tokens));
}

/**
 * Login and return JWT tokens. Cached to disk to avoid hitting rate limits
 * across test files (5/min on the login endpoint).
 */
export async function login(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<Tokens> {
  // Check disk cache first
  const cached = readCachedTokens(email);
  if (cached) return cached;

  const res = await request.post(`${API_BASE}/api/v1/auth/login`, {
    form: { username: email, password },
  });
  if (!res.ok()) {
    throw new Error(`Login failed (${res.status()}): ${await res.text()}`);
  }
  const tokens: Tokens = await res.json();
  writeCachedTokens(email, tokens);
  return tokens;
}

/**
 * Clear the token cache. Call this if tokens have expired.
 */
export function clearTokenCache(): void {
  if (fs.existsSync(CACHE_DIR)) {
    fs.rmSync(CACHE_DIR, { recursive: true, force: true });
  }
}

/**
 * Create an authenticated helper that attaches the Bearer token to every request.
 */
export class AuthenticatedClient {
  constructor(
    private request: APIRequestContext,
    private tokens: Tokens,
  ) {}

  private get headers() {
    return { Authorization: `Bearer ${this.tokens.access_token}` };
  }

  private url(path: string) {
    return `${API_BASE}${path}`;
  }

  async get(path: string, params?: Record<string, string | number | boolean>) {
    return this.request.get(this.url(path), {
      headers: this.headers,
      params: params as Record<string, string>,
    });
  }

  async post(path: string, data?: unknown) {
    return this.request.post(this.url(path), {
      headers: this.headers,
      data,
    });
  }

  async put(path: string, data?: unknown) {
    return this.request.put(this.url(path), {
      headers: this.headers,
      data,
    });
  }

  async patch(path: string, data?: unknown) {
    return this.request.patch(this.url(path), {
      headers: this.headers,
      data,
    });
  }

  async delete(path: string) {
    return this.request.delete(this.url(path), {
      headers: this.headers,
    });
  }
}

/**
 * Convenience: login + return an AuthenticatedClient.
 */
export async function authenticatedClient(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<AuthenticatedClient> {
  const tokens = await login(request, email, password);
  return new AuthenticatedClient(request, tokens);
}
