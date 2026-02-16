import { useQuery } from '@tanstack/react-query';
import { Calendar } from 'lucide-react';
import { api } from '@/services/api';
import { Event } from '@/types';

export const EventsPage = () => {
  const { data: events, isLoading } = useQuery({
    queryKey: ['events'],
    queryFn: async () => {
      const res = await api.get('/events?limit=100');
      return res.items || [];
    },
  });

  if (isLoading) return <div>Lädt...</div>;

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
                  event.event_type === 'training' ? '-blue' :
                  event.event_type === 'meeting' ? '-yellow' :
                  event.event_type === 'tournament' ? '-green' : ''
                }`}>
                  {event.event_type}
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
