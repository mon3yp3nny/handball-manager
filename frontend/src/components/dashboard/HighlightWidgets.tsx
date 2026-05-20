import { useQuery } from '@tanstack/react-query';
import { Calendar, Cake, MapPin, Clock } from 'lucide-react';
import { api } from '@/services/api';

type NextMatch = {
  id: number;
  team_id: number;
  opponent: string;
  location: string | null;
  scheduled_at: string | null;
  is_home_game: boolean | null;
} | null;

type Birthday = {
  player_id: number;
  team_id: number | null;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string;
  days_until: number;
  turning: number;
};

type WidgetsPayload = {
  next_match: NextMatch;
  upcoming_birthdays: Birthday[];
};

function formatCountdown(iso: string): string {
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return 'jetzt';
  const days = Math.floor(ms / 86_400_000);
  const hours = Math.floor((ms % 86_400_000) / 3_600_000);
  if (days > 0) return `in ${days} Tag${days === 1 ? '' : 'en'}`;
  if (hours > 0) return `in ${hours} Std`;
  const minutes = Math.floor((ms % 3_600_000) / 60_000);
  return `in ${minutes} Min`;
}

const NextMatchCard = ({ match }: { match: NextMatch }) => (
  <div className="card p-6">
    <div className="flex items-center mb-3">
      <Calendar className="w-5 h-5 text-primary-600 mr-2" />
      <h2 className="text-lg font-semibold text-gray-900">Nächstes Spiel</h2>
    </div>
    {match ? (
      <>
        <p className="text-xl font-bold text-gray-900 mb-1">
          vs {match.opponent}
        </p>
        <p className="text-sm text-gray-500 mb-3">
          {match.is_home_game ? 'Heimspiel' : 'Auswärtsspiel'}
        </p>
        <div className="text-sm space-y-1.5">
          {match.scheduled_at && (
            <div className="flex items-center text-gray-700">
              <Clock className="w-4 h-4 mr-2 text-gray-400" />
              <span>
                {new Date(match.scheduled_at).toLocaleDateString('de-DE', {
                  weekday: 'short',
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                })}
                {' · '}
                {new Date(match.scheduled_at).toLocaleTimeString('de-DE', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
              <span className="ml-2 px-2 py-0.5 text-xs font-medium text-primary-700 bg-primary-50 rounded">
                {formatCountdown(match.scheduled_at)}
              </span>
            </div>
          )}
          {match.location && (
            <div className="flex items-center text-gray-700">
              <MapPin className="w-4 h-4 mr-2 text-gray-400" />
              <span>{match.location}</span>
            </div>
          )}
        </div>
      </>
    ) : (
      <p className="text-gray-500 text-sm">Aktuell keine geplanten Spiele.</p>
    )}
  </div>
);

const BirthdaysCard = ({ list }: { list: Birthday[] }) => (
  <div className="card p-6">
    <div className="flex items-center mb-3">
      <Cake className="w-5 h-5 text-pink-500 mr-2" />
      <h2 className="text-lg font-semibold text-gray-900">Geburtstage diese Woche</h2>
    </div>
    {list.length === 0 ? (
      <p className="text-gray-500 text-sm">Keine Geburtstage in den nächsten 7 Tagen.</p>
    ) : (
      <ul className="space-y-2">
        {list.map((b) => (
          <li
            key={b.player_id}
            className="flex items-center justify-between text-sm border-b border-gray-100 last:border-b-0 pb-2 last:pb-0"
          >
            <div>
              <span className="font-medium text-gray-900">
                {b.first_name} {b.last_name}
              </span>
              <span className="ml-2 text-gray-500">wird {b.turning}</span>
            </div>
            <span className="text-pink-600 font-medium">
              {b.days_until === 0
                ? 'heute'
                : b.days_until === 1
                  ? 'morgen'
                  : `in ${b.days_until} Tagen`}
            </span>
          </li>
        ))}
      </ul>
    )}
  </div>
);

export const HighlightWidgets = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-widgets'],
    queryFn: () => api.get<WidgetsPayload>('/dashboard/widgets'),
    // 5 min — fresh enough for countdowns, light on the backend.
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="card p-6 animate-pulse h-32" />
        <div className="card p-6 animate-pulse h-32" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
      <NextMatchCard match={data?.next_match ?? null} />
      <BirthdaysCard list={data?.upcoming_birthdays ?? []} />
    </div>
  );
};
