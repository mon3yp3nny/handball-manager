/**
 * Tests for the Sentry wrapper (#55, covering the #64 wiring).
 *
 * We mock `@sentry/react` wholesale so the tests assert what our
 * wrapper does — calls init when DSN is set, no-ops when it's not,
 * scrubs credentials before send, drops 4xx axios errors — without
 * involving the real SDK or network.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

// Mock the sentry-react module before importing the wrapper. The mock
// has to be hoisted because vi.mock factories run before imports.
vi.mock('@sentry/react', () => ({
  init: vi.fn(),
  setUser: vi.fn(),
  withScope: vi.fn((fn) => fn({ setExtra: vi.fn() })),
  captureException: vi.fn(),
  browserTracingIntegration: vi.fn(() => ({ name: 'BrowserTracing' })),
}));

import * as Sentry from '@sentry/react';
import { initSentry, setSentryUser, clearSentryUser, captureError } from '../sentry';

// Helper: stash a backup of import.meta.env that we can restore after
// each test. import.meta.env is partially writable in Vite.
const originalEnv = { ...import.meta.env };

afterEach(() => {
  vi.clearAllMocks();
  // Restore env so tests don't leak state.
  for (const key of Object.keys(import.meta.env)) {
    if (!(key in originalEnv)) {
      delete (import.meta.env as any)[key];
    }
  }
  Object.assign(import.meta.env, originalEnv);
});

describe('initSentry', () => {
  it('returns false and does nothing when VITE_SENTRY_DSN is unset', () => {
    delete (import.meta.env as any).VITE_SENTRY_DSN;
    expect(initSentry()).toBe(false);
    expect(Sentry.init).not.toHaveBeenCalled();
  });

  it('returns false when VITE_SENTRY_DSN is empty string', () => {
    (import.meta.env as any).VITE_SENTRY_DSN = '';
    expect(initSentry()).toBe(false);
    expect(Sentry.init).not.toHaveBeenCalled();
  });

  it('calls Sentry.init with DSN + release tag when configured', () => {
    (import.meta.env as any).VITE_SENTRY_DSN = 'https://abc@o0.ingest.sentry.io/0';
    (import.meta.env as any).VITE_GIT_SHA = 'deadbeef';
    (import.meta.env as any).VITE_SENTRY_ENVIRONMENT = 'production';

    expect(initSentry()).toBe(true);
    expect(Sentry.init).toHaveBeenCalledOnce();

    const cfg = (Sentry.init as any).mock.calls[0][0];
    expect(cfg.dsn).toBe('https://abc@o0.ingest.sentry.io/0');
    expect(cfg.release).toBe('deadbeef');
    expect(cfg.environment).toBe('production');
    expect(cfg.sendDefaultPii).toBe(false);
    expect(typeof cfg.beforeSend).toBe('function');
  });

  it('falls back to MODE when VITE_SENTRY_ENVIRONMENT is unset', () => {
    (import.meta.env as any).VITE_SENTRY_DSN = 'https://abc@o0.ingest.sentry.io/0';
    delete (import.meta.env as any).VITE_SENTRY_ENVIRONMENT;
    (import.meta.env as any).MODE = 'staging';

    initSentry();
    const cfg = (Sentry.init as any).mock.calls[0][0];
    expect(cfg.environment).toBe('staging');
  });
});

describe('beforeSend filter', () => {
  // Trigger init once and pull the beforeSend it registered.
  function getBeforeSend() {
    (import.meta.env as any).VITE_SENTRY_DSN = 'https://abc@o0.ingest.sentry.io/0';
    initSentry();
    return (Sentry.init as any).mock.calls[0][0].beforeSend;
  }

  it('drops axios errors with 4xx response.status', () => {
    const beforeSend = getBeforeSend();
    const event = {} as any;
    const hint = {
      originalException: { response: { status: 404 } },
    };
    expect(beforeSend(event, hint)).toBeNull();
  });

  it('drops axios errors with status 401 (cookie expired etc.)', () => {
    const beforeSend = getBeforeSend();
    const result = beforeSend({} as any, {
      originalException: { response: { status: 401 } },
    });
    expect(result).toBeNull();
  });

  it('passes 5xx errors through', () => {
    const beforeSend = getBeforeSend();
    const event = { request: {} } as any;
    const result = beforeSend(event, {
      originalException: { response: { status: 500 } },
    });
    expect(result).toBe(event);  // returned, not nullified
  });

  it('passes plain Error (no response status) through', () => {
    const beforeSend = getBeforeSend();
    const event = { request: {} } as any;
    const result = beforeSend(event, { originalException: new Error('boom') });
    expect(result).toBe(event);
  });

  it('scrubs Authorization header from passing events', () => {
    const beforeSend = getBeforeSend();
    const event = {
      request: { headers: { Authorization: 'Bearer secret', 'X-Other': 'ok' } },
    } as any;
    const result = beforeSend(event, { originalException: new Error('boom') });
    expect(result.request.headers.Authorization).toBe('[scrubbed]');
    expect(result.request.headers['X-Other']).toBe('ok');
  });

  it('scrubs cookie + csrf headers (case-insensitive)', () => {
    const beforeSend = getBeforeSend();
    const event = {
      request: {
        headers: {
          cookie: 'access_token=x',
          'Set-Cookie': 'y=1',
          'x-csrf-token': 'abc',
        },
      },
    } as any;
    const result = beforeSend(event, { originalException: new Error('x') });
    expect(result.request.headers.cookie).toBe('[scrubbed]');
    expect(result.request.headers['Set-Cookie']).toBe('[scrubbed]');
    expect(result.request.headers['x-csrf-token']).toBe('[scrubbed]');
  });

  it('scrubs password + token fields from request body', () => {
    const beforeSend = getBeforeSend();
    const event = {
      request: {
        data: {
          email: 'a@b.test',
          password: 'hunter2',
          new_password: 'x',
          refresh_token: 'rt',
        },
      },
    } as any;
    const result = beforeSend(event, { originalException: new Error('x') });
    expect(result.request.data.email).toBe('a@b.test');
    expect(result.request.data.password).toBe('[scrubbed]');
    expect(result.request.data.new_password).toBe('[scrubbed]');
    expect(result.request.data.refresh_token).toBe('[scrubbed]');
  });

  it('handles events without a request dict (background tasks)', () => {
    const beforeSend = getBeforeSend();
    const event = { level: 'error' } as any;
    const result = beforeSend(event, { originalException: new Error('x') });
    expect(result).toEqual({ level: 'error' });
  });
});

describe('setSentryUser / clearSentryUser', () => {
  it('attaches id + role on login', () => {
    setSentryUser(42, 'coach');
    expect(Sentry.setUser).toHaveBeenCalledWith({ id: '42', role: 'coach' });
  });

  it('attaches id only when role is missing', () => {
    setSentryUser(7);
    expect(Sentry.setUser).toHaveBeenCalledWith({ id: '7' });
  });

  it('passes role through when provided as null (treated as missing)', () => {
    setSentryUser(7, null);
    expect(Sentry.setUser).toHaveBeenCalledWith({ id: '7' });
  });

  it('coerces numeric ids to strings (Sentry expects strings)', () => {
    setSentryUser(123, 'admin');
    expect(Sentry.setUser).toHaveBeenCalledWith({ id: '123', role: 'admin' });
  });

  it('clears user context on logout', () => {
    clearSentryUser();
    expect(Sentry.setUser).toHaveBeenCalledWith(null);
  });
});

describe('captureError', () => {
  it('forwards plain errors to Sentry.captureException', () => {
    const err = new Error('boom');
    captureError(err);
    expect(Sentry.captureException).toHaveBeenCalledWith(err);
  });

  it('attaches extra context inside a withScope when provided', () => {
    const err = new Error('boom');
    const setExtra = vi.fn();
    (Sentry.withScope as any).mockImplementationOnce((fn: any) => fn({ setExtra }));

    captureError(err, { boundary: 'root', componentStack: 'stack' });

    expect(setExtra).toHaveBeenCalledWith('boundary', 'root');
    expect(setExtra).toHaveBeenCalledWith('componentStack', 'stack');
    expect(Sentry.captureException).toHaveBeenCalledWith(err);
  });
});
