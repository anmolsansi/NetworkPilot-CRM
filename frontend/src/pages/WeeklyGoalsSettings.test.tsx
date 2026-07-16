import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { workspaceApi, workspaceMembersApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { SettingsPage } from './SettingsPage'

vi.mock('../api/httpClient', () => ({
  workspaceApi: { update: vi.fn() },
  workspaceMembersApi: { getMe: vi.fn(), updateMe: vi.fn() },
  calendarApi: { getReminderLink: vi.fn() },
  pipelineStagesApi: { list: vi.fn().mockResolvedValue([]) },
  tagsApi: { list: vi.fn().mockResolvedValue([]), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  customFieldsApi: { list: vi.fn().mockResolvedValue([]) },
  workspaceInvitesApi: { list: vi.fn().mockResolvedValue([]) },
}))

describe('weekly goal settings', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ currentWorkspace: {
      id: 'workspace-1', name: 'Workspace', owner_id: 'user-1', default_follow_up_delay_days: 3,
      default_acceptance_check_delay_days: 1, daily_reminder_time: '09:00:00', timezone: 'UTC',
      quiet_hours_start: null, quiet_hours_end: null, email_reminders_enabled: true,
      daily_digest_enabled: true, overdue_alerts_enabled: true,
    }, fetchWorkspaces: vi.fn() as any })
    vi.mocked(workspaceMembersApi.getMe).mockResolvedValue({ weekly_goals: { profiles_added: 10, invitations_sent: 20, follow_ups_sent: 30, replies_received: 5 } })
    vi.mocked(workspaceApi.update).mockResolvedValue({})
    vi.mocked(workspaceMembersApi.updateMe).mockResolvedValue({})
  })

  it('loads and saves all four weekly targets', async () => {
    render(<MemoryRouter><SettingsPage /></MemoryRouter>)
    expect(await screen.findByDisplayValue('10')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Replies received'), { target: { value: '8' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Settings' }))
    await waitFor(() => expect(workspaceMembersApi.updateMe).toHaveBeenCalledWith('workspace-1', {
      weekly_goals: { profiles_added: 10, invitations_sent: 20, follow_ups_sent: 30, replies_received: 8 },
    }))
  })
})
