import { useCallback, useEffect, useState } from 'react'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { dashboardApi, exportsApi, workspaceApi, workspaceMembersApi } from '../api/httpClient'
import { downloadCsvBlob } from '../api/csvDownload'
import { DuePersonCard } from '../components/people/DuePersonCard'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Modal } from '../components/common/Modal'
import { logError, logInfo, maskId } from '../utils/logger'

interface DashboardSummary {
  due_today: number
  overdue: number
  waiting_for_reply: number
  active_total: number
}

interface DashboardConfig {
  show_summary?: boolean
  show_tags?: boolean
  show_due?: boolean
}

const DEFAULT_CONFIG: DashboardConfig = {
  show_summary: true,
  show_tags: true,
  show_due: true,
}

export function DashboardPage() {
  const { currentWorkspace, fetchWorkspaces } = useWorkspaceStore()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [duePeople, setDuePeople] = useState<any[]>([])
  const [tagSections, setTagSections] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<string | null>(null)
  const [workspaceName, setWorkspaceName] = useState('My Workspace')
  const [creatingWorkspace, setCreatingWorkspace] = useState(false)
  
  // Customization state
  const [config, setConfig] = useState<DashboardConfig>(DEFAULT_CONFIG)
  const [isCustomizing, setIsCustomizing] = useState(false)
  const [savingConfig, setSavingConfig] = useState(false)

  const fetchData = useCallback(async () => {
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
      const [summaryData, dueData, tagData, memberData] = await Promise.all([
        dashboardApi.getSummary(currentWorkspace.id),
        dashboardApi.getDue(currentWorkspace.id, { include_overdue: 'true' }),
        dashboardApi.getTags(currentWorkspace.id),
        workspaceMembersApi.getMe(currentWorkspace.id).catch(() => null),
      ])
      setSummary(summaryData)
      setDuePeople(dueData)
      setTagSections(tagData)
      if (memberData?.dashboard_config) {
        setConfig({ ...DEFAULT_CONFIG, ...memberData.dashboard_config })
      }
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
  }, [currentWorkspace])

  useEffect(() => {
    fetchData()
  }, [fetchData])

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

  const handleSaveConfig = async () => {
    if (!currentWorkspace) return
    setSavingConfig(true)
    try {
      await workspaceMembersApi.updateMe(currentWorkspace.id, { dashboard_config: config })
      setIsCustomizing(false)
    } catch (err: any) {
      setError(err.message || 'Failed to save dashboard config')
    } finally {
      setSavingConfig(false)
    }
  }

  if (loading && !summary) {
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

  if (error && !summary) {
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
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600">Who needs follow-up today</p>
        </div>
        <div className="mt-4 sm:mt-0 flex gap-2">
          <Button variant="secondary" onClick={() => setIsCustomizing(true)}>
            Customize Widgets
          </Button>
        </div>
      </div>

      {error && <div className="mt-4"><ErrorAlert message={error} onRetry={fetchData} /></div>}

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
      {config.show_summary !== false && summary && (
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

      {/* Tags Widget */}
      {config.show_tags !== false && tagSections.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg font-medium text-gray-900">People by tag</h2>
          <div className="mt-3 flex flex-wrap gap-3">
            {tagSections.map(tag => (
              <a
                key={tag.id}
                href={`/people?tag_id=${tag.id}`}
                className="rounded-lg border bg-white px-4 py-3 shadow-sm"
              >
                <span className="rounded px-2 py-1 text-sm text-white" style={{ backgroundColor: tag.color || '#64748b' }}>{tag.name}</span>
                <span className="ml-3 font-semibold text-gray-900">{tag.people_count}</span>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Due People List */}
      {config.show_due !== false && (
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
      )}

      <Modal
        isOpen={isCustomizing}
        onClose={() => setIsCustomizing(false)}
        title="Customize Dashboard"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-500">Choose which widgets to display on your dashboard.</p>
          
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.show_summary !== false}
              onChange={(e) => setConfig({ ...config, show_summary: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-600"
            />
            <span className="text-sm font-medium text-gray-900">Summary Cards</span>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.show_due !== false}
              onChange={(e) => setConfig({ ...config, show_due: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-600"
            />
            <span className="text-sm font-medium text-gray-900">Due Follow-ups List</span>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.show_tags !== false}
              onChange={(e) => setConfig({ ...config, show_tags: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-600"
            />
            <span className="text-sm font-medium text-gray-900">People by Tag Widget</span>
          </label>

          <div className="mt-6 flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setIsCustomizing(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveConfig} disabled={savingConfig}>
              {savingConfig ? 'Saving...' : 'Save Configuration'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/DashboardPage.tsx')
