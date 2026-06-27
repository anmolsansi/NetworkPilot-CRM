import { useState, useEffect } from 'react'
import { extensionApi, Template } from '../api/extensionApi'
import { renderTemplate } from '../utils/templateRender'

interface Props {
  person?: {
    name?: string
    company?: string
    role?: string
  }
}

export function TemplateCopyPanel({ person }: Props) {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const data = await extensionApi.getTemplates()
      setTemplates(data)
    } catch (error) {
      console.error('Failed to fetch templates:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async (template: Template) => {
    const rendered = person ? renderTemplate(template.body, person) : template.body
    await navigator.clipboard.writeText(rendered)
    setCopiedId(template.id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const filteredTemplates = categoryFilter === 'all'
    ? templates
    : templates.filter(t => t.category === categoryFilter)

  if (loading) {
    return (
      <div className="p-3 text-center text-sm text-gray-500">
        Loading templates...
      </div>
    )
  }

  if (templates.length === 0) {
    return (
      <div className="p-3 text-center text-sm text-gray-500">
        No templates yet. Create some in the web app.
      </div>
    )
  }

  return (
    <div className="border-t border-gray-200 pt-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900">Templates</h3>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="text-xs border border-gray-300 rounded px-2 py-1"
        >
          <option value="all">All</option>
          <option value="connection_request">Connection</option>
          <option value="first_message">First Message</option>
          <option value="follow_up">Follow-up</option>
        </select>
      </div>
      
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            className="bg-gray-50 rounded p-2 text-xs"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-gray-700">{template.name}</span>
              <button
                onClick={() => handleCopy(template)}
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                {copiedId === template.id ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="text-gray-500 line-clamp-2">
              {person ? renderTemplate(template.body, person) : template.body}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
