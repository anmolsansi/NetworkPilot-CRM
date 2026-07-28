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

  it('moves every selected person to the chosen category', async () => {
    const onSuccess = vi.fn()
    render(
      <BulkActionBar
        workspaceId="workspace-1"
        selectedIds={['person-1', 'person-2']}
        onClearSelection={vi.fn()}
        onSuccess={onSuccess}
        pipelineStages={[
          { id: 'invites', name: 'Invites', order: 0, allowed_next_stage_ids: [] },
          { id: 'follow-up-1', name: 'Follow-up 1', order: 1, allowed_next_stage_ids: ['follow-up-2'] },
          { id: 'follow-up-2', name: 'Follow-up 2', order: 2, allowed_next_stage_ids: [] },
        ]}
        currentCategory={{
          key: 'stage:follow-up-1',
          name: 'Follow-up 1',
          stageId: 'follow-up-1',
          order: 1,
          allowedNextStageIds: ['follow-up-2'],
        }}
        members={[]}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Move category' }))
    expect(screen.getByRole('option', { name: 'Invites (unavailable)' })).toBeDisabled()
    expect(screen.getByRole('option', { name: 'Follow-up 1 (unavailable)' })).toBeDisabled()
    expect(screen.getByRole('option', { name: 'Follow-up 2' })).not.toBeDisabled()
    fireEvent.change(screen.getByLabelText('Move to category'), {
      target: { value: 'follow-up-2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    await waitFor(() => expect(peopleApi.bulkAction).toHaveBeenCalledWith({
      workspace_id: 'workspace-1',
      person_ids: ['person-1', 'person-2'],
      action: 'set_stage',
      payload: { stage_id: 'follow-up-2' },
    }))
    expect(onSuccess).toHaveBeenCalled()
  })
})
