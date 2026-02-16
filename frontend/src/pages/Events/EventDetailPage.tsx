import { useParams } from 'react-router-dom';

export const EventDetailPage = () => {
  const { id } = useParams<{ id: string }>;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Termin Details</h1>
      </div>

      <div className="card p-6">
        <p className="text-gray-500">Termin ID: {id}</p>
      </div>
    </div>
  );
};
