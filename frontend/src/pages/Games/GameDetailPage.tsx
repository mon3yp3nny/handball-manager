import { useParams } from 'react-router-dom';

export const GameDetailPage = () => {
  const { id } = useParams<{ id: string }>;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Spiel Details</h1>
      </div>

      <div className="card p-6">
        <p className="text-gray-500">Spiel ID: {id}</p>
        <p className="mt-4">Hier werden die Spieldetails und Ergebnisse angezeigt.</p>
      </div>
    </div>
  );
};
