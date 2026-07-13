import { useState, useEffect, useRef } from 'react'
import { tagsApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import type { Tag } from '../../types'

interface TagSelectProps {
  selectedTagIds: string[]
  onChange: (tagIds: string[]) => void
}

export function TagSelect({ selectedTagIds, onChange }: TagSelectProps) {
  const { currentWorkspace } = useWorkspaceStore()
  const [tags, setTags] = useState<Tag[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (currentWorkspace) {
      tagsApi.list(currentWorkspace.id).then(setTags).catch(console.error)
    }
  }, [currentWorkspace])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleTag = (tagId: string) => {
    if (selectedTagIds.includes(tagId)) {
      onChange(selectedTagIds.filter(id => id !== tagId))
    } else {
      onChange([...selectedTagIds, tagId])
    }
  }

  const handleCreateTag = async () => {
    if (!currentWorkspace || !newTagName.trim()) return
    try {
      const newTag = await tagsApi.create(currentWorkspace.id, { name: newTagName.trim() })
      setTags([...tags, newTag])
      onChange([...selectedTagIds, newTag.id])
      setNewTagName('')
    } catch (err) {
      console.error('Failed to create tag', err)
    }
  }

  const selectedTags = tags.filter(t => selectedTagIds.includes(t.id))

  return (
    <div className="relative" ref={containerRef}>
      <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
      <div 
        className="min-h-[38px] w-full border border-gray-300 rounded-md p-1 flex flex-wrap gap-1 cursor-text bg-white"
        onClick={() => setIsOpen(true)}
      >
        {selectedTags.map(tag => (
          <span key={tag.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
            {tag.name}
            <button
              type="button"
              className="ml-1 text-blue-600 hover:text-blue-800 focus:outline-none"
              onClick={(e) => {
                e.stopPropagation()
                toggleTag(tag.id)
              }}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          className="flex-1 min-w-[60px] outline-none text-sm p-1"
          placeholder={selectedTags.length === 0 ? "Select or create tags..." : ""}
          value={newTagName}
          onChange={(e) => setNewTagName(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && newTagName.trim()) {
              e.preventDefault()
              handleCreateTag()
            }
          }}
        />
      </div>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto sm:text-sm">
          {tags.filter(t => t.name.toLowerCase().includes(newTagName.toLowerCase())).map((tag) => (
            <div
              key={tag.id}
              className={`cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-gray-100 ${selectedTagIds.includes(tag.id) ? 'bg-blue-50' : ''}`}
              onClick={() => toggleTag(tag.id)}
            >
              <span className={`block truncate ${selectedTagIds.includes(tag.id) ? 'font-semibold' : 'font-normal'}`}>
                {tag.name}
              </span>
              {selectedTagIds.includes(tag.id) && (
                <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600">
                  ✓
                </span>
              )}
            </div>
          ))}
          {newTagName.trim() && !tags.some(t => t.name.toLowerCase() === newTagName.trim().toLowerCase()) && (
            <div
              className="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-gray-100 text-blue-600"
              onClick={handleCreateTag}
            >
              Create "{newTagName.trim()}"
            </div>
          )}
        </div>
      )}
    </div>
  )
}
