import { useState } from 'react';
import { User, Mail, Phone, Shield } from 'lucide-react';
import { useRole, useAuthStore } from '@/store/authStore';
import { UserRole } from '@/types';

export const ProfilePage = () => {
  const { user, role } = useRole();
  const [isEditing, setIsEditing] = useState(false);

  const getRoleLabel = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN: return 'Administrator';
      case UserRole.COACH: return 'Trainer';
      case UserRole.SUPERVISOR: return 'Betreuer';
      case UserRole.PLAYER: return 'Spieler';
      case UserRole.PARENT: return 'Elternteil';
      default: return role;
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Mein Profil</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="card p-6">
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 bg-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-4">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            
            <h2 className="text-xl font-bold text-gray-900">
              {user?.first_name} {user?.last_name}
            </h2>
            
            <span className="badge-blue mt-2">{getRoleLabel(role!)}</span>
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex items-center">
              <Mail className="w-5 h-5 text-gray-400 mr-3" />
              <span>{user?.email}</span>
            </div>

            <div className="flex items-center">
              <Phone className="w-5 h-5 text-gray-400 mr-3" />
              <span>{user?.phone || 'Keine Telefonnummer'}</span>
            </div>

            <div className="flex items-center">
              <Shield className="w-5 h-5 text-gray-400 mr-3" />
              <span>Rolle: {getRoleLabel(role!)}</span>
            </div>
          </div>

          <button 
            onClick={() => setIsEditing(!isEditing)}
            className="btn-primary w-full mt-6"
          >
            Profil bearbeiten
          </button>
        </div>

        {/* Activity Card */}
        <div className="lg:col-span-2 card p-6">
          <h2 className="text-lg font-semibold mb-4">Aktivität</h2>
          
          <p className="text-gray-500">Hier werden zukünftig Ihre Aktivitäten angezeigt.</p>
        </div>
      </div>
    </div>
  );
};
