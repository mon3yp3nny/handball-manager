import { useState } from 'react';
import { Menu, Bell, User as UserIcon, X } from 'lucide-react';
import { useRole, useAuthStore } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { user } = useRole();
  const { logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-white shadow-sm z-50 flex items-center justify-between px-4">
      <button 
        onClick={onMenuClick}
        className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-md"
      >
        <Menu className="w-6 h-6" />
      </button>
      
      <div className="font-bold text-lg text-primary-600">
        Handball Manager
      </div>
      
      <div className="relative">
        <button
          onClick={() => setShowProfile(!showProfile)}
          className="p-2 -mr-2 text-gray-600 hover:bg-gray-100 rounded-md flex items-center gap-2"
        >
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-medium">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
        </button>
        
        {showProfile && (
          <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg py-2 border">
            <div className="px-4 py-2 border-b">
              <p className="font-medium">{user?.first_name} {user?.last_name}</p>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
            
            <a
              href="/profile"
              className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100"
              onClick={() => setShowProfile(false)}
            >
              <UserIcon className="w-4 h-4 mr-2" />
              Profil
            </a>
            
            <button
              onClick={() => {
                logout();
                setShowProfile(false);
              }}
              className="w-full text-left flex items-center px-4 py-2 text-red-600 hover:bg-gray-100"
            >
              <X className="w-4 h-4 mr-2" />
              Abmelden
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
