import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { PeopleListPage } from './PeopleListPage'
import { SettingsPage } from './SettingsPage'
import { TemplatesPage } from './TemplatesPage'
import { peopleApi, templatesApi, workspaceApi, calendarApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'

vi.mock('../api/httpClient', () => ({
  peopleApi: {
    list: vi.fn(),
  },
  exportsApi: {
    peopleCsv: vi.fn(),
  },
  templatesApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  workspaceApi: {
    update: vi.fn(),
  },
  workspaceMembersApi: {
    list: vi.fn().mockResolvedValue([
      { user_id: 'user-1', email: 'owner@example.com', display_name: 'Owner' },
    ]),
  },
  calendarApi: {
    getReminderLink: vi.fn(),
  },
  pipelineStagesApi: {
    list: vi.fn().mockResolvedValue([]),
  },
  tagsApi: {
    list: vi.fn().mockResolvedValue([]),
  },
  savedViewsApi: {
    list: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

function renderPage(page: ReactNode) {
  return render(<MemoryRouter>{page}</MemoryRouter>)
}

describe('workspace-required pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useWorkspaceStore.setState({
      workspaces: [],
      currentWorkspace: null,
      loading: false,
      error: null,
    })
  })

  it('shows a no-workspace state on People without loading people', () => {
    renderPage(<PeopleListPage />)

    expect(screen.getByRole('heading', { name: 'People' })).toBeInTheDocument()
    expect(screen.getByText('Create a workspace first')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Go to Dashboard' })).toBeInTheDocument()
    expect(peopleApi.list).not.toHaveBeenCalled()
  })

  it('applies column filters and sorting to People requests', async () => {
    useWorkspaceStore.setState({
      currentWorkspace: {
        id: 'workspace-1', name: 'Workspace', owner_id: 'user-1',
        default_follow_up_delay_days: 3, default_acceptance_check_delay_days: 7,
        daily_reminder_time: '09:00', timezone: 'UTC', quiet_hours_start: null,
        quiet_hours_end: null, email_reminders_enabled: true, daily_digest_enabled: true,
        overdue_alerts_enabled: true,
      },
    })
    vi.mocked(peopleApi.list).mockResolvedValue({
      total: 1, page: 1, limit: 20,
      items: [{
        id: 'person-1', name: 'Ada Lovelace', first_name: 'Ada', last_name: 'Lovelace',
        company: 'Acme', role: 'Engineer', location: 'London', email: 'ada@example.com',
        phone_number: null, premium: true, company_website: null, processed_at: null,
        processed_at_millis: null, invite_accepted_at: null, invite_accepted_at_millis: null,
        is_favorite: true, favorite_notes: 'Strong candidate',
        linkedin_url: 'linkedin.com/in/ada', stage: 'invite_sent', priority: 'B', status: 'active',
        next_action_type: null, next_action_date: null,
      }],
    })

    renderPage(<PeopleListPage />)
    await screen.findByText('Ada')

    fireEvent.change(screen.getByLabelText('Company'), { target: { value: 'Acme' } })
    fireEvent.change(screen.getByLabelText('Premium'), { target: { value: 'true' } })
    fireEvent.change(screen.getByLabelText('Favourite'), { target: { value: 'true' } })
    fireEvent.change(screen.getByLabelText('Favourite notes contain'), { target: { value: 'candidate' } })
    fireEvent.change(screen.getByLabelText('Contact owner'), { target: { value: 'user-1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply Filters' }))
    await waitFor(() => expect(peopleApi.list).toHaveBeenLastCalledWith(expect.objectContaining({
      company: 'Acme',
      premium: 'true',
      favorite: 'true',
      favorite_notes: 'candidate',
      owner_id: 'user-1',
    })))

    fireEvent.click(screen.getByRole('button', { name: 'Sort by Company' }))
    await waitFor(() => expect(peopleApi.list).toHaveBeenLastCalledWith(expect.objectContaining({
      sort_by: 'company',
      sort_order: 'desc',
    })))
  })

  it('shows a no-workspace state on Templates without loading templates', () => {
    renderPage(<TemplatesPage />)

    expect(screen.getByRole('heading', { name: 'Templates' })).toBeInTheDocument()
    expect(screen.getByText('Create a workspace first')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Go to Dashboard' })).toBeInTheDocument()
    expect(templatesApi.list).not.toHaveBeenCalled()
  })

  it('shows a no-workspace state on Settings without workspace calls', () => {
    renderPage(<SettingsPage />)

    expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument()
    expect(screen.getByText('Create a workspace first')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Go to Dashboard' })).toBeInTheDocument()
    expect(workspaceApi.update).not.toHaveBeenCalled()
    expect(calendarApi.getReminderLink).not.toHaveBeenCalled()
  })
})

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/WorkspaceRequiredPages.test.tsx')
