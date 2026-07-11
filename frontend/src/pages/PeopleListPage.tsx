import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { exportsApi, peopleApi } from '../api/httpClient'
import { downloadCsvBlob } from '../api/csvDownload'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Select } from '../components/common/Select'
import { Badge } from '../components/common/Badge'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'
import { ImportCsvModal } from '../components/imports/ImportCsvModal'

interface Person {
  id: string
  name: string
  company: string | null
  role: string | null
  location: string | null
  email: string | null
  linkedin_url: string
  stage: string
  priority: string
  status: string
  next_action_type: string | null
  next_action_date: string | null
}

interface PeopleResponse {
  items: Person[]
  total: number
  page: number
  limit: number
}

const stageOptions = [
  { value: '', label: 'All Stages' },
  { value: 'invite_sent', label: 'Invite Sent' },
  { value: 'invite_pending', label: 'Invite Pending' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'waiting_for_reply', label: 'Waiting for Reply' },
  { value: 'replied', label: 'Replied' },
  { value: 'archived', label: 'Archived' },
]

const priorityOptions = [
  { value: '', label: 'All Priorities' },
  { value: 'A', label: 'A - High' },
  { value: 'B', label: 'B - Medium' },
  { value: 'C', label: 'C - Low' },
]

const priorityVariant = {
  A: 'danger',
  B: 'warning',
  C: 'default',
} as const

export function PeopleListPage() {
  const navigate = useNavigate()
  const { currentWorkspace } = useWorkspaceStore()
  const [people, setPeople] = useState<Person[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [importOpen, setImportOpen] = useState(false)
  const [exporting, setExporting] = useState(false)

  // Filters
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')

  const fetchPeople = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot PeopleList]', 'Loading people', {
      workspaceId: currentWorkspace.id.slice(-8),
      page,
      hasSearch: Boolean(search),
      stageFilter,
      priorityFilter,
    })
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {
        workspace_id: currentWorkspace.id,
        page: String(page),
        limit: '20',
      }
      if (search) params.search = search
      if (stageFilter) params.stage = stageFilter
      if (priorityFilter) params.priority = priorityFilter

      const response: PeopleResponse = await peopleApi.list(params)
      setPeople(response.items)
      setTotal(response.total)
      console.info('[NetworkPilot PeopleList]', 'People loaded', {
        workspaceId: currentWorkspace.id.slice(-8),
        count: response.items.length,
        total: response.total,
      })
    } catch (err: any) {
      console.error('[NetworkPilot PeopleList]', 'Failed to load people', {
        workspaceId: currentWorkspace.id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to load people')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPeople()
  }, [currentWorkspace, page, stageFilter, priorityFilter])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchPeople()
  }

  const handleExport = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot PeopleList]', 'Exporting people CSV', {
      workspaceId: currentWorkspace.id.slice(-8),
      stageFilter,
      priorityFilter,
    })
    setExporting(true)
    setError(null)
    try {
      const params: Record<string, string> = {
        workspace_id: currentWorkspace.id,
      }
      if (stageFilter) params.stage = stageFilter
      if (priorityFilter) params.priority = priorityFilter
      const blob = await exportsApi.peopleCsv(params)
      downloadCsvBlob(blob, 'networkpilot-people-export.csv')
      console.info('[NetworkPilot PeopleList]', 'People CSV exported', {
        workspaceId: currentWorkspace.id.slice(-8),
        byteSize: blob.size,
      })
    } catch (err: any) {
      console.error('[NetworkPilot PeopleList]', 'People CSV export failed', {
        workspaceId: currentWorkspace.id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to export people')
    } finally {
      setExporting(false)
    }
  }

  const totalPages = Math.ceil(total / 20)

  if (!currentWorkspace) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">People</h1>
        <EmptyState
          title="Create a workspace first"
          description="Create a workspace before adding people, importing CSVs, or exporting contacts."
          action={<Button onClick={() => navigate('/')}>Go to Dashboard</Button>}
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">People</h1>
        <div className="mt-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">People</h1>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setImportOpen(true)}>Import CSV</Button>
          <Button variant="secondary" onClick={handleExport} disabled={exporting}>
            {exporting ? 'Exporting...' : 'Export CSV'}
          </Button>
          <Button onClick={() => navigate('/people/new')}>Add Person</Button>
        </div>
      </div>

      {/* Filters */}
      <div className="mt-6 bg-white shadow rounded-lg p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Search by name, company, role, email, or location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="w-48">
            <Select
              options={stageOptions}
              value={stageFilter}
              onChange={(e) => { setStageFilter(e.target.value); setPage(1) }}
            />
          </div>
          <div className="w-48">
            <Select
              options={priorityOptions}
              value={priorityFilter}
              onChange={(e) => { setPriorityFilter(e.target.value); setPage(1) }}
            />
          </div>
          <Button type="submit" variant="secondary">Search</Button>
        </form>
      </div>

      {error && (
        <div className="mt-4">
          <ErrorAlert message={error} onRetry={fetchPeople} />
        </div>
      )}

      {/* People List */}
      <div className="mt-6">
        {people.length === 0 ? (
          <EmptyState
            title="No people found"
            description="Try adjusting your filters or add a new person."
            action={<Button onClick={() => navigate('/people/new')}>Add Person</Button>}
          />
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stage</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Next Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {people.map((person) => (
                  <tr
                    key={person.id}
                    onClick={() => navigate(`/people/${person.id}`)}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{person.name}</div>
                      {person.role && (
                        <div className="text-sm text-gray-500">{person.role}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {person.company || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div>{person.email || '-'}</div>
                      {person.location && <div className="text-xs text-gray-400">{person.location}</div>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant="primary">{person.stage.replace(/_/g, ' ')}</Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={priorityVariant[person.priority as keyof typeof priorityVariant]}>
                        {person.priority}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {person.next_action_type ? (
                        <span>
                          {person.next_action_type.replace(/_/g, ' ')}
                          {person.next_action_date && (
                            <span className="ml-1 text-gray-400">
                              ({new Date(person.next_action_date).toLocaleDateString()})
                            </span>
                          )}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-700">
              Showing page {page} of {totalPages} ({total} total)
            </p>
            <div className="flex space-x-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {currentWorkspace && (
        <ImportCsvModal
          isOpen={importOpen}
          workspaceId={currentWorkspace.id}
          onClose={() => setImportOpen(false)}
          onImported={fetchPeople}
        />
      )}
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/PeopleListPage.tsx')
