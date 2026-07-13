import { useCallback, useEffect, useState } from 'react'
import { tagsApi } from '../../api/httpClient'
import type { Tag } from '../../types'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { ErrorAlert } from '../common/ErrorAlert'

export function TagsSettings({ workspaceId }: { workspaceId: string }) {
  const [tags, setTags] = useState<Tag[]>([])
  const [name, setName] = useState('')
  const [color, setColor] = useState('#2563eb')
  const [error, setError] = useState<string | null>(null)

  const loadTags = useCallback(async () => {
    try {
      setTags(await tagsApi.list(workspaceId))
    } catch (err: any) {
      setError(err.message || 'Failed to load tags')
    }
  }, [workspaceId])

  useEffect(() => { loadTags() }, [loadTags])

  const createTag = async () => {
    if (!name.trim()) return
    try {
      await tagsApi.create(workspaceId, { name: name.trim(), color })
      setName('')
      await loadTags()
    } catch (err: any) {
      setError(err.message || 'Failed to create tag')
    }
  }

  const updateColor = async (tag: Tag, nextColor: string) => {
    await tagsApi.update(tag.id, workspaceId, { color: nextColor })
    setTags(current => current.map(item => item.id === tag.id ? { ...item, color: nextColor } : item))
  }

  const deleteTag = async (tag: Tag) => {
    if (!window.confirm(`Delete the “${tag.name}” tag? It will be removed from every person.`)) return
    await tagsApi.delete(tag.id, workspaceId)
    setTags(current => current.filter(item => item.id !== tag.id))
  }

  return (
    <section className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900">Tags</h2>
      <p className="mt-1 text-sm text-gray-500">Create reusable coloured labels for people and bulk workflows.</p>
      {error && <div className="mt-4"><ErrorAlert message={error} /></div>}
      <div className="mt-4 flex items-end gap-3">
        <div className="flex-1"><Input label="Tag name" value={name} onChange={event => setName(event.target.value)} /></div>
        <label className="text-sm font-medium text-gray-700">Colour
          <input className="ml-2 h-9 w-12 align-middle" type="color" value={color} onChange={event => setColor(event.target.value)} />
        </label>
        <Button onClick={createTag} disabled={!name.trim()}>Add tag</Button>
      </div>
      <ul className="mt-5 divide-y">
        {tags.map(tag => (
          <li key={tag.id} className="flex items-center justify-between py-3">
            <span className="rounded px-2 py-1 text-sm text-white" style={{ backgroundColor: tag.color || '#64748b' }}>{tag.name}</span>
            <div className="flex items-center gap-3">
              <input aria-label={`Colour for ${tag.name}`} type="color" value={tag.color || '#64748b'} onChange={event => updateColor(tag, event.target.value)} />
              <button className="text-sm text-red-600 hover:text-red-800" onClick={() => deleteTag(tag)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
