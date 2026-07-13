import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { exportsApi, peopleApi, pipelineStagesApi } from '../api/httpClient'
import { downloadCsvBlob } from '../api/csvDownload'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Select } from '../components/common/Select'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Skeleton } from '../components/common/Skeleton'
import { BulkActionBar } from '../features/bulk-actions/BulkActionBar'
import { SavedViewsDropdown } from '../features/saved-views/SavedViewsDropdown'
import { SaveViewModal } from '../features/saved-views/SaveViewModal'
import { DuplicatesModal } from '../features/duplicates/DuplicatesModal'
import { savedViewsApi } from '../api/httpClient'

interface Person {
  id: string
  name: string
  first_name: string | null
  last_name: string | null
  company: string | null
  role: string | null
  location: string | null
  email: string | null
  phone_number: string | null
  premium: boolean | null
  company_website: string | null
  processed_at: string | null
  processed_at_millis: number | null
  invite_accepted_at: string | null
  invite_accepted_at_millis: number | null
  is_favorite: boolean
  favorite_notes: string | null
  linkedin_url: string
  stage: string
  stage_id: string | null
  pipeline_stage: any | null
  priority: string
  status: string
  next_action_type: string | null
  next_action_date: string | null
  tags: { id: string; name: string; color: string | null }[]
}

type SortOrder = 'asc' | 'desc'
type SortKey =
  | 'linkedin_url' | 'first_name' | 'last_name' | 'company' | 'role' | 'email'
  | 'phone_number' | 'premium' | 'location' | 'company_website' | 'processed_at'
  | 'processed_at_millis' | 'invite_accepted_at' | 'invite_accepted_at_millis'
  | 'is_favorite' | 'favorite_notes'

interface PeopleFilters {
  search: string
  company: string
  role: string
  email: string
  location: string
  premium: string
  favorite: string
  favoriteNotes: string
  processedFrom: string
  processedTo: string
  stage: string
  priority: string
  deleted: boolean
}

const emptyFilters: PeopleFilters = {
  search: '',
  company: '',
  role: '',
  email: '',
  location: '',
  premium: '',
  favorite: '',
  favoriteNotes: '',
  processedFrom: '',
  processedTo: '',
  stage: '',
  priority: '',
  deleted: false,
}

const csvColumns: { label: string; key: SortKey | 'tags' | 'stage' }[] = [
  { label: 'Tags', key: 'tags' },
  { label: 'Favourite', key: 'is_favorite' },
  { label: 'Favourite notes', key: 'favorite_notes' },
  { label: 'Stage', key: 'stage' },
  { label: 'Link', key: 'linkedin_url' },
  { label: 'First name', key: 'first_name' },
  { label: 'Last name', key: 'last_name' },
  { label: 'Company', key: 'company' },
  { label: 'Position', key: 'role' },
  { label: 'Email', key: 'email' },
  { label: 'Phone number', key: 'phone_number' },
  { label: 'Premium', key: 'premium' },
  { label: 'Location', key: 'location' },
  { label: 'Company website', key: 'company_website' },
  { label: 'Processed at', key: 'processed_at' },
  { label: 'Processed at millis', key: 'processed_at_millis' },
  { label: 'Invite accepted at', key: 'invite_accepted_at' },
  { label: 'Invite accepted at millis', key: 'invite_accepted_at_millis' },
]

const priorityOptions = [
  { value: '', label: 'All Priorities' },
  { value: 'A', label: 'A - High' },
  { value: 'B', label: 'B - Medium' },
  { value: 'C', label: 'C - Low' },
]

const premiumOptions = [
  { value: '', label: 'All' },
  { value: 'true', label: 'Premium' },
  { value: 'false', label: 'Not premium' },
]

const favoriteOptions = [
  { value: '', label: 'All people' },
  { value: 'true', label: 'Favourites only' },
  { value: 'false', label: 'Not favourites' },
]

function octopusDate(value: string | null) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(new Date(value))
}

function octopusLink(value: string) {
  return `https://${value.replace(/^https?:\/\//, '').replace(/\/$/, '')}/`
}

export function PeopleListPage() {
  const navigate = useNavigate()
  const { currentWorkspace } = useWorkspaceStore()
  const [people, setPeople] = useState<Person[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [selectedPersonIds, setSelectedPersonIds] = useState<string[]>([])
  
  const [saveViewOpen, setSaveViewOpen] = useState(false)
  const [duplicatesOpen, setDuplicatesOpen] = useState(false)
  const [savedViewsRefreshTrigger, setSavedViewsRefreshTrigger] = useState(0)
  const [pipelineStages, setPipelineStages] = useState<any[]>([])
  
  const [searchParams] = useSearchParams()
  const viewParam = searchParams.get('view')

  const initialFilters = { ...emptyFilters }
  if (viewParam === 'archived') {
    initialFilters.stage = 'archived'
  } else if (viewParam === 'trash') {
    initialFilters.deleted = true
  }

  const [filterDraft, setFilterDraft] = useState<PeopleFilters>(initialFilters)
  const [filters, setFilters] = useState<PeopleFilters>(initialFilters)
  const [sortBy, setSortBy] = useState<SortKey>('processed_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  useEffect(() => {
    const newFilters = { ...emptyFilters }
    if (viewParam === 'archived') {
      newFilters.stage = 'archived'
    } else if (viewParam === 'trash') {
      newFilters.deleted = true
    }
    setFilterDraft(newFilters)
    setFilters(newFilters)
    setPage(1)
  }, [viewParam])

  const fetchPeople = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot PeopleList]', 'Loading people', {
      workspaceId: currentWorkspace.id.slice(-8),
      page,
      hasSearch: Boolean(filters.search),
      sortBy,
      sortOrder,
    })
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {
        workspace_id: currentWorkspace.id,
        page: String(page),
        limit: '20',
        sort_by: sortBy,
        sort_order: sortOrder,
      }
      if (filters.search) params.search = filters.search
      if (filters.company) params.company = filters.company
      if (filters.role) params.role = filters.role
      if (filters.email) params.email = filters.email
      if (filters.location) params.location = filters.location
      if (filters.premium) params.premium = filters.premium
      if (filters.favorite) params.favorite = filters.favorite
      if (filters.favoriteNotes) params.favorite_notes = filters.favoriteNotes
      if (filters.processedFrom) params.processed_from = `${filters.processedFrom}T00:00:00.000Z`
      if (filters.processedTo) params.processed_to = `${filters.processedTo}T23:59:59.999Z`
      if (filters.stage) params.stage = filters.stage
      if (filters.priority) params.priority = filters.priority
      if (filters.deleted) params.include_deleted = 'true'

      const [response, stagesResponse] = await Promise.all([
        peopleApi.list(params),
        pipelineStagesApi.list(currentWorkspace.id)
      ])
      
      setPipelineStages(stagesResponse)
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
  }, [currentWorkspace, page, filters, sortBy, sortOrder])

  const applyFilters = () => {
    setPage(1)
    setFilters(filterDraft)
  }

  const clearFilters = () => {
    setFilterDraft(emptyFilters)
    setFilters(emptyFilters)
    setPage(1)
  }

  const toggleSelectAll = () => {
    if (people.length === 0) return
    const allOnPageAreSelected = people.every((p) => selectedPersonIds.includes(p.id))
    if (allOnPageAreSelected) {
      setSelectedPersonIds((prev) => prev.filter((id) => !people.find((p) => p.id === id)))
    } else {
      const idsToAdd = people.filter((p) => !selectedPersonIds.includes(p.id)).map((p) => p.id)
      setSelectedPersonIds((prev) => [...prev, ...idsToAdd])
    }
  }

  const toggleSelectPerson = (id: string) => {
    setSelectedPersonIds((prev) =>
      prev.includes(id) ? prev.filter((pId) => pId !== id) : [...prev, id]
    )
  }

  const handleSort = (key: SortKey) => {
    setPage(1)
    if (sortBy === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(key)
      setSortOrder('desc')
    }
  }

  const handleToggleFavorite = async (personId: string, currentStatus: boolean, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!currentWorkspace) return
    try {
      await peopleApi.update(personId, { is_favorite: !currentStatus }, currentWorkspace.id)
      setPeople((prev) => prev.map((p) => p.id === personId ? { ...p, is_favorite: !currentStatus } : p))
    } catch (err) {
      console.error('Failed to toggle favorite', err)
    }
  }

  const handleRestore = async (personId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!currentWorkspace) return
    try {
      await peopleApi.restore(personId, currentWorkspace.id)
      setPeople((prev) => prev.filter((p) => p.id !== personId))
    } catch (err) {
      console.error('Failed to restore person', err)
    }
  }

  const handleExport = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot PeopleList]', 'Exporting people CSV', {
      workspaceId: currentWorkspace.id.slice(-8),
      stageFilter: filters.stage,
      priorityFilter: filters.priority,
    })
    setExporting(true)
    setError(null)
    try {
      const params: Record<string, string> = {
        workspace_id: currentWorkspace.id,
      }
      if (filters.stage) params.stage = filters.stage
      if (filters.priority) params.priority = filters.priority
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

  const handleApplySavedView = (newFilters: any, newSortBy: string, newSortOrder: string) => {
    setFilterDraft(newFilters)
    setFilters(newFilters)
    setSortBy(newSortBy as SortKey)
    setSortOrder(newSortOrder as 'asc' | 'desc')
    setPage(1)
  }

  const handleSaveView = async (name: string) => {
    if (!currentWorkspace) return
    await savedViewsApi.create({
      name,
      filters,
      sort_by: sortBy,
      sort_order: sortOrder
    }, currentWorkspace.id)
    setSavedViewsRefreshTrigger(prev => prev + 1)
  }

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
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-gray-900">People</h1>
            <SavedViewsDropdown 
              workspaceId={currentWorkspace.id} 
              onSelectView={handleApplySavedView} 
              refreshTrigger={savedViewsRefreshTrigger} 
            />
          </div>
          <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={handleExport} disabled={exporting}>
            {exporting ? 'Exporting...' : 'Export CSV'}
          </Button>
          <Button variant="secondary" onClick={() => setDuplicatesOpen(true)}>
            Duplicates
          </Button>
          <Button onClick={() => navigate('/people/new')}>Add Person</Button>
        </div>
      </div>

      {/* Filters */}
      <div className="mt-6 bg-white shadow rounded-lg p-4">
        <form onSubmit={(e) => { e.preventDefault(); applyFilters(); }} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="md:col-span-2">
            <Input
              label="Search"
              placeholder="Search by name, company, role, email, or location..."
              value={filterDraft.search}
              onChange={(e) => setFilterDraft({ ...filterDraft, search: e.target.value })}
            />
          </div>
          <Input label="Company" value={filterDraft.company} onChange={(e) => setFilterDraft({ ...filterDraft, company: e.target.value })} />
          <Input label="Position" value={filterDraft.role} onChange={(e) => setFilterDraft({ ...filterDraft, role: e.target.value })} />
          <Input label="Email" value={filterDraft.email} onChange={(e) => setFilterDraft({ ...filterDraft, email: e.target.value })} />
          <Input label="Location" value={filterDraft.location} onChange={(e) => setFilterDraft({ ...filterDraft, location: e.target.value })} />
          <Select
            label="Premium"
            options={premiumOptions}
            value={filterDraft.premium}
            onChange={(e) => setFilterDraft({ ...filterDraft, premium: e.target.value })}
          />
          <Select
            label="Favourite"
            options={favoriteOptions}
            value={filterDraft.favorite}
            onChange={(e) => setFilterDraft({ ...filterDraft, favorite: e.target.value })}
          />
          <Input
            label="Favourite notes contain"
            value={filterDraft.favoriteNotes}
            onChange={(e) => setFilterDraft({ ...filterDraft, favoriteNotes: e.target.value })}
          />
          <Input label="Processed from" type="date" value={filterDraft.processedFrom} onChange={(e) => setFilterDraft({ ...filterDraft, processedFrom: e.target.value })} />
          <Input label="Processed to" type="date" value={filterDraft.processedTo} onChange={(e) => setFilterDraft({ ...filterDraft, processedTo: e.target.value })} />
          <div>
            <Select
              label="Stage"
              options={[
                { value: '', label: 'All Stages' },
                ...pipelineStages.map(s => ({ value: s.id, label: s.name })),
                { value: 'archived', label: 'Archived (Legacy)' }
              ]}
              value={filterDraft.stage}
              onChange={(e) => setFilterDraft({ ...filterDraft, stage: e.target.value })}
            />
          </div>
          <div>
            <Select
              label="Priority"
              options={priorityOptions}
              value={filterDraft.priority}
              onChange={(e) => setFilterDraft({ ...filterDraft, priority: e.target.value })}
            />
          </div>
          <div className="flex items-end gap-2">
                <Button variant="secondary" onClick={clearFilters}>
                  Clear
                </Button>
                <Button variant="secondary" onClick={() => setSaveViewOpen(true)}>
                  Save View
                </Button>
                <Button onClick={applyFilters}>Apply Filters</Button>
              </div>
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
          <div className="overflow-x-auto bg-white shadow sm:rounded-lg">
            <table className="min-w-max divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left w-10">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      checked={people.length > 0 && people.every(p => selectedPersonIds.includes(p.id))}
                      onChange={toggleSelectAll}
                    />
                  </th>
                  {csvColumns.map((column) => (
                    <th key={column.key} className="whitespace-nowrap px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      {column.key === 'tags' || column.key === 'stage' ? (
                        <span>{column.label}</span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleSort(column.key as SortKey)}
                          className="inline-flex items-center gap-1 hover:text-gray-900"
                          aria-label={`Sort by ${column.label}`}
                        >
                          {column.label}
                          <span aria-hidden="true">{sortBy === column.key ? (sortOrder === 'asc' ? '▲' : '▼') : '↕'}</span>
                        </button>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {people.map((person) => (
                  <tr
                    key={person.id}
                    onClick={() => navigate(`/people/${person.id}`)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        navigate(`/people/${person.id}`)
                      }
                    }}
                    role="link"
                    tabIndex={0}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-4 py-3 w-10" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        checked={selectedPersonIds.includes(person.id)}
                        onChange={() => toggleSelectPerson(person.id)}
                      />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {person.tags?.map(t => (
                          <span key={t.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {t.name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td 
                      className="whitespace-nowrap px-4 py-3 text-lg cursor-pointer hover:text-yellow-500" 
                      aria-label={person.is_favorite ? 'Favourite status: yes' : 'Favourite status: no'}
                      onClick={(e) => filters.deleted ? undefined : handleToggleFavorite(person.id, person.is_favorite, e)}
                    >
                      {filters.deleted ? (
                        <button
                          onClick={(e) => handleRestore(person.id, e)}
                          className="text-sm px-2 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded"
                        >
                          Restore
                        </button>
                      ) : (
                        <span className={person.is_favorite ? "text-yellow-400" : "text-gray-300"}>
                          {person.is_favorite ? '★' : '☆'}
                        </span>
                      )}
                    </td>
                    <td className="max-w-xs truncate px-4 py-3 text-gray-600" title={person.favorite_notes || ''}>{person.favorite_notes || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium">
                      {person.pipeline_stage ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                          {person.pipeline_stage.name}
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-50 text-gray-600 border border-gray-200">
                          {person.stage === 'archived' ? 'Archived (Legacy)' : person.stage}
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-blue-600 underline">{octopusLink(person.linkedin_url)}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-900">{person.first_name || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-900">{person.last_name || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.company || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.role || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.email || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.phone_number || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.premium === null ? '' : person.premium ? 'TRUE' : 'FALSE'}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.location || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{person.company_website || ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{octopusDate(person.processed_at)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-gray-600">{person.processed_at_millis ?? ''}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{octopusDate(person.invite_accepted_at)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-gray-600">{person.invite_accepted_at_millis ?? ''}</td>
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
        <BulkActionBar
          workspaceId={currentWorkspace.id}
          selectedIds={selectedPersonIds}
          onClearSelection={() => setSelectedPersonIds([])}
          onSuccess={() => {
            setSelectedPersonIds([])
            fetchPeople()
          }}
          pipelineStages={pipelineStages}
        />
      )}

      <SaveViewModal
        isOpen={saveViewOpen}
        onClose={() => setSaveViewOpen(false)}
        onSave={handleSaveView}
      />

      {duplicatesOpen && (
        <DuplicatesModal
          onClose={() => setDuplicatesOpen(false)}
          onMergeComplete={() => fetchPeople()}
        />
      )}
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/PeopleListPage.tsx')
