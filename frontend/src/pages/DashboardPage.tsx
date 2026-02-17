import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Trophy,
  Calendar,
  ClipboardCheck,
  TrendingUp,
  Activity
} from 'lucide-react';
import { api } from '@/services/api';
import { useRole } from '@/store/authStore';
import { Game, Event } from '@/types';
import { ParentDashboard } from './Family/ParentDashboard';

export const DashboardPage = () => {
  const { user, isCoach, isPlayer, isParent } = useRole();

  const { data: teamsCount } = useQuery({
    queryKey: ['teams-count'],
    queryFn: async () => {
      const res = await api.get<{ total?: number }>('/teams?limit=1');
      return res.total || 0;
    },
    enabled: !isParent,
  });

  const { data: upcomingGames } = useQuery({
    queryKey: ['upcoming-games'],
    queryFn: async () => {
      const res = await api.get<{ items?: Game[] }>('/games?upcoming=true&limit=5');
      return res.items || [];
    },
    enabled: !isParent,
  });

  const { data: upcomingEvents } = useQuery({
    queryKey: ['upcoming-events'],
    queryFn: async () => {
      const res = await api.get<{ items?: Event[] }>('/events?upcoming=true&limit=5');
      return res.items || [];
    },
    enabled: !isParent,
  });

  // Show parent-specific dashboard (after all hooks)
  if (isParent) {
    return <ParentDashboard />;
  }

  const stats = [
    { label: 'Mannschaften', value: teamsCount || 0, icon: Users, color: 'bg-blue-500' },
    { label: 'Kommende Spiele', value: upcomingGames?.length || 0, icon: Trophy, color: 'bg-green-500' },
    { label: 'Termine', value: upcomingEvents?.length || 0, icon: Calendar, color: 'bg-purple-500' },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-gray-500">
            Hallo {user?.first_name}, willkommen zurück beim Handball Manager!
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="card p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 ${stat.color} rounded-lg p-3`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Upcoming Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Games */}
        <div className="card">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Kommende Spiele</h2>
          </div>
          <div className="p-4">
            {(upcomingGames?.length ?? 0) > 0 ? (
              <div className="space-y-3">
                {upcomingGames!.map((game: Game) => (
                  <div key={game.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">
                        {game.team_name} vs {game.opponent}
                      </p>
                      <p className="text-sm text-gray-500">{game.location}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-900">
                        {new Date(game.scheduled_at).toLocaleDateString('de-DE')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Keine kommenden Spiele</p>
            )}
          </div>
        </div>

        {/* Upcoming Events */}
        <div className="card">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Kommende Termine</h2>
          </div>
          <div className="p-4">
            {(upcomingEvents?.length ?? 0) > 0 ? (
              <div className="space-y-3">
                {upcomingEvents!.map((event: Event) => (
                  <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{event.title}</p>
                      <p className="text-sm text-gray-500">{event.location}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-900">
                        {new Date(event.start_time).toLocaleDateString('de-DE')}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(event.start_time).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Keine kommenden Termine</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
