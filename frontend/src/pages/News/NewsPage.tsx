import { useQuery } from '@tanstack/react-query';
import { Newspaper } from 'lucide-react';
import { api } from '@/services/api';
import { News } from '@/types';

export const NewsPage = () => {
  const { data: news, isLoading, isError } = useQuery({
    queryKey: ['news'],
    queryFn: async () => {
      const res = await api.get('/news?limit=20');
      return res.items || [];
    },
  });

  if (isLoading) return <div>Lädt...</div>;
  if (isError) return <div className="text-center py-12 text-red-600">Fehler beim Laden der Nachrichten</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <Newspaper className="w-6 h-6 mr-2 text-primary-600" />
          <h1 className="page-title">Nachrichten</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {news?.map((item: News) => (
          <div key={item.id} className="card p-6">
            <div className="flex items-start justify-between mb-2">
              <span className={`badge${item.is_published ? '-green' : '-yellow'}`}>
                {item.is_published ? 'Veröffentlicht' : 'Entwurf'}
              </span>
              
              <span className="text-xs text-gray-500">
                {new Date(item.created_at).toLocaleDateString('de-DE')}
              </span>
            </div>
            
            <h2 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h2>
            <p className="text-gray-600 line-clamp-3">{item.content}</p>
            
            <div className="mt-4 text-sm text-gray-500">
              Von {item.author_name}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
