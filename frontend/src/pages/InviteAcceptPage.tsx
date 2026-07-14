import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { workspaceInvitesApi } from '../api/httpClient'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { Button } from '../components/common/Button'

export function InviteAcceptPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { fetchWorkspaces } = useWorkspaceStore()
  const [status, setStatus] = useState('Accepting invitation...')
  const [accepted, setAccepted] = useState(false)

  useEffect(() => {
    const token = params.get('token')
    if (!token) { setStatus('This invitation link is invalid.'); return }
    workspaceInvitesApi.accept(token).then(async () => {
      await fetchWorkspaces()
      setAccepted(true)
      setStatus('Invitation accepted. You can now open the workspace.')
    }).catch((error) => setStatus(error.message || 'Unable to accept invitation.'))
  }, [fetchWorkspaces, params])

  return <div className="mx-auto mt-20 max-w-lg rounded-lg bg-white p-8 text-center shadow"><h1 className="text-xl font-semibold">Workspace invitation</h1><p className="mt-4 text-gray-600">{status}</p>{accepted && <Button className="mt-6" onClick={() => navigate('/')}>Open workspace</Button>}</div>
}
