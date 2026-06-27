import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { peopleApi, activitiesApi } from '../api/httpClient'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Textarea } from '../components/common/Textarea'
import { Badge } from '../components/common/Badge'
import { Skeleton } from '../components/common/Skeleton'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { ActivityTimeline } from '../components/activities/ActivityTimeline'

interface Person {
  id: string
  name: string
  linkedin_url: string
  company: string | null
  role: string | null
  location: string | null
  priority: string
  stage: string
  status: string
  notes: string | null
  connection_note: string | null
  next_action_type: string | null
  next_action_date: string | null
}

const priorityVariant = {
  A: 'danger',
  B: 'warning',
  C: 'default',
} as const

export function PersonDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentWorkspace } = useWorkspaceStore()
  const [person, setPerson] = useState<Person | null>(null)
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({ name: '', role: '', company: '', notes: '' })
  const [actionNote, setActionNote] = useState('')

  const fetchData = async () => {
    if (!currentWorkspace || !id) return

    setLoading(true)
    setError(null)
    try {
      const [personData, activitiesData] = await Promise.all([
        peopleApi.get(id, currentWorkspace.id),
        activitiesApi.list(id, currentWorkspace.id),
      ])
      setPerson(personData)
      setActivities(activitiesData)
      setEditForm({
        name: personData.name,
        role: personData.role || '',
        company: personData.company || '',
        notes: personData.notes || '',
      })
    } catch (err: any) {
      setError(err.message || 'Failed to load person')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [currentWorkspace, id])

  const handleSaveProfile = async () => {
    if (!currentWorkspace || !id) return

    try {
      await peopleApi.update(id, editForm, currentWorkspace.id)
      setEditing(false)
      fetchData()
    } catch (err: any) {
      setError(err.message || 'Failed to update person')
    }
  }

  const handleQuickAction = async (actionType: string) => {
    if (!currentWorkspace || !id) return

    try {
      await activitiesApi.create(id, {
        action_type: actionType,
        source: 'web_app',
        notes: actionNote || undefined,
      }, currentWorkspace.id)
      setActionNote('')
      fetchData()
    } catch (err: any) {
      setError(err.message || 'Failed to record action')
    }
  }

  const handleArchive = async () => {
    if (!currentWorkspace || !id) return

    try {
      await peopleApi.archive(id, {}, currentWorkspace.id)
      fetchData()
    } catch (err: any) {
      setError(err.message || 'Failed to archive person')
    }
  }

  if (loading) {
    return (
      <div>
        <Skeleton className="h-8 w-48 mb-4" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    )
  }

  if (error || !person) {
    return <ErrorAlert message={error || 'Person not found'} onRetry={fetchData} />
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={() => navigate('/people')} className="text-sm text-gray-500 hover:text-gray-700 mb-2">
            ← Back to People
          </button>
          <h1 className="text-2xl font-semibold text-gray-900">{person.name}</h1>
        </div>
        <div className="flex space-x-2">
          <a
            href={person.linkedin_url.startsWith('http') ? person.linkedin_url : `https://${person.linkedin_url}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700"
          >
            View on LinkedIn
          </a>
          <Button variant="danger" size="sm" onClick={handleArchive}>Archive</Button>
        </div>
      </div>

      {error && <div className="mb-4"><ErrorAlert message={error} /></div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1 bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Profile</h2>
            <Button variant="ghost" size="sm" onClick={() => setEditing(!editing)}>
              {editing ? 'Cancel' : 'Edit'}
            </Button>
          </div>

          {editing ? (
            <div className="space-y-4">
              <Input
                label="Name"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              />
              <Input
                label="Role"
                value={editForm.role}
                onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
              />
              <Input
                label="Company"
                value={editForm.company}
                onChange={(e) => setEditForm({ ...editForm, company: e.target.value })}
              />
              <Textarea
                label="Notes"
                value={editForm.notes}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                rows={3}
              />
              <Button onClick={handleSaveProfile}>Save</Button>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">Role</span>
                <p className="text-sm text-gray-900">{person.role || '-'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Company</span>
                <p className="text-sm text-gray-900">{person.company || '-'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Location</span>
                <p className="text-sm text-gray-900">{person.location || '-'}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">Priority</span>
                <Badge variant={priorityVariant[person.priority as keyof typeof priorityVariant]}>
                  {person.priority}
                </Badge>
              </div>
              <div>
                <span className="text-sm text-gray-500">Stage</span>
                <Badge variant="primary">{person.stage.replace(/_/g, ' ')}</Badge>
              </div>
              {person.notes && (
                <div>
                  <span className="text-sm text-gray-500">Notes</span>
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">{person.notes}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quick Actions & Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Actions */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
            <div className="flex flex-wrap gap-2 mb-4">
              <Button size="sm" onClick={() => handleQuickAction('accepted')}>Accepted</Button>
              <Button size="sm" onClick={() => handleQuickAction('message_sent')}>Message Sent</Button>
              <Button size="sm" onClick={() => handleQuickAction('follow_up_1_sent')}>Follow-up 1</Button>
              <Button size="sm" onClick={() => handleQuickAction('follow_up_2_sent')}>Follow-up 2</Button>
              <Button size="sm" onClick={() => handleQuickAction('reply_received')}>Reply Received</Button>
            </div>
            <Textarea
              placeholder="Add a note to this action (optional)"
              value={actionNote}
              onChange={(e) => setActionNote(e.target.value)}
              rows={2}
            />
          </div>

          {/* Activity Timeline */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Activity Timeline</h2>
            <ActivityTimeline activities={activities} />
          </div>
        </div>
      </div>
    </div>
  )
}
