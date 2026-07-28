import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { peopleApi } from '../../api/httpClient'
import { BulkActionBar } from './BulkActionBar'

vi.mock('../../api/httpClient', () => ({
  peopleApi: {
    bulkAction: vi.fn(),
  },
}))

describe('BulkActionBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(peopleApi.bulkAction).mockResolvedValue({ updated_count: 2 })
  })

  it('advances every selected person to the fixed next workflow action', async () => {
    const onSuccess = vi.fn()
    render(
      <BulkActionBar
        workspaceId="workspace-1"
        selectedIds={['person-1', 'person-2']}
        onClearSelection={vi.fn()}
        onSuccess={onSuccess}
        currentCategory={{
          key: 'workflow:invite_pending',
          name: 'Invite Sent',
          nextActionLabel: 'Accepted',
        }}
        members={[]}
      />,
    )

    expect(screen.queryByRole('button', { name: 'Move category' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next: Accepted' }))
    expect(screen.getByText('Advance 2 people to Accepted?')).toBeInTheDocument()
    expect(screen.queryByRole('textbox', { name: 'Next Action' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    await waitFor(() => expect(peopleApi.bulkAction).toHaveBeenCalledWith({
      workspace_id: 'workspace-1',
      person_ids: ['person-1', 'person-2'],
      action: 'advance_workflow',
      payload: {},
    }))
    expect(onSuccess).toHaveBeenCalled()
  })
})
