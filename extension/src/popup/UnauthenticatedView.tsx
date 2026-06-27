import { useState } from 'react'
import { setToken } from '../auth/tokenStorage'

interface Props {
  onAuth: () => void
}

export function UnauthenticatedView({ onAuth }: Props) {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000/api/v1')
  const [token, setTokenValue] = useState('')
  const [workspaceId, setWorkspaceId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!token.trim() || !apiUrl.trim() || !workspaceId.trim()) {
      setError('Please fill in all fields')
      return
    }

    setSaving(true)
    setError(null)

    try {
      await setToken(token.trim(), apiUrl.trim(), workspaceId.trim())
      onAuth()
    } catch (err) {
      setError('Failed to save credentials')
      setSaving(false)
    }
  }

  return (
    <div className="p-4">
      <h1 className="text-lg font-bold text-gray-900 mb-4">NetworkPilot CRM</h1>
      <p className="text-sm text-gray-600 mb-4">
        Enter your API credentials to connect.
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm mb-4">
          {error}
        </div>
      )}

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">API URL</label>
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="http://localhost:8000/api/v1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
          <input
            type="password"
            value={token}
            onChange={(e) => setTokenValue(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="Supabase access token"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Workspace ID</label>
          <input
            type="text"
            value={workspaceId}
            onChange={(e) => setWorkspaceId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="UUID of workspace"
          />
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {saving ? 'Connecting...' : 'Connect'}
        </button>
      </div>
    </div>
  )
}
