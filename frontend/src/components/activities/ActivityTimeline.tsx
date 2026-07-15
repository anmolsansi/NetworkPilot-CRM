import { useState, useRef } from 'react'
import { Badge } from '../common/Badge'
import { Button } from '../common/Button'
import { Textarea } from '../common/Textarea'
import { Input } from '../common/Input'
import { Select } from '../common/Select'
import { activitiesApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'

export interface Attachment {
  id: string
  file_name: string
  file_size: number
  content_type: string
}

export interface Activity {
  id: string
  action_type: string
  source: string
  previous_stage: string | null
  new_stage: string | null
  message: string | null
  notes: string | null
  interaction_summary: string | null
  outcome: string | null
  next_steps: string | null
  created_at: string
  is_pinned: boolean
  attachments?: Attachment[]
}

const sourceVariant = {
  web_app: 'primary',
  chrome_extension: 'success',
  system: 'default',
} as const

export interface ActivityFilters {
  action_type: string
  source: string
  created_from: string
  created_to: string
}

const emptyActivityFilters: ActivityFilters = {
  action_type: '',
  source: '',
  created_from: '',
  created_to: '',
}

export function ActivityTimeline({
  activities,
  onRefresh,
  filters = emptyActivityFilters,
  onFiltersChange,
}: {
  activities: Activity[]
  onRefresh?: () => void
  filters?: ActivityFilters
  onFiltersChange?: (filters: ActivityFilters) => void
}) {
  const { currentWorkspace } = useWorkspaceStore()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editDetails, setEditDetails] = useState({
    notes: '',
    interaction_summary: '',
    outcome: '',
    next_steps: '',
  })
  const [uploadingId, setUploadingId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleTogglePin = async (activity: Activity) => {
    if (!currentWorkspace) return
    try {
      await activitiesApi.update(activity.id, { is_pinned: !activity.is_pinned }, currentWorkspace.id)
      onRefresh?.()
    } catch (err) {
      console.error('Failed to pin activity', err)
    }
  }

  const handleDelete = async (activity: Activity) => {
    if (!currentWorkspace || !window.confirm('Are you sure you want to delete this activity?')) return
    try {
      await activitiesApi.delete(activity.id, currentWorkspace.id)
      onRefresh?.()
    } catch (err) {
      console.error('Failed to delete activity', err)
    }
  }

  const handleStartEdit = (activity: Activity) => {
    setEditingId(activity.id)
    setEditDetails({
      notes: activity.notes || '',
      interaction_summary: activity.interaction_summary || '',
      outcome: activity.outcome || '',
      next_steps: activity.next_steps || '',
    })
  }

  const handleSaveEdit = async (activity: Activity) => {
    if (!currentWorkspace) return
    try {
      await activitiesApi.update(activity.id, editDetails, currentWorkspace.id)
      setEditingId(null)
      onRefresh?.()
    } catch (err) {
      console.error('Failed to update activity', err)
    }
  }

  const handleFileUpload = async (activityId: string, event: React.ChangeEvent<HTMLInputElement>) => {
    if (!currentWorkspace || !event.target.files || event.target.files.length === 0) return
    const file = event.target.files[0]
    setUploadingId(activityId)
    try {
      await activitiesApi.uploadAttachment(activityId, file, currentWorkspace.id)
      onRefresh?.()
    } catch (err) {
      console.error('Failed to upload file', err)
    } finally {
      setUploadingId(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleAttachmentDownload = async (attachment: Attachment) => {
    if (!currentWorkspace) return
    const { url } = await activitiesApi.getAttachmentDownloadUrl(
      attachment.id,
      currentWorkspace.id,
    )
    const link = document.createElement('a')
    link.href = url
    link.download = attachment.file_name
    link.rel = 'noopener noreferrer'
    link.click()
  }

  const handleAttachmentDelete = async (attachment: Attachment) => {
    if (!currentWorkspace || !window.confirm(`Delete ${attachment.file_name}?`)) return
    await activitiesApi.deleteAttachment(attachment.id, currentWorkspace.id)
    onRefresh?.()
  }

  return (
    <div>
      {onFiltersChange && (
        <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Select
            label="Activity type"
            options={[
              { value: '', label: 'All activity types' },
              { value: 'invite_sent', label: 'Invite sent' },
              { value: 'accepted', label: 'Accepted' },
              { value: 'message_sent', label: 'Message sent' },
              { value: 'follow_up_1_sent', label: 'Follow-up 1 sent' },
              { value: 'follow_up_2_sent', label: 'Follow-up 2 sent' },
              { value: 'reply_received', label: 'Reply received' },
            ]}
            value={filters.action_type}
            onChange={(event) => onFiltersChange({ ...filters, action_type: event.target.value })}
          />
          <Select
            label="Activity source"
            options={[
              { value: '', label: 'All sources' },
              { value: 'web_app', label: 'Web app' },
              { value: 'chrome_extension', label: 'Chrome extension' },
              { value: 'csv_import', label: 'CSV import' },
              { value: 'system', label: 'System' },
            ]}
            value={filters.source}
            onChange={(event) => onFiltersChange({ ...filters, source: event.target.value })}
          />
          <Input
            label="Activity from"
            type="date"
            value={filters.created_from}
            onChange={(event) => onFiltersChange({ ...filters, created_from: event.target.value })}
          />
          <Input
            label="Activity to"
            type="date"
            value={filters.created_to}
            onChange={(event) => onFiltersChange({ ...filters, created_to: event.target.value })}
          />
        </div>
      )}
      {activities.length === 0 ? (
        <p className="py-4 text-center text-sm text-gray-500">No activities match these filters.</p>
      ) : (
      <div className="flow-root">
      <ul className="-mb-8">
        {activities.map((activity, idx) => (
          <li key={activity.id}>
            <div className="relative pb-8">
              {idx !== activities.length - 1 && (
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" />
              )}
              <div className="relative flex space-x-3">
                <div>
                  <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${activity.is_pinned ? 'bg-amber-100' : 'bg-primary-100'}`}>
                    <span className={`${activity.is_pinned ? 'text-amber-600' : 'text-primary-600'} text-sm`}>
                      {activity.is_pinned ? '📌' :
                       activity.action_type === 'message_sent' ? '💬' :
                       activity.action_type === 'accepted' ? '✓' :
                       activity.action_type === 'reply_received' ? '↩' : '•'}
                    </span>
                  </span>
                </div>
                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1">
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 flex items-center gap-2">
                      <span className="font-medium">{activity.action_type.replace(/_/g, ' ')}</span>
                      {activity.new_stage && (
                        <span className="text-gray-500">
                          {' → '}
                          <Badge variant="primary">{activity.new_stage.replace(/_/g, ' ')}</Badge>
                        </span>
                      )}
                    </p>

                    {editingId === activity.id ? (
                      <div className="mt-2 space-y-2">
                        <Textarea
                          label="Notes"
                          value={editDetails.notes}
                          onChange={(e) => setEditDetails({ ...editDetails, notes: e.target.value })}
                          rows={2}
                        />
                        <Textarea
                          label="Interaction summary"
                          value={editDetails.interaction_summary}
                          onChange={(e) => setEditDetails({ ...editDetails, interaction_summary: e.target.value })}
                          rows={2}
                        />
                        <Textarea
                          label="Outcome"
                          value={editDetails.outcome}
                          onChange={(e) => setEditDetails({ ...editDetails, outcome: e.target.value })}
                          rows={2}
                        />
                        <Textarea
                          label="Next steps"
                          value={editDetails.next_steps}
                          onChange={(e) => setEditDetails({ ...editDetails, next_steps: e.target.value })}
                          rows={2}
                        />
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => handleSaveEdit(activity)}>Save</Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-2 space-y-1 text-sm text-gray-600">
                        {activity.notes && <p className="whitespace-pre-wrap">{activity.notes}</p>}
                        {activity.interaction_summary && (
                          <p className="whitespace-pre-wrap"><span className="font-medium text-gray-700">Summary:</span> {activity.interaction_summary}</p>
                        )}
                        {activity.outcome && (
                          <p className="whitespace-pre-wrap"><span className="font-medium text-gray-700">Outcome:</span> {activity.outcome}</p>
                        )}
                        {activity.next_steps && (
                          <p className="whitespace-pre-wrap"><span className="font-medium text-gray-700">Next steps:</span> {activity.next_steps}</p>
                        )}
                      </div>
                    )}

                    {/* Attachments List */}
                    {activity.attachments && activity.attachments.length > 0 && (
                      <div className="mt-2 flex flex-col gap-1">
                        {activity.attachments.map(att => (
                          <div key={att.id} className="text-xs text-gray-500 flex items-center gap-2 bg-gray-50 p-1.5 rounded w-fit border border-gray-100">
                            <button className="text-primary-600 hover:underline" onClick={() => handleAttachmentDownload(att)}>
                              📎 {att.file_name}
                            </button>
                            <span className="text-gray-400">({Math.round(att.file_size / 1024)} KB)</span>
                            <button className="text-red-500" aria-label={`Delete ${att.file_name}`} onClick={() => handleAttachmentDelete(att)}>×</button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="whitespace-nowrap flex flex-col items-end space-y-2">
                    <div className="text-sm text-gray-500 text-right">
                      <time>{new Date(activity.created_at).toLocaleDateString()}</time>
                      <div className="mt-1">
                        <Badge variant={sourceVariant[activity.source as keyof typeof sourceVariant] || 'default'}>
                          {activity.source.replace(/_/g, ' ')}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity" style={{ opacity: 1 }}>
                      {/* Using opacity 1 here for now, but usually it would be on hover */}
                      <button 
                        onClick={() => handleTogglePin(activity)}
                        className={`text-xs ${activity.is_pinned ? 'text-amber-500 hover:text-amber-600' : 'text-gray-400 hover:text-gray-600'}`}
                        title={activity.is_pinned ? "Unpin" : "Pin"}
                      >
                        📌
                      </button>
                      <button 
                        onClick={() => handleStartEdit(activity)}
                        className="text-xs text-blue-500 hover:text-blue-600 px-1"
                        title="Edit interaction notes"
                      >
                        ✏️
                      </button>
                      <label className="text-xs text-green-500 hover:text-green-600 cursor-pointer px-1" title="Attach file">
                        📎
                        <input 
                          type="file" 
                          className="hidden" 
                          ref={fileInputRef}
                          onChange={(e) => handleFileUpload(activity.id, e)}
                          disabled={uploadingId === activity.id}
                        />
                      </label>
                      <button 
                        onClick={() => handleDelete(activity)}
                        className="text-xs text-red-500 hover:text-red-600 px-1"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                    {uploadingId === activity.id && <span className="text-xs text-gray-400">Uploading...</span>}
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
      </div>
      )}
    </div>
  )
}
