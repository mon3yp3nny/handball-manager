import { UserRole } from '@/types';
import { useAuthStore, useUIStore, roleLabels, roleColors } from '@/store/authStore';
import { Bug, X } from 'lucide-react';

export const DevRoleSwitcher = () => {
  const { isDevMode, user, devSwitchRole, logout } = useAuthStore();
  const { showDevSwitcher, setShowDevSwitcher } = useUIStore();

  if (!isDevMode || !showDevSwitcher) return null;

  const roles = Object.values(UserRole);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-gray-900 text-white rounded-lg shadow-lg p-3 max-w-xs">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center text-xs text-yellow-400">
            <Bug className="w-3 h-3 mr-1" />
            Dev Mode
          </div>
          <button 
            onClick={() => setShowDevSwitcher(false)}
            className="text-gray-400 hover:text-white"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
        
        <div className="text-xs text-gray-400 mb-2">
          Aktuell: <span className="text-white font-medium">{user ? roleLabels[user.role] : 'Nicht eingeloggt'}</span>
        </div>
        
        <div className="space-y-1">
          {roles.map((role) => (
            <button
              key={role}
              onClick={() => devSwitchRole(role)}
              className={`w-full text-left px-2 py-1 rounded text-xs transition-colors ${
                user?.role === role
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {roleLabels[role]}
            </button>
          ))}
        </div>
        
        {user && (
          <button
            onClick={logout}
            className="w-full mt-2 px-2 py-1 rounded text-xs bg-red-900/50 text-red-300 hover:bg-red-900"
          >
            Ausloggen
          </button>
        )}
      </div>
    </div>
  );
};
