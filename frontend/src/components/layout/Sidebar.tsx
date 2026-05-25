import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  Users,
  Trophy,
  Calendar,
  Newspaper,
  ClipboardCheck,
  User,
  Shield,
  ShieldCheck,
  UserCheck,
  X,
} from 'lucide-react';
import { useRole, useUIStore } from '@/store/authStore';
import { UserRole, PublicTeam } from '@/types';
import { api } from '@/services/api';
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
};

// "Allgemein" — club-wide items that don't depend on a selected team.
const generalItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard,
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/teams', label: 'Mannschaften', icon: Shield,
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/games', label: 'Spiele', icon: Trophy,
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/news', label: 'News', icon: Newspaper,
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
  { path: '/approvals', label: 'Genehmigungen', icon: UserCheck,
    roles: [UserRole.ADMIN, UserRole.COACH] },
  { path: '/profile', label: 'Profil', icon: User,
    roles: [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR, UserRole.PLAYER, UserRole.PARENT] },
];

// Team-scoped items — repeated under each team section; they filter their
// pages by the active team (set when the item is clicked).
const teamItems: { path: string; label: string; icon: typeof LayoutDashboard }[] = [
  { path: '/players', label: 'Spieler', icon: Users },
  { path: '/events', label: 'Training & Termine', icon: Calendar },
  { path: '/attendance', label: 'Anwesenheit', icon: ClipboardCheck },
];

const ROLE_LABEL: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Administrator',
  [UserRole.COACH]: 'Trainer',
  [UserRole.SUPERVISOR]: 'Betreuer',
  [UserRole.PLAYER]: 'Spieler',
  [UserRole.PARENT]: 'Eltern',
};

const linkClass = (active: boolean) =>
  `flex items-center gap-3 px-3 py-2.5 rounded-tvf-sm text-sm font-semibold transition-colors ${
    active
      ? 'bg-tvf-red text-white shadow-tvf-sm'
      : 'text-tvf-ink-on-navy/85 hover:bg-white/5 hover:text-tvf-ink-on-navy'
  }`;

// One team section ("Meine Trainer-Mannschaft" / "Meine Mannschaft").
// Has its own selected team (a dropdown when more than one); clicking a
// page activates that team globally so the page filters to it.
function TeamSection({
  title,
  icon: SectionIcon,
  teams,
  onNavigate,
}: {
  title: string;
  icon: typeof LayoutDashboard;
  teams: PublicTeam[];
  onNavigate: () => void;
}) {
  const location = useLocation();
  const { currentTeam, setCurrentTeam } = useUIStore();
  const [selectedId, setSelectedId] = useState<number>(teams[0].id);

  // Keep selection valid if the team list changes (e.g. after refetch).
  useEffect(() => {
    if (!teams.some((t) => t.id === selectedId)) setSelectedId(teams[0].id);
  }, [teams, selectedId]);

  const selectedTeam = teams.find((t) => t.id === selectedId) ?? teams[0];

  return (
    <div>
      <div className="tvf-eyebrow text-tvf-ink-on-navy/55 px-3 mb-1 flex items-center gap-2">
        <SectionIcon className="w-3.5 h-3.5" />
        <span>{title}</span>
      </div>

      {teams.length > 1 ? (
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(Number(e.target.value))}
          className="mx-3 mb-2 w-[calc(100%-1.5rem)] bg-tvf-navy-deep text-tvf-ink-on-navy text-sm rounded-tvf-sm px-2 py-1.5 border border-white/10"
        >
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}{t.age_group ? ` (${t.age_group})` : ''}
            </option>
          ))}
        </select>
      ) : (
        <div className="px-3 mb-2 text-sm font-semibold text-tvf-ink-on-navy/90 truncate">
          {selectedTeam.name}{selectedTeam.age_group ? ` (${selectedTeam.age_group})` : ''}
        </div>
      )}

      <ul className="space-y-1">
        {teamItems.map((item) => {
          const active =
            location.pathname === item.path && currentTeam?.id === selectedTeam.id;
          return (
            <li key={item.path}>
              {/* A real link (accessible + cmd-clickable). onClick sets this
                  section's team as the active scope before navigating. */}
              <Link
                to={item.path}
                onClick={() => {
                  setCurrentTeam(selectedTeam);
                  onNavigate();
                }}
                className={linkClass(active)}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const { user, role, isAdmin, isCoach } = useRole();
  const { currentTeam, setCurrentTeam } = useUIStore();

  const canApprove = isAdmin || isCoach;
  const { data: pending = [] } = useQuery({
    queryKey: ['pending-registrations'],
    queryFn: () => api.getPendingRegistrations(),
    enabled: canApprove,
  });
  const pendingCount = pending.length;

  const { data: myTeams } = useQuery({
    queryKey: ['my-teams'],
    queryFn: () => api.getMyTeams(),
  });
  const managed = useMemo(() => myTeams?.managed ?? [], [myTeams]);
  const member = useMemo(() => myTeams?.member ?? [], [myTeams]);

  // Default the active team once teams load, so team pages have a scope.
  useEffect(() => {
    if (currentTeam) return;
    const first = managed[0] ?? member[0];
    if (first) setCurrentTeam(first);
  }, [managed, member, currentTeam, setCurrentTeam]);

  const general = role ? generalItems.filter((i) => i.roles.includes(role)) : [];

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-tvf-navy-deep/60 z-40 md:hidden"
          onClick={onClose}
        />
      )}

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

          {/* Navigation */}
          <div className="flex-1 overflow-y-auto py-3 px-3 space-y-4">
            {general.length > 0 && (
              <div>
                <div className="tvf-eyebrow text-tvf-ink-on-navy/55 px-3 mb-1">
                  Allgemein
                </div>
                <ul className="space-y-1">
                  {general.map((item) => {
                    const badge =
                      item.path === '/approvals' && pendingCount > 0 ? pendingCount : null;
                    return (
                      <li key={item.path}>
                        <NavLink
                          to={item.path}
                          onClick={onClose}
                          end={item.path === '/'}
                          className={({ isActive }) => linkClass(isActive)}
                        >
                          <item.icon className="w-5 h-5" />
                          <span className="flex-1">{item.label}</span>
                          {badge !== null && (
                            <span className="inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full bg-tvf-red text-white text-xs font-bold">
                              {badge}
                            </span>
                          )}
                        </NavLink>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {managed.length > 0 && (
              <TeamSection
                title="Meine Trainer-Mannschaft"
                icon={ShieldCheck}
                teams={managed}
                onNavigate={onClose}
              />
            )}

            {member.length > 0 && (
              <TeamSection
                title="Meine Mannschaft"
                icon={Users}
                teams={member}
                onNavigate={onClose}
              />
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
