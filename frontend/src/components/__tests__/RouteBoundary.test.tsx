/**
 * Tests for RouteBoundary (#101).
 *
 * The point of this helper is route-keyed isolation:
 *   1. A crash inside the boundary renders the inline fallback —
 *      not the full-screen "reload the page" fallback.
 *   2. Sibling content OUTSIDE the boundary keeps working (this is
 *      the win — Sidebar/Header survive page crashes).
 *   3. Navigating to a different path auto-resets the boundary
 *      (resetKey={pathname}), so the user doesn't see a stale error
 *      after they've moved on.
 */
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route, Link } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/lib/sentry', () => ({
  captureError: vi.fn(),
}));

import { RouteBoundary } from '../RouteBoundary';
import { captureError } from '@/lib/sentry';

function Bomb({ message = 'crash' }: { message?: string }): JSX.Element {
  throw new Error(message);
}

let consoleErrorSpy: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => {
  consoleErrorSpy.mockRestore();
  cleanup();
  vi.clearAllMocks();
});

describe('RouteBoundary', () => {
  it('renders children when nothing throws', () => {
    render(
      <MemoryRouter initialEntries={['/foo']}>
        <RouteBoundary>
          <p>page content</p>
        </RouteBoundary>
      </MemoryRouter>,
    );
    expect(screen.getByText('page content')).toBeInTheDocument();
  });

  it('shows the inline (in-page) fallback when a child throws', () => {
    render(
      <MemoryRouter initialEntries={['/teams']}>
        <RouteBoundary>
          <Bomb />
        </RouteBoundary>
      </MemoryRouter>,
    );
    // The inline fallback's German copy.
    expect(
      screen.getByText('Diese Seite konnte nicht geladen werden'),
    ).toBeInTheDocument();
    // Not the full-screen variant.
    expect(screen.queryByText('Etwas ist schiefgelaufen')).not.toBeInTheDocument();
  });

  it('tags Sentry with the explicit name when provided', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <RouteBoundary name="login-page">
          <Bomb />
        </RouteBoundary>
      </MemoryRouter>,
    );
    const [, ctx] = (captureError as any).mock.calls[0];
    expect(ctx.boundary).toBe('login-page');
  });

  it('falls back to the pathname as the Sentry tag when name is omitted', () => {
    render(
      <MemoryRouter initialEntries={['/players']}>
        <RouteBoundary>
          <Bomb />
        </RouteBoundary>
      </MemoryRouter>,
    );
    const [, ctx] = (captureError as any).mock.calls[0];
    expect(ctx.boundary).toBe('/players');
  });

  it('switches to the full-screen fallback when inline=false', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <RouteBoundary inline={false}>
          <Bomb />
        </RouteBoundary>
      </MemoryRouter>,
    );
    expect(screen.getByText('Etwas ist schiefgelaufen')).toBeInTheDocument();
    expect(
      screen.queryByText('Diese Seite konnte nicht geladen werden'),
    ).not.toBeInTheDocument();
  });
});

describe('RouteBoundary — shell isolation (the #101 win)', () => {
  /** Simulates the AppLayout pattern: a "Sidebar" sibling outside the
   *  boundary, and a route-rendered page inside. A crash in the page
   *  must not affect the Sidebar. */
  function AppShell({ children }: { children: React.ReactNode }) {
    return (
      <div>
        <nav data-testid="sidebar">
          <Link to="/safe">Safe</Link>
          <Link to="/crashy">Crashy</Link>
        </nav>
        <main>
          <RouteBoundary>{children}</RouteBoundary>
        </main>
      </div>
    );
  }

  it('keeps sibling shell content rendered when a page crashes', () => {
    render(
      <MemoryRouter initialEntries={['/crashy']}>
        <AppShell>
          <Bomb />
        </AppShell>
      </MemoryRouter>,
    );
    // Sibling sidebar still alive even though the page exploded.
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByText('Safe')).toBeInTheDocument();
    // And the page region shows the inline fallback.
    expect(
      screen.getByText('Diese Seite konnte nicht geladen werden'),
    ).toBeInTheDocument();
  });

  it('auto-clears the boundary when the route changes (resetKey on pathname)', async () => {
    /** Use real <Routes> so navigation actually changes pathname and
     *  RouteBoundary's resetKey flips. */
    function App() {
      return (
        <div>
          <nav data-testid="sidebar">
            <Link to="/safe">go safe</Link>
            <Link to="/crashy">go crashy</Link>
          </nav>
          <main>
            <Routes>
              <Route
                path="/safe"
                element={
                  <RouteBoundary>
                    <p>safe page</p>
                  </RouteBoundary>
                }
              />
              <Route
                path="/crashy"
                element={
                  <RouteBoundary>
                    <Bomb />
                  </RouteBoundary>
                }
              />
            </Routes>
          </main>
        </div>
      );
    }

    render(
      <MemoryRouter initialEntries={['/crashy']}>
        <App />
      </MemoryRouter>,
    );

    // Initial state: on the crashy route, inline fallback visible.
    expect(
      screen.getByText('Diese Seite konnte nicht geladen werden'),
    ).toBeInTheDocument();

    // Navigate to the safe route. The boundary should reset because
    // its resetKey (pathname) just changed.
    await userEvent.click(screen.getByText('go safe'));

    expect(screen.getByText('safe page')).toBeInTheDocument();
    expect(
      screen.queryByText('Diese Seite konnte nicht geladen werden'),
    ).not.toBeInTheDocument();
  });
});
