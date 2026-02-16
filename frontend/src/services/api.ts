import axios, { AxiosError, AxiosInstance } from 'axios';
import { User, UserLogin, UserRegister, TokenResponse } from '@/types';
import mockApi from './mockApi';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Check if we should use mock API (in dev mode or if backend is not available)
const isDev = import.meta.env.DEV;
let useMockApi = isDev;

class ApiService {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 5000, // 5 second timeout
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        this.token = localStorage.getItem('token');
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && originalRequest) {
          // Try to refresh token
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('token', response.access_token);
              localStorage.setItem('refreshToken', response.refresh_token);
              
              // Retry original request
              originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
              return this.client(originalRequest);
            } catch {
              // Refresh failed, clear tokens and redirect
              localStorage.removeItem('token');
              localStorage.removeItem('refreshToken');
              window.location.href = '/login';
            }
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  async checkBackend(): Promise<boolean> {
    if (!useMockApi) return true;
    try {
      await this.client.get('/health', { timeout: 2000 });
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

  async setOAuthRole(role: string): Promise<void> {
    await this.client.post('/oauth/set-role', { role });
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
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
  async get<T>(path: string, params?: Record<string, any>): Promise<T> {
    if (useMockApi) {
      return mockApi.get(path + (params ? '?' + new URLSearchParams(params).toString() : '')) as Promise<T>;
    }
    
    try {
      const response = await this.client.get<T>(path, { params });
      return response.data;
    } catch (error) {
      // If request fails, try mock
      if (isDev) {
        console.log('Backend unavailable, using mock data');
        useMockApi = true;
        return mockApi.get(path) as Promise<T>;
      }
      throw error;
    }
  }

  async post<T>(path: string, data?: any): Promise<T> {
    if (useMockApi) {
      return mockApi.post(path, data) as Promise<T>;
    }
    
    try {
      const response = await this.client.post<T>(path, data);
      return response.data;
    } catch (error) {
      if (isDev) {
        useMockApi = true;
        return mockApi.post(path, data) as Promise<T>;
      }
      throw error;
    }
  }

  async put<T>(path: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(path, data);
    return response.data;
  }

  async patch<T>(path: string, data?: any): Promise<T> {
    if (useMockApi) {
      return mockApi.patch(path, data) as Promise<T>;
    }
    
    try {
      const response = await this.client.patch<T>(path, data);
      return response.data;
    } catch (error) {
      if (isDev) {
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
