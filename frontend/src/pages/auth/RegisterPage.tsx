import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '@/services/api';
import { UserRole } from '@/types';
import { roleLabels } from '@/store/authStore';
import toast from 'react-hot-toast';

interface RegisterForm {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  roles: UserRole[];
}

export const RegisterPage = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterForm>({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    roles: [UserRole.PLAYER],
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await api.register({
        ...form,
        phone: form.phone || undefined,
        roles: form.roles, // Send as array
      });
      toast.success('Registrierung erfolgreich! Bitte melde dich an.');
      navigate('/login');
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Registrierung fehlgeschlagen';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const roles = [
    { value: UserRole.PLAYER, label: roleLabels[UserRole.PLAYER] },
    { value: UserRole.PARENT, label: roleLabels[UserRole.PARENT] },
    { value: UserRole.COACH, label: roleLabels[UserRole.COACH] },
  ];

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
          <p className="text-gray-600 mt-2">Neues Konto erstellen</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="label">Vorname *</label>
                <input
                  id="first_name"
                  type="text"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label htmlFor="last_name" className="label">Nachname *</label>
                <input
                  id="last_name"
                  type="text"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className="input"
                  required
                />
              </div>
            </div>
            
            <div>
              <label htmlFor="email" className="label">E-Mail *</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="input"
                required
              />
            </div>
            
            <div>
              <label htmlFor="phone" className="label">Telefon (optional)</label>
              <input
                id="phone"
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="input"
                placeholder="+49 123 456789"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="label">Passwort *</label>
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="input"
                required
                minLength={8}
              />
              <p className="text-xs text-gray-500 mt-1">Mindestens 8 Zeichen</p>
            </div>
            
            <div>
              <label className="label">Rollen im Verein *</label>
              <p className="text-xs text-gray-500 mb-2">Mehrere Rollen möglich</p>
              <div className="space-y-2">
                {roles.map((role) => (
                  <label key={role.value} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="checkbox"
                      name="roles"
                      value={role.value}
                      checked={form.roles.includes(role.value)}
                      onChange={(e) => {
                        const value = e.target.value as UserRole;
                        if (e.target.checked) {
                          setForm({ ...form, roles: [...form.roles, value] });
                        } else {
                          setForm({ ...form, roles: form.roles.filter(r => r !== value) });
                        }
                      }}
                      className="mr-3"
                    />
                    <div>
                      <div className="font-medium">{role.label}</div>
                      <div className="text-xs text-gray-500">
                        {role.value === UserRole.PLAYER && 'Spieler im Verein'}
                        {role.value === UserRole.PARENT && 'Elternteil eines Spielers'}
                        {role.value === UserRole.COACH && 'Trainer oder Betreuer'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? 'Wird registriert...' : 'Konto erstellen'}
            </button>
          </form>
          
          <div className="mt-6 text-center text-sm">
            <span className="text-gray-500">Bereits registriert? </span>
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              Hier anmelden
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
