/**
 * Vitest setup — runs before every test file (#55).
 *
 * - Wires @testing-library/jest-dom so we can assert `toBeInTheDocument`
 *   and friends without importing them in every test file.
 * - Auto-cleans up the DOM between tests so leftover renders don't
 *   leak state across `it()` blocks.
 * - Provides stable stubs for browser APIs jsdom doesn't ship by default
 *   (matchMedia, IntersectionObserver, scrollTo) — landing pages call
 *   these on mount and would otherwise crash before the actual assertion.
 */
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

// matchMedia — used by Tailwind's responsive utilities & some libs.
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// IntersectionObserver — Recharts, virtualization libs, lazy images.
class MockIntersectionObserver {
  readonly root = null;
  readonly rootMargin = '';
  readonly thresholds: readonly number[] = [];
  disconnect = vi.fn();
  observe = vi.fn();
  takeRecords = vi.fn().mockReturnValue([]);
  unobserve = vi.fn();
}
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: MockIntersectionObserver,
});

// scrollTo — react-router calls this on navigation in some setups.
Object.defineProperty(window, 'scrollTo', { writable: true, value: vi.fn() });
