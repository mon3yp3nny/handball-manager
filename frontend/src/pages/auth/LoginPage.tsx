import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { UserLogin, UserRole } from '@/types';
import { useAuthStore, roleLabels } from '@/store/authStore';
import { Bug } from 'lucide-react';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { isDevMode, devAutoLogin } = useAuthStore();
  const [credentials, setCredentials] = useState<UserLogin>({
    email: '',
    password: '',
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

  const handleDevLogin = (role: UserRole) => {
    devAutoLogin(role);
    navigate('/');
  };

  const roles = Object.values(UserRole);

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
          
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>Demo-Zugangsdaten:</p>
            <p>admin@handball.de / admin123</p>
          </div>
        </div>

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
