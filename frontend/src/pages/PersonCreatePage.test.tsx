import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { peopleApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { PersonCreatePage } from './PersonCreatePage'

const navigateMock = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock('../api/httpClient', () => ({
  peopleApi: {
    create: vi.fn(),
  },
  tagsApi: {
    list: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
  },
}))

const workspace = {
  id: 'workspace-1',
  name: 'QA Workspace',
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

describe('PersonCreatePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useWorkspaceStore.setState({
      workspaces: [],
      currentWorkspace: null,
      loading: false,
      error: null,
    })
  })

  it('shows a no-workspace state before a workspace exists', () => {
    render(
      <MemoryRouter>
        <PersonCreatePage />
      </MemoryRouter>
    )

    expect(screen.getByRole('heading', { name: 'Add Person' })).toBeInTheDocument()
    expect(screen.getByText('Create a workspace first')).toBeInTheDocument()
    expect(peopleApi.create).not.toHaveBeenCalled()
  })

  it('creates a person in the current workspace', async () => {
    useWorkspaceStore.setState({
      workspaces: [workspace],
      currentWorkspace: workspace,
      loading: false,
      error: null,
    })
    vi.mocked(peopleApi.create).mockResolvedValue({ id: 'person-1' })

    render(
      <MemoryRouter>
        <PersonCreatePage />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'Ada Lovelace' },
    })
    fireEvent.change(screen.getByLabelText('LinkedIn URL'), {
      target: { value: 'https://www.linkedin.com/in/ada-lovelace/' },
    })
    fireEvent.change(screen.getByLabelText('Role'), {
      target: { value: 'Founder' },
    })
    fireEvent.change(screen.getByLabelText('Company'), {
      target: { value: 'Analytical Engines Inc' },
    })
    fireEvent.change(screen.getByLabelText('Priority'), {
      target: { value: 'A' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add Person' }))

    await waitFor(() => {
      expect(peopleApi.create).toHaveBeenCalledWith(
        {
          name: 'Ada Lovelace',
          linkedin_url: 'https://www.linkedin.com/in/ada-lovelace/',
          role: 'Founder',
          company: 'Analytical Engines Inc',
          location: undefined,
          priority: 'A',
          connection_note: undefined,
          notes: undefined,
          tag_ids: [],
        },
        'workspace-1'
      )
    })
    expect(navigateMock).toHaveBeenCalledWith('/people/person-1')
  })
})

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/PersonCreatePage.test.tsx')
