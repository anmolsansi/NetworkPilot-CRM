import { useCallback, useEffect, useState } from 'react'
import { pipelineStagesApi } from '../../api/httpClient'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { ErrorAlert } from '../common/ErrorAlert'

interface PipelineStage {
  id: string
  name: string
  order: number
  color: string | null
  allowed_next_stage_ids: string[]
}

export function PipelineStagesSettings({ workspaceId }: { workspaceId: string }) {
  const [stages, setStages] = useState<PipelineStage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [newStageName, setNewStageName] = useState('')

  const fetchStages = useCallback(async () => {
    setLoading(true)
    try {
      const data = await pipelineStagesApi.list(workspaceId)
      setStages(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch stages')
    } finally {
      setLoading(false)
    }
  }, [workspaceId])

  useEffect(() => {
    fetchStages()
  }, [fetchStages])

  const handleCreate = async () => {
    if (!newStageName.trim()) return
    try {
      await pipelineStagesApi.create({
        name: newStageName.trim(),
        order: stages.length,
      }, workspaceId)
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

  const handleSave = async (stage: PipelineStage) => {
    try {
      await pipelineStagesApi.update(stage.id, {
        name: stage.name,
        color: stage.color,
        allowed_next_stage_ids: stage.allowed_next_stage_ids,
      }, workspaceId)
      await fetchStages()
    } catch (err: any) {
      setError(err.message || 'Failed to update stage')
    }
  }

  const handleMove = async (index: number, direction: -1 | 1) => {
    const target = index + direction
    if (target < 0 || target >= stages.length) return
    const reordered = [...stages]
    ;[reordered[index], reordered[target]] = [reordered[target], reordered[index]]
    try {
      setStages(reordered)
      await pipelineStagesApi.reorder(reordered.map(stage => stage.id), workspaceId)
      await fetchStages()
    } catch (err: any) {
      setError(err.message || 'Failed to reorder stages')
      await fetchStages()
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
            {stages.map((stage, index) => (
              <li key={stage.id} className="py-3 space-y-3">
                <div className="flex items-center gap-2">
                  <button aria-label={`Move ${stage.name} up`} onClick={() => handleMove(index, -1)} disabled={index === 0}>↑</button>
                  <button aria-label={`Move ${stage.name} down`} onClick={() => handleMove(index, 1)} disabled={index === stages.length - 1}>↓</button>
                  <input
                    className="flex-1 rounded border-gray-300 text-sm"
                    value={stage.name}
                    onChange={(event) => setStages(current => current.map(item => item.id === stage.id ? { ...item, name: event.target.value } : item))}
                  />
                  <input
                    aria-label={`Colour for ${stage.name}`}
                    type="color"
                    value={stage.color || '#2563eb'}
                    onChange={(event) => setStages(current => current.map(item => item.id === stage.id ? { ...item, color: event.target.value } : item))}
                  />
                  <button onClick={() => handleSave(stage)} className="text-blue-600 hover:text-blue-800 text-sm">Save</button>
                  <button onClick={() => handleDelete(stage.id)} className="text-red-600 hover:text-red-800 text-sm">Delete</button>
                </div>
                <label className="block text-xs text-gray-500">
                  Allowed next stages (leave empty to allow any)
                  <select
                    multiple
                    className="mt-1 block w-full rounded border-gray-300 text-sm"
                    value={stage.allowed_next_stage_ids || []}
                    onChange={(event) => {
                      const selected = Array.from(event.target.selectedOptions, option => option.value)
                      setStages(current => current.map(item => item.id === stage.id ? { ...item, allowed_next_stage_ids: selected } : item))
                    }}
                  >
                    {stages.filter(option => option.id !== stage.id).map(option => <option key={option.id} value={option.id}>{option.name}</option>)}
                  </select>
                </label>
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
