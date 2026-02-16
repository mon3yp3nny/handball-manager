import { useQuery } from '@tanstack/react-query';
import { ClipboardCheck } from 'lucide-react';
import { api } from '@/services/api';
import { Attendance } from '@/types';

export const AttendancePage = () => {
  const { data: records, isLoading } = useQuery({
    queryKey: ['attendance'],
    queryFn: async () => {
      const res = await api.get('/attendance?limit=100');
      return res.items || [];
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present': return 'badge-green';
      case 'absent': return 'badge-red';
      case 'excused': return 'badge-yellow';
      default: return 'badge-blue';
    }
  };

  if (isLoading) return <div>Lädt...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <ClipboardCheck className="w-6 h-6 mr-2 text-primary-600" />
          <h1 className="page-title">Anwesenheit</h1>
        </div>
      </div>

      <div className="card">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Spieler</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notizen</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Datum</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {records?.map((record: Attendance) => (
              <tr key={record.id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">{record.player_name}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`badge ${getStatusColor(record.status)}`}>
                    {record.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">{record.notes || '-'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                  {new Date(record.recorded_at).toLocaleString('de-DE')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
