import { useParams } from 'react-router-dom';
import { User } from 'lucide-react';

export const PlayerDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-xl font-bold">
            <User className="w-8 h-8" />
          </div>
          <div className="ml-4">
            <h1 className="page-title">Spieler Details</h1>
            <p className="text-gray-500">ID: {id}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Profilinformationen</h2>
          <p className="text-gray-500">Hier werden Spielerdetails angezeigt...</p>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Statistiken</h2>
          <p className="text-gray-500">Hier werden Spielerstatistiken angezeigt...</p>
        </div>
      </div>
    </div>
  );
};
