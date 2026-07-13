import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { peopleApi } from '../api/httpClient'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Input } from '../components/common/Input'
import { Select } from '../components/common/Select'
import { Textarea } from '../components/common/Textarea'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { TagSelect } from '../components/people/TagSelect'

const priorityOptions = [
  { value: 'A', label: 'A - High' },
  { value: 'B', label: 'B - Medium' },
  { value: 'C', label: 'C - Low' },
]

export function PersonCreatePage() {
  const navigate = useNavigate()
  const { currentWorkspace } = useWorkspaceStore()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: '',
    linkedin_url: '',
    role: '',
    company: '',
    location: '',
    priority: 'B',
    connection_note: '',
    notes: '',
    tag_ids: [] as string[],
  })

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!currentWorkspace || saving) return

    setSaving(true)
    setError(null)
    try {
      const person = await peopleApi.create(
        {
          name: form.name.trim(),
          linkedin_url: form.linkedin_url.trim(),
          role: form.role.trim() || undefined,
          company: form.company.trim() || undefined,
          location: form.location.trim() || undefined,
          priority: form.priority,
          connection_note: form.connection_note.trim() || undefined,
          notes: form.notes.trim() || undefined,
          tag_ids: form.tag_ids,
        },
        currentWorkspace.id
      )
      navigate(`/people/${person.id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to add person')
    } finally {
      setSaving(false)
    }
  }

  if (!currentWorkspace) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Add Person</h1>
        <EmptyState
          title="Create a workspace first"
          description="Create a workspace before adding people."
          action={<Button onClick={() => navigate('/')}>Go to Dashboard</Button>}
        />
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <button onClick={() => navigate('/people')} className="text-sm text-gray-500 hover:text-gray-700 mb-4">
        Back to People
      </button>
      <h1 className="text-2xl font-semibold text-gray-900">Add Person</h1>
      <p className="mt-2 text-sm text-gray-600">
        Add a LinkedIn prospect to this workspace.
      </p>

      {error && <div className="mt-4"><ErrorAlert message={error} /></div>}

      <form onSubmit={handleSubmit} className="mt-6 bg-white shadow rounded-lg p-6 space-y-4">
        <Input
          label="Name"
          value={form.name}
          onChange={(event) => setForm({ ...form, name: event.target.value })}
          required
        />
        <Input
          label="LinkedIn URL"
          value={form.linkedin_url}
          onChange={(event) => setForm({ ...form, linkedin_url: event.target.value })}
          placeholder="https://www.linkedin.com/in/example"
          required
        />
        <Input
          label="Role"
          value={form.role}
          onChange={(event) => setForm({ ...form, role: event.target.value })}
        />
        <Input
          label="Company"
          value={form.company}
          onChange={(event) => setForm({ ...form, company: event.target.value })}
        />
        <Input
          label="Location"
          value={form.location}
          onChange={(event) => setForm({ ...form, location: event.target.value })}
        />
        <Select
          label="Priority"
          options={priorityOptions}
          value={form.priority}
          onChange={(event) => setForm({ ...form, priority: event.target.value })}
        />
        <Textarea
          label="Connection Note"
          value={form.connection_note}
          onChange={(event) => setForm({ ...form, connection_note: event.target.value })}
          rows={3}
        />
        <Textarea
          label="Notes"
          value={form.notes}
          onChange={(event) => setForm({ ...form, notes: event.target.value })}
          rows={4}
        />
        <TagSelect 
          selectedTagIds={form.tag_ids} 
          onChange={(tagIds) => setForm({ ...form, tag_ids: tagIds })} 
        />
        <div className="flex justify-end space-x-2">
          <Button type="button" variant="secondary" onClick={() => navigate('/people')}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving || !form.name.trim() || !form.linkedin_url.trim()}>
            {saving ? 'Adding...' : 'Add Person'}
          </Button>
        </div>
      </form>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/PersonCreatePage.tsx')
