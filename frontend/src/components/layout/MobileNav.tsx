import { NavLink } from 'react-router-dom';
import { Home, Calendar, Users, MoreHorizontal } from 'lucide-react';

// Four-tab bottom nav — matches the floating-pill pattern from the
// TV Fischbek mobile design. Items chosen for what a player/parent
// reaches for most. Other pages live in the side menu.
const mobileNavItems = [
  { path: '/', label: 'Home', icon: Home, end: true },
  { path: '/games', label: 'Spiele', icon: Calendar, end: false },
  { path: '/players', label: 'Team', icon: Users, end: false },
  { path: '/profile', label: 'Mehr', icon: MoreHorizontal, end: false },
];

export const MobileNav = () => {
  return (
    <nav
      className="md:hidden fixed bottom-4 left-4 right-4 z-50 bg-tvf-surface border border-tvf-line rounded-tvf-xl p-1.5 flex justify-around items-stretch"
      style={{
        boxShadow:
          '0 10px 28px rgba(14,42,71,0.14), 0 2px 6px rgba(14,42,71,0.06)',
      }}
    >
      {mobileNavItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.end}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center justify-center py-2 px-2 text-[11px] font-bold rounded-tvf-md transition-colors ${
              isActive
                ? 'bg-tvf-navy text-tvf-ink-on-navy'
                : 'text-tvf-ink-2 hover:text-tvf-ink'
            }`
          }
        >
          <item.icon className="w-5 h-5 mb-1" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
};
