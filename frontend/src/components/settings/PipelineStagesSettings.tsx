import { useEffect, useState } from 'react'
import { pipelineStagesApi } from '../../api/httpClient'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { ErrorAlert } from '../common/ErrorAlert'

interface PipelineStage {
  id: string
  name: string
  order: number
  color: string | null
}

export function PipelineStagesSettings({ workspaceId }: { workspaceId: string }) {
  const [stages, setStages] = useState<PipelineStage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [newStageName, setNewStageName] = useState('')

  const fetchStages = async () => {
    setLoading(true)
    try {
      const data = await pipelineStagesApi.list(workspaceId)
      setStages(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch stages')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStages()
  }, [workspaceId])

  const handleCreate = async () => {
    if (!newStageName.trim()) return
    try {
      await pipelineStagesApi.create(workspaceId, {
        name: newStageName.trim(),
        order: stages.length,
      })
      setNewStageName('')
      await fetchStages()
    } catch (err: any) {
      setError(err.message || 'Failed to create stage')
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this stage? This will set people in this stage to no stage.')) return
    try {
      await pipelineStagesApi.delete(id, workspaceId)
      await fetchStages()
    } catch (err: any) {
      setError(err.message || 'Failed to delete stage')
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6 mt-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Pipeline Stages</h2>
      
      {error && <div className="mb-4"><ErrorAlert message={error} /></div>}

      <div className="space-y-4 mb-4">
        {loading ? (
          <div className="text-sm text-gray-500">Loading stages...</div>
        ) : stages.length === 0 ? (
          <div className="text-sm text-gray-500 italic">No custom pipeline stages defined.</div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {stages.map((stage) => (
              <li key={stage.id} className="py-3 flex justify-between items-center">
                <div className="text-sm font-medium text-gray-900">{stage.name}</div>
                <button
                  onClick={() => handleDelete(stage.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="New stage name..."
          value={newStageName}
          onChange={(e) => setNewStageName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
        />
        <Button onClick={handleCreate} disabled={!newStageName.trim()}>
          Add Stage
        </Button>
      </div>
    </div>
  )
}
