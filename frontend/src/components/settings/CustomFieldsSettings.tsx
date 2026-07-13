import { useState, useEffect } from 'react'
import { customFieldsApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { ErrorAlert } from '../common/ErrorAlert'
import { Select } from '../common/Select'

export function CustomFieldsSettings() {
  const { currentWorkspace } = useWorkspaceStore()
  const [fields, setFields] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // New field state
  const [newFieldName, setNewFieldName] = useState('')
  const [newFieldType, setNewFieldType] = useState('text')

  useEffect(() => {
    fetchFields()
  }, [currentWorkspace])

  const fetchFields = async () => {
    if (!currentWorkspace) return
    setLoading(true)
    setError(null)
    try {
      const data = await customFieldsApi.list(currentWorkspace.id)
      setFields(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load custom fields')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentWorkspace || !newFieldName.trim()) return

    setLoading(true)
    try {
      await customFieldsApi.create({
        name: newFieldName.trim(),
        field_type: newFieldType,
      }, currentWorkspace.id)
      setNewFieldName('')
      setNewFieldType('text')
      fetchFields()
    } catch (err: any) {
      setError(err.message || 'Failed to create custom field')
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!currentWorkspace || !window.confirm('Are you sure you want to delete this custom field? People using this field will not lose data, but it will stop displaying.')) return

    setLoading(true)
    try {
      await customFieldsApi.delete(id, currentWorkspace.id)
      fetchFields()
    } catch (err: any) {
      setError(err.message || 'Failed to delete custom field')
      setLoading(false)
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Custom Fields</h2>
      <p className="text-sm text-gray-500 mb-4">
        Define custom fields to store extra information about people.
      </p>

      {error && <div className="mb-4"><ErrorAlert message={error} /></div>}

      <form onSubmit={handleCreate} className="flex items-end gap-2 mb-6">
        <div className="flex-1">
          <Input
            label="New Field Name"
            value={newFieldName}
            onChange={(e) => setNewFieldName(e.target.value)}
            placeholder="e.g. Birthday"
          />
        </div>
        <div className="w-48">
          <Select
            label="Field Type"
            value={newFieldType}
            onChange={(e) => setNewFieldType(e.target.value)}
            options={[
              { value: 'text', label: 'Text' },
              { value: 'number', label: 'Number' },
              { value: 'date', label: 'Date' },
              { value: 'boolean', label: 'Checkbox' }
            ]}
          />
        </div>
        <Button type="submit" disabled={!newFieldName.trim() || loading}>
          Add
        </Button>
      </form>

      {loading && fields.length === 0 ? (
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      ) : fields.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No custom fields defined yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 border-t border-b border-gray-200 mt-4">
          {fields.map(field => (
            <li key={field.id} className="py-3 flex items-center justify-between">
              <div>
                <span className="font-medium text-gray-900">{field.name}</span>
                <span className="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded uppercase">{field.field_type}</span>
              </div>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDelete(field.id)}
                disabled={loading}
              >
                Delete
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
