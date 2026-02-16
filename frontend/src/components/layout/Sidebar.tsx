import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Trophy, 
  Calendar, 
  Newspaper, 
  ClipboardCheck, 
  User,
  Shield,
  X
} from 'lucide-react';
import { useRole } from '@/store/authStore';
import { UserRole } from '@/types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/teams', label: 'Mannschaften', icon: Shield, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/players', label: 'Spieler', icon: Users, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/games', label: 'Spiele', icon: Trophy, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/events', label: 'Termine', icon: Calendar, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/attendance', label: 'Anwesenheit', icon: ClipboardCheck, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/news', label: 'News', icon: Newspaper, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/profile', label: 'Profil', icon: User, roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
];

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const { user, role } = useRole();
  const location = useLocation();
  
  const filteredNavItems = navItems.filter(item => 
    role && item.roles.includes(role)
  );

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <nav
        className={`
          fixed md:sticky top-0 left-0 z-50 
          w-64 h-screen bg-white border-r border-gray-200 
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-6 border-b">
            <div className="font-bold text-xl text-primary-600">
              Handball Manager
            </div>
            <button
              onClick={onClose}
              className="md:hidden p-2 text-gray-500 hover:text-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* User info */}
          <div className="px-4 py-4 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center text-white font-medium">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-sm text-gray-500">
                  {role === UserRole.ADMIN && 'Administrator'}
                  {role === UserRole.COACH && 'Trainer'}
                  {role === UserRole.SUPERVISOR && 'Betreuer'}
                  {role === UserRole.PLAYER && 'Spieler'}
                  {role === UserRole.PARENT && 'Eltern'}
                </p>
              </div>
            </div>
          </div>
          
          {/* Navigation */}
          <div className="flex-1 overflow-y-auto py-4">
            <ul className="space-y-1 px-3">
              {filteredNavItems.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                      }`
                    }
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Footer */}
          <div className="p-4 border-t text-xs text-gray-400 text-center">
            Handball Manager v1.0
          </div>
        </div>
      </nav>
    </>
  );
};
