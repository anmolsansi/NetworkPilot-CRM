import { useState, useEffect } from 'react'
import { duplicatesApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'

interface DuplicateGroup {
  group_id: string
  people: any[]
}

interface DuplicatesModalProps {
  onClose: () => void
  onMergeComplete: () => void
}

export function DuplicatesModal({ onClose, onMergeComplete }: DuplicatesModalProps) {
  const { currentWorkspace } = useWorkspaceStore()
  const [groups, setGroups] = useState<DuplicateGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [merging, setMerging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!currentWorkspace) return
    
    let mounted = true
    setLoading(true)
    duplicatesApi.find(currentWorkspace.id)
      .then((res: any[]) => {
        if (mounted) {
          setGroups(res)
          setLoading(false)
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || 'Failed to load duplicates')
          setLoading(false)
        }
      })

    return () => { mounted = false }
  }, [currentWorkspace])

  const handleMerge = async (_groupId: string, targetId: string, sourceId: string) => {
    if (!currentWorkspace) return
    setMerging(true)
    setError(null)
    try {
      await duplicatesApi.merge({
        target_person_id: targetId,
        source_person_id: sourceId,
        fields_to_keep_from_source: ['email', 'linkedin_url', 'phone'] // simplistic merge for now
      }, currentWorkspace.id)
      
      // Remove group from list if it's handled (only 2 people merged). 
      // If there were 3, we'd ideally re-fetch. Let's just re-fetch.
      const freshGroups = await duplicatesApi.find(currentWorkspace.id)
      setGroups(freshGroups)
      onMergeComplete()
    } catch (err: any) {
      setError(err.message || 'Failed to merge')
    } finally {
      setMerging(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold">Resolve Duplicates</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            &times;
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto flex-1">
          {error && <div className="text-red-500 mb-4">{error}</div>}
          
          {loading ? (
            <div className="text-gray-500">Scanning for duplicates...</div>
          ) : groups.length === 0 ? (
            <div className="text-green-600 font-medium">No duplicates found!</div>
          ) : (
            <div className="space-y-6">
              {groups.map((group) => (
                <div key={group.group_id} className="border rounded-lg p-4 bg-gray-50">
                  <h3 className="text-sm font-medium text-gray-500 mb-3">Group: {group.group_id}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {group.people.map(person => (
                      <div key={person.id} className="bg-white p-4 rounded border shadow-sm flex flex-col">
                        <div className="flex-1">
                          <div className="font-semibold">{person.first_name} {person.last_name}</div>
                          <div className="text-sm text-gray-600">{person.company || 'No Company'}</div>
                          {person.email && <div className="text-xs text-gray-500">{person.email}</div>}
                          {person.linkedin_url && <div className="text-xs text-blue-500 truncate">{person.linkedin_url}</div>}
                          <div className="text-xs text-gray-400 mt-2">ID: {person.id}</div>
                        </div>
                        <div className="mt-4 border-t pt-2 flex gap-2">
                          <button
                            disabled={merging}
                            onClick={() => {
                              // Find another person in the group to merge into this one
                              const source = group.people.find(p => p.id !== person.id)
                              if (source) {
                                handleMerge(group.group_id, person.id, source.id)
                              }
                            }}
                            className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600 disabled:opacity-50"
                          >
                            Keep this & merge other
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
