import axios, { AxiosError, AxiosInstance } from 'axios';
import { User, UserLogin, TokenResponse, OAuthLoginResponse, UserRole } from '@/types';
// Only import mock API in development - Vite tree-shakes this in production
import mockApi from './mockApi';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Mock API fallback is only used in development when no backend URL is set
let useMockApi = !import.meta.env.VITE_API_URL && import.meta.env.DEV;

// Read a cookie by name; used to pull the csrf_token (NOT httpOnly,
// readable from JS by design — see backend/app/core/csrf.py). Returns
// null when the cookie isn't set yet (pre-login).
function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const m = document.cookie.match(
    new RegExp('(?:^|; )' + name.replace(/[-.+*]/g, '\\$&') + '=([^;]*)'),
  );
  return m ? decodeURIComponent(m[1]) : null;
}

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 5000, // 5 second timeout
      // #42: auth tokens live in httpOnly cookies set by the backend on
      // login. `withCredentials: true` tells the browser to attach
      // those cookies to every cross-origin XHR (the deployed SPA and
      // API live on different Cloud Run subdomains).
      withCredentials: true,
    });

    // Request interceptor — attach the CSRF token (double-submit) on
    // state-changing requests. The backend middleware checks that the
    // X-CSRF-Token header equals the csrf_token cookie.
    this.client.interceptors.request.use(
      (config) => {
        const method = (config.method || 'get').toUpperCase();
        if (!SAFE_METHODS.has(method)) {
          const csrf = readCookie('csrf_token');
          if (csrf) {
            config.headers['X-CSRF-Token'] = csrf;
          }
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // Response interceptor — on 401, try a one-shot refresh. The
    // refresh cookie travels automatically thanks to withCredentials,
    // so we never had to read or write tokens from JS.
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as typeof error.config & { _retry?: boolean };
        if (
          error.response?.status === 401 &&
          originalRequest &&
          !originalRequest._retry &&
          !originalRequest.url?.includes('/auth/login') &&
          !originalRequest.url?.includes('/auth/refresh')
        ) {
          originalRequest._retry = true;
          try {
            await this.client.post('/auth/refresh');
            return this.client(originalRequest);
          } catch {
            // Refresh failed — surface the original 401 and let the
            // route guard send the user to /login.
          }
        }
        return Promise.reject(error);
      },
    );
  }

  async checkBackend(): Promise<boolean> {
    if (!useMockApi) return true;
    try {
      // Health check should hit /api/v1/health/live (backend health endpoint)
      await this.client.get('/health/live', { timeout: 2000 });
      useMockApi = false;
      return true;
    } catch {
      useMockApi = true;
      return false;
    }
  }

  // Auth
  async login(credentials: UserLogin): Promise<TokenResponse> {
    if (useMockApi) {
      const result = await mockApi.login(credentials.email, credentials.password);
      if (!result) throw new Error('Login failed');
      return {
        access_token: result.access_token,
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: result.user,
      };
    }
    
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await this.client.post<TokenResponse>(
      '/auth/login',
      formData.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  }

  // OAuth Login
  async oauthLogin(provider: 'google' | 'apple', token: string, firstName?: string, lastName?: string): Promise<OAuthLoginResponse> {
    const response = await this.client.post<OAuthLoginResponse>(`/oauth/${provider}`, {
      token,
      provider,
      first_name: firstName,
      last_name: lastName,
    });
    return response.data;
  }

  // Register new user. requested_team_id is required by the backend for
  // player/parent sign-ups (routes approval to that team's coach).
  async register(userData: { email: string; password: string; first_name: string; last_name: string; phone?: string; role: UserRole; requested_team_id?: number }): Promise<User> {
    const response = await this.client.post<User>('/auth/register', userData);
    return response.data;
  }

  // Public team list for the sign-up team picker (no auth).
  async getPublicTeams(): Promise<import('@/types').PublicTeam[]> {
    const response = await this.client.get<import('@/types').PublicTeam[]>('/teams/public');
    return response.data;
  }

  // The current user's teams (managed vs member) for the sidebar.
  async getMyTeams(): Promise<import('@/types').MyTeams> {
    const response = await this.client.get<import('@/types').MyTeams>('/teams/my');
    return response.data;
  }

  // Approval queue (approvers only).
  async getPendingRegistrations(): Promise<import('@/types').PendingRegistration[]> {
    const response = await this.client.get<import('@/types').PendingRegistration[]>('/registrations/pending');
    return response.data;
  }

  async approveRegistration(userId: number): Promise<void> {
    await this.client.post(`/registrations/${userId}/approve`);
  }

  async rejectRegistration(userId: number, reason: string): Promise<void> {
    await this.client.post(`/registrations/${userId}/reject`, { reason });
  }

  // Delete user account
  async deleteAccount(): Promise<void> {
    await this.client.delete('/users/me/account');
    return;
  }

  // requested_team_id is required by the backend for player/parent
  // (routes approval to that team's coach). After this the OAuth user is
  // PENDING approval — callers should refresh /auth/me.
  async setOAuthRole(role: UserRole, requestedTeamId?: number): Promise<void> {
    await this.client.post('/oauth/set-role', { role, requested_team_id: requestedTeamId });
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  /** Server-side logout. Clears the httpOnly auth cookies (#42).
   * The frontend `useAuth.logout` should also wipe local state + the
   * React Query cache. */
  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch {
      // Network/CSRF failures shouldn't block a client-side logout —
      // the user can still drop their local state and be redirected.
    }
  }

  async getMe(): Promise<User> {
    if (useMockApi) {
      const user = await mockApi.getMe();
      if (!user) throw new Error('Not authenticated');
      return user;
    }
    
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  // Generic methods with mock fallback
  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    if (useMockApi) {
      return mockApi.get(path + (params ? '?' + new URLSearchParams(params).toString() : '')) as Promise<T>;
    }
    
    try {
      const response = await this.client.get<T>(path, { params });
      return response.data;
    } catch (error) {
      // If request fails, try mock
      if (import.meta.env.DEV) {
        console.log('Backend unavailable, using mock data');
        useMockApi = true;
        return mockApi.get(path) as Promise<T>;
      }
      throw error;
    }
  }

  async post<T>(path: string, data?: unknown): Promise<T> {
    if (useMockApi) {
      return mockApi.post(path, data) as Promise<T>;
    }
    
    try {
      const response = await this.client.post<T>(path, data);
      return response.data;
    } catch (error) {
      if (import.meta.env.DEV) {
        useMockApi = true;
        return mockApi.post(path, data) as Promise<T>;
      }
      throw error;
    }
  }

  async put<T>(path: string, data?: unknown): Promise<T> {
    const response = await this.client.put<T>(path, data);
    return response.data;
  }

  async patch<T>(path: string, data?: unknown): Promise<T> {
    if (useMockApi) {
      return mockApi.patch(path, data) as Promise<T>;
    }
    
    try {
      const response = await this.client.patch<T>(path, data);
      return response.data;
    } catch (error) {
      if (import.meta.env.DEV) {
        useMockApi = true;
        return mockApi.patch(path, data) as Promise<T>;
      }
      throw error;
    }
  }

  async delete<T>(path: string): Promise<T> {
    if (useMockApi) {
      return mockApi.delete(path) as Promise<T>;
    }
    
    const response = await this.client.delete<T>(path);
    return response.data;
  }
}

export const api = new ApiService();
