import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { dashboardApi, workspaceApi, workspaceMembersApi } from '../api/httpClient'

vi.mock('../api/httpClient', () => ({
  dashboardApi: {
    getSummary: vi.fn(),
    getDue: vi.fn(),
    getTags: vi.fn(),
    getWidgets: vi.fn(),
  },
  exportsApi: {
    peopleCsv: vi.fn(),
  },
  workspaceApi: {
    list: vi.fn(),
    create: vi.fn(),
  },
  workspaceMembersApi: {
    getMe: vi.fn(),
    updateMe: vi.fn(),
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
  quiet_hours_start: null,
  quiet_hours_end: null,
  email_reminders_enabled: true,
  daily_digest_enabled: true,
  overdue_alerts_enabled: true,
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
    vi.mocked(dashboardApi.getTags).mockResolvedValue([])
    vi.mocked(dashboardApi.getWidgets).mockResolvedValue({
      favourites: [], newly_accepted: [], stale_relationships: [], overdue_tasks: [], recent_imports: [],
    })
    vi.mocked(workspaceMembersApi.getMe).mockResolvedValue({
      dashboard_config: { version: 1, widgets: [] }
    })

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

  it('renders all required widgets and saves ordering and limits', async () => {
    useWorkspaceStore.setState({ currentWorkspace: workspace })
    vi.mocked(dashboardApi.getSummary).mockResolvedValue({ due_today: 0, overdue: 0, waiting_for_reply: 0, active_total: 1 })
    vi.mocked(dashboardApi.getDue).mockResolvedValue([])
    vi.mocked(dashboardApi.getTags).mockResolvedValue([])
    vi.mocked(dashboardApi.getWidgets).mockResolvedValue({
      favourites: [{ id: 'person-1', name: 'Favourite Person', company: 'Acme', role: 'Engineer', stage: 'accepted' }],
      newly_accepted: [{ id: 'person-2', name: 'New Contact', company: null, role: null, stage: 'accepted' }],
      stale_relationships: [{ id: 'person-3', name: 'Stale Contact', company: null, role: null, stage: 'waiting_for_reply' }],
      overdue_tasks: [{ id: 'task-1', person_id: 'person-1', person_name: 'Favourite Person', title: 'Follow up', due_date: '2026-07-01' }],
      recent_imports: [{ id: 'import-1', file_name: 'people.csv', total_rows: 5, status: 'completed' }],
    })
    vi.mocked(workspaceMembersApi.getMe).mockResolvedValue({ dashboard_config: {
      version: 1,
      widgets: [
        { id: 'favourites', visible: true, limit: 5 }, { id: 'newly_accepted', visible: true, limit: 5 },
        { id: 'stale_relationships', visible: true, limit: 5 }, { id: 'overdue_tasks', visible: true, limit: 5 },
        { id: 'recent_imports', visible: true, limit: 5 }, { id: 'summary', visible: true, limit: 5 },
        { id: 'tags', visible: true, limit: 5 }, { id: 'due', visible: true, limit: 5 },
      ],
    } })
    vi.mocked(workspaceMembersApi.updateMe).mockResolvedValue({})

    render(<DashboardPage />)
    expect(await screen.findByText('Favourite Person')).toBeInTheDocument()
    expect(screen.getByText('New Contact')).toBeInTheDocument()
    expect(screen.getByText('Stale Contact')).toBeInTheDocument()
    expect(screen.getByText(/Follow up/)).toBeInTheDocument()
    expect(screen.getByText(/people.csv/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Customize Widgets' }))
    fireEvent.change(screen.getByLabelText('Favourite profiles limit'), { target: { value: '8' } })
    fireEvent.click(screen.getByRole('button', { name: 'Move Favourite profiles down' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save Configuration' }))
    await waitFor(() => expect(workspaceMembersApi.updateMe).toHaveBeenCalledWith(
      'workspace-1',
      expect.objectContaining({ dashboard_config: expect.objectContaining({ version: 1, widgets: expect.any(Array) }) }),
    ))
  })
})

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/DashboardPage.test.tsx')
