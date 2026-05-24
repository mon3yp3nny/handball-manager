import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, useEffect } from 'react';
import { useAuthStore, useRole } from '@/store/authStore';
import { api } from '@/services/api';
import { ApprovalStatus } from '@/types';

// Layout — eagerly loaded; it wraps every protected route, so lazying
// it would only buy a few KB at the cost of a flash on every cold start.
import { AppLayout } from '@/components/layout/AppLayout';
import { RouteBoundary } from '@/components/RouteBoundary';
import { PageLoader } from '@/components/PageLoader';
import { AccountStatusPage } from '@/pages/AccountStatusPage';
import { lazyNamed } from '@/lib/lazy';

// Pages — lazy-loaded so each route is its own chunk (#102). Visitors
// only pay for the pages they actually hit; CalendarPage in particular
// (~33 KB) no longer ships in the initial bundle. The lazyNamed helper
// adapts our named-export convention to React.lazy's default-export
// expectation.
const LoginPage = lazyNamed(() => import('@/pages/auth/LoginPage'), 'LoginPage');
const RegisterPage = lazyNamed(() => import('@/pages/auth/RegisterPage'), 'RegisterPage');
const DashboardPage = lazyNamed(() => import('@/pages/DashboardPage'), 'DashboardPage');
const TeamsPage = lazyNamed(() => import('@/pages/Teams/TeamsPage'), 'TeamsPage');
const TeamDetailPage = lazyNamed(() => import('@/pages/Teams/TeamDetailPage'), 'TeamDetailPage');
const PlayersPage = lazyNamed(() => import('@/pages/Players/PlayersPage'), 'PlayersPage');
const PlayerDetailPage = lazyNamed(() => import('@/pages/Players/PlayerDetailPage'), 'PlayerDetailPage');
const GamesPage = lazyNamed(() => import('@/pages/Games/GamesPage'), 'GamesPage');
const GameDetailPage = lazyNamed(() => import('@/pages/Games/GameDetailPage'), 'GameDetailPage');
const EventsPage = lazyNamed(() => import('@/pages/Events/EventsPage'), 'EventsPage');
const EventDetailPage = lazyNamed(() => import('@/pages/Events/EventDetailPage'), 'EventDetailPage');
const CalendarPage = lazyNamed(() => import('@/pages/CalendarPage'), 'CalendarPage');
const NewsPage = lazyNamed(() => import('@/pages/News/NewsPage'), 'NewsPage');
const NewsDetailPage = lazyNamed(() => import('@/pages/News/NewsDetailPage'), 'NewsDetailPage');
const AttendancePage = lazyNamed(() => import('@/pages/Attendance/AttendancePage'), 'AttendancePage');
const ProfilePage = lazyNamed(() => import('@/pages/ProfilePage'), 'ProfilePage');
const ApprovalsPage = lazyNamed(() => import('@/pages/Approvals/ApprovalsPage'), 'ApprovalsPage');
const NotFoundPage = lazyNamed(() => import('@/pages/NotFoundPage'), 'NotFoundPage');

// Protected route wrapper. After #42 the credential is an httpOnly
// cookie that JS can't see — we no longer probe localStorage for a
// token. The persisted `user` in the zustand store is enough to render
// optimistically; if the cookie is invalid the next API call will 401
// and the route guard sends the user to /login.
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, user } = useRole();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  // Registration approval gate. A pending/rejected user can authenticate
  // but gets a status screen instead of the app (the backend also 403s
  // their data calls). approval_status is absent on a stale persisted
  // user blob — treat that as approved until /auth/me refreshes it.
  const status = user?.approval_status;
  if (status && status !== ApprovalStatus.APPROVED) {
    return <AccountStatusPage status={status} reason={user?.rejection_reason} />;
  }
  return <>{children}</>;
};

function App() {
  const { setUser } = useAuthStore();
  const { isAuthenticated } = useRole();

  // One-time cleanup of legacy localStorage tokens from the pre-#42
  // era. Nothing reads them now, but evicting them shrinks the XSS
  // surface for anyone running the new build with an old cookie jar.
  useEffect(() => {
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
    } catch {
      // Safari private mode rejects localStorage writes; ignore.
    }
  }, []);

  // Revalidate the session against the server on mount. The auth
  // cookie travels automatically thanks to `withCredentials: true`
  // on the axios client (services/api.ts).
  useEffect(() => {
    api
      .getMe()
      .then((u) => setUser(u))
      .catch(() => {
        // Cookie missing or expired — clear any optimistic state.
        useAuthStore.setState({ user: null, isAuthenticated: false, token: null });
      });
  }, [setUser]);

  // Single Suspense boundary at the Routes level — works for both
  // public and protected branches. Each route's RouteBoundary
  // contains the per-page error fallback; this Suspense provides the
  // per-page loading fallback. They compose: a chunk that fails to
  // load (network blip) trips Suspense → error → RouteBoundary's
  // inline fallback inside the shell.
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes — wrapped in their own RouteBoundary because they
            bypass AppLayout (which already has its own boundary around
            the protected-route Outlet). A crash in LoginPage shouldn't
            take down the whole app and prevent the user from retrying. */}
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <RouteBoundary name="login" inline={false}>
                <LoginPage />
              </RouteBoundary>
            )
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <RouteBoundary name="register" inline={false}>
                <RegisterPage />
              </RouteBoundary>
            )
          }
        />

        {/* Protected routes */}
        <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route index element={<DashboardPage />} />

          {/* Teams */}
          <Route path="teams" element={<TeamsPage />} />
          <Route path="teams/:id" element={<TeamDetailPage />} />

          {/* Players */}
          <Route path="players" element={<PlayersPage />} />
          <Route path="players/:id" element={<PlayerDetailPage />} />

          {/* Games */}
          <Route path="games" element={<GamesPage />} />
          <Route path="games/:id" element={<GameDetailPage />} />

          {/* Events */}
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:id" element={<EventDetailPage />} />

          {/* Calendar */}
          <Route path="calendar" element={<CalendarPage />} />

          {/* News */}
          <Route path="news" element={<NewsPage />} />
          <Route path="news/:id" element={<NewsDetailPage />} />

          {/* Attendance */}
          <Route path="attendance" element={<AttendancePage />} />

          {/* Profile */}
          <Route path="profile" element={<ProfilePage />} />

          {/* Approvals (coach/admin) */}
          <Route path="approvals" element={<ApprovalsPage />} />

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
