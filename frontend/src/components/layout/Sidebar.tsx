import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Trophy,
  Calendar,
  Newspaper,
  ClipboardCheck,
  User,
  Shield,
  X,
} from 'lucide-react';
import { useRole } from '@/store/authStore';
import { UserRole } from '@/types';
import { ClubCrest } from '@/components/brand/ClubCrest';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

type NavItem = {
  path: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
  section: 'verein' | 'mannschaft';
};

// Sections mirror the design — "Verein" (club-wide) above "Mannschaft"
// (team-scoped). Both groups apply to every role today; the section
// split is a visual grouping, not an RBAC distinction.
const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, section: 'verein',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/teams', label: 'Mannschaften', icon: Shield, section: 'verein',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/games', label: 'Spiele', icon: Trophy, section: 'verein',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/news', label: 'News', icon: Newspaper, section: 'verein',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },

  { path: '/players', label: 'Spieler', icon: Users, section: 'mannschaft',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/events', label: 'Training & Termine', icon: Calendar, section: 'mannschaft',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/attendance', label: 'Anwesenheit', icon: ClipboardCheck, section: 'mannschaft',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/profile', label: 'Profil', icon: User, section: 'mannschaft',
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
];

const ROLE_LABEL: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Administrator',
  [UserRole.COACH]: 'Trainer',
  [UserRole.SUPERVISOR]: 'Betreuer',
  [UserRole.PLAYER]: 'Spieler',
  [UserRole.PARENT]: 'Eltern',
};

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const { user, role } = useRole();

  const visible = role ? navItems.filter((i) => i.roles.includes(role)) : [];
  const verein = visible.filter((i) => i.section === 'verein');
  const mannschaft = visible.filter((i) => i.section === 'mannschaft');

  const renderLink = (item: NavItem) => (
    <li key={item.path}>
      <NavLink
        to={item.path}
        onClick={onClose}
        end={item.path === '/'}
        className={({ isActive }) =>
          `flex items-center gap-3 px-3 py-2.5 rounded-tvf-sm text-sm font-semibold transition-colors ${
            isActive
              ? 'bg-tvf-red text-white shadow-tvf-sm'
              : 'text-tvf-ink-on-navy/85 hover:bg-white/5 hover:text-tvf-ink-on-navy'
          }`
        }
      >
        <item.icon className="w-5 h-5" />
        <span>{item.label}</span>
      </NavLink>
    </li>
  );

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-tvf-navy-deep/60 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar — dark navy with subtle diagonal stripe texture.
          `fixed md:sticky` is the position; do NOT add `relative` to this
          className — Tailwind's generated CSS has .relative AFTER .fixed,
          so adding it here would silently turn off `fixed` (the nav would
          take 100vh of layout space at the top of the page and push every
          mobile route a full viewport down). The `tvf-stripes-overlay`
          class uses position:absolute on ::before, which works fine with
          `fixed` or `sticky` as the containing block. */}
      <nav
        className={`
          tvf-stripes-overlay
          fixed md:sticky top-0 left-0 z-50
          w-64 h-screen bg-tvf-navy text-tvf-ink-on-navy
          border-r border-tvf-navy-deep
          transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        <div className="relative flex flex-col h-full">
          {/* Brand header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <ClubCrest size={36} />
              <div>
                <div className="font-display tracking-wide leading-none text-base">
                  Handball Manager
                </div>
                <div className="text-[10.5px] font-semibold opacity-60 mt-1">
                  Verein · Mannschaft · Spielplan
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="md:hidden p-2 text-white/70 hover:text-white"
              aria-label="Menü schließen"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Logged-in user pill */}
          <div className="px-4 py-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-tvf-red text-white flex items-center justify-center font-bold">
                {user?.first_name?.[0]}
                {user?.last_name?.[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-tvf-ink-on-navy truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-tvf-ink-on-navy/60">
                  {role ? ROLE_LABEL[role] : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation — grouped */}
          <div className="flex-1 overflow-y-auto py-3 px-3 space-y-4">
            {verein.length > 0 && (
              <div>
                <div className="tvf-eyebrow text-tvf-ink-on-navy/55 px-3 mb-1">
                  Verein
                </div>
                <ul className="space-y-1">{verein.map(renderLink)}</ul>
              </div>
            )}
            {mannschaft.length > 0 && (
              <div>
                <div className="tvf-eyebrow text-tvf-ink-on-navy/55 px-3 mb-1">
                  Mannschaft
                </div>
                <ul className="space-y-1">{mannschaft.map(renderLink)}</ul>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-white/10 text-[11px] text-tvf-ink-on-navy/45 text-center font-semibold tracking-wider uppercase">
            Handball · v1.0
          </div>
        </div>
      </nav>
    </>
  );
};
