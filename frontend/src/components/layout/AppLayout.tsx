import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { ErrorAlert } from '../common/ErrorAlert'
import { Skeleton } from '../common/Skeleton'
import { useWorkspaceStore } from '../../stores/workspaceStore'

export function AppLayout() {
  const { loading, error, fetchWorkspaces } = useWorkspaceStore()

  useEffect(() => {
    fetchWorkspaces().catch(() => {
      // The store owns the visible error state.
    })
  }, [fetchWorkspaces])

  return (
    <div className="min-h-screen bg-gray-100">
      <Sidebar />
      <div className="lg:pl-64 flex flex-col flex-1">
        <Topbar />
        <main className="flex-1 py-6 px-4 sm:px-6 lg:px-8">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-64 rounded-lg" />
            </div>
          ) : error ? (
            <ErrorAlert message={error} onRetry={fetchWorkspaces} />
          ) : (
            <Outlet />
          )}
        </main>
      </div>
    </div>
  )
}
