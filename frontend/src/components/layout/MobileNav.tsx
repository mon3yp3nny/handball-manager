import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Shield, Users, Calendar, Trophy } from 'lucide-react';

const mobileNavItems = [
  { path: '/', label: 'Home', icon: LayoutDashboard },
  { path: '/teams', label: 'Teams', icon: Shield },
  { path: '/players', label: 'Spieler', icon: Users },
  { path: '/games', label: 'Spiele', icon: Trophy },
  { path: '/events', label: 'Termine', icon: Calendar },
];

export const MobileNav = () => {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t z-50">
      <div className="flex justify-around">
        {mobileNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center py-2 px-4 text-xs ${
                isActive
                  ? 'text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`
            }
          >
            <item.icon className="w-5 h-5 mb-1" />
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};
