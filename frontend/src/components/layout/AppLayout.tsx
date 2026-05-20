import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { MobileNav } from './MobileNav';
import { DevRoleSwitcher } from '@/components/dev/DevRoleSwitcher';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col md:flex-row">
      {/* Mobile header */}
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      {/* Sidebar - desktop always visible, mobile toggle */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 pt-14 md:pt-0">
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-7xl mx-auto">
            {/* Per-page boundary: a crash in one page keeps the shell usable.
                resetKey on pathname clears the error when the user navigates. */}
            <ErrorBoundary name={location.pathname} resetKey={location.pathname} inline>
              <Outlet />
            </ErrorBoundary>
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
