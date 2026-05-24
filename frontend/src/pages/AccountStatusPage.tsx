import { useAuth } from '@/hooks/useAuth';
import { ApprovalStatus } from '@/types';

interface Props {
  status: ApprovalStatus;
  reason?: string;
}

// Shown to a logged-in user whose registration isn't approved yet. The
// backend already 403s their data calls; this replaces the app shell so
// they get a clear explanation instead of a broken-looking blank page.
export const AccountStatusPage = ({ status, reason }: Props) => {
  const { logout } = useAuth();
  const rejected = status === ApprovalStatus.REJECTED;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border p-8 text-center">
        <div
          className={`inline-flex items-center justify-center w-14 h-14 rounded-full mb-4 ${
            rejected ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600'
          }`}
        >
          {rejected ? (
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>

        <h1 className="text-xl font-bold text-gray-900">
          {rejected ? 'Registrierung abgelehnt' : 'Konto wartet auf Freigabe'}
        </h1>

        {rejected ? (
          <>
            <p className="text-gray-600 mt-2">
              Deine Registrierung wurde leider abgelehnt.
            </p>
            {reason && (
              <p className="mt-3 text-sm text-gray-700 bg-gray-50 border rounded-lg p-3">
                <span className="font-medium">Begründung:</span> {reason}
              </p>
            )}
            <p className="text-sm text-gray-500 mt-3">
              Bei Fragen wende dich bitte an deinen Verein.
            </p>
          </>
        ) : (
          <p className="text-gray-600 mt-2">
            Deine Registrierung wurde übermittelt und muss noch von einem Trainer
            oder Administrator freigegeben werden. Du erhältst eine E-Mail, sobald
            dein Konto freigeschaltet ist.
          </p>
        )}

        <button onClick={logout} className="btn-secondary w-full mt-6">
          Abmelden
        </button>
      </div>
    </div>
  );
};
