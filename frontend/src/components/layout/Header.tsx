import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, User as UserIcon, X, LogOut } from 'lucide-react';
import { useRole } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth';
import { ClubCrest } from '@/components/brand/ClubCrest';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { user } = useRole();
  const { logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-tvf-navy text-tvf-ink-on-navy z-50 flex items-center justify-between px-4 shadow-tvf-md">
      <button
        onClick={onMenuClick}
        className="p-2 -ml-2 text-tvf-ink-on-navy/80 hover:bg-white/10 rounded-tvf-sm"
        aria-label="Menü öffnen"
      >
        <Menu className="w-6 h-6" />
      </button>

      <div className="flex items-center gap-2">
        <ClubCrest size={26} />
        <span className="font-display tracking-wide text-base leading-none">
          Handball Manager
        </span>
      </div>

      <div className="relative">
        <button
          onClick={() => setShowProfile(!showProfile)}
          className="p-1 -mr-1 rounded-full hover:bg-white/10"
          aria-label="Profilmenü"
        >
          <div className="w-8 h-8 bg-tvf-red rounded-full flex items-center justify-center text-white font-bold text-sm">
            {user?.first_name?.[0]}
            {user?.last_name?.[0]}
          </div>
        </button>

        {showProfile && (
          <div className="absolute right-0 top-full mt-2 w-56 bg-tvf-surface rounded-tvf-md shadow-tvf-lg py-2 border border-tvf-line text-tvf-ink">
            <div className="px-4 py-2 border-b border-tvf-line">
              <p className="font-semibold">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-tvf-ink-3 truncate">{user?.email}</p>
            </div>

            <Link
              to="/profile"
              className="flex items-center px-4 py-2 text-tvf-ink hover:bg-tvf-surface-2 text-sm font-semibold"
              onClick={() => setShowProfile(false)}
            >
              <UserIcon className="w-4 h-4 mr-2" />
              Profil
            </Link>

            <button
              onClick={() => {
                logout();
                setShowProfile(false);
              }}
              className="w-full text-left flex items-center px-4 py-2 text-tvf-red-deep hover:bg-tvf-red-soft text-sm font-semibold"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Abmelden
            </button>
          </div>
        )}
      </div>

      {/* invisible hint for screen readers; X icon used only inside menu */}
      <span className="sr-only">
        <X aria-hidden="true" />
      </span>
    </header>
  );
};
