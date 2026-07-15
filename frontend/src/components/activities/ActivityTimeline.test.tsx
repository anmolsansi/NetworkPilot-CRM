import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { activitiesApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { ActivityTimeline, type Activity } from './ActivityTimeline'

vi.mock('../../api/httpClient', () => ({
  activitiesApi: {
    update: vi.fn(),
    delete: vi.fn(),
    uploadAttachment: vi.fn(),
  },
}))

const activity: Activity = {
  id: 'activity-1',
  action_type: 'reply_received',
  source: 'web_app',
  previous_stage: 'messaged',
  new_stage: 'replied',
  message: null,
  notes: 'Raw notes',
  interaction_summary: 'Discussed the roadmap',
  outcome: 'Review scheduled',
  next_steps: 'Send architecture notes',
  created_at: '2026-07-14T00:00:00Z',
  is_pinned: false,
  attachments: [],
}

describe('ActivityTimeline structured notes', () => {
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
  })

  it('renders and updates summary, outcome, and next steps', async () => {
    render(<ActivityTimeline activities={[activity]} />)

    expect(screen.getByText(/Discussed the roadmap/)).toBeInTheDocument()
    expect(screen.getByText(/Review scheduled/)).toBeInTheDocument()
    expect(screen.getByText(/Send architecture notes/)).toBeInTheDocument()

    fireEvent.click(screen.getByTitle('Edit interaction notes'))
    fireEvent.change(screen.getByLabelText('Outcome'), { target: { value: 'Review complete' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(activitiesApi.update).toHaveBeenCalledWith(
      'activity-1',
      expect.objectContaining({
        interaction_summary: 'Discussed the roadmap',
        outcome: 'Review complete',
        next_steps: 'Send architecture notes',
      }),
      'workspace-1',
    ))
  })
})
