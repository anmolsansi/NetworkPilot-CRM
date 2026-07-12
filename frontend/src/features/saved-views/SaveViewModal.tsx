import { useState } from 'react'
import { Modal } from '../../components/common/Modal'
import { Input } from '../../components/common/Input'
import { Button } from '../../components/common/Button'
import { ErrorAlert } from '../../components/common/ErrorAlert'

interface SaveViewModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (name: string) => Promise<void>
  initialName?: string
}

export function SaveViewModal({ isOpen, onClose, onSave, initialName = '' }: SaveViewModalProps) {
  const [name, setName] = useState(initialName)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Name is required')
      return
    }

    setLoading(true)
    setError(null)
    try {
      await onSave(name.trim())
      setName('')
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to save view')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Save View">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <ErrorAlert message={error} onRetry={() => setError(null)} />}
        
        <Input
          label="View Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Hot Leads, Software Engineers"
          autoFocus
        />

        <div className="flex justify-end gap-2 mt-6">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? 'Saving...' : 'Save View'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
