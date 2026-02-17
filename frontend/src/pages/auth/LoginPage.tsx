import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin, GoogleOAuthProvider, CredentialResponse } from '@react-oauth/google';
import { useAuth } from '@/hooks/useAuth';
import { UserLogin, UserRole } from '@/types';
import { useAuthStore, roleLabels } from '@/store/authStore';
import { Bug } from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { isDevMode, devAutoLogin, setAuth } = useAuthStore();
  const [credentials, setCredentials] = useState<UserLogin>({
    email: '',
    password: '',
  });
  const [needsRoleSelection, setNeedsRoleSelection] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [isOAuthLoading, setIsOAuthLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login.mutateAsync(credentials);
      navigate('/');
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleDevLogin = (role: UserRole) => {
    devAutoLogin(role);
    navigate('/');
  };

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    setIsOAuthLoading(true);
    try {
      const result = await api.oauthLogin('google', credentialResponse.credential ?? '');

      // Store tokens
      localStorage.setItem('token', result.access_token);
      localStorage.setItem('refreshToken', result.refresh_token);

      if (result.needs_role_selection) {
        // Show role selection modal
        setNewUserEmail(result.email);
        setNeedsRoleSelection(true);
      } else {
        // Complete login
        setAuth({
          id: result.user_id,
          email: result.email,
          first_name: result.first_name,
          last_name: result.last_name,
          role: result.role,
          is_active: true,
          created_at: new Date().toISOString(),
        }, result.access_token);
        navigate('/');
        toast.success(`Willkommen, ${result.first_name}!`);
      }
    } catch {
      toast.error('Anmeldung fehlgeschlagen. Bitte versuche es erneut.');
    } finally {
      setIsOAuthLoading(false);
    }
  };

  const handleAppleSignIn = async () => {
    setIsOAuthLoading(true);
    try {
      AppleID.auth.init({
        clientId: appleClientId,
        scope: 'name email',
        redirectURI: window.location.origin,
        usePopup: true,
      });

      const response = await AppleID.auth.signIn();
      const idToken = response.authorization.id_token;
      const firstName = response.user?.name?.firstName;
      const lastName = response.user?.name?.lastName;

      const result = await api.oauthLogin('apple', idToken, firstName, lastName);

      localStorage.setItem('token', result.access_token);
      localStorage.setItem('refreshToken', result.refresh_token);

      if (result.needs_role_selection) {
        setNewUserEmail(result.email);
        setNeedsRoleSelection(true);
      } else {
        setAuth({
          id: result.user_id,
          email: result.email,
          first_name: result.first_name,
          last_name: result.last_name,
          role: result.role,
          is_active: true,
          created_at: new Date().toISOString(),
        }, result.access_token);
        navigate('/');
        toast.success(`Willkommen, ${result.first_name}!`);
      }
    } catch {
      toast.error('Apple-Anmeldung fehlgeschlagen.');
    } finally {
      setIsOAuthLoading(false);
    }
  };

  const handleRoleSelection = async (role: UserRole) => {
    try {
      await api.setOAuthRole(role);
      toast.success('Rolle gespeichert! Anmeldung erfolgreich.');
      navigate('/');
    } catch (error) {
      toast.error('Fehler beim Speichern der Rolle.');
    }
  };

  const roles = Object.values(UserRole);

  // OAuth Client IDs from environment
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const appleClientId = import.meta.env.VITE_APPLE_CLIENT_ID || '';

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-xl mb-4">
            <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
              <circle cx="12" cy="12" r="5"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Handball Manager</h1>
          <p className="text-gray-600 mt-2">Willkommen zurück</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-8">
          {/* OAuth Login Buttons */}
          <div className="space-y-3 mb-6">
            {/* Google Sign In */}
            {googleClientId && (
              <div className="flex justify-center">
                <GoogleOAuthProvider clientId={googleClientId}>
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => toast.error('Google-Anmeldung fehlgeschlagen')}
                    useOneTap
                  />
                </GoogleOAuthProvider>
              </div>
            )}
            
            {/* Apple Sign In Button */}
            {appleClientId && (
              <button
                onClick={handleAppleSignIn}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
                disabled={isOAuthLoading}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.2-.93 3.52-.84 1.55.1 2.68.67 3.44 1.65-2.88 1.68-2.24 5.98.22 7.13-.34 1.48-.84 2.9-1.26 4.23zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
                </svg>
                <span>Mit Apple anmelden</span>
              </button>
            )}
          </div>
          
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">oder</span>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="label">Email</label>
              <input
                id="email"
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
                className="input"
                required
              />
            </div>
            
            <div>
              <label htmlFor="password" className="label">Passwort</label>
              <input
                id="password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                className="input"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={login.isPending}
              className="btn-primary w-full"
            >
              {login.isPending ? 'Wird angemeldet...' : 'Anmelden'}
            </button>
          </form>
          
          {import.meta.env.DEV && (
            <div className="mt-6 text-center text-sm text-gray-500">
              <p>Demo-Zugangsdaten:</p>
              <p>admin@handball.de / admin123</p>
            </div>
          )}
        </div>

        {/* Role Selection Modal */}
        {needsRoleSelection && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-lg p-6 max-w-sm w-full">
              <h2 className="text-lg font-semibold mb-2">Wähle deine Rolle</h2>
              <p className="text-sm text-gray-600 mb-4">
                {newUserEmail} - Bitte wähle deine Rolle im Verein aus:
              </p>
              <div className="space-y-2">
                {roles.map((role) => (
                  <button
                    key={role}
                    onClick={() => handleRoleSelection(role)}
                    className="w-full px-4 py-2 text-left rounded-lg border hover:bg-primary-50 hover:border-primary-300 transition-colors"
                  >
                    <span className="font-medium">{roleLabels[role]}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Dev Auto-Login Section */}
        {isDevMode && (
          <div className="mt-6 bg-yellow-50 rounded-xl border border-yellow-200 p-6">
            <div className="flex items-center justify-center mb-4">
              <Bug className="w-5 h-5 text-yellow-600 mr-2" />
              <h3 className="text-sm font-semibold text-yellow-800">Entwicklungs-Modus</h3>
            </div>
            <p className="text-xs text-yellow-600 text-center mb-4">
              Schneller Login mit Test-Rollen
            </p>
            <div className="grid grid-cols-2 gap-2">
              {roles.map((role) => (
                <button
                  key={role}
                  onClick={() => handleDevLogin(role)}
                  className="px-3 py-2 rounded-lg text-xs font-medium bg-white border border-yellow-300 text-yellow-700 hover:bg-yellow-100 transition-colors"
                >
                  Als {roleLabels[role]}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
