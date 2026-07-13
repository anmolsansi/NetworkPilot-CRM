import { useCallback, useEffect, useState } from 'react'
import { notificationsApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'

export function NotificationsPage() {
  const { currentWorkspace } = useWorkspaceStore()
  const [notifications, setNotifications] = useState<any[]>([])

  const load = useCallback(async () => {
    if (currentWorkspace) setNotifications(await notificationsApi.list(currentWorkspace.id))
  }, [currentWorkspace])

  useEffect(() => { load() }, [load])

  if (!currentWorkspace) return <EmptyState title="Create a workspace first" description="Notifications belong to a workspace." />

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Notifications</h1>
        {notifications.some(item => !item.is_read) && (
          <Button variant="secondary" onClick={async () => { await notificationsApi.markAllRead(currentWorkspace.id); await load() }}>Mark all read</Button>
        )}
      </div>
      <div className="mt-6 space-y-3">
        {notifications.length === 0 ? <EmptyState title="You’re all caught up" description="Follow-up and overdue alerts will appear here." /> : notifications.map(item => (
          <button
            key={item.id}
            className={`block w-full rounded-lg border p-4 text-left ${item.is_read ? 'bg-white' : 'border-blue-200 bg-blue-50'}`}
            onClick={async () => { if (!item.is_read) { await notificationsApi.markRead(item.id, currentWorkspace.id); await load() } }}
          >
            <div className="font-medium text-gray-900">{item.title}</div>
            <div className="mt-1 text-sm text-gray-600">{item.body}</div>
            <time className="mt-2 block text-xs text-gray-400">{new Date(item.created_at).toLocaleString()}</time>
          </button>
        ))}
      </div>
    </div>
  )
}
