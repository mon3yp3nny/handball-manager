import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { TeamWithPlayers } from '@/types';

export const TeamDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  const { data: team, isLoading, isError } = useQuery({
    queryKey: ['team', id],
    queryFn: () => api.get<TeamWithPlayers>(`/teams/${id}`),
  });

  if (isLoading) return <div>Lädt...</div>;
  if (isError) return <div className="text-center py-12 text-red-600">Fehler beim Laden der Mannschaft</div>;
  if (!team) return <div>Mannschaft nicht gefunden</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{team.name}</h1>
          {team.age_group && <span className="badge-blue">{team.age_group}</span>}
        </div>
      </div>

      <div className="card mb-6">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Spieler</h2>
        </div>
        <div className="p-4">
          {team.players?.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Position</th>
                  <th className="px-4 py-2 text-left">Trikot</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {team.players.map((player) => (
                  <tr key={player.id}>
                    <td className="px-4 py-2">{player.user?.first_name} {player.user?.last_name}</td>
                    <td className="px-4 py-2">{player.position}</td>
                    <td className="px-4 py-2">{player.jersey_number}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500">Keine Spieler in dieser Mannschaft</p>
          )}
        </div>
      </div>
    </div>
  );
};
