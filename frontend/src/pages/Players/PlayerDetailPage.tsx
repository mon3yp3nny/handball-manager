import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { User, Phone, Mail, Shield, Calendar, Trophy, Users, ArrowLeft, UserCircle } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../services/api';

interface Player {
  id: number;
  user_id: number;
  team_id: number | null;
  jersey_number: number | null;
  position: string | null;
  date_of_birth: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  games_played: number;
  goals_scored: number;
  assists: number;
  created_at: string;
  updated_at: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    phone: string | null;
    role: string;
    is_active: boolean;
    is_verified: boolean;
  };
  team_name: string | null;
  parents: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    phone: string | null;
  }[];
}

export const PlayerDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [player, setPlayer] = useState<Player | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPlayer = async () => {
      try {
        const response = await api.get(`/players/${id}`);
        setPlayer(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Fehler beim Laden der Spielerdaten');
      } finally {
        setLoading(false);
      }
    };
    fetchPlayer();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!player) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p>Spieler nicht gefunden</p>
      </div>
    );
  }

  const getPositionLabel = (position: string | null) => {
    const positions: { [key: string]: string } = {
      goalkeeper: 'Torwart',
      left_wing: 'Linksaußen',
      left_back: 'Rückraum Links',
      center_back: 'Rückraum Mitte',
      right_back: 'Rückraum Rechts',
      right_wing: 'Rechtsaußen',
      pivot: 'Kreisläufer',
      defense: 'Deckung',
    };
    return position ? positions[position] || position : 'Nicht angegeben';
  };

  const getInitials = () => {
    return `${player.user.first_name.charAt(0)}${player.user.last_name.charAt(0)}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center">
          <Link
            to="/players"
            className="mr-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-white text-xl font-bold">
            {getInitials()}
          </div>
          <div className="ml-4">
            <h1 className="text-2xl font-bold">
              {player.user.first_name} {player.user.last_name}
            </h1>
            <p className="text-gray-500">
              {player.jersey_number && `#${player.jersey_number} • `}
              {getPositionLabel(player.position)}
            </p>
          </div>
        </div>
        {(user?.role === 'admin' || user?.role === 'coach') && (
          <Link
            to={`/players/${id}/edit`}
            className="btn btn-primary"
          >
            Bearbeiten
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Information */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <User className="w-5 h-5 mr-2" />
            Profilinformationen
          </h2>
          <div className="space-y-4">
            <div className="flex items-center">
              <Mail className="w-4 h-4 text-gray-400 mr-3" />
              <div>
                <p className="text-sm text-gray-500">E-Mail</p>
                <p>{player.user.email}</p>
              </div>
            </div>
            {player.user.phone && (
              <div className="flex items-center">
                <Phone className="w-4 h-4 text-gray-400 mr-3" />
                <div>
                  <p className="text-sm text-gray-500">Telefon</p>
                  <p>{player.user.phone}</p>
                </div>
              </div>
            )}
            {player.date_of_birth && (
              <div className="flex items-center">
                <Calendar className="w-4 h-4 text-gray-400 mr-3" />
                <div>
                  <p className="text-sm text-gray-500">Geburtsdatum</p>
                  <p>{new Date(player.date_of_birth).toLocaleDateString('de-DE')}</p>
                </div>
              </div>
            )}
            <div className="flex items-center">
              <Shield className="w-4 h-4 text-gray-400 mr-3" />
              <div>
                <p className="text-sm text-gray-500">Rolle</p>
                <p className="capitalize">{player.user.role}</p>
              </div>
            </div>
            {player.team_name && (
              <div className="flex items-center">
                <Users className="w-4 h-4 text-gray-400 mr-3" />
                <div>
                  <p className="text-sm text-gray-500">Team</p>
                  <Link to={`/teams/${player.team_id}`} className="text-primary-600 hover:underline">
                    {player.team_name}
                  </Link>
                </div>
              </div>
            )}
            {player.emergency_contact_name && (
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-500 mb-2">Notfallkontakt</p>
                <p className="font-medium">{player.emergency_contact_name}</p>
                {player.emergency_contact_phone && (
                  <p className="text-sm">{player.emergency_contact_phone}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Statistics */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Trophy className="w-5 h-5 mr-2" />
            Statistiken
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-primary-600">{player.games_played}</p>
              <p className="text-sm text-gray-500">Spiele</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{player.goals_scored}</p>
              <p className="text-sm text-gray-500">Tore</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{player.assists}</p>
              <p className="text-sm text-gray-500">Assists</p>
            </div>
          </div>
          {player.games_played > 0 && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Tore pro Spiel</span>
                <span className="font-semibold">
                  {(player.goals_scored / player.games_played).toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Parents */}
        {(user?.role === 'admin' || user?.role === 'coach' || user?.id === player.user_id || 
          player.parents.some(p => p.id === user?.id)) && (
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <UserCircle className="w-5 h-5 mr-2" />
              Eltern/Verantwortliche
            </h2>
            {player.parents.length === 0 ? (
              <p className="text-gray-500">Keine Eltern verknüpft</p>
            ) : (
              <div className="space-y-4">
                {player.parents.map((parent) => (
                  <div key={parent.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center mb-2">
                      <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-white text-sm font-bold">
                        {parent.first_name.charAt(0)}{parent.last_name.charAt(0)}
                      </div>
                      <div className="ml-3">
                        <p className="font-medium">{parent.first_name} {parent.last_name}</p>
                      </div>
                    </div>
                    <div className="ml-11 space-y-1">
                      <div className="flex items-center text-sm">
                        <Mail className="w-3 h-3 text-gray-400 mr-2" />
                        <span>{parent.email}</span>
                      </div>
                      {parent.phone && (
                        <div className="flex items-center text-sm">
                          <Phone className="w-3 h-3 text-gray-400 mr-2" />
                          <span>{parent.phone}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {(user?.role === 'admin' || user?.role === 'coach') && (
              <div className="mt-4">
                <button className="btn btn-secondary w-full">
                  Elternteil hinzufügen
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
