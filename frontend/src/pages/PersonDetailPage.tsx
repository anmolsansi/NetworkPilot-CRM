import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { peopleApi, activitiesApi, pipelineStagesApi, customFieldsApi } from '../api/httpClient'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Textarea } from '../components/common/Textarea'
import { Badge } from '../components/common/Badge'
import { Skeleton } from '../components/common/Skeleton'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { ActivityTimeline, type ActivityFilters } from '../components/activities/ActivityTimeline'
import { TagSelect } from '../components/people/TagSelect'
import { PersonOwnerControl } from '../components/people/PersonOwnerControl'
import { PersonTasksPanel } from '../components/tasks/PersonTasksPanel'

interface Person {
  id: string
  name: string
  linkedin_url: string
  company: string | null
  role: string | null
  location: string | null
  email: string | null
  phone_number: string | null
  premium: boolean | null
  company_website: string | null
  processed_at: string | null
  invite_accepted_at: string | null
  priority: string
  stage: string
  stage_id: string | null
  pipeline_stage: any | null
  status: string
  notes: string | null
  connection_note: string | null
  is_favorite: boolean
  favorite_notes: string | null
  next_action_type: string | null
  next_action_date: string | null
  tags: { id: string; name: string; color: string | null }[]
  custom_fields_data: Record<string, any> | null
  manual_warmth: number | null
  calculated_freshness: number | null
  engagement_score: number
  relationship_health: string
  last_engaged_at: string | null
  owner_id: string | null
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
  const [activityFilters, setActivityFilters] = useState<ActivityFilters>({
    action_type: '', source: '', created_from: '', created_to: '',
  })
  const [pipelineStages, setPipelineStages] = useState<any[]>([])
  const [customFields, setCustomFields] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '', role: '', company: '', notes: '', is_favorite: false, favorite_notes: '', tag_ids: [] as string[], stage_id: '', custom_fields_data: {} as Record<string, any>, manual_warmth: null as number | null
  })
  const [actionDetails, setActionDetails] = useState({
    notes: '',
    interaction_summary: '',
    outcome: '',
    next_steps: '',
  })
  const [deleted, setDeleted] = useState(false)

  const fetchData = useCallback(async () => {
    if (!currentWorkspace || !id) return

    console.info('[NetworkPilot PersonDetail]', 'Loading person detail', {
      workspaceId: currentWorkspace.id.slice(-8),
      personId: id.slice(-8),
    })
    setLoading(true)
    setError(null)
    try {
      const [personData, activitiesData, stagesData, fieldsData] = await Promise.all([
        peopleApi.get(id, currentWorkspace.id),
        activitiesApi.list(id, currentWorkspace.id, {
          ...(activityFilters.action_type && { action_type: activityFilters.action_type }),
          ...(activityFilters.source && { source: activityFilters.source }),
          ...(activityFilters.created_from && { created_from: `${activityFilters.created_from}T00:00:00Z` }),
          ...(activityFilters.created_to && { created_to: `${activityFilters.created_to}T23:59:59.999Z` }),
        }),
        pipelineStagesApi.list(currentWorkspace.id),
        customFieldsApi.list(currentWorkspace.id),
      ])
      setPipelineStages(stagesData)
      setCustomFields(fieldsData)
      setPerson(personData)
      setActivities(activitiesData)
      setEditForm({
        name: personData.name,
        role: personData.role || '',
        company: personData.company || '',
        notes: personData.notes || '',
        is_favorite: personData.is_favorite,
        favorite_notes: personData.favorite_notes || '',
        tag_ids: personData.tags?.map((t: any) => t.id) || [],
        stage_id: personData.stage_id || '',
        custom_fields_data: personData.custom_fields_data || {},
        manual_warmth: personData.manual_warmth,
      })
      console.info('[NetworkPilot PersonDetail]', 'Person detail loaded', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
        activityCount: activitiesData.length,
        stage: personData.stage,
      })
    } catch (err: any) {
      console.error('[NetworkPilot PersonDetail]', 'Failed to load person detail', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to load person')
    } finally {
      setLoading(false)
    }
  }, [activityFilters, currentWorkspace, id])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleSaveProfile = async () => {
    if (!currentWorkspace || !id) return

    try {
      console.info('[NetworkPilot PersonDetail]', 'Saving person profile', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
      })
      const payload = {
        ...editForm,
        stage_id: editForm.stage_id || null
      }
      await peopleApi.update(id, payload, currentWorkspace.id)
      setEditing(false)
      fetchData()
    } catch (err: any) {
      console.error('[NetworkPilot PersonDetail]', 'Failed to save person profile', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to update person')
    }
  }

  const handleQuickAction = async (actionType: string) => {
    if (!currentWorkspace || !id) return

    try {
      console.info('[NetworkPilot PersonDetail]', 'Recording quick action', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
        actionType,
      })
      await activitiesApi.create(id, {
        action_type: actionType,
        source: 'web_app',
        notes: actionDetails.notes || undefined,
        interaction_summary: actionDetails.interaction_summary || undefined,
        outcome: actionDetails.outcome || undefined,
        next_steps: actionDetails.next_steps || undefined,
      }, currentWorkspace.id)
      setActionDetails({ notes: '', interaction_summary: '', outcome: '', next_steps: '' })
      fetchData()
    } catch (err: any) {
      console.error('[NetworkPilot PersonDetail]', 'Failed to record quick action', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
        actionType,
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to record action')
    }
  }

  const handleArchive = async () => {
    if (!currentWorkspace || !id) return

    try {
      console.info('[NetworkPilot PersonDetail]', 'Archiving person', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
      })
      await peopleApi.archive(id, {}, currentWorkspace.id)
      fetchData()
    } catch (err: any) {
      console.error('[NetworkPilot PersonDetail]', 'Failed to archive person', {
        workspaceId: currentWorkspace.id.slice(-8),
        personId: id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to archive person')
    }
  }

  const handleDelete = async () => {
    if (!currentWorkspace || !id || !window.confirm('Move this person to Trash?')) return
    try {
      await peopleApi.delete(id, currentWorkspace.id)
      setDeleted(true)
    } catch (err: any) {
      setError(err.message || 'Failed to move person to Trash')
    }
  }

  const handleUndoDelete = async () => {
    if (!currentWorkspace || !id) return
    try {
      await peopleApi.restore(id, currentWorkspace.id)
      setDeleted(false)
      await fetchData()
    } catch (err: any) {
      setError(err.message || 'Failed to restore person')
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
          <Button variant="secondary" size="sm" onClick={handleArchive}>Archive</Button>
          <Button variant="danger" size="sm" onClick={handleDelete}>Move to Trash</Button>
        </div>
      </div>

      {deleted && (
        <div className="mb-4 flex items-center justify-between rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <span>This person was moved to Trash.</span>
          <Button size="sm" onClick={handleUndoDelete}>Undo</Button>
        </div>
      )}

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
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={editForm.is_favorite}
                  onChange={(e) => setEditForm({ ...editForm, is_favorite: e.target.checked })}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                Favourite person
              </label>
              <Textarea
                label="Favourite notes"
                value={editForm.favorite_notes}
                onChange={(e) => setEditForm({ ...editForm, favorite_notes: e.target.value })}
                rows={3}
              />
              <TagSelect
                selectedTagIds={editForm.tag_ids}
                onChange={(tagIds) => setEditForm({ ...editForm, tag_ids: tagIds })}
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Manual Warmth</label>
                <select
                  value={editForm.manual_warmth || ''}
                  onChange={(e) => setEditForm({ ...editForm, manual_warmth: e.target.value ? parseInt(e.target.value, 10) : null })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">Auto (Use Calculated Freshness)</option>
                  <option value="1">1 - Ice Cold</option>
                  <option value="2">2 - Cold</option>
                  <option value="3">3 - Warm</option>
                  <option value="4">4 - Hot</option>
                  <option value="5">5 - On Fire</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stage</label>
                <select
                  value={editForm.stage_id}
                  onChange={(e) => setEditForm({ ...editForm, stage_id: e.target.value })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">No custom stage</option>
                  {pipelineStages.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              
              {/* Custom Fields Edit */}
              {customFields.length > 0 && (
                <div className="pt-4 mt-4 border-t border-gray-200 space-y-4">
                  <h3 className="text-sm font-medium text-gray-900">Custom Fields</h3>
                  {customFields.map(field => (
                    <div key={field.id}>
                      {field.field_type === 'boolean' ? (
                        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                          <input
                            type="checkbox"
                            checked={!!editForm.custom_fields_data[field.id]}
                            onChange={(e) => setEditForm({
                              ...editForm,
                              custom_fields_data: {
                                ...editForm.custom_fields_data,
                                [field.id]: e.target.checked
                              }
                            })}
                            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                          {field.name}
                        </label>
                      ) : field.field_type === 'select' ? (
                        <label className="block text-sm font-medium text-gray-700">
                          {field.name}
                          <select
                            className="mt-1 block w-full rounded-md border-gray-300"
                            value={editForm.custom_fields_data[field.id] || ''}
                            onChange={(e) => setEditForm({
                              ...editForm,
                              custom_fields_data: { ...editForm.custom_fields_data, [field.id]: e.target.value },
                            })}
                          >
                            <option value="">Select…</option>
                            {(field.options?.choices || []).map((choice: string) => <option key={choice} value={choice}>{choice}</option>)}
                          </select>
                        </label>
                      ) : (
                        <Input
                          label={field.name}
                          type={field.field_type === 'number' ? 'number' : field.field_type === 'date' ? 'date' : 'text'}
                          value={editForm.custom_fields_data[field.id] || ''}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            custom_fields_data: {
                              ...editForm.custom_fields_data,
                              [field.id]: field.field_type === 'number' ? Number(e.target.value) : e.target.value
                            }
                          })}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}

              <Button onClick={handleSaveProfile}>Save</Button>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">Tags</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {person.tags?.length > 0 ? (
                    person.tags.map(t => (
                      <span key={t.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        {t.name}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-gray-400">None</span>
                  )}
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-500">Favourite</span>
                <p className="text-sm text-gray-900">{person.is_favorite ? '★ Yes' : 'No'}</p>
              </div>
              {person.favorite_notes && (
                <div>
                  <span className="text-sm text-gray-500">Favourite notes</span>
                  <p className="whitespace-pre-wrap text-sm text-gray-900">{person.favorite_notes}</p>
                </div>
              )}
              <PersonOwnerControl personId={person.id} ownerId={person.owner_id} onUpdated={fetchData} />
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
              <div>
                <span className="text-sm text-gray-500">Email</span>
                <p className="text-sm text-gray-900">{person.email || '-'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Phone</span>
                <p className="text-sm text-gray-900">{person.phone_number || '-'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Company website</span>
                <p className="text-sm text-gray-900">
                  {person.company_website ? (
                    <a href={person.company_website} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:text-primary-700">
                      {person.company_website}
                    </a>
                  ) : '-'}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500">LinkedIn Premium</span>
                <p className="text-sm text-gray-900">{person.premium == null ? '-' : person.premium ? 'Yes' : 'No'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Processed</span>
                <p className="text-sm text-gray-900">{person.processed_at ? new Date(person.processed_at).toLocaleString() : '-'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Invite accepted</span>
                <p className="text-sm text-gray-900">{person.invite_accepted_at ? new Date(person.invite_accepted_at).toLocaleString() : '-'}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Last engaged</span>
                <p className="text-sm text-gray-900">{person.last_engaged_at ? new Date(person.last_engaged_at).toLocaleString() : 'Never'}</p>
              </div>
              <div className="flex flex-col space-y-1">
                <span className="text-sm text-gray-500">Relationship health</span>
                <Badge variant={person.relationship_health === 'strong' ? 'success' : person.relationship_health === 'healthy' ? 'primary' : person.relationship_health === 'needs_attention' ? 'warning' : 'default'}>
                  {person.relationship_health.replace(/_/g, ' ')}
                </Badge>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2.5 max-w-[150px]">
                    <div className="bg-primary-600 h-2.5 rounded-full" style={{ width: `${person.calculated_freshness || 0}%` }}></div>
                  </div>
                  <span className="text-xs text-gray-600">{person.calculated_freshness || 0}/100</span>
                </div>
                <span className="text-xs text-gray-600">Engagement: {person.engagement_score}/100</span>
                {person.manual_warmth && (
                  <span className="text-xs text-amber-600 font-medium">Overridden (Manual: {person.manual_warmth}/5)</span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">Priority</span>
                <Badge variant={priorityVariant[person.priority as keyof typeof priorityVariant]}>
                  {person.priority}
                </Badge>
              </div>
              <div>
                <span className="text-sm text-gray-500">Stage</span>
                {person.pipeline_stage ? (
                  <Badge variant="primary">{person.pipeline_stage.name}</Badge>
                ) : (
                  <Badge variant="default">{person.stage.replace(/_/g, ' ')} (Legacy)</Badge>
                )}
              </div>
              {person.notes && (
                <div>
                  <span className="text-sm text-gray-500">Notes</span>
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">{person.notes}</p>
                </div>
              )}

              {/* Custom Fields View */}
              {customFields.length > 0 && (
                <div className="pt-4 mt-4 border-t border-gray-200 space-y-3">
                  <h3 className="text-sm font-medium text-gray-900">Custom Fields</h3>
                  {customFields.map(field => {
                    const value = person.custom_fields_data?.[field.id]
                    return (
                      <div key={field.id}>
                        <span className="text-sm text-gray-500">{field.name}</span>
                        <p className="text-sm text-gray-900">
                          {value === undefined || value === null || value === '' ? '-' : 
                            field.field_type === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                        </p>
                      </div>
                    )
                  })}
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
            <div className="grid gap-3 sm:grid-cols-2">
              <Textarea
                label="Notes"
                placeholder="Free-form context (optional)"
                value={actionDetails.notes}
                onChange={(e) => setActionDetails({ ...actionDetails, notes: e.target.value })}
                rows={2}
              />
              <Textarea
                label="Interaction summary"
                placeholder="What was discussed?"
                value={actionDetails.interaction_summary}
                onChange={(e) => setActionDetails({ ...actionDetails, interaction_summary: e.target.value })}
                rows={2}
              />
              <Textarea
                label="Outcome"
                placeholder="What was decided or achieved?"
                value={actionDetails.outcome}
                onChange={(e) => setActionDetails({ ...actionDetails, outcome: e.target.value })}
                rows={2}
              />
              <Textarea
                label="Next steps"
                placeholder="What should happen next?"
                value={actionDetails.next_steps}
                onChange={(e) => setActionDetails({ ...actionDetails, next_steps: e.target.value })}
                rows={2}
              />
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Activity Timeline</h2>
            <ActivityTimeline
              activities={activities}
              onRefresh={fetchData}
              filters={activityFilters}
              onFiltersChange={setActivityFilters}
            />
          </div>

          <PersonTasksPanel personId={id!} />
        </div>
      </div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/PersonDetailPage.tsx')
