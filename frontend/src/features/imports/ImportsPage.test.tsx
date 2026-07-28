import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { importsApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { ImportsPage } from './ImportsPage'

vi.mock('../../api/httpClient', () => ({
  importsApi: {
    list: vi.fn(),
    commit: vi.fn(),
    retry: vi.fn(),
    downloadErrors: vi.fn(),
  },
}))

describe('ImportsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(importsApi.list).mockResolvedValue([])
    vi.mocked(importsApi.commit).mockResolvedValue({ status: 'pending' })
    useWorkspaceStore.setState({
      currentWorkspace: {
        id: 'workspace-1',
        name: 'Workspace',
        owner_id: 'user-1',
        default_follow_up_delay_days: 3,
        default_acceptance_check_delay_days: 7,
        daily_reminder_time: '09:00',
        timezone: 'UTC',
        quiet_hours_start: null,
        quiet_hours_end: null,
        email_reminders_enabled: true,
        daily_digest_enabled: true,
        overdue_alerts_enabled: true,
      },
    })
  })

  it('updates matching profiles by default when uploading a CSV', async () => {
    render(
      <MemoryRouter>
        <ImportsPage />
      </MemoryRouter>,
    )
    await screen.findByText('No import history.')
    expect(screen.getByLabelText('Existing profiles')).toHaveValue('update')

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['name,linkedin_url\nAda,https://linkedin.com/in/ada\n'], 'people.csv', {
      type: 'text/csv',
    })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(importsApi.commit).toHaveBeenCalledWith(
      'workspace-1',
      file,
      'update',
    ))
  })
})
