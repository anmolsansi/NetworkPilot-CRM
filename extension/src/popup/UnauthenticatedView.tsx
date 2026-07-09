import { useState } from 'react'
import { setWorkspaceSettings, signInWithGoogle } from '../auth/tokenStorage'
import { authSetupApi, Workspace } from '../api/extensionApi'

interface Props {
  onAuth: () => void
}

export function UnauthenticatedView({ onAuth }: Props) {
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1')
  const [accessToken, setAccessToken] = useState('')
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [workspaceId, setWorkspaceId] = useState('')
  const [newWorkspaceName, setNewWorkspaceName] = useState('My Workspace')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleGoogleSignIn = async () => {
    if (!apiUrl.trim()) {
      console.warn('[NetworkPilot Extension Setup]', 'Google sign-in blocked; missing API URL')
      setError('Please enter your API URL')
      return
    }

    setSaving(true)
    setError(null)

    try {
      console.info('[NetworkPilot Extension Setup]', 'Starting Google sign-in from popup')
      const session = await signInWithGoogle(apiUrl)
      const token = session.access_token
      setAccessToken(token)
      const workspaceList = await authSetupApi.listWorkspaces(apiUrl, token)
      setWorkspaces(workspaceList)
      console.info('[NetworkPilot Extension Setup]', 'Workspaces loaded after sign-in', {
        count: workspaceList.length,
      })

      if (workspaceList.length === 1) {
        await setWorkspaceSettings(apiUrl, workspaceList[0].id)
        console.info('[NetworkPilot Extension Setup]', 'Auto-selected only workspace', {
          workspaceId: workspaceList[0].id.slice(-8),
        })
        onAuth()
      } else if (workspaceList.length > 0) {
        setWorkspaceId(workspaceList[0].id)
        setSaving(false)
      } else {
        setSaving(false)
      }
    } catch (err: any) {
      console.error('[NetworkPilot Extension Setup]', 'Google sign-in setup failed', {
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to sign in with Google')
      setSaving(false)
    }
  }

  const handleUseWorkspace = async () => {
    if (!workspaceId) {
      console.warn('[NetworkPilot Extension Setup]', 'Workspace selection blocked; no workspace selected')
      setError('Select a workspace')
      return
    }

    console.info('[NetworkPilot Extension Setup]', 'Using selected workspace', {
      workspaceId: workspaceId.slice(-8),
    })
    await setWorkspaceSettings(apiUrl, workspaceId)
    onAuth()
  }

  const handleCreateWorkspace = async () => {
    const name = newWorkspaceName.trim()
    if (!name || !accessToken) return

    setSaving(true)
    setError(null)
    try {
      console.info('[NetworkPilot Extension Setup]', 'Creating workspace from extension setup', {
        nameLength: name.length,
      })
      const workspace = await authSetupApi.createWorkspace(apiUrl, accessToken, name)
      await setWorkspaceSettings(apiUrl, workspace.id)
      console.info('[NetworkPilot Extension Setup]', 'Workspace created from extension setup', {
        workspaceId: workspace.id.slice(-8),
      })
      onAuth()
    } catch (err: any) {
      console.error('[NetworkPilot Extension Setup]', 'Failed to create workspace from setup', {
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to create workspace')
      setSaving(false)
    }
  }

  return (
    <div className="p-4">
      <h1 className="text-lg font-bold text-gray-900 mb-4">NetworkPilot CRM</h1>
      <p className="text-sm text-gray-600 mb-4">
        Sign in with the same Google account you use in the web app.
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

        {workspaces.length > 1 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Workspace</label>
            <select
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>{workspace.name}</option>
              ))}
            </select>
            <button
              onClick={handleUseWorkspace}
              className="mt-2 w-full bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700"
            >
              Use selected workspace
            </button>
          </div>
        )}

        {accessToken && workspaces.length === 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Create Workspace</label>
            <input
              type="text"
              value={newWorkspaceName}
              onChange={(e) => setNewWorkspaceName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <button
              onClick={handleCreateWorkspace}
              disabled={saving || !newWorkspaceName.trim()}
              className="mt-2 w-full bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create workspace'}
            </button>
          </div>
        )}

        {!accessToken && (
          <button
            onClick={handleGoogleSignIn}
            disabled={saving}
            className="w-full bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? 'Connecting...' : 'Continue with Google'}
          </button>
        )}
      </div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/UnauthenticatedView.tsx')
