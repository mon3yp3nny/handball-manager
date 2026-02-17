import { useParams } from 'react-router-dom';

export const NewsDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Nachricht</h1>
      </div>

      <div className="card p-6">
        <p className="text-gray-500">Nachricht ID: {id}</p>
      </div>
    </div>
  );
};
