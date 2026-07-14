import { useCallback, useEffect, useState } from 'react'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { analyticsApi } from '../api/httpClient'
import { downloadCsvBlob } from '../api/csvDownload'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'
import { Button } from '../components/common/Button'
import { logError, maskId } from '../utils/logger'

interface FunnelMetrics {
  total_saved: number
  total_contacted: number
  total_replied: number
  contact_rate: number
  reply_rate: number
}

interface TemplatePerformance {
  template_id: string
  template_name: string
  times_used: number
  replies_received: number
  reply_rate: number
}

interface WeeklyGoalProgress {
  target: number
  current: number
  percentage: number
  period_start: string
  period_end: string
}

export function AnalyticsPage() {
  const { currentWorkspace } = useWorkspaceStore()
  const [funnel, setFunnel] = useState<FunnelMetrics | null>(null)
  const [performance, setPerformance] = useState<TemplatePerformance[]>([])
  const [goals, setGoals] = useState<WeeklyGoalProgress | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [reportFrom, setReportFrom] = useState('')
  const [reportTo, setReportTo] = useState('')

  const fetchData = useCallback(async () => {
    if (!currentWorkspace) return

    setLoading(true)
    setError(null)
    try {
      const [funnelData, perfData, goalsData] = await Promise.all([
        analyticsApi.getFunnel(currentWorkspace.id),
        analyticsApi.getPerformance(currentWorkspace.id),
        analyticsApi.getGoals(currentWorkspace.id),
      ])
      setFunnel(funnelData)
      setPerformance(perfData)
      setGoals(goalsData)
    } catch (err: any) {
      logError('AnalyticsPage', 'Failed to load analytics data', {
        workspaceId: maskId(currentWorkspace.id),
        message: err.message,
      })
      setError(err.message || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [currentWorkspace])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleExport = async (format: 'csv' | 'pdf') => {
    if (!currentWorkspace) return

    setExporting(true)
    setError(null)
    try {
      const params = { ...(reportFrom ? { date_from: reportFrom } : {}), ...(reportTo ? { date_to: reportTo } : {}) }
      const blob = format === 'csv' ? await analyticsApi.exportCsv(currentWorkspace.id, params) : await analyticsApi.exportPdf(currentWorkspace.id, params)
      downloadCsvBlob(blob, `analytics-report-${new Date().toISOString().slice(0, 10)}.${format}`)
    } catch (err: any) {
      setError(err.message || 'Failed to export analytics')
    } finally {
      setExporting(false)
    }
  }

  if (loading && !funnel) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
        <Skeleton className="h-40 rounded-lg" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    )
  }

  if (!currentWorkspace) {
    return (
      <EmptyState
        title="No workspace selected"
        description="Select or create a workspace to view analytics."
      />
    )
  }

  return (
    <div className="space-y-8">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
          <p className="mt-2 text-sm text-gray-700">
            Track your outreach funnel, follow-up performance, and weekly goals.
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <div className="flex flex-wrap gap-2"><input aria-label="Report from" type="date" value={reportFrom} onChange={(e) => setReportFrom(e.target.value)} /><input aria-label="Report to" type="date" value={reportTo} onChange={(e) => setReportTo(e.target.value)} /><Button onClick={() => handleExport('csv')} disabled={exporting}>Export CSV</Button><Button onClick={() => handleExport('pdf')} disabled={exporting}>Export PDF</Button></div>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchData} />}

      {/* Goals Widget */}
      {goals && (
        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Weekly Goal Progress</h2>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-700">Outreach Goal</span>
                <span className="text-gray-500">{goals.current} / {goals.target}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-primary-600 h-2.5 rounded-full" 
                  style={{ width: `${Math.min(goals.percentage, 100)}%` }}
                ></div>
              </div>
            </div>
            <div className="text-2xl font-semibold text-gray-900">
              {Math.round(goals.percentage)}%
            </div>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Period: {new Date(goals.period_start).toLocaleDateString()} - {new Date(goals.period_end).toLocaleDateString()}
          </p>
        </section>
      )}

      {/* Funnel Metrics */}
      {funnel && (
        <section>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Outreach Funnel</h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border-l-4 border-gray-400">
              <dt className="text-sm font-medium text-gray-500 truncate">Total Saved</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900">{funnel.total_saved}</dd>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border-l-4 border-blue-500">
              <dt className="text-sm font-medium text-gray-500 truncate">Contacted</dt>
              <dd className="mt-1 flex items-baseline gap-2">
                <span className="text-3xl font-semibold text-gray-900">{funnel.total_contacted}</span>
                <span className="text-sm text-gray-500">({Math.round(funnel.contact_rate)}%)</span>
              </dd>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border-l-4 border-green-500">
              <dt className="text-sm font-medium text-gray-500 truncate">Replied</dt>
              <dd className="mt-1 flex items-baseline gap-2">
                <span className="text-3xl font-semibold text-gray-900">{funnel.total_replied}</span>
                <span className="text-sm text-gray-500">({Math.round(funnel.reply_rate)}%)</span>
              </dd>
            </div>
          </div>
        </section>
      )}

      {/* Performance Table */}
      <section>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Follow-up Performance</h2>
        {performance.length > 0 ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Times Used</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Replies Received</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reply Rate</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {performance.map((item) => (
                  <tr key={item.template_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.template_name || 'Unknown Template'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.times_used}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.replies_received}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {Math.round(item.reply_rate)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="No performance data"
            description="Start sending follow-ups with templates to see performance metrics."
          />
        )}
      </section>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/AnalyticsPage.tsx')
