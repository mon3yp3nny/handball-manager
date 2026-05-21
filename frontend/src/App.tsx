import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore, useRole } from '@/store/authStore';
import { api } from '@/services/api';

// Layout
import { AppLayout } from '@/components/layout/AppLayout';

// Pages
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { TeamsPage } from '@/pages/Teams/TeamsPage';
import { TeamDetailPage } from '@/pages/Teams/TeamDetailPage';
import { PlayersPage } from '@/pages/Players/PlayersPage';
import { PlayerDetailPage } from '@/pages/Players/PlayerDetailPage';
import { GamesPage } from '@/pages/Games/GamesPage';
import { GameDetailPage } from '@/pages/Games/GameDetailPage';
import { EventsPage } from '@/pages/Events/EventsPage';
import { EventDetailPage } from '@/pages/Events/EventDetailPage';
import { CalendarPage } from '@/pages/CalendarPage';
import { NewsPage } from '@/pages/News/NewsPage';
import { NewsDetailPage } from '@/pages/News/NewsDetailPage';
import { AttendancePage } from '@/pages/Attendance/AttendancePage';
import { ProfilePage } from '@/pages/ProfilePage';
import { NotFoundPage } from '@/pages/NotFoundPage';

// Protected route wrapper. After #42 the credential is an httpOnly
// cookie that JS can't see — we no longer probe localStorage for a
// token. The persisted `user` in the zustand store is enough to render
// optimistically; if the cookie is invalid the next API call will 401
// and the route guard sends the user to /login.
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useRole();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
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

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />} />

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
        
        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
