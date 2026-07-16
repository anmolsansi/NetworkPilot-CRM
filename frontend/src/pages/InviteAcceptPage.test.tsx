import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { workspaceInvitesApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { InviteAcceptPage } from './InviteAcceptPage'

vi.mock('../api/httpClient', () => ({ workspaceInvitesApi: { accept: vi.fn() } }))

describe('InviteAcceptPage', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ fetchWorkspaces: vi.fn().mockResolvedValue(undefined) as any })
  })

  it('accepts the token and refreshes workspaces', async () => {
    vi.mocked(workspaceInvitesApi.accept).mockResolvedValue({ workspace_id: 'workspace-1' })
    render(<MemoryRouter initialEntries={['/invites/accept?token=secret']}><InviteAcceptPage /></MemoryRouter>)
    await waitFor(() => expect(workspaceInvitesApi.accept).toHaveBeenCalledWith('secret'))
    expect(await screen.findByText(/Invitation accepted/)).toBeInTheDocument()
    expect(useWorkspaceStore.getState().fetchWorkspaces).toHaveBeenCalled()
  })
})
