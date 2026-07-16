import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { peopleApi, tasksApi, workspaceMembersApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { TasksPage } from './TasksPage'

vi.mock('../api/httpClient', () => ({
  peopleApi: { list: vi.fn() },
  workspaceMembersApi: { getMe: vi.fn() },
  tasksApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  },
}))

describe('TasksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useWorkspaceStore.setState({
      currentWorkspace: {
        id: 'workspace-1',
        name: 'Workspace',
        owner_id: 'owner-1',
        default_follow_up_delay_days: 3,
        default_acceptance_check_delay_days: 1,
        daily_reminder_time: '09:00',
        timezone: 'UTC',
        quiet_hours_start: null,
        quiet_hours_end: null,
        email_reminders_enabled: true,
        daily_digest_enabled: true,
        overdue_alerts_enabled: true,
      },
    })
    vi.mocked(workspaceMembersApi.getMe).mockResolvedValue({ user_id: 'user-1' })
    vi.mocked(peopleApi.list).mockResolvedValue({
      items: [{ id: 'person-1', name: 'Ada Lovelace' }],
    })
    vi.mocked(tasksApi.list).mockResolvedValue({
      items: [{
        id: 'task-1',
        person_id: 'person-1',
        person_name: 'Ada Lovelace',
        title: 'Send proposal',
        description: null,
        due_date: '2026-07-15',
        status: 'open',
        assigned_to: 'user-1',
        assignee_email: 'ada@example.com',
      }],
    })
  })

  it('loads My Tasks and completes a task', async () => {
    render(<MemoryRouter><TasksPage /></MemoryRouter>)

    await screen.findByText('Send proposal')
    expect(tasksApi.list).toHaveBeenCalledWith('workspace-1', {
      assigned_to: 'user-1',
      status: 'open',
    })

    fireEvent.click(screen.getByRole('checkbox'))
    await waitFor(() => expect(tasksApi.update).toHaveBeenCalledWith(
      'workspace-1',
      'task-1',
      { status: 'completed' },
    ))
  })
})
