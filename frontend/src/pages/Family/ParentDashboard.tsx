import { useMyChildren } from '@/hooks/useParent';
import { useAuthStore } from '@/store/authStore';
import { PlayerCard } from '@/components/players/PlayerCard';
import { Link } from 'react-router-dom';
import { Calendar, Users, Trophy } from 'lucide-react';

export const ParentDashboard = () => {
  const { user } = useAuthStore();
  const { data: children, isLoading } = useMyChildren();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold">Hallo, {user?.first_name || 'Eltern'}!</h1>
        <p className="mt-2 text-primary-100">
          Hier sehen Sie alle Informationen zu {children?.length || 0} {children?.length === 1 ? 'Kind' : 'Kinder'}
        </p>
      </div>

      {/* Children Cards */}
      {children && children.length > 0 ? (
        <div className="grid gap-6">
          {children.map((child) => (
            <div
              key={child.id}
              className="bg-white rounded-xl shadow-sm border overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                      <span className="text-xl font-bold text-primary-600">
                        {child.user?.first_name?.[0]}{child.user?.last_name?.[0]}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold">
                        {child.user?.first_name} {child.user?.last_name}
                      </h3>
                      <p className="text-gray-500 text-sm">{child.team_name || 'Keinem Team zugewiesen'}</p>
                    </div>
                  </div>
                  {child.team_id && (
                    <div className="flex gap-2">
                      <Link
                        to={`/teams/${child.team_id}`}
                        className="btn-secondary text-sm flex items-center gap-1"
                      >
                        <Users size={14} />
                        Team
                      </Link>
                    </div>
                  )}
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t">
                  <div className="text-center">
                    <Trophy className="w-5 h-5 mx-auto text-amber-500 mb-1" />
                    <p className="text-2xl font-bold text-gray-900">{child.games_played || 0}</p>
                    <p className="text-xs text-gray-500">Spiele</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary-600">{child.goals_scored || 0}</div>
                    <p className="text-xs text-gray-500">Tore</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">-</div>
                    <p className="text-xs text-gray-500">Anwesenheit</p>
                  </div>
                </div>

                {/* Team Info */}
                {child.team_id && (
                  <>
                    <div className="mt-4 pt-4 border-t">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Aktueller Spielplan</h4>
                      <Link
                        to={`/calendar?team=${child.team_id}`}
                        className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
                      >
                        <Calendar size={16} />
                        Kalender ansehen →
                      </Link>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Keine Kinder verknüpft</h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Sie haben noch keine Kinder mit Ihrem Konto verknüpft. 
            Wenden Sie sich an einen Trainer oder Administrator, um Ihre Kinder hinzuzufügen.
          </p>
        </div>
      )}
    </div>
  );
};
