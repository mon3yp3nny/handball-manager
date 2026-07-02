/**
 * ApprovalsPage — the approver queue (registration approval workflow, #148).
 * API is mocked; no network / no prod data is touched.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// vi.hoisted: the vi.mock factory is hoisted above normal consts, so the
// mock object must be created in a hoisted block to exist when it runs.
const api = vi.hoisted(() => ({
  getPendingRegistrations: vi.fn(),
  approveRegistration: vi.fn(),
  rejectRegistration: vi.fn(),
}));
vi.mock('@/services/api', () => ({ api }));
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

import { ApprovalsPage } from '../ApprovalsPage';

const PENDING = [{
  id: 7, email: 'pat@example.com', first_name: 'Pat', last_name: 'Pending',
  role: 'player', roles: ['player'], requested_team_id: 3,
  requested_team_name: 'A-Jugend', created_at: '2026-01-01T00:00:00Z',
}];

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ApprovalsPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => vi.clearAllMocks());

describe('ApprovalsPage', () => {
  it('lists pending registrations with role + team', async () => {
    api.getPendingRegistrations.mockResolvedValue(PENDING);
    renderPage();
    expect(await screen.findByText('Pat Pending')).toBeInTheDocument();
    expect(screen.getByText(/A-Jugend/)).toBeInTheDocument();
  });

  it('shows the empty state when there are no pending registrations', async () => {
    api.getPendingRegistrations.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText(/Keine offenen Registrierungen/i)).toBeInTheDocument();
  });

  it('approves via the API when "Freigeben" is clicked', async () => {
    api.getPendingRegistrations.mockResolvedValue(PENDING);
    api.approveRegistration.mockResolvedValue(undefined);
    renderPage();
    await screen.findByText('Pat Pending');
    await userEvent.click(screen.getByRole('button', { name: /Freigeben/i }));
    expect(api.approveRegistration).toHaveBeenCalledWith(7);
  });

  it('rejects only with a reason', async () => {
    api.getPendingRegistrations.mockResolvedValue(PENDING);
    api.rejectRegistration.mockResolvedValue(undefined);
    renderPage();
    await screen.findByText('Pat Pending');

    // open the reject form
    await userEvent.click(screen.getByRole('button', { name: /^Ablehnen$/i }));
    // confirming with no reason must NOT call the API
    await userEvent.click(screen.getByRole('button', { name: /Ablehnung bestätigen/i }));
    expect(api.rejectRegistration).not.toHaveBeenCalled();

    // with a reason it does
    await userEvent.type(
      screen.getByPlaceholderText(/nicht dem Verein/i), 'Doppelte Anmeldung');
    await userEvent.click(screen.getByRole('button', { name: /Ablehnung bestätigen/i }));
    expect(api.rejectRegistration).toHaveBeenCalledWith(7, 'Doppelte Anmeldung');
  });
});
