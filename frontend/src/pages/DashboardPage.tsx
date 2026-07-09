import { useEffect, useState } from 'react'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { dashboardApi, exportsApi, workspaceApi } from '../api/httpClient'
import { downloadCsvBlob } from '../api/csvDownload'
import { DuePersonCard } from '../components/people/DuePersonCard'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { logError, logInfo, maskId } from '../utils/logger'

interface DashboardSummary {
  due_today: number
  overdue: number
  waiting_for_reply: number
  active_total: number
}

export function DashboardPage() {
  const { currentWorkspace, fetchWorkspaces } = useWorkspaceStore()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [duePeople, setDuePeople] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<string | null>(null)
  const [workspaceName, setWorkspaceName] = useState('My Workspace')
  const [creatingWorkspace, setCreatingWorkspace] = useState(false)

  const fetchData = async () => {
    if (!currentWorkspace) {
      logInfo('DashboardPage', 'Skipping dashboard data load; no workspace selected')
      setLoading(false)
      return
    }

    logInfo('DashboardPage', 'Loading dashboard data', {
      workspaceId: maskId(currentWorkspace.id),
    })
    setLoading(true)
    setError(null)
    try {
      const [summaryData, dueData] = await Promise.all([
        dashboardApi.getSummary(currentWorkspace.id),
        dashboardApi.getDue(currentWorkspace.id, { include_overdue: 'true' }),
      ])
      setSummary(summaryData)
      setDuePeople(dueData)
      logInfo('DashboardPage', 'Dashboard data loaded', {
        workspaceId: maskId(currentWorkspace.id),
        dueCount: dueData.length,
        activeTotal: summaryData.active_total,
        overdue: summaryData.overdue,
      })
    } catch (err: any) {
      logError('DashboardPage', 'Failed to load dashboard data', {
        workspaceId: maskId(currentWorkspace.id),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [currentWorkspace])

  const handleCreateWorkspace = async () => {
    const name = workspaceName.trim()
    if (!name) return

    setCreatingWorkspace(true)
    setError(null)
    try {
      logInfo('DashboardPage', 'Creating first workspace', {
        nameLength: name.length,
      })
      await workspaceApi.create({ name })
      await fetchWorkspaces()
      logInfo('DashboardPage', 'First workspace created and workspace list refreshed')
    } catch (err: any) {
      logError('DashboardPage', 'Failed to create workspace', {
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to create workspace')
    } finally {
      setCreatingWorkspace(false)
    }
  }

  const handleExport = async (name: string, params: Record<string, string>) => {
    if (!currentWorkspace) return

    logInfo('DashboardPage', 'Starting people CSV export', {
      exportName: name,
      workspaceId: maskId(currentWorkspace.id),
    })
    setExporting(name)
    setError(null)
    try {
      const blob = await exportsApi.peopleCsv({
        workspace_id: currentWorkspace.id,
        ...params,
      })
      downloadCsvBlob(blob, `networkpilot-${name}.csv`)
      logInfo('DashboardPage', 'People CSV export completed', {
        exportName: name,
        workspaceId: maskId(currentWorkspace.id),
        byteSize: blob.size,
      })
    } catch (err: any) {
      logError('DashboardPage', 'People CSV export failed', {
        exportName: name,
        workspaceId: maskId(currentWorkspace.id),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to export people')
    } finally {
      setExporting(null)
    }
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <div className="mt-8 space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  if (!currentWorkspace) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div className="mt-6 max-w-xl bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-medium text-gray-900">Create your workspace</h2>
          <p className="mt-2 text-sm text-gray-600">
            Workspaces keep your people, templates, and reminders organized.
          </p>
          {error && <div className="mt-4"><ErrorAlert message={error} /></div>}
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <Input
              aria-label="Workspace name"
              value={workspaceName}
              onChange={(event) => setWorkspaceName(event.target.value)}
              className="sm:w-72"
            />
            <Button onClick={handleCreateWorkspace} disabled={creatingWorkspace || !workspaceName.trim()}>
              {creatingWorkspace ? 'Creating...' : 'Create workspace'}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div className="mt-6">
          <ErrorAlert message={error} onRetry={fetchData} />
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
      <p className="mt-2 text-sm text-gray-600">
        Who needs follow-up today
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleExport('today-follow-ups', { due: 'today' })}
          disabled={!!exporting}
        >
          {exporting === 'today-follow-ups' ? 'Exporting...' : 'Export Today'}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleExport('overdue-follow-ups', { due: 'overdue' })}
          disabled={!!exporting}
        >
          {exporting === 'overdue-follow-ups' ? 'Exporting...' : 'Export Overdue'}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleExport('second-follow-up-due', { next_action_type: 'follow_up_2', due: 'today' })}
          disabled={!!exporting}
        >
          {exporting === 'second-follow-up-due' ? 'Exporting...' : 'Export Second Follow-up'}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleExport('accepted-not-messaged', { stage: 'accepted', next_action_type: 'send_first_message' })}
          disabled={!!exporting}
        >
          {exporting === 'accepted-not-messaged' ? 'Exporting...' : 'Export Accepted'}
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Due Today</dt>
            <dd className="mt-1 text-3xl font-semibold text-primary-600">{summary.due_today}</dd>
          </div>
          <div className="bg-white overflow-hidden shadow rounded-lg p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Overdue</dt>
            <dd className="mt-1 text-3xl font-semibold text-red-600">{summary.overdue}</dd>
          </div>
          <div className="bg-white overflow-hidden shadow rounded-lg p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Waiting for Reply</dt>
            <dd className="mt-1 text-3xl font-semibold text-yellow-600">{summary.waiting_for_reply}</dd>
          </div>
          <div className="bg-white overflow-hidden shadow rounded-lg p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Active Total</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{summary.active_total}</dd>
          </div>
        </div>
      )}

      {/* Due People List */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900">Due Follow-ups</h2>
        {duePeople.length === 0 ? (
          <EmptyState
            title="No due follow-ups"
            description="All caught up! No one needs follow-up right now."
          />
        ) : (
          <div className="mt-4 space-y-4">
            {duePeople.map((person) => (
              <DuePersonCard key={person.id} person={person} onUpdate={fetchData} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
