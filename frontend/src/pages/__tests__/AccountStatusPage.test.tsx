/**
 * AccountStatusPage — the screen a logged-in but not-yet-approved user sees
 * instead of the app (registration approval workflow, #148).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApprovalStatus } from '@/types';

const logout = vi.fn();
vi.mock('@/hooks/useAuth', () => ({ useAuth: () => ({ logout }) }));

import { AccountStatusPage } from '../AccountStatusPage';

beforeEach(() => vi.clearAllMocks());

describe('AccountStatusPage', () => {
  it('shows the awaiting-approval message for PENDING (and no rejection text)', () => {
    render(<AccountStatusPage status={ApprovalStatus.PENDING} />);
    expect(screen.getByText(/wartet auf Freigabe/i)).toBeInTheDocument();
    expect(screen.queryByText(/abgelehnt/i)).not.toBeInTheDocument();
  });

  it('shows the rejection message and the reason for REJECTED', () => {
    render(<AccountStatusPage status={ApprovalStatus.REJECTED} reason="Nicht dem Verein zugehörig" />);
    expect(screen.getByRole('heading', { name: /abgelehnt/i })).toBeInTheDocument();
    expect(screen.getByText(/Nicht dem Verein zugehörig/)).toBeInTheDocument();
  });

  it('logs out when the button is clicked', async () => {
    render(<AccountStatusPage status={ApprovalStatus.PENDING} />);
    await userEvent.click(screen.getByRole('button', { name: /Abmelden/i }));
    expect(logout).toHaveBeenCalledOnce();
  });
});
