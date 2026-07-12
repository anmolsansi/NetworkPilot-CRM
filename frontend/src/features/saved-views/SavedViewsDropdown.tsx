import { useState, useEffect } from 'react'
import { savedViewsApi } from '../../api/httpClient'
import { Button } from '../../components/common/Button'

interface SavedView {
  id: string
  name: string
  filters: any
  sort_by: string
  sort_order: string
}

interface SavedViewsDropdownProps {
  workspaceId: string
  onSelectView: (filters: any, sortBy: string, sortOrder: string) => void
  refreshTrigger: number
}

export function SavedViewsDropdown({ workspaceId, onSelectView, refreshTrigger }: SavedViewsDropdownProps) {
  const [views, setViews] = useState<SavedView[]>([])
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  const fetchViews = async () => {
    if (!workspaceId) return
    setLoading(true)
    try {
      const data = await savedViewsApi.list(workspaceId)
      setViews(data)
    } catch (err) {
      console.error('Failed to fetch saved views', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchViews()
  }, [workspaceId, refreshTrigger])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!window.confirm('Delete this saved view?')) return
    
    try {
      await savedViewsApi.delete(id, workspaceId)
      fetchViews()
    } catch (err) {
      console.error('Failed to delete view', err)
    }
  }

  return (
    <div className="relative inline-block text-left">
      <Button
        variant="secondary"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        Saved Views {views.length > 0 && `(${views.length})`}
      </Button>

      {isOpen && (
        <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
          <div className="py-1" role="menu" aria-orientation="vertical">
            {loading && <div className="px-4 py-2 text-sm text-gray-500">Loading...</div>}
            
            {!loading && views.length === 0 && (
              <div className="px-4 py-2 text-sm text-gray-500 italic">No saved views</div>
            )}
            
            {views.map(view => (
              <div
                key={view.id}
                className="flex items-center justify-between px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 cursor-pointer group"
                onClick={() => {
                  onSelectView(view.filters, view.sort_by, view.sort_order)
                  setIsOpen(false)
                }}
              >
                <span className="truncate pr-2">{view.name}</span>
                <button
                  onClick={(e) => handleDelete(e, view.id)}
                  className="text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Delete view"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
