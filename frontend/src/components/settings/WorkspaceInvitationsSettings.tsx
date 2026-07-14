import { useEffect, useState } from 'react'
import { workspaceInvitesApi } from '../../api/httpClient'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { Select } from '../common/Select'
import { ErrorAlert } from '../common/ErrorAlert'
import { Skeleton } from '../common/Skeleton'
import { logError } from '../../utils/logger'

interface WorkspaceInvitationsSettingsProps {
  workspaceId: string
}

interface Invite {
  id: string
  email: string
  role: string
  status: string
  expires_at: string
}

export function WorkspaceInvitationsSettings({ workspaceId }: WorkspaceInvitationsSettingsProps) {
  const [invites, setInvites] = useState<Invite[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('member')
  const [sending, setSending] = useState(false)

  const fetchInvites = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await workspaceInvitesApi.list(workspaceId)
      setInvites(data)
    } catch (err: any) {
      logError('WorkspaceInvitationsSettings', 'Failed to fetch invites', { workspaceId, error: err })
      setError(err.message || 'Failed to fetch invitations.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInvites()
  }, [workspaceId])

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setSending(true)
    setError(null)
    try {
      await workspaceInvitesApi.create(workspaceId, { email: email.trim(), role })
      setEmail('')
      await fetchInvites()
    } catch (err: any) {
      logError('WorkspaceInvitationsSettings', 'Failed to send invite', { workspaceId, error: err })
      setError(err.message || 'Failed to send invitation.')
    } finally {
      setSending(false)
    }
  }

  const handleDelete = async (inviteId: string) => {
    if (!confirm('Are you sure you want to revoke this invitation?')) return
    
    setError(null)
    try {
      await workspaceInvitesApi.delete(workspaceId, inviteId)
      await fetchInvites()
    } catch (err: any) {
      logError('WorkspaceInvitationsSettings', 'Failed to delete invite', { workspaceId, inviteId, error: err })
      setError(err.message || 'Failed to delete invitation.')
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Workspace Invitations</h2>
      <p className="text-sm text-gray-600 mb-4">
        Invite team members to collaborate in this workspace.
      </p>

      {error && <div className="mb-4"><ErrorAlert message={error} /></div>}

      <form onSubmit={handleInvite} className="flex gap-3 mb-6 items-end">
        <div className="flex-1">
          <Input 
            label="Email Address" 
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            placeholder="colleague@company.com" 
            required 
          />
        </div>
        <div className="w-32">
          <Select 
            label="Role" 
            value={role} 
            onChange={(e) => setRole(e.target.value)}
            options={[
              { value: 'member', label: 'Member' },
              { value: 'admin', label: 'Admin' }
            ]}
          />
        </div>
        <Button type="submit" disabled={sending || !email.trim()}>
          {sending ? 'Sending...' : 'Send Invite'}
        </Button>
      </form>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full rounded" />
          <Skeleton className="h-10 w-full rounded" />
        </div>
      ) : invites.length > 0 ? (
        <div className="border rounded-md divide-y">
          {invites.map((invite) => (
            <div key={invite.id} className="flex items-center justify-between p-3 text-sm">
              <div>
                <p className="font-medium text-gray-900">{invite.email}</p>
                <p className="text-gray-500">
                  Role: <span className="capitalize">{invite.role}</span> &bull; Status: <span className="capitalize text-yellow-600">{invite.status}</span>
                </p>
              </div>
              <Button variant="secondary" size="sm" onClick={() => handleDelete(invite.id)}>
                Revoke
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500 italic">No pending invitations.</p>
      )}
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/components/settings/WorkspaceInvitationsSettings.tsx')
