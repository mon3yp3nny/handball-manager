import { useEffect, useState } from 'react';
import { Calendar, Copy, RefreshCw, Check } from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

type TokenResponse = { token: string; url: string };

/**
 * "Kalender abonnieren" panel.
 *
 * The .ics URL is a per-user secret — anyone holding it can read the
 * user's training/game schedule. Showing it once + offering rotation is
 * the same trust model as a personal access token.
 */
export const CalendarSubscription = () => {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<TokenResponse>('/calendar/me/token')
      .then((res) => {
        if (!cancelled) setUrl(res.url);
      })
      .catch(() => {
        if (!cancelled) toast.error('Kalender-Link konnte nicht geladen werden');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCopy = async () => {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success('Link kopiert');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Kopieren fehlgeschlagen');
    }
  };

  const handleRotate = async () => {
    if (!window.confirm('Neuen Link erzeugen? Der alte Link funktioniert dann nicht mehr.')) {
      return;
    }
    setRotating(true);
    try {
      const res = await api.post<TokenResponse>('/calendar/me/token');
      setUrl(res.url);
      toast.success('Neuer Kalender-Link erstellt');
    } catch {
      toast.error('Neuer Link konnte nicht erstellt werden');
    } finally {
      setRotating(false);
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-center mb-2">
        <Calendar className="w-5 h-5 text-primary-600 mr-2" />
        <h2 className="text-lg font-semibold">Kalender abonnieren</h2>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Abonniere diesen Link in deiner Kalender-App (iOS, Google, Outlook).
        Trainings, Spiele und Vereinstermine erscheinen dann automatisch.
      </p>

      {loading ? (
        <div className="text-sm text-gray-400">Wird geladen…</div>
      ) : url ? (
        <>
          <div className="flex items-stretch gap-2">
            <input
              type="text"
              value={url}
              readOnly
              onFocus={(e) => e.currentTarget.select()}
              className="flex-1 min-w-0 px-3 py-2 text-sm font-mono bg-gray-50 border border-gray-200 rounded-lg focus:outline-none"
              aria-label="Kalender-Abonnement-URL"
            />
            <button
              onClick={handleCopy}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1.5"
              aria-label="Link kopieren"
            >
              {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
              <span className="text-sm hidden sm:inline">{copied ? 'Kopiert' : 'Kopieren'}</span>
            </button>
          </div>

          <div className="mt-4 text-xs text-gray-500 space-y-1">
            <p>
              <strong>iOS:</strong> Einstellungen → Kalender → Accounts → Account hinzufügen → Andere → Kalenderabo
            </p>
            <p>
              <strong>Google Calendar:</strong> Andere Kalender → + → Per URL
            </p>
          </div>

          <button
            onClick={handleRotate}
            disabled={rotating}
            className="mt-4 text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${rotating ? 'animate-spin' : ''}`} />
            Link neu erzeugen
          </button>
        </>
      ) : (
        <div className="text-sm text-red-600">Kalender-Link nicht verfügbar.</div>
      )}
    </div>
  );
};
