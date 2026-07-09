import { render, screen } from '@testing-library/react'
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
  calendarApi: {
    getReminderLink: vi.fn(),
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
