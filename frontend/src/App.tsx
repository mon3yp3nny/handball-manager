import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore, useRole } from '@/store/authStore';
import { api } from '@/services/api';

// Layout
import { AppLayout } from '@/components/layout/AppLayout';

// Pages
import { LoginPage } from '@/pages/auth/LoginPage';
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

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useRole();
  const token = localStorage.getItem('token');
  
  if (!isAuthenticated && !token) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  const { setUser, setToken } = useAuthStore();
  const { isAuthenticated } = useRole();

  // Check token on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && !isAuthenticated) {
      // Token exists but not in store, try to fetch user
      api.getMe()
        .then((user) => {
          setUser(user);
          setToken(token);
        })
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
        });
    }
  }, [setUser, setToken, isAuthenticated]);

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />

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
