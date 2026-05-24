import { useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { MobileNav } from './MobileNav';
import { DevRoleSwitcher } from '@/components/dev/DevRoleSwitcher';
import { RouteBoundary } from '@/components/RouteBoundary';
import { useWebSocket } from '@/hooks/useWebSocket';

// Which cached queries to refetch when the server signals a resource
// changed. Over-invalidating is safe: the refetch goes through the REST
// API, which enforces per-user visibility.
const INVALIDATION_MAP: Record<string, string[][]> = {
  games: [['games'], ['upcoming-games'], ['dashboard-widgets']],
  events: [['events'], ['upcoming-events'], ['child-team-events'], ['dashboard-widgets']],
  news: [['news']],
  attendance: [['attendance'], ['child-attendance'], ['dashboard-widgets']],
  registrations: [['pending-registrations']],
};

export const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const queryClient = useQueryClient();

  // Live updates (#42): the server broadcasts a resource-level
  // "something changed" frame; we invalidate the matching queries so the
  // UI refetches. Stable callback so the WS doesn't reconnect each render.
  const onMessage = useCallback(
    (message: { type: string; resource?: string }) => {
      if (message.type !== 'resource_changed' || !message.resource) return;
      const keys = INVALIDATION_MAP[message.resource];
      if (!keys) return;
      keys.forEach((queryKey) => queryClient.invalidateQueries({ queryKey }));
    },
    [queryClient],
  );

  useWebSocket(onMessage);

  return (
    <div className="tvf-app min-h-screen bg-tvf-canvas flex flex-col md:flex-row">
      {/* Mobile header */}
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      {/* Sidebar - desktop always visible, mobile toggle */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 pt-14 md:pt-0">
        <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-28 md:pb-6">
          <div className="max-w-7xl mx-auto">
            {/* Per-page boundary: a crash in one page keeps the shell
                (Sidebar / Header / MobileNav) usable. resetKey on
                pathname clears the error when the user navigates away.
                See #101 + components/RouteBoundary.tsx. */}
            <RouteBoundary>
              <Outlet />
            </RouteBoundary>
          </div>
        </main>

        {/* Mobile bottom nav */}
        <MobileNav />
      </div>

      {/* Dev Role Switcher - only in development */}
      {import.meta.env.DEV && <DevRoleSwitcher />}
    </div>
  );
};
