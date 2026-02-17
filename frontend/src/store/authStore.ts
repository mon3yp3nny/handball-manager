import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserRole, Team, AppNotification } from '@/types';

// Demo users for development - only available in dev builds
const demoUsers: Record<UserRole, User> | null = import.meta.env.DEV
  ? {
      [UserRole.ADMIN]: {
        id: 'admin-1',
        email: 'admin@handball.de',
        first_name: 'Max',
        last_name: 'Admin',
        role: UserRole.ADMIN,
        phone: '+49 123 456789',
        created_at: new Date().toISOString(),
        is_active: true,
      },
      [UserRole.COACH]: {
        id: 'coach-1',
        email: 'coach@handball.de',
        first_name: 'Thomas',
        last_name: 'Trainer',
        role: UserRole.COACH,
        phone: '+49 123 456790',
        created_at: new Date().toISOString(),
        is_active: true,
      },
      [UserRole.SUPERVISOR]: {
        id: 'supervisor-1',
        email: 'supervisor@handball.de',
        first_name: 'Anna',
        last_name: 'Betreuer',
        role: UserRole.SUPERVISOR,
        phone: '+49 123 456791',
        created_at: new Date().toISOString(),
        is_active: true,
      },
      [UserRole.PLAYER]: {
        id: 'player-1',
        email: 'spieler@handball.de',
        first_name: 'Lukas',
        last_name: 'Spieler',
        role: UserRole.PLAYER,
        phone: '+49 123 456792',
        created_at: new Date().toISOString(),
        is_active: true,
      },
      [UserRole.PARENT]: {
        id: 'parent-1',
        email: 'eltern@handball.de',
        first_name: 'Maria',
        last_name: 'Elternteil',
        role: UserRole.PARENT,
        phone: '+49 123 456793',
        created_at: new Date().toISOString(),
        is_active: true,
      },
    }
  : null;

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  // Dev features
  devAutoLogin: (role: UserRole) => void;
  devSwitchRole: (role: UserRole) => void;
  isDevMode: boolean;
}

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  currentTeam: Team | null;
  setCurrentTeam: (team: Team | null) => void;
  // Dev role switcher
  showDevSwitcher: boolean;
  setShowDevSwitcher: (show: boolean) => void;
}

interface NotificationState {
  notifications: AppNotification[];
  addNotification: (notification: AppNotification) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

const isDev = import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true';

export const useAuthStore = create<AuthState>(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      isDevMode: isDev,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        set({ user: null, token: null, isAuthenticated: false });
      },
      // Dev auto-login
      devAutoLogin: (role) => {
        if (!isDev || !demoUsers) return;
        const user = demoUsers[role];
        set({ user, token: 'dev-token', isAuthenticated: true, isDevMode: true });
      },
      // Dev role switch
      devSwitchRole: (role) => {
        if (!isDev || !demoUsers) return;
        const user = demoUsers[role];
        set({ user, token: 'dev-token', isAuthenticated: true });
      },
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
  showDevSwitcher: isDev,
  setShowDevSwitcher: (show) => set({ showDevSwitcher: show }),
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
  const isDevMode = useAuthStore((state) => state.isDevMode);
  
  return {
    isAdmin: user?.role === UserRole.ADMIN,
    isCoach: user?.role === UserRole.COACH || user?.role === UserRole.ADMIN,
    isSupervisor: user?.role === UserRole.SUPERVISOR || user?.role === UserRole.COACH || user?.role === UserRole.ADMIN,
    isPlayer: user?.role === UserRole.PLAYER,
    isParent: user?.role === UserRole.PARENT,
    role: user?.role,
    user,
    isDevMode,
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
