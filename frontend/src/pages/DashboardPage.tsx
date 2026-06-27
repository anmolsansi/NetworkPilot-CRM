import { useEffect, useState } from 'react'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { dashboardApi } from '../api/httpClient'
import { DuePersonCard } from '../components/people/DuePersonCard'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'

interface DashboardSummary {
  due_today: number
  overdue: number
  waiting_for_reply: number
  active_total: number
}

export function DashboardPage() {
  const { currentWorkspace } = useWorkspaceStore()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [duePeople, setDuePeople] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    if (!currentWorkspace) return

    setLoading(true)
    setError(null)
    try {
      const [summaryData, dueData] = await Promise.all([
        dashboardApi.getSummary(currentWorkspace.id),
        dashboardApi.getDue(currentWorkspace.id, { include_overdue: 'true' }),
      ])
      setSummary(summaryData)
      setDuePeople(dueData)
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [currentWorkspace])

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
