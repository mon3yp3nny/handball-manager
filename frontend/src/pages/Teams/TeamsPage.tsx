import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Shield, Users, ChevronRight } from 'lucide-react';
import { api } from '@/services/api';
import { useRole } from '@/store/authStore';
import { Team } from '@/types';
import toast from 'react-hot-toast';

export const TeamsPage = () => {
  const queryClient = useQueryClient();
  const { isCoach } = useRole();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeam, setNewTeam] = useState({ name: '', description: '', age_group: '' });

  const { data: teams, isLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const res = await api.get('/teams?limit=100');
      return res.items || [];
    },
  });

  const createTeam = useMutation({
    mutationFn: async (teamData: { name: string; description: string; age_group: string }) => {
      return await api.post('/teams', teamData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      setShowCreateModal(false);
      setNewTeam({ name: '', description: '', age_group: '' });
      toast.success('Mannschaft erstellt');
    },
    onError: () => {
      toast.error('Fehler beim Erstellen');
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createTeam.mutate(newTeam);
  };

  const ageGroups = ['U8', 'U10', 'U12', 'U14', 'U16', 'U18', 'U20', 'Erwachsene'];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Mannschaften</h1>
        
        {isCoach && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            <Plus className="w-4 h-4 mr-2" />
            Neue Mannschaft
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12">Lädt...</div>
      ) : teams?.length === 0 ? (
        <div className="card p-12 text-center">
          <Shield className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Keine Mannschaften vorhanden</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams?.map((team: Team) => (
            <a
              key={team.id}
              href={`/teams/${team.id}`}
              className="card p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <div className="bg-primary-100 rounded-lg p-3">
                    <Shield className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="ml-4">
                    <h2 className="font-semibold text-gray-900">{team.name}</h2>
                    {team.age_group && (
                      <span className="badge-blue">{team.age_group}</span>
                    )}
                  </div>
                </div>
                
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
              
              <div className="mt-4 flex items-center text-sm text-gray-500">
                <Users className="w-4 h-4 mr-1" />
                {team.player_count || 0} Spieler
              </div>
              
              {team.description && (
                <p className="mt-2 text-sm text-gray-500 line-clamp-2">{team.description}</p>
              )}
            </a>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Neue Mannschaft</h2>
            
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="label">Name</label>
                <input
                  type="text"
                  value={newTeam.name}
                  onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                  className="input"
                  required
                  placeholder="z.B. 1. Mannschaft"
                />
              </div>
              
              <div>
                <label className="label">Altersgruppe</label>
                <select
                  value={newTeam.age_group}
                  onChange={(e) => setNewTeam({ ...newTeam, age_group: e.target.value })}
                  className="input"
                >
                  <option value="">-- Auswählen --</option>
                  {ageGroups.map((group) => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="label">Beschreibung</label>
                <textarea
                  value={newTeam.description}
                  onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                  className="input"
                  rows={3}
                />
              </div>
              
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Abbrechen
                </button>
                <button
                  type="submit"
                  disabled={createTeam.isPending}
                  className="btn-primary"
                >
                  Erstellen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
