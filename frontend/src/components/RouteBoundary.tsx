/**
 * Per-route ErrorBoundary helper (#101).
 *
 * The root `<ErrorBoundary>` in `main.tsx` is the catastrophic catch-all
 * — when it fires the whole SPA goes to a "Seite neu laden" full-screen
 * fallback. Most page crashes don't warrant nuking the entire shell;
 * the Sidebar, Header, and MobileNav should keep working so the user
 * can navigate away.
 *
 * `AppLayout` already wraps its `<Outlet />` with an inline boundary
 * keyed to the current pathname — that handles every protected route
 * (`/teams`, `/players`, etc.). This helper extends the same pattern
 * to public routes (`/login`, `/register`) which bypass AppLayout.
 *
 * Usage:
 *   <Route path="/login" element={
 *     <RouteBoundary name="login"><LoginPage /></RouteBoundary>
 *   } />
 */
import { useLocation } from 'react-router-dom';
import { ErrorBoundary } from './ErrorBoundary';

interface Props {
  children: React.ReactNode;
  /** Sentry tag for this boundary. Defaults to the current pathname,
   *  which is fine — explicit names just make the issue list nicer. */
  name?: string;
  /** Use the inline (in-page) fallback instead of the full-screen one.
   *  Default true: most route-level crashes are page-scoped, not
   *  app-fatal. */
  inline?: boolean;
}

export function RouteBoundary({ children, name, inline = true }: Props) {
  const { pathname } = useLocation();
  return (
    <ErrorBoundary
      name={name ?? pathname}
      resetKey={pathname}
      inline={inline}
    >
      {children}
    </ErrorBoundary>
  );
}
