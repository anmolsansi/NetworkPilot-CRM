import { useCallback, useEffect, useState, useRef } from 'react'
import { importsApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { Button } from '../../components/common/Button'
import { Select } from '../../components/common/Select'
import { useNavigate } from 'react-router-dom'

export function ImportsPage() {
  const { currentWorkspace } = useWorkspaceStore()
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [duplicateStrategy, setDuplicateStrategy] = useState<'skip' | 'update'>('skip')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const fetchJobs = useCallback(async () => {
    if (!currentWorkspace) return
    try {
      const data = await importsApi.list(currentWorkspace.id)
      setJobs(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [currentWorkspace])

  useEffect(() => {
    fetchJobs()
    // Poll for updates if any job is pending or processing
    const interval = setInterval(() => {
      setJobs((prevJobs) => {
        const hasActive = prevJobs.some(j => j.status === 'pending' || j.status === 'processing')
        if (hasActive) {
          fetchJobs()
        }
        return prevJobs
      })
    }, 5000)
    return () => clearInterval(interval)
  }, [fetchJobs])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !currentWorkspace) return
    const file = e.target.files[0]
    setUploading(true)
    try {
      await importsApi.commit(currentWorkspace.id, file, duplicateStrategy)
      fetchJobs()
    } catch (err) {
      console.error(err)
      alert("Failed to upload file")
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleRetry = async (jobId: string) => {
    if (!currentWorkspace) return
    try {
      await importsApi.retry(jobId, currentWorkspace.id)
      fetchJobs()
    } catch (err) {
      console.error(err)
      alert("Failed to retry job")
    }
  }

  const handleDownloadErrors = async (jobId: string) => {
    if (!currentWorkspace) return
    try {
      await importsApi.downloadErrors(jobId, currentWorkspace.id)
    } catch {
      alert('Failed to download the error report')
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/people')}>
            &larr; Back
          </Button>
          <h1 className="text-2xl font-bold">Import History</h1>
        </div>
        <div className="flex items-end gap-3">
          <Select
            label="Existing profiles"
            options={[
              { value: 'skip', label: 'Skip duplicates' },
              { value: 'update', label: 'Update matching profiles' },
            ]}
            value={duplicateStrategy}
            onChange={(event) => setDuplicateStrategy(event.target.value as 'skip' | 'update')}
          />
          <input
            type="file"
            accept=".csv"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileUpload}
          />
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            📥 {uploading ? 'Uploading...' : 'New Import'}
          </Button>
        </div>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="space-y-4">
          {jobs.length === 0 ? (
            <div className="text-center py-10 text-gray-500">No import history.</div>
          ) : (
            jobs.map(job => (
              <div key={job.id} className="bg-white border rounded-lg shadow-sm">
                <div className="px-4 py-3 border-b flex justify-between items-center bg-gray-50 rounded-t-lg">
                  <h3 className="text-lg font-medium">Import {new Date(job.created_at).toLocaleString()}</h3>
                  <span className={`px-2 py-1 rounded text-sm ${
                    job.status === 'completed' ? 'bg-green-100 text-green-800' :
                    job.status === 'failed' ? 'bg-red-100 text-red-800' :
                    job.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {job.status.toUpperCase()}
                  </span>
                </div>
                <div className="p-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-gray-600">
                        Progress: {job.processed_rows} / {job.total_rows || '?'} rows
                      </p>
                      {job.error_log && job.error_log.length > 0 && (
                        <p className="text-sm text-red-600 mt-1">
                          {job.error_log.length} errors encountered
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {job.error_log?.length > 0 && (
                        <Button variant="secondary" size="sm" onClick={() => handleDownloadErrors(job.id)}>
                          Download errors
                        </Button>
                      )}
                      {(job.status === 'failed' || (job.status === 'completed' && job.error_log?.length > 0)) && job.attempt_count < 3 && (
                        <Button variant="secondary" size="sm" onClick={() => handleRetry(job.id)}>
                          🔄 Retry
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
