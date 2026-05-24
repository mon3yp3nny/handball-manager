import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserRole, PublicTeam, AppNotification } from '@/types';

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
  currentTeam: PublicTeam | null;
  setCurrentTeam: (team: PublicTeam | null) => void;
}

interface NotificationState {
  notifications: AppNotification[];
  addNotification: (notification: AppNotification) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useAuthStore = create<AuthState>(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => {
        // The httpOnly auth cookie is cleared server-side by
        // useAuth().logout calling /auth/logout (#42). Local cleanup
        // just resets the in-memory store.
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      // #42: never persist the token. It's no longer a credential — the
      // actual credential is the httpOnly auth cookie set by the server.
      // Persisting only the `user` blob (display name, role, etc.) lets
      // ProtectedRoute render optimistically on reload without keeping
      // anything credential-shaped in localStorage.
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
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
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return {
    isAdmin: user?.role === UserRole.ADMIN,
    isCoach: user?.role === UserRole.COACH || user?.role === UserRole.ADMIN,
    isSupervisor: user?.role === UserRole.SUPERVISOR || user?.role === UserRole.COACH || user?.role === UserRole.ADMIN,
    isPlayer: user?.role === UserRole.PLAYER,
    isParent: user?.role === UserRole.PARENT,
    role: user?.role,
    user,
    isAuthenticated,
  };
};

// Dev role labels for UI
export const roleLabels: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Administrator',
  [UserRole.COACH]: 'Trainer',
  [UserRole.SUPERVISOR]: 'Betreuer',
  [UserRole.PLAYER]: 'Spieler',
  [UserRole.PARENT]: 'Eltern',
};

export const roleColors: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'bg-red-100 text-red-800',
  [UserRole.COACH]: 'bg-blue-100 text-blue-800',
  [UserRole.SUPERVISOR]: 'bg-green-100 text-green-800',
  [UserRole.PLAYER]: 'bg-purple-100 text-purple-800',
  [UserRole.PARENT]: 'bg-orange-100 text-orange-800',
};
