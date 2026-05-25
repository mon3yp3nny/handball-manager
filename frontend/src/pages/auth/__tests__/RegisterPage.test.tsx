/**
 * RegisterPage — the single-role sign-up with a team picker for player/parent
 * (registration approval workflow, #148/#150). API is mocked.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// vi.hoisted: the vi.mock factory runs before normal consts, so build the
// mock object in a hoisted block.
const api = vi.hoisted(() => ({ register: vi.fn(), getPublicTeams: vi.fn() }));
vi.mock('@/services/api', () => ({ api }));
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

import { RegisterPage } from '../RegisterPage';

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function fillBasics() {
  await userEvent.type(screen.getByLabelText(/Vorname/i), 'Tom');
  await userEvent.type(screen.getByLabelText(/Nachname/i), 'Test');
  await userEvent.type(screen.getByLabelText(/E-Mail/i), 'tom@example.com');
  await userEvent.type(screen.getByLabelText(/Passwort/i), 'Test1234!');
}

beforeEach(() => {
  vi.clearAllMocks();
  api.getPublicTeams.mockResolvedValue([
    { id: 3, name: 'A-Jugend', age_group: 'U18' },
  ]);
});

describe('RegisterPage', () => {
  it('shows the team picker for the default Player role', async () => {
    renderPage();
    expect(await screen.findByLabelText(/^Team/i)).toBeInTheDocument();
  });

  it('hides the team picker for the Coach role', async () => {
    renderPage();
    await screen.findByLabelText(/^Team/i);
    await userEvent.click(screen.getByRole('radio', { name: /Trainer/i }));
    expect(screen.queryByLabelText(/^Team/i)).not.toBeInTheDocument();
  });

  it('does not register a player until a team is chosen', async () => {
    renderPage();
    await fillBasics();
    await screen.findByLabelText(/^Team/i); // team picker present, none selected
    await userEvent.click(screen.getByRole('button', { name: /Konto erstellen/i }));
    // blocked (required team + JS guard) — no registration goes out
    expect(api.register).not.toHaveBeenCalled();
  });

  it('registers a player with the chosen team', async () => {
    api.register.mockResolvedValue({ approval_status: 'pending' });
    renderPage();
    await fillBasics();
    await userEvent.selectOptions(await screen.findByLabelText(/^Team/i), '3');
    await userEvent.click(screen.getByRole('button', { name: /Konto erstellen/i }));
    await waitFor(() => expect(api.register).toHaveBeenCalled());
    expect(api.register.mock.calls[0][0]).toMatchObject({
      email: 'tom@example.com', role: 'player', requested_team_id: 3,
    });
  });
});
