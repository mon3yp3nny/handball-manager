/**
 * Tests for ErrorBoundary (#55).
 *
 * The boundary is the SPA's last line of defense against component-tree
 * crashes — if it ever stops catching, users see a white screen. These
 * tests cover:
 *   - happy path (renders children)
 *   - caught error → fallback UI (full-page + inline variants)
 *   - resetKey change → auto-clears error state
 *   - manual reset button works in the inline variant
 *   - captureError (Sentry hook) is called with boundary name + stack
 */
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock the Sentry wrapper so we can assert it was called without
// touching the real SDK.
vi.mock('@/lib/sentry', () => ({
  captureError: vi.fn(),
}));

import { ErrorBoundary } from '../ErrorBoundary';
import { captureError } from '@/lib/sentry';

/** Throws on render — used to trigger the boundary. */
function Bomb({ message = 'boom' }: { message?: string }): JSX.Element {
  throw new Error(message);
}

/** Suppress React's loud error logging during these tests — we expect
 *  errors and don't want them spamming the test output. */
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => {
  consoleErrorSpy.mockRestore();
  cleanup();
  vi.clearAllMocks();
});

describe('ErrorBoundary — happy path', () => {
  it('renders children when no error is thrown', () => {
    render(
      <ErrorBoundary>
        <p>hello world</p>
      </ErrorBoundary>,
    );
    expect(screen.getByText('hello world')).toBeInTheDocument();
  });
});

describe('ErrorBoundary — full-page fallback', () => {
  it('shows the German "Etwas ist schiefgelaufen" copy when a child throws', () => {
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Etwas ist schiefgelaufen')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Seite neu laden/i }),
    ).toBeInTheDocument();
  });

  it('calls captureError with the boundary name + componentStack', () => {
    render(
      <ErrorBoundary name="dashboard">
        <Bomb message="downstream crash" />
      </ErrorBoundary>,
    );
    expect(captureError).toHaveBeenCalledOnce();
    const [error, ctx] = (captureError as any).mock.calls[0];
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe('downstream crash');
    expect(ctx).toMatchObject({ boundary: 'dashboard' });
    expect(typeof ctx.componentStack).toBe('string');
  });

  it('defaults the boundary name to "root" when none is provided', () => {
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    );
    const [, ctx] = (captureError as any).mock.calls[0];
    expect(ctx.boundary).toBe('root');
  });
});

describe('ErrorBoundary — inline fallback', () => {
  it('renders the smaller in-page fallback when inline=true', () => {
    render(
      <ErrorBoundary inline>
        <Bomb />
      </ErrorBoundary>,
    );
    expect(
      screen.getByText('Diese Seite konnte nicht geladen werden'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Erneut versuchen/i }),
    ).toBeInTheDocument();
  });

  it('the "Erneut versuchen" button resets the boundary so children can re-render', async () => {
    let shouldThrow = true;
    function Conditional() {
      if (shouldThrow) throw new Error('first render boom');
      return <p>recovered</p>;
    }

    render(
      <ErrorBoundary inline>
        <Conditional />
      </ErrorBoundary>,
    );
    expect(
      screen.getByText('Diese Seite konnte nicht geladen werden'),
    ).toBeInTheDocument();

    // Stop the bomb, then click reset.
    shouldThrow = false;
    await userEvent.click(screen.getByRole('button', { name: /Erneut versuchen/i }));

    expect(screen.getByText('recovered')).toBeInTheDocument();
  });
});

describe('ErrorBoundary — resetKey behavior', () => {
  it('clears its error state when resetKey changes (e.g. on route navigation)', () => {
    function Wrapper({ k, shouldBomb }: { k: string; shouldBomb: boolean }) {
      return (
        <ErrorBoundary resetKey={k}>
          {shouldBomb ? <Bomb /> : <p>recovered</p>}
        </ErrorBoundary>
      );
    }

    const { rerender } = render(<Wrapper k="a" shouldBomb={true} />);
    expect(screen.getByText('Etwas ist schiefgelaufen')).toBeInTheDocument();

    // Simulate route navigation: resetKey flips, child stops throwing.
    rerender(<Wrapper k="b" shouldBomb={false} />);
    expect(screen.getByText('recovered')).toBeInTheDocument();
  });

  it('does NOT clear when resetKey stays the same', () => {
    function Wrapper({ k }: { k: string }) {
      return (
        <ErrorBoundary resetKey={k}>
          <Bomb />
        </ErrorBoundary>
      );
    }

    const { rerender } = render(<Wrapper k="a" />);
    expect(screen.getByText('Etwas ist schiefgelaufen')).toBeInTheDocument();

    rerender(<Wrapper k="a" />);
    // Still in error state — resetKey didn't change.
    expect(screen.getByText('Etwas ist schiefgelaufen')).toBeInTheDocument();
  });
});
