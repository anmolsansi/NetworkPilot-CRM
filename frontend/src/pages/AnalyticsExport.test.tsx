import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { analyticsApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { AnalyticsPage } from './AnalyticsPage'

vi.mock('../api/httpClient', () => ({ analyticsApi: {
  getFunnel: vi.fn(), getPerformance: vi.fn(), getGoals: vi.fn(), exportCsv: vi.fn(), exportPdf: vi.fn(),
} }))
vi.mock('../api/csvDownload', () => ({ downloadCsvBlob: vi.fn() }))

describe('analytics report downloads', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ currentWorkspace: { id: 'workspace-1', name: 'Workspace' } as any })
    vi.mocked(analyticsApi.getFunnel).mockResolvedValue(null)
    vi.mocked(analyticsApi.getPerformance).mockResolvedValue([])
    vi.mocked(analyticsApi.getGoals).mockResolvedValue(null)
    vi.mocked(analyticsApi.exportCsv).mockResolvedValue(new Blob(['csv']))
    vi.mocked(analyticsApi.exportPdf).mockResolvedValue(new Blob(['pdf']))
  })

  it('passes the selected period to CSV and PDF exports', async () => {
    render(<AnalyticsPage />)
    await screen.findByText('Analytics')
    fireEvent.change(screen.getByLabelText('Report from'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('Report to'), { target: { value: '2026-01-31' } })
    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))
    await waitFor(() => expect(analyticsApi.exportCsv).toHaveBeenCalledWith('workspace-1', { date_from: '2026-01-01', date_to: '2026-01-31' }))
    fireEvent.click(screen.getByRole('button', { name: 'Export PDF' }))
    await waitFor(() => expect(analyticsApi.exportPdf).toHaveBeenCalledWith('workspace-1', { date_from: '2026-01-01', date_to: '2026-01-31' }))
  })
})
