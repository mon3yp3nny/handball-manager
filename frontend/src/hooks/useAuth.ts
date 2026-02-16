import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { UserLogin, User } from '@/types';
import toast from 'react-hot-toast';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const { setAuth, logout: storeLogout, user } = useAuthStore();

  const login = useMutation({
    mutationFn: async (credentials: UserLogin) => {
      const response = await api.login(credentials);
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('refreshToken', response.refresh_token);
      
      // Get user data
      const user = await api.getMe();
      setAuth(user, response.access_token);
      return { user, token: response.access_token };
    },
    onSuccess: () => {
      toast.success('Willkommen zurück!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Anmeldung fehlgeschlagen');
    },
  });

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    storeLogout();
    queryClient.clear();
    toast.success('Abgemeldet');
  };

  const refreshUser = useQuery({
    queryKey: ['me'],
    queryFn: api.getMe,
    enabled: typeof window !== 'undefined' && !!localStorage.getItem('token'),
    onSuccess: (user: User) => {
      const token = localStorage.getItem('token') || '';
      useAuthStore.setState({ user, isAuthenticated: true, token });
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
