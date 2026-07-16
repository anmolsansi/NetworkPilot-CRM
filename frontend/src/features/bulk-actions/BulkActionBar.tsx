import { useState } from 'react'
import { Button } from '../../components/common/Button'
import { Select } from '../../components/common/Select'
import { Modal } from '../../components/common/Modal'
import { Input } from '../../components/common/Input'
import { ErrorAlert } from '../../components/common/ErrorAlert'
import { peopleApi } from '../../api/httpClient'

interface BulkActionBarProps {
  workspaceId: string
  selectedIds: string[]
  onClearSelection: () => void
  onSuccess: () => void
  pipelineStages: any[]
  members: { user_id: string; email: string; display_name: string | null }[]
}

const priorityOptions = [
  { value: 'A', label: 'A - High' },
  { value: 'B', label: 'B - Medium' },
  { value: 'C', label: 'C - Low' },
]

export function BulkActionBar({ workspaceId, selectedIds, onClearSelection, onSuccess, pipelineStages, members }: BulkActionBarProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Modal states
  const [modalType, setModalType] = useState<'stage' | 'priority' | 'tags_add' | 'tags_remove' | 'next_action' | 'owner' | null>(null)
  
  // Form states
  const [stageValue, setStageValue] = useState('')
  const [priorityValue, setPriorityValue] = useState(priorityOptions[0].value)
  const [tagsValue, setTagsValue] = useState('')
  const [nextActionType, setNextActionType] = useState('')
  const [nextActionDate, setNextActionDate] = useState('')
  const [ownerId, setOwnerId] = useState('')

  if (selectedIds.length === 0) return null

  const handleBulkAction = async (action: string, payload: any) => {
    setLoading(true)
    setError(null)
    try {
      await peopleApi.bulkAction({
        workspace_id: workspaceId,
        person_ids: selectedIds,
        action,
        payload,
      })
      setModalType(null)
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Bulk action failed')
    } finally {
      setLoading(false)
    }
  }

  const renderModal = () => {
    if (!modalType) return null

    return (
      <Modal
        isOpen={!!modalType}
        onClose={() => setModalType(null)}
        title={`Bulk Update (${selectedIds.length} selected)`}
      >
        <div className="space-y-4">
          {error && <ErrorAlert message={error} onRetry={() => setError(null)} />}

          {modalType === 'stage' && (
            <Select
              label="New Stage"
              options={[
                { value: '', label: 'No custom stage (Clear)' },
                ...pipelineStages.map(s => ({ value: s.id, label: s.name }))
              ]}
              value={stageValue}
              onChange={(e) => setStageValue(e.target.value)}
            />
          )}

          {modalType === 'priority' && (
            <Select
              label="New Priority"
              options={priorityOptions}
              value={priorityValue}
              onChange={(e) => setPriorityValue(e.target.value)}
            />
          )}

          {(modalType === 'tags_add' || modalType === 'tags_remove') && (
            <Input
              label={modalType === 'tags_add' ? 'Tags to Add (comma separated)' : 'Tags to Remove (comma separated)'}
              value={tagsValue}
              onChange={(e) => setTagsValue(e.target.value)}
              placeholder="e.g. follow-up, client, VIP"
            />
          )}

          {modalType === 'next_action' && (
            <>
              <Input
                label="Next Action"
                value={nextActionType}
                onChange={(e) => setNextActionType(e.target.value)}
                placeholder="e.g. Send email"
              />
              <Input
                label="Date"
                type="date"
                value={nextActionDate}
                onChange={(e) => setNextActionDate(e.target.value)}
              />
            </>
          )}

          {modalType === 'owner' && (
            <Select
              label="Contact owner"
              options={[
                { value: '', label: 'Unassigned' },
                ...members.map(member => ({
                  value: member.user_id,
                  label: member.display_name || member.email,
                })),
              ]}
              value={ownerId}
              onChange={(e) => setOwnerId(e.target.value)}
            />
          )}

          <div className="flex justify-end gap-2 mt-6">
            <Button variant="secondary" onClick={() => setModalType(null)}>Cancel</Button>
            <Button
              disabled={loading}
              onClick={() => {
                if (modalType === 'stage') handleBulkAction('set_stage', { stage_id: stageValue || null })
                if (modalType === 'priority') handleBulkAction('set_priority', { priority: priorityValue })
                if (modalType === 'tags_add') handleBulkAction('add_tags', { tags: tagsValue.split(',').map(t => t.trim()).filter(Boolean) })
                if (modalType === 'tags_remove') handleBulkAction('remove_tags', { tags: tagsValue.split(',').map(t => t.trim()).filter(Boolean) })
                if (modalType === 'next_action') handleBulkAction('set_next_action', { next_action_type: nextActionType || null, next_action_date: nextActionDate || null })
                if (modalType === 'owner') handleBulkAction('set_owner', { owner_id: ownerId || null })
              }}
            >
              {loading ? 'Updating...' : 'Confirm'}
            </Button>
          </div>
        </div>
      </Modal>
    )
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 p-4 z-40">
      <div className="max-w-7xl mx-auto bg-gray-900 shadow-lg rounded-xl text-white px-6 py-4 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <span className="font-semibold text-lg">{selectedIds.length} selected</span>
          <button onClick={onClearSelection} className="text-gray-400 hover:text-white text-sm underline">
            Clear selection
          </button>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleBulkAction('set_favorite', { is_favorite: true })}>★ Favourite</Button>
          <Button variant="secondary" size="sm" onClick={() => handleBulkAction('set_favorite', { is_favorite: false })}>☆ Unfavourite</Button>
          <Button variant="secondary" size="sm" onClick={() => setModalType('priority')}>Priority</Button>
          <Button variant="secondary" size="sm" onClick={() => setModalType('stage')}>Stage</Button>
          <Button variant="secondary" size="sm" onClick={() => setModalType('tags_add')}>+ Tags</Button>
          <Button variant="secondary" size="sm" onClick={() => setModalType('tags_remove')}>- Tags</Button>
          <Button variant="secondary" size="sm" onClick={() => setModalType('next_action')}>Next Action</Button>
          <Button variant="secondary" size="sm" onClick={() => setModalType('owner')}>Owner</Button>
          <Button 
            size="sm" 
            className="bg-red-600 hover:bg-red-700 text-white border-none"
            onClick={() => {
              if (window.confirm(`Are you sure you want to archive ${selectedIds.length} people?`)) {
                handleBulkAction('archive', {})
              }
            }}
          >
            Archive
          </Button>
        </div>
      </div>
      {renderModal()}
    </div>
  )
}
