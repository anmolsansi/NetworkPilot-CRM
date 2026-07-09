import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { dashboardApi, workspaceApi } from '../api/httpClient'

vi.mock('../api/httpClient', () => ({
  dashboardApi: {
    getSummary: vi.fn(),
    getDue: vi.fn(),
  },
  exportsApi: {
    peopleCsv: vi.fn(),
  },
  workspaceApi: {
    list: vi.fn(),
    create: vi.fn(),
  },
}))

const workspace = {
  id: 'workspace-1',
  name: 'Created Workspace',
  owner_id: 'user-1',
  default_follow_up_delay_days: 3,
  default_acceptance_check_delay_days: 1,
  daily_reminder_time: '09:00:00',
  timezone: 'UTC',
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useWorkspaceStore.setState({
      workspaces: [],
      currentWorkspace: null,
      loading: false,
      error: null,
    })
  })

  it('lets new users create their first workspace', async () => {
    vi.mocked(workspaceApi.create).mockResolvedValue(workspace)
    vi.mocked(workspaceApi.list).mockResolvedValue([workspace])
    vi.mocked(dashboardApi.getSummary).mockResolvedValue({
      due_today: 0,
      overdue: 0,
      waiting_for_reply: 0,
      active_total: 0,
    })
    vi.mocked(dashboardApi.getDue).mockResolvedValue([])

    render(<DashboardPage />)

    expect(screen.getByText('Create your workspace')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Workspace name'), {
      target: { value: 'Sales Pipeline' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() => {
      expect(workspaceApi.create).toHaveBeenCalledWith({ name: 'Sales Pipeline' })
    })
    await waitFor(() => {
      expect(useWorkspaceStore.getState().currentWorkspace).toEqual(workspace)
    })
  })
})

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/DashboardPage.test.tsx')
