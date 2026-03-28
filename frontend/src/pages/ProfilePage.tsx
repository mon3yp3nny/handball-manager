import { useState } from 'react';
import { User, Mail, Phone, Shield, AlertTriangle } from 'lucide-react';
import { useRole, useAuthStore } from '@/store/authStore';
import { UserRole } from '@/types';
import { api } from '@/services/api';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export const ProfilePage = () => {
  const { user, role } = useRole();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [confirmText, setConfirmText] = useState('');

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

  const handleDeleteAccount = async () => {
    if (confirmText !== 'LÖSCHEN') {
      toast.error('Bitte gib "LÖSCHEN" ein, um fortzufahren');
      return;
    }
    
    setIsDeleting(true);
    try {
      await api.deleteAccount();
      toast.success('Dein Konto wurde erfolgreich gelöscht');
      logout();
      navigate('/login');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Fehler beim Löschen des Kontos');
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
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

        {/* Settings Card */}
        <div className="lg:col-span-2 space-y-6">
          {/* Activity Card */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">Aktivität</h2>
            
            <p className="text-gray-500">Hier werden zukünftig Ihre Aktivitäten angezeigt.</p>
          </div>

          {/* Danger Zone */}
          <div className="card p-6 border-red-200">
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
              <h2 className="text-lg font-semibold text-red-600">Gefahrenzone</h2>
            </div>
            
            <p className="text-gray-600 mb-4">
              Das Löschen deines Kontos kann nicht rückgängig gemacht werden. Alle deine Daten werden dauerhaft gelöscht.
            </p>
            
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Konto löschen
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full">
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-6 h-6 text-red-600 mr-2" />
              <h2 className="text-xl font-semibold text-red-600">Konto löschen</h2>
            </div>
            
            <p className="text-gray-700 mb-4">
              Bist du sicher, dass du dein Konto löschen möchtest? Diese Aktion kann <strong>nicht rückgängig</strong> gemacht werden.
            </p>
            
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="text-sm text-gray-600">
                Gib <code className="bg-gray-200 px-1 rounded">LÖSCHEN</code> ein, um zu bestätigen:
              </p>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="LÖSCHEN"
              />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setConfirmText('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={isDeleting}
              >
                Abbrechen
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={isDeleting || confirmText !== 'LÖSCHEN'}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {isDeleting ? 'Wird gelöscht...' : 'Endgültig löschen'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
