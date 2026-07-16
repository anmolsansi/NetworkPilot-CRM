import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

describe('AnalyticsPage follow-up performance', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useWorkspaceStore.setState({
      currentWorkspace: {
        id: 'workspace-1', name: 'Workspace', owner_id: 'user-1',
        default_follow_up_delay_days: 3, default_acceptance_check_delay_days: 7,
        daily_reminder_time: '09:00', timezone: 'UTC', quiet_hours_start: null,
        quiet_hours_end: null, email_reminders_enabled: true, daily_digest_enabled: true,
        overdue_alerts_enabled: true,
      },
    })
    vi.mocked(analyticsApi.getFunnel).mockResolvedValue({ stages: [] })
    vi.mocked(analyticsApi.getPerformance).mockResolvedValue([
      { dimension: 'template', dimension_key: 'template-a', dimension_label: 'Template A', sent_count: 2, reply_count: 1, reply_rate: 50 },
    ])
    vi.mocked(analyticsApi.getGoals).mockResolvedValue(null)
  })

  it('renders the shared fields and requests selected dimensions and dates', async () => {
    render(<AnalyticsPage />)
    expect(await screen.findByText('Template A')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Performance breakdown'), { target: { value: 'company' } })
    fireEvent.change(screen.getByLabelText('Performance from'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('Performance to'), { target: { value: '2026-01-31' } })

    await waitFor(() => expect(analyticsApi.getPerformance).toHaveBeenLastCalledWith(
      'workspace-1',
      { group_by: 'company', date_from: '2026-01-01', date_to: '2026-01-31' },
    ))
  })
})
