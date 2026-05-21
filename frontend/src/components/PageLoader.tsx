/**
 * Suspense fallback shown while a lazy route chunk loads (#102).
 *
 * Deliberately minimal — most chunks are <30 KB gzipped and load in
 * <200 ms on a warm connection, so this rarely flashes. The pulse uses
 * the existing canvas/surface design tokens so it visually anchors
 * inside the AppLayout main area without flashing white.
 */
export function PageLoader() {
  return (
    <div
      role="status"
      aria-label="Lädt …"
      className="animate-pulse space-y-4"
    >
      {/* Header band — matches the typical PageHeader's vertical rhythm. */}
      <div className="h-8 bg-tvf-surface/60 rounded w-1/3" />
      {/* Three content rows — generic enough to plausibly map to any page. */}
      <div className="h-24 bg-tvf-surface/60 rounded" />
      <div className="h-24 bg-tvf-surface/60 rounded" />
      <div className="h-24 bg-tvf-surface/60 rounded" />
    </div>
  );
}
