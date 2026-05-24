import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { GoogleLogin, GoogleOAuthProvider, CredentialResponse } from '@react-oauth/google';
import { useAuth } from '@/hooks/useAuth';
import { UserLogin, UserRole } from '@/types';
import { useAuthStore, roleLabels } from '@/store/authStore';
import { api } from '@/services/api';
import toast from 'react-hot-toast';
import { ClubCrest } from '@/components/brand/ClubCrest';

// Player/parent must pick a team during OAuth role selection (routes
// approval to that team's coach), mirroring password registration.
const TEAM_REQUIRED_ROLES = [UserRole.PLAYER, UserRole.PARENT];

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { setAuth, setUser } = useAuthStore();
  const [credentials, setCredentials] = useState<UserLogin>({
    email: '',
    password: '',
  });
  const [needsRoleSelection, setNeedsRoleSelection] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [isOAuthLoading, setIsOAuthLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [selectedTeamId, setSelectedTeamId] = useState<number | undefined>(undefined);

  // Team picker options for the OAuth role-selection modal (player/parent).
  const { data: teams = [], isLoading: teamsLoading } = useQuery({
    queryKey: ['public-teams'],
    queryFn: () => api.getPublicTeams(),
    enabled: needsRoleSelection,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login.mutateAsync(credentials);
      navigate('/');
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    setIsOAuthLoading(true);
    try {
      // OAuth login (#42): backend sets the httpOnly auth cookies on
      // the response — no tokens kept in JS.
      const result = await api.oauthLogin('google', credentialResponse.credential ?? '');

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

  const loadAppleSDK = (): Promise<void> => {
    if (typeof AppleID !== 'undefined') return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/4/en_US/appleid.auth.js';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Apple Sign In SDK'));
      document.head.appendChild(script);
    });
  };

  const handleAppleSignIn = async () => {
    setIsOAuthLoading(true);
    try {
      await loadAppleSDK();
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

      // Apple OAuth: backend sets the httpOnly auth cookies (#42).
      const result = await api.oauthLogin('apple', idToken, firstName, lastName);

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

  const handleRoleSelection = async () => {
    if (!selectedRole) return;
    const needsTeam = TEAM_REQUIRED_ROLES.includes(selectedRole);
    if (needsTeam && !selectedTeamId) {
      toast.error('Bitte wähle ein Team aus.');
      return;
    }
    try {
      await api.setOAuthRole(selectedRole, needsTeam ? selectedTeamId : undefined);
      // The account is now PENDING approval — refresh /auth/me so the
      // route guard shows the pending screen instead of the app shell.
      try {
        const me = await api.getMe();
        setUser(me);
      } catch {
        // ignore — guard will re-fetch on next mount
      }
      setNeedsRoleSelection(false);
      toast.success('Rolle gespeichert! Dein Konto muss noch freigegeben werden.');
      navigate('/');
    } catch (error) {
      toast.error('Fehler beim Speichern der Rolle.');
    }
  };

  // Public sign-up roles (no admin/supervisor self-assignment).
  const roles = [UserRole.PLAYER, UserRole.PARENT, UserRole.COACH];

  // OAuth Client IDs from environment
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const appleClientId = import.meta.env.VITE_APPLE_CLIENT_ID || '';

  return (
    <div className="tvf-app min-h-screen bg-tvf-canvas flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <ClubCrest size={64} />
          </div>
          <h1 className="font-display tracking-wide uppercase text-3xl text-tvf-ink">
            Handball Manager
          </h1>
          <p className="text-tvf-ink-2 mt-2">Willkommen zurück</p>
        </div>

        <div className="card p-8">
          {/* Social login + the "oder" divider only render when at least
              one OAuth provider is configured. Otherwise the divider would
              sit at the top of the card with nothing above it. */}
          {(googleClientId || appleClientId) && (
            <>
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
            </>
          )}

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

          {/* Registration Link */}
          <div className="mt-6 text-center">
            <span className="text-gray-500 text-sm">Noch kein Konto? </span>
            <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium text-sm">
              Jetzt registrieren
            </Link>
          </div>
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
                    onClick={() => {
                      setSelectedRole(role);
                      setSelectedTeamId(undefined);
                    }}
                    className={`w-full px-4 py-2 text-left rounded-lg border transition-colors ${
                      selectedRole === role
                        ? 'bg-primary-50 border-primary-400'
                        : 'hover:bg-primary-50 hover:border-primary-300'
                    }`}
                  >
                    <span className="font-medium">{roleLabels[role]}</span>
                  </button>
                ))}
              </div>

              {selectedRole && TEAM_REQUIRED_ROLES.includes(selectedRole) && (
                <div className="mt-4">
                  <label htmlFor="oauth-team" className="label">Team *</label>
                  <select
                    id="oauth-team"
                    className="input"
                    value={selectedTeamId ?? ''}
                    onChange={(e) =>
                      setSelectedTeamId(e.target.value ? Number(e.target.value) : undefined)
                    }
                  >
                    <option value="" disabled>
                      {teamsLoading ? 'Teams werden geladen…' : 'Team auswählen'}
                    </option>
                    {teams.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}{t.age_group ? ` (${t.age_group})` : ''}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Der Trainer dieses Teams gibt deine Registrierung frei.
                  </p>
                </div>
              )}

              <button
                onClick={handleRoleSelection}
                disabled={!selectedRole}
                className="btn-primary w-full mt-4 disabled:opacity-50"
              >
                Bestätigen
              </button>
              <p className="text-xs text-gray-500 mt-3 text-center">
                Nach der Auswahl muss dein Konto noch freigegeben werden.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
