import { useState } from 'react'
import { extensionApi } from '../api/extensionApi'

interface Props {
  url: string
  suggestedName: string
  onSuccess: () => void
}

const priorityOptions = [
  { value: 'A', label: 'A - High' },
  { value: 'B', label: 'B - Medium' },
  { value: 'C', label: 'C - Low' },
]

const actionOptions = [
  { value: 'invite_sent', label: 'Invite Sent' },
  { value: 'saved_for_later', label: 'Saved for Later' },
  { value: 'message_sent', label: 'Message Sent' },
]

export function NewProfileView({ url, suggestedName, onSuccess }: Props) {
  const [name, setName] = useState(suggestedName)
  const [role, setRole] = useState('')
  const [company, setCompany] = useState('')
  const [priority, setPriority] = useState('B')
  const [initialAction, setInitialAction] = useState('invite_sent')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Name is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await extensionApi.quickCreate({
        linkedin_url: url,
        name: name.trim(),
        role: role.trim() || undefined,
        company: company.trim() || undefined,
        priority,
        initial_action: initialAction,
        notes: notes.trim() || undefined,
      })
      setSuccess(true)
      setTimeout(onSuccess, 1500)
    } catch (err: any) {
      setError(err.message || 'Failed to save profile')
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="p-4 text-center">
        <div className="text-4xl mb-2">✓</div>
        <h2 className="text-lg font-semibold text-gray-900">Saved!</h2>
        <p className="text-sm text-gray-600">Profile has been saved successfully.</p>
      </div>
    )
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Save New Profile</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm mb-4">
          {error}
        </div>
      )}

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <input
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="e.g., Software Engineer"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="e.g., Google"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {priorityOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Initial Action *</label>
          <select
            value={initialAction}
            onChange={(e) => setInitialAction(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {actionOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            rows={2}
          />
        </div>
        <button
          onClick={handleSave}
          disabled={loading}
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  )
}
