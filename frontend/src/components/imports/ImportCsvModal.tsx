import { useState } from 'react'
import { importsApi } from '../../api/httpClient'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { Modal } from '../common/Modal'
import { Select } from '../common/Select'

interface ImportCsvModalProps {
  isOpen: boolean
  workspaceId: string
  onClose: () => void
  onImported: () => void
}

const actionOptions = [
  { value: 'invite_sent', label: 'Invite Sent' },
  { value: 'saved_for_later', label: 'Saved for Later' },
  { value: 'already_connected', label: 'Already Connected' },
  { value: 'accepted_no_message', label: 'Accepted, No Message' },
  { value: 'first_message_sent', label: 'First Message Sent' },
  { value: 'custom_from_csv', label: 'Custom from CSV Column' },
]

const priorityOptions = [
  { value: 'A', label: 'A - High' },
  { value: 'B', label: 'B - Medium' },
  { value: 'C', label: 'C - Low' },
]

export function ImportCsvModal({ isOpen, workspaceId, onClose, onImported }: ImportCsvModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [defaultAction, setDefaultAction] = useState('invite_sent')
  const [defaultPriority, setDefaultPriority] = useState('B')
  const [preview, setPreview] = useState<any | null>(null)
  const [summary, setSummary] = useState<any | null>(null)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reset = () => {
    setFile(null)
    setDefaultAction('invite_sent')
    setDefaultPriority('B')
    setPreview(null)
    setSummary(null)
    setError(null)
    setImporting(false)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handlePreview = async () => {
    if (!file) {
      console.warn('[NetworkPilot ImportCsv]', 'Preview requested without a file', {
        workspaceId: workspaceId.slice(-8),
      })
      setError('Choose a CSV file first.')
      return
    }

    console.info('[NetworkPilot ImportCsv]', 'Previewing CSV import', {
      workspaceId: workspaceId.slice(-8),
      filename: file.name,
      defaultAction,
      defaultPriority,
      byteSize: file.size,
    })
    setImporting(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('workspace_id', workspaceId)
      formData.append('file', file)
      formData.append('default_initial_action_type', defaultAction)
      formData.append('duplicate_strategy', 'skip')
      formData.append('default_priority', defaultPriority)
      const result = await importsApi.previewPeople(formData)
      setPreview(result)
      setSummary(null)
      console.info('[NetworkPilot ImportCsv]', 'CSV import preview loaded', {
        workspaceId: workspaceId.slice(-8),
        totalRows: result.summary.total_rows,
        validRows: result.summary.valid_rows,
        invalidRows: result.summary.invalid_rows,
      })
    } catch (err: any) {
      console.error('[NetworkPilot ImportCsv]', 'CSV import preview failed', {
        workspaceId: workspaceId.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Preview failed')
    } finally {
      setImporting(false)
    }
  }

  const handleCommit = async () => {
    if (!preview) return

    console.info('[NetworkPilot ImportCsv]', 'Committing CSV import', {
      workspaceId: workspaceId.slice(-8),
      importBatchId: preview.import_batch_id?.slice(-8) || null,
    })
    setImporting(true)
    setError(null)
    try {
      const rows = preview.rows
        .filter((row: any) => row.status === 'valid')
        .map((row: any) => ({
          name: row.name,
          first_name: row.first_name,
          last_name: row.last_name,
          linkedin_url: row.linkedin_url,
          current_role: row.current_role,
          current_company: row.current_company,
          location: row.location,
          email: row.email,
          phone_number: row.phone_number,
          premium: row.premium,
          company_website: row.company_website,
          processed_at: row.processed_at,
          processed_at_millis: row.processed_at_millis,
          invite_accepted_at: row.invite_accepted_at,
          invite_accepted_at_millis: row.invite_accepted_at_millis,
          priority: row.priority,
          connection_note: row.connection_note,
          conversation_context: row.conversation_context,
          tags: row.tags,
          initial_action_type: row.initial_action_type,
          next_action_date: row.next_action_date,
        }))

      const result = await importsApi.commitPeople({
        workspace_id: workspaceId,
        default_initial_action_type: defaultAction,
        duplicate_strategy: 'skip',
        default_priority: defaultPriority,
        import_batch_id: preview.import_batch_id,
        rows,
      })
      setSummary(result.summary)
      setPreview(null)
      onImported()
      console.info('[NetworkPilot ImportCsv]', 'CSV import committed', {
        workspaceId: workspaceId.slice(-8),
        created: result.summary.created_count,
        failed: result.summary.failed_count,
      })
    } catch (err: any) {
      console.error('[NetworkPilot ImportCsv]', 'CSV import commit failed', {
        workspaceId: workspaceId.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Import failed')
    } finally {
      setImporting(false)
    }
  }

  const downloadErrorReport = () => {
    if (!preview) return
    console.info('[NetworkPilot ImportCsv]', 'Downloading import error report', {
      workspaceId: workspaceId.slice(-8),
      importBatchId: preview.import_batch_id?.slice(-8) || null,
    })
    const rows = preview.rows.filter((row: any) => row.status !== 'valid')
    const csv = [
      'row_number,status,name,linkedin_url,errors',
      ...rows.map((row: any) => [
        row.row_number,
        row.status,
        JSON.stringify(row.name || ''),
        JSON.stringify(row.linkedin_url || ''),
        JSON.stringify((row.errors || []).join('; ')),
      ].join(',')),
    ].join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'networkpilot-import-errors.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  const validRows = preview?.rows?.filter((row: any) => row.status === 'valid') || []
  const issueRows = preview?.rows?.filter((row: any) => row.status !== 'valid') || []

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Import CSV" size="xl">
      <div className="space-y-5">
        <div className="grid gap-4 md:grid-cols-3">
          <Input
            label="CSV File"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
          <Select
            label="Default Initial Action"
            value={defaultAction}
            onChange={(event) => setDefaultAction(event.target.value)}
            options={actionOptions}
          />
          <Select
            label="Default Priority"
            value={defaultPriority}
            onChange={(event) => setDefaultPriority(event.target.value)}
            options={priorityOptions}
          />
        </div>

        {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        {preview && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Summary label="Total" value={preview.summary.total_rows} />
              <Summary label="Valid" value={preview.summary.valid_rows} />
              <Summary label="Duplicates" value={preview.summary.duplicate_rows} />
              <Summary label="Invalid" value={preview.summary.invalid_rows} />
            </div>

            <div className="max-h-80 overflow-auto rounded-md border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Row</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Status</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Name</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">LinkedIn URL</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Errors</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {preview.rows.map((row: any) => (
                    <tr key={row.row_number}>
                      <td className="px-3 py-2 text-gray-600">{row.row_number}</td>
                      <td className="px-3 py-2 text-gray-900">{row.status}</td>
                      <td className="px-3 py-2 text-gray-900">{row.name || '-'}</td>
                      <td className="px-3 py-2 text-gray-600">{row.normalized_profile_url || row.linkedin_url || '-'}</td>
                      <td className="px-3 py-2 text-red-600">{(row.errors || []).join('; ') || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {summary && (
          <div className="rounded-md bg-green-50 p-4 text-sm text-green-800">
            Created {summary.created_count} records. Skipped {summary.skipped_duplicates} duplicates. Failed {summary.failed_count} rows.
          </div>
        )}

        <div className="flex flex-wrap justify-end gap-3">
          {issueRows.length > 0 && (
            <Button type="button" variant="secondary" onClick={downloadErrorReport}>
              Download Error Report
            </Button>
          )}
          <Button type="button" variant="secondary" onClick={handleClose}>
            Close
          </Button>
          {!preview ? (
            <Button type="button" onClick={handlePreview} disabled={importing}>
              {importing ? 'Previewing...' : 'Preview Import'}
            </Button>
          ) : (
            <Button type="button" onClick={handleCommit} disabled={importing || validRows.length === 0}>
              {importing ? 'Importing...' : `Confirm Import (${validRows.length})`}
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-gray-200 p-3">
      <div className="text-xs font-medium uppercase text-gray-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-gray-900">{value}</div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/components/imports/ImportCsvModal.tsx')
