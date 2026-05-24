import { useQuery } from '@tanstack/react-query';
import { Calendar } from 'lucide-react';
import { api } from '@/services/api';
import { useUIStore } from '@/store/authStore';
import { Event, EventType, EventTypeLabels } from '@/types';

export const EventsPage = () => {
  // Scoped to the active team chosen in the sidebar (all visible if none).
  const teamId = useUIStore((s) => s.currentTeam?.id);
  const { data: events, isLoading, isError } = useQuery({
    queryKey: ['events', teamId ?? null],
    queryFn: async () => {
      const qs = teamId ? `?team_id=${teamId}&limit=100` : '?limit=100';
      const res = await api.get('/events' + qs);
      return res.items || [];
    },
  });

  if (isLoading) return <div>Lädt...</div>;
  if (isError) return <div className="text-center py-12 text-red-600">Fehler beim Laden der Termine</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <Calendar className="w-6 h-6 mr-2 text-primary-600" />
          <h1 className="page-title">Termine</h1>
        </div>
      </div>

      <div className="space-y-4">
        {events?.map((event: Event) => (
          <div key={event.id} className="card p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-900">{event.title}</p>
                <p className="text-sm text-gray-500 mt-1">{event.description}</p>
                <p className="text-sm text-gray-600 mt-2">📍 {event.location}</p>
              </div>
              
              <div className="text-right">
                <span className={`badge${
                  event.event_type === EventType.TRAINING ? '-blue' :
                  event.event_type === EventType.MEETING ? '-yellow' :
                  event.event_type === EventType.TOURNAMENT ? '-green' : ''
                }`}>
                  {EventTypeLabels[event.event_type]}
                </span>
                <p className="text-sm text-gray-500 mt-2">
                  {new Date(event.start_time).toLocaleString('de-DE')}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
