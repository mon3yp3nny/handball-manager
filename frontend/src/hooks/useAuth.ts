import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { api } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { UserLogin, User } from '@/types';
import toast from 'react-hot-toast';

/**
 * Auth flow uses cookies (#42). After login the backend sets httpOnly
 * access/refresh cookies + a readable csrf_token cookie; the SPA never
 * touches the access token. We persist a non-credential `user` blob in
 * the zustand store so `isAuthenticated` survives a page reload, then
 * `refreshUser` revalidates against /auth/me on mount.
 */
export const useAuth = () => {
  const queryClient = useQueryClient();
  const { setAuth, logout: storeLogout, user } = useAuthStore();

  const login = useMutation({
    mutationFn: async (credentials: UserLogin) => {
      // The response body still carries the tokens for backward compat
      // with Bearer-header API clients, but the cookies are what the
      // browser will actually send on subsequent requests.
      await api.login(credentials);
      const me = await api.getMe();
      // Pass empty-string token — we no longer track it in JS, but the
      // store API still expects the field. (#42 follow-up could trim
      // it from the store type.)
      setAuth(me, '');
      return { user: me };
    },
    onSuccess: () => {
      toast.success('Willkommen zurück!');
    },
    onError: (error: Error) => {
      let message = 'Anmeldung fehlgeschlagen';
      if (error instanceof AxiosError && error.response?.data) {
        const data = error.response.data as Record<string, string>;
        if (data.detail) message = data.detail;
      }
      toast.error(message);
    },
  });

  const logout = async () => {
    // Best-effort server-side logout to clear the httpOnly cookies.
    // We don't await before clearing local state because the user
    // experience should snap to "logged out" immediately regardless of
    // network conditions.
    void api.logout();
    storeLogout();
    queryClient.clear();
    toast.success('Abgemeldet');
  };

  // On mount, ask the server "who am I?". If the auth cookie is valid,
  // we get the canonical User back; if not, the 401 falls through and
  // the route guard sends them to /login. No localStorage probe — the
  // cookie itself is the source of truth.
  const refreshUser = useQuery({
    queryKey: ['me'],
    queryFn: api.getMe,
    enabled: typeof window !== 'undefined',
    retry: false,
    onSuccess: (fresh: User) => {
      useAuthStore.setState({ user: fresh, isAuthenticated: true, token: '' });
    },
    onError: () => {
      // Cookie missing/expired — clear any stale persisted user.
      useAuthStore.setState({ user: null, isAuthenticated: false, token: null });
    },
  });

  return {
    login,
    logout,
    refreshUser,
    user,
    isAuthenticated: !!user,
  };
};
