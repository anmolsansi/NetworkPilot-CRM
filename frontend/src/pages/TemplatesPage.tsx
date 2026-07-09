import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { templatesApi } from '../api/httpClient'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Textarea } from '../components/common/Textarea'
import { Select } from '../components/common/Select'
import { Modal } from '../components/common/Modal'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'

interface Template {
  id: string
  name: string
  category: string
  body: string
  variables: string[] | null
  is_default: boolean
}

const categoryOptions = [
  { value: 'connection_request', label: 'Connection Request' },
  { value: 'first_message', label: 'First Message' },
  { value: 'follow_up', label: 'Follow Up' },
]

const categoryLabels: Record<string, string> = {
  connection_request: 'Connection Request',
  first_message: 'First Message',
  follow_up: 'Follow Up',
}

export function TemplatesPage() {
  const navigate = useNavigate()
  const { currentWorkspace } = useWorkspaceStore()
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const [form, setForm] = useState({ name: '', category: 'connection_request', body: '' })
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const fetchTemplates = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot Templates]', 'Loading templates', {
      workspaceId: currentWorkspace.id.slice(-8),
    })
    setLoading(true)
    setError(null)
    try {
      const data = await templatesApi.list(currentWorkspace.id)
      setTemplates(data)
      console.info('[NetworkPilot Templates]', 'Templates loaded', {
        workspaceId: currentWorkspace.id.slice(-8),
        count: data.length,
      })
    } catch (err: any) {
      console.error('[NetworkPilot Templates]', 'Failed to load templates', {
        workspaceId: currentWorkspace.id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to load templates')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTemplates()
  }, [currentWorkspace])

  const handleOpenModal = (template?: Template) => {
    if (template) {
      setEditingTemplate(template)
      setForm({ name: template.name, category: template.category, body: template.body })
    } else {
      setEditingTemplate(null)
      setForm({ name: '', category: 'connection_request', body: '' })
    }
    setShowModal(true)
  }

  const handleSave = async () => {
    if (!currentWorkspace) return

    try {
      console.info('[NetworkPilot Templates]', 'Saving template', {
        workspaceId: currentWorkspace.id.slice(-8),
        templateId: editingTemplate?.id.slice(-8) || null,
        category: form.category,
      })
      if (editingTemplate) {
        await templatesApi.update(editingTemplate.id, form, currentWorkspace.id)
      } else {
        await templatesApi.create(form, currentWorkspace.id)
      }
      setShowModal(false)
      fetchTemplates()
    } catch (err: any) {
      console.error('[NetworkPilot Templates]', 'Failed to save template', {
        workspaceId: currentWorkspace.id.slice(-8),
        templateId: editingTemplate?.id.slice(-8) || null,
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to save template')
    }
  }

  const handleDelete = async (id: string) => {
    if (!currentWorkspace || !confirm('Delete this template?')) return

    try {
      console.info('[NetworkPilot Templates]', 'Deleting template', {
        workspaceId: currentWorkspace.id.slice(-8),
        templateId: id.slice(-8),
      })
      await templatesApi.delete(id, currentWorkspace.id)
      fetchTemplates()
    } catch (err: any) {
      console.error('[NetworkPilot Templates]', 'Failed to delete template', {
        workspaceId: currentWorkspace.id.slice(-8),
        templateId: id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to delete template')
    }
  }

  const handleCopy = async (template: Template) => {
    console.info('[NetworkPilot Templates]', 'Copying template body', {
      templateId: template.id.slice(-8),
      category: template.category,
    })
    await navigator.clipboard.writeText(template.body)
    setCopiedId(template.id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const renderTemplate = (body: string) => {
    return body
      .replace(/\{\{first_name\}\}/g, '{{first_name}}')
      .replace(/\{\{name\}\}/g, '{{name}}')
      .replace(/\{\{company\}\}/g, '{{company}}')
      .replace(/\{\{role\}\}/g, '{{role}}')
  }

  if (!currentWorkspace) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Templates</h1>
        <EmptyState
          title="Create a workspace first"
          description="Create a workspace before managing message templates."
          action={<Button onClick={() => navigate('/')}>Go to Dashboard</Button>}
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Templates</h1>
        <div className="mt-6 space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Templates</h1>
        <Button onClick={() => handleOpenModal()}>Add Template</Button>
      </div>

      {error && <div className="mt-4"><ErrorAlert message={error} /></div>}

      {templates.length === 0 ? (
        <EmptyState
          title="No templates yet"
          description="Create templates to quickly copy messages."
          action={<Button onClick={() => handleOpenModal()}>Create Template</Button>}
        />
      ) : (
        <div className="mt-6 space-y-4">
          {templates.map((template) => (
            <div key={template.id} className="bg-white shadow rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-medium text-gray-900">{template.name}</h3>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      {categoryLabels[template.category]}
                    </span>
                    {template.is_default && (
                      <span className="text-xs text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
                        Default
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-gray-600 whitespace-pre-wrap">
                    {renderTemplate(template.body)}
                  </p>
                  {template.variables && template.variables.length > 0 && (
                    <p className="mt-2 text-xs text-gray-400">
                      Variables: {template.variables.map(v => `{{${v}}}`).join(', ')}
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleCopy(template)}
                  >
                    {copiedId === template.id ? 'Copied!' : 'Copy'}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleOpenModal(template)}>
                    Edit
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(template.id)}>
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingTemplate ? 'Edit Template' : 'New Template'}
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g., Connection Request"
          />
          <Select
            label="Category"
            options={categoryOptions}
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          />
          <Textarea
            label="Body"
            value={form.body}
            onChange={(e) => setForm({ ...form, body: e.target.value })}
            rows={6}
            placeholder="Hi {{first_name}}, ..."
          />
          <p className="text-xs text-gray-500">
            Use {'{{first_name}}'}, {'{{name}}'}, {'{{company}}'}, {'{{role}}'} for personalization.
          </p>
          <div className="flex justify-end space-x-2">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button onClick={handleSave}>{editingTemplate ? 'Save' : 'Create'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/TemplatesPage.tsx')
