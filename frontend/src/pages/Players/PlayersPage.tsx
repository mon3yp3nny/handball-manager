import { useQuery } from '@tanstack/react-query';
import { Users } from 'lucide-react';
import { api } from '@/services/api';
import { Player } from '@/types';

export const PlayersPage = () => {
  const { data: players, isLoading } = useQuery({
    queryKey: ['players'],
    queryFn: async () => {
      const res = await api.get('/players?limit=100');
      return res.items || [];
    },
  });

  if (isLoading) return <div>Lädt...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <Users className="w-6 h-6 mr-2 text-primary-600" />
          <h1 className="page-title">Spieler</h1>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Suchen..."
              className="input max-w-xs"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trikot</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Spiele</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tore</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {players?.map((player: Player) => (
                <tr key={player.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">
                      {player.user?.first_name} {player.user?.last_name}
                    </div>
                    <div className="text-sm text-gray-500">{player.user?.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{player.jersey_number || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                      {player.position || '-'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{player.games_played}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{player.goals_scored}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
