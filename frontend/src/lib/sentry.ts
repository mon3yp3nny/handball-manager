/**
 * Sentry wiring for the SPA (#64).
 *
 * Mirrors the backend contract: no-op when VITE_SENTRY_DSN is unset, and
 * never ships PII — only user_id + role go on the scope, never email or
 * name. The Sentry SDK is still imported eagerly so `setSentryUser`
 * etc. can be called safely whether init ran or not.
 *
 * Build-time env vars (Vite inlines anything prefixed with VITE_):
 *   VITE_SENTRY_DSN              — required to enable. Leave unset to disable.
 *   VITE_SENTRY_ENVIRONMENT      — 'development' | 'production' (default: MODE).
 *   VITE_GIT_SHA                 — short SHA from Cloud Build; used as release tag.
 *   VITE_SENTRY_TRACES_RATE      — sample rate for perf transactions (default 0.1).
 */
import * as Sentry from '@sentry/react';

/** Headers + body fields we wipe before an event leaves the browser. */
const SCRUB_HEADERS = new Set([
  'authorization',
  'cookie',
  'set-cookie',
  'x-csrf-token',
]);
const SCRUB_BODY_KEYS = new Set([
  'password',
  'current_password',
  'new_password',
  'token',
  'refresh_token',
]);

function scrubRequest(request: Record<string, any> | undefined) {
  if (!request) return;
  const headers = request.headers;
  if (headers && typeof headers === 'object') {
    for (const k of Object.keys(headers)) {
      if (SCRUB_HEADERS.has(k.toLowerCase())) headers[k] = '[scrubbed]';
    }
  }
  const data = request.data;
  if (data && typeof data === 'object') {
    for (const k of Object.keys(data)) {
      if (SCRUB_BODY_KEYS.has(k.toLowerCase())) data[k] = '[scrubbed]';
    }
  }
}

/** Returns true iff Sentry was initialized — i.e. a DSN was present. */
export function initSentry(): boolean {
  const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;
  if (!dsn) {
    // No console noise — this is the dev default.
    return false;
  }

  const release = (import.meta.env.VITE_GIT_SHA as string | undefined) || undefined;
  const environment =
    (import.meta.env.VITE_SENTRY_ENVIRONMENT as string | undefined) ||
    import.meta.env.MODE;
  const tracesSampleRate = Number(
    import.meta.env.VITE_SENTRY_TRACES_RATE ?? 0.1,
  );

  Sentry.init({
    dsn,
    release,
    environment,
    tracesSampleRate,
    // Don't send the IP address, cookies, or other browser PII.
    sendDefaultPii: false,
    integrations: [Sentry.browserTracingIntegration()],
    beforeSend(event, hint) {
      // Filter expected 4xx HTTP errors raised from axios — they
      // aren't actionable bugs.
      const err = hint?.originalException as any;
      const status =
        err?.response?.status ??
        err?.status ??
        undefined;
      if (typeof status === 'number' && status >= 400 && status < 500) {
        return null;
      }
      scrubRequest(event.request as Record<string, any> | undefined);
      return event;
    },
  });
  return true;
}

/** Attach user_id + role to the Sentry scope after login. */
export function setSentryUser(userId: number | string, role?: string | null) {
  Sentry.setUser({ id: String(userId), ...(role ? { role } : {}) });
}

/** Drop user context (called on logout). */
export function clearSentryUser() {
  Sentry.setUser(null);
}

/** Manually capture a caught error with optional extra context. */
export function captureError(error: unknown, context?: Record<string, unknown>) {
  if (context) {
    Sentry.withScope((scope) => {
      Object.entries(context).forEach(([k, v]) => scope.setExtra(k, v));
      Sentry.captureException(error);
    });
  } else {
    Sentry.captureException(error);
  }
}
