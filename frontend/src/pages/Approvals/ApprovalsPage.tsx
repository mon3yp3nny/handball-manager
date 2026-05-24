import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { roleLabels } from '@/store/authStore';
import { PendingRegistration } from '@/types';
import toast from 'react-hot-toast';

export const ApprovalsPage = () => {
  const queryClient = useQueryClient();
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [reason, setReason] = useState('');

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ['pending-registrations'],
    queryFn: () => api.getPendingRegistrations(),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['pending-registrations'] });
  };

  const approve = useMutation({
    mutationFn: (id: number) => api.approveRegistration(id),
    onSuccess: () => {
      toast.success('Registrierung freigegeben');
      invalidate();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'Freigabe fehlgeschlagen'),
  });

  const reject = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      api.rejectRegistration(id, reason),
    onSuccess: () => {
      toast.success('Registrierung abgelehnt');
      setRejectingId(null);
      setReason('');
      invalidate();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'Ablehnung fehlgeschlagen'),
  });

  const submitReject = (id: number) => {
    if (!reason.trim()) {
      toast.error('Bitte gib eine Begründung an.');
      return;
    }
    reject.mutate({ id, reason: reason.trim() });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-tvf-ink mb-1">Genehmigungen</h1>
      <p className="text-tvf-ink-2 mb-6">Registrierungen, die auf deine Freigabe warten.</p>

      {isLoading ? (
        <p className="text-tvf-ink-2">Wird geladen…</p>
      ) : pending.length === 0 ? (
        <div className="card p-8 text-center text-tvf-ink-2">
          Keine offenen Registrierungen.
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((r: PendingRegistration) => (
            <div key={r.id} className="card p-4">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <div className="font-medium text-tvf-ink">
                    {r.first_name} {r.last_name}
                  </div>
                  <div className="text-sm text-tvf-ink-2">{r.email}</div>
                  <div className="text-sm text-tvf-ink-2 mt-1">
                    Rolle: {roleLabels[r.role]}
                    {r.requested_team_name ? ` · Team: ${r.requested_team_name}` : ''}
                  </div>
                </div>
                {rejectingId !== r.id && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => approve.mutate(r.id)}
                      disabled={approve.isPending}
                      className="btn-primary"
                    >
                      Freigeben
                    </button>
                    <button
                      onClick={() => {
                        setRejectingId(r.id);
                        setReason('');
                      }}
                      className="btn-secondary"
                    >
                      Ablehnen
                    </button>
                  </div>
                )}
              </div>

              {rejectingId === r.id && (
                <div className="mt-3 border-t pt-3">
                  <label className="label">Begründung der Ablehnung *</label>
                  <textarea
                    className="input"
                    rows={2}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="z. B. nicht dem Verein zugehörig"
                  />
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => submitReject(r.id)}
                      disabled={reject.isPending}
                      className="btn-primary"
                    >
                      Ablehnung bestätigen
                    </button>
                    <button
                      onClick={() => {
                        setRejectingId(null);
                        setReason('');
                      }}
                      className="btn-secondary"
                    >
                      Abbrechen
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
