import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserRole, Team, CalendarEvent } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  currentTeam: Team | null;
  setCurrentTeam: (team: Team | null) => void;
}

interface NotificationState {
  notifications: CalendarEvent[];
  addNotification: (notification: CalendarEvent) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useAuthStore = create<AuthState>(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  currentTeam: null,
  setCurrentTeam: (team) => set({ currentTeam: team }),
}));

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [...state.notifications, notification],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}));

// Helper hook for role checking
export const useRole = () => {
  const user = useAuthStore((state) => state.user);
  
  return {
    isAdmin: user?.role === UserRole.ADMIN,
    isCoach: user?.role === UserRole.COACH || user?.role === UserRole.ADMIN,
    isSupervisor: user?.role === UserRole.SUPERVISOR || user?.role === UserRole.COACH || user?.role === UserRole.ADMIN,
    isPlayer: user?.role === UserRole.PLAYER,
    isParent: user?.role === UserRole.PARENT,
    role: user?.role,
    user,
  };
};
