import { useQuery } from '@tanstack/react-query';
import { Trophy } from 'lucide-react';
import { api } from '@/services/api';
import { Game } from '@/types';

export const GamesPage = () => {
  const { data: games, isLoading } = useQuery({
    queryKey: ['games'],
    queryFn: async () => {
      const res = await api.get('/games?limit=100');
      return res.items || [];
    },
  });

  if (isLoading) return <div>Lädt...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <Trophy className="w-6 h-6 mr-2 text-primary-600" />
          <h1 className="page-title">Spiele</h1>
        </div>
      </div>

      <div className="space-y-4">
        {games?.map((game: Game) => (
          <div key={game.id} className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">
                  {game.team_name} vs {game.opponent}
                </p>
                <p className="text-sm text-gray-500">
                  {game.location} • {new Date(game.scheduled_at).toLocaleString('de-DE')}
                </p>
              </div>
              
              <div className="text-right">
                {game.status === 'completed' ? (
                  <p className="font-bold text-gray-900">
                    {game.home_score} : {game.away_score}
                  </p>
                ) : (
                  <span className={`badge${
                    game.status === 'scheduled' ? '-blue' : 
                    game.status === 'cancelled' ? '-red' : '-yellow'
                  }`}>
                    {game.status}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
