import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { analyticsApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { AnalyticsPage } from './AnalyticsPage'

vi.mock('../api/httpClient', () => ({
  analyticsApi: {
    getFunnel: vi.fn(),
    getPerformance: vi.fn(),
    getGoals: vi.fn(),
    exportCsv: vi.fn(),
  },
}))

describe('AnalyticsPage funnel contract', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useWorkspaceStore.setState({
      currentWorkspace: {
        id: 'workspace-1',
        name: 'Workspace',
        owner_id: 'user-1',
        default_follow_up_delay_days: 3,
        default_acceptance_check_delay_days: 7,
        daily_reminder_time: '09:00',
        timezone: 'UTC',
        quiet_hours_start: null,
        quiet_hours_end: null,
        email_reminders_enabled: true,
        daily_digest_enabled: true,
        overdue_alerts_enabled: true,
      },
    })
    vi.mocked(analyticsApi.getFunnel).mockResolvedValue({
      stages: [
        { key: 'saved', label: 'Saved', count: 5, conversion_from_previous: 100, conversion_from_saved: 100 },
        { key: 'invite_sent', label: 'Invite sent', count: 4, conversion_from_previous: 80, conversion_from_saved: 80 },
        { key: 'accepted', label: 'Accepted', count: 3, conversion_from_previous: 75, conversion_from_saved: 60 },
        { key: 'messaged', label: 'Messaged', count: 2, conversion_from_previous: 66.67, conversion_from_saved: 40 },
        { key: 'replied', label: 'Replied', count: 1, conversion_from_previous: 50, conversion_from_saved: 20 },
      ],
    })
    vi.mocked(analyticsApi.getPerformance).mockResolvedValue([])
    vi.mocked(analyticsApi.getGoals).mockResolvedValue(null)
  })

  it('renders every funnel stage and both conversion rates', async () => {
    render(<AnalyticsPage />)

    expect(await screen.findByText('Invite sent')).toBeInTheDocument()
    expect(screen.getByText('Accepted')).toBeInTheDocument()
    expect(screen.getByText('Messaged')).toBeInTheDocument()
    expect(screen.getByText('Replied')).toBeInTheDocument()
    expect(screen.getByText('75% from previous')).toBeInTheDocument()
    expect(screen.getByText('60% from saved')).toBeInTheDocument()
  })
})
