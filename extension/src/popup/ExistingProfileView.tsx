import { useState } from 'react'
import { extensionApi, LookupResponse } from '../api/extensionApi'
import { TemplateCopyPanel } from './TemplateCopyPanel'

interface Props {
  lookupResult: LookupResponse
  onSuccess: () => void
}

const actionButtons = [
  { action: 'accepted', label: 'Accepted', color: 'bg-green-600 hover:bg-green-700' },
  { action: 'message_sent', label: 'Message Sent', color: 'bg-primary-600 hover:bg-primary-700' },
  { action: 'follow_up_1_sent', label: 'Follow-up 1', color: 'bg-yellow-500 hover:bg-yellow-600' },
  { action: 'follow_up_2_sent', label: 'Follow-up 2', color: 'bg-yellow-500 hover:bg-yellow-600' },
  { action: 'reply_received', label: 'Reply Received', color: 'bg-purple-600 hover:bg-purple-700' },
]

export function ExistingProfileView({ lookupResult, onSuccess }: Props) {
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [notes, setNotes] = useState('')

  const handleAction = async (actionType: string) => {
    setLoading(actionType)
    setError(null)

    try {
      console.info('[NetworkPilot Extension ExistingProfile]', 'Recording quick action', {
        personId: lookupResult.person_id?.slice(-8) || null,
        actionType,
        hasNotes: Boolean(notes.trim()),
      })
      await extensionApi.quickAction({
        person_id: lookupResult.person_id!,
        action_type: actionType,
        notes: notes.trim() || undefined,
      })
      setSuccess(actionType)
      setNotes('')
      setTimeout(() => {
        setSuccess(null)
        onSuccess()
      }, 1500)
      console.info('[NetworkPilot Extension ExistingProfile]', 'Quick action recorded', {
        personId: lookupResult.person_id?.slice(-8) || null,
        actionType,
      })
    } catch (err: any) {
      console.error('[NetworkPilot Extension ExistingProfile]', 'Quick action failed', {
        personId: lookupResult.person_id?.slice(-8) || null,
        actionType,
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to perform action')
      setLoading(null)
    }
  }

  const stageLabels: Record<string, string> = {
    invite_sent: 'Invite Sent',
    invite_pending: 'Invite Pending',
    accepted: 'Accepted',
    waiting_for_reply: 'Waiting for Reply',
    follow_up_1_sent: 'Follow-up 1 Sent',
    follow_up_2_sent: 'Follow-up 2 Sent',
    replied: 'Replied',
    archived: 'Archived',
  }

  return (
    <div className="p-4">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">{lookupResult.name}</h2>
        <div className="flex items-center space-x-2 mt-1">
          <span className="text-xs bg-primary-100 text-primary-800 px-2 py-0.5 rounded">
            {stageLabels[lookupResult.stage || ''] || lookupResult.stage}
          </span>
          <span className="text-xs bg-gray-100 text-gray-800 px-2 py-0.5 rounded">
            Priority: {lookupResult.priority}
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded text-sm mb-4">
          Action recorded successfully!
        </div>
      )}

      <div className="space-y-4">
        {/* Quick Action Buttons */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Quick Actions</label>
          <div className="grid grid-cols-2 gap-2">
            {actionButtons.map((btn) => (
              <button
                key={btn.action}
                onClick={() => handleAction(btn.action)}
                disabled={loading !== null}
                className={`${btn.color} text-white py-2 px-3 rounded-md text-sm font-medium disabled:opacity-50`}
              >
                {loading === btn.action ? '...' : btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Add Note</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            rows={2}
            placeholder="Optional note to attach to action..."
          />
        </div>

        {/* Info */}
        {lookupResult.next_action_type && (
          <div className="text-xs text-gray-500">
            <span className="font-medium">Next action:</span> {lookupResult.next_action_type.replace(/_/g, ' ')}
            {lookupResult.next_action_date && (
              <span> (due {new Date(lookupResult.next_action_date).toLocaleDateString()})</span>
            )}
          </div>
        )}

        {/* Templates */}
        <TemplateCopyPanel
          person={{
            name: lookupResult.name,
          }}
        />
      </div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/ExistingProfileView.tsx')
