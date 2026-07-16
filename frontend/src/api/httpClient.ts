import { supabase } from '../auth/supabaseClient'
import type { Tag } from '../types'

const API_VERSION_PREFIX = '/api/v1'
const API_LOG_PREFIX = '[NetworkPilot API]'

export const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL)

if (import.meta.env.VITE_API_BASE_URL && API_BASE_URL !== trimTrailingSlashes(import.meta.env.VITE_API_BASE_URL)) {
  console.info(API_LOG_PREFIX, 'Normalized API base URL', {
    configured: import.meta.env.VITE_API_BASE_URL,
    resolved: API_BASE_URL,
  })
}

export function resolveApiBaseUrl(configuredUrl?: string): string {
  const fallbackUrl = configuredUrl?.trim() || API_VERSION_PREFIX
  const normalizedUrl = trimTrailingSlashes(fallbackUrl)

  if (normalizedUrl.endsWith(API_VERSION_PREFIX)) return normalizedUrl
  if (normalizedUrl.endsWith('/api')) return `${normalizedUrl}/v1`
  if (normalizedUrl.startsWith('/')) return normalizedUrl

  try {
    const url = new URL(normalizedUrl)
    if (!url.pathname || url.pathname === '/') {
      return `${url.origin}${API_VERSION_PREFIX}`
    }
  } catch {
    console.warn(API_LOG_PREFIX, 'Using API base URL without URL normalization', {
      configured: configuredUrl,
      resolved: normalizedUrl,
    })
  }

  return normalizedUrl
}

function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, '')
}

async function getToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token || null
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getToken()
  const isFormData = options.body instanceof FormData

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const url = `${API_BASE_URL}${path}`
  const startedAt = Date.now()
  console.debug(API_LOG_PREFIX, 'Request', {
    method: options.method || 'GET',
    path,
    url,
    authenticated: Boolean(token),
  })

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    console.warn(API_LOG_PREFIX, 'Unauthorized response; signing out', {
      method: options.method || 'GET',
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
    })
    await supabase.auth.signOut()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    console.error(API_LOG_PREFIX, 'Request failed', {
      method: options.method || 'GET',
      path,
      url,
      status: response.status,
      durationMs: Date.now() - startedAt,
      error: errorData?.error || null,
    })
    throw {
      code: errorData?.error?.code || 'HTTP_ERROR',
      message: errorData?.error?.message || `Request failed with status ${response.status}`,
      details: errorData?.error?.details,
    }
  }

  if (response.status === 204) {
    console.debug(API_LOG_PREFIX, 'Request succeeded with no content', {
      method: options.method || 'GET',
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
    })
    return undefined as T
  }

  console.debug(API_LOG_PREFIX, 'Request succeeded', {
    method: options.method || 'GET',
    path,
    status: response.status,
    durationMs: Date.now() - startedAt,
  })
  return response.json()
}

async function requestBlob(path: string): Promise<Blob> {
  const token = await getToken()
  const headers: Record<string, string> = {}

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const url = `${API_BASE_URL}${path}`
  const startedAt = Date.now()
  console.debug(API_LOG_PREFIX, 'Blob request', {
    method: 'GET',
    path,
    url,
    authenticated: Boolean(token),
  })

  const response = await fetch(url, { headers })

  if (response.status === 401) {
    console.warn(API_LOG_PREFIX, 'Unauthorized blob response; signing out', {
      method: 'GET',
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
    })
    await supabase.auth.signOut()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    console.error(API_LOG_PREFIX, 'Blob request failed', {
      method: 'GET',
      path,
      url,
      status: response.status,
      durationMs: Date.now() - startedAt,
      error: errorData?.error || null,
    })
    throw {
      code: errorData?.error?.code || 'HTTP_ERROR',
      message: errorData?.error?.message || `Request failed with status ${response.status}`,
      details: errorData?.error?.details,
    }
  }

  const blob = await response.blob()
  console.debug(API_LOG_PREFIX, 'Blob request succeeded', {
    method: 'GET',
    path,
    status: response.status,
    durationMs: Date.now() - startedAt,
    byteSize: blob.size,
  })
  return blob
}

// User API
export const userApi = {
  getMe: () => request<any>('/me'),
}

// Workspace API
export const workspaceApi = {
  list: () => request<any[]>('/workspaces'),
  create: (data: any) => request<any>('/workspaces', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/workspaces/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
}

// Workspace Members API
export const workspaceMembersApi = {
  list: (workspaceId: string) => request<any[]>(`/workspaces/${workspaceId}/members`),
  getMe: (workspaceId: string) => request<any>(`/workspaces/${workspaceId}/members/me`),
  updateMe: (workspaceId: string, data: any) => request<any>(`/workspaces/${workspaceId}/members/me`, { method: 'PATCH', body: JSON.stringify(data) }),
}

// Workspace Invites API
export const workspaceInvitesApi = {
  list: (workspaceId: string) => request<any[]>(`/workspaces/${workspaceId}/invites`),
  create: (workspaceId: string, data: any) => request<any>(`/workspaces/${workspaceId}/invites`, { method: 'POST', body: JSON.stringify(data) }),
  delete: (workspaceId: string, inviteId: string) => request<void>(`/workspaces/${workspaceId}/invites/${inviteId}`, { method: 'DELETE' }),
}

// People API
export const peopleApi = {
  list: (params: Record<string, string>) => {
    const query = new URLSearchParams(params).toString()
    return request<any>(`/people?${query}`)
  },
  get: (id: string, workspaceId: string) =>
    request<any>(`/people/${id}?workspace_id=${workspaceId}`),
  create: (data: any, workspaceId: string) =>
    request<any>(`/people?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any, workspaceId: string) =>
    request<any>(`/people/${id}?workspace_id=${workspaceId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string, workspaceId: string) =>
    request<void>(`/people/${id}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
  snooze: (id: string, data: any, workspaceId: string) =>
    request<any>(`/people/${id}/snooze?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  archive: (id: string, data: any, workspaceId: string) =>
    request<any>(`/people/${id}/archive?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  restore: (id: string, workspaceId: string) =>
    request<any>(`/people/${id}/restore?workspace_id=${workspaceId}`, { method: 'POST' }),
  unarchive: (id: string, workspaceId: string) =>
    request<any>(`/people/${id}/unarchive?workspace_id=${workspaceId}`, { method: 'POST' }),
  bulkAction: (data: any) =>
    request<any>('/people/bulk-actions', { method: 'POST', body: JSON.stringify(data) }),
}

// --- Imports ---

export const importsApi = {
  preview: async (workspaceId: string, file: File): Promise<any> => {
    const formData = new FormData()
    formData.append('workspace_id', workspaceId)
    formData.append('file', file)
    return request<any>('/imports/people/preview', {
      method: 'POST',
      body: formData,
    })
  },

  commit: async (
    workspaceId: string,
    file: File,
    duplicateStrategy: 'skip' | 'update' = 'skip',
  ): Promise<any> => {
    const formData = new FormData()
    formData.append('workspace_id', workspaceId)
    formData.append('file', file)
    formData.append('duplicate_strategy', duplicateStrategy)
    return request<any>('/imports/people/commit', {
      method: 'POST',
      body: formData,
    })
  },

  list: async (workspaceId: string): Promise<any[]> => {
    return request<any[]>(`/imports?workspace_id=${workspaceId}`)
  },

  get: async (jobId: string, workspaceId: string): Promise<any> => {
    return request<any>(`/imports/${jobId}?workspace_id=${workspaceId}`)
  },

  retry: async (jobId: string, workspaceId: string): Promise<any> => {
    return request(`/imports/${jobId}/retry?workspace_id=${workspaceId}`, { method: 'POST' })
  },

  downloadErrors: async (jobId: string, workspaceId: string): Promise<void> => {
    const token = await getToken()
    const response = await fetch(
      `${API_BASE_URL}/imports/${jobId}/errors.csv?workspace_id=${workspaceId}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    )
    if (!response.ok) throw new Error('Failed to download import errors')
    const blobUrl = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `import-${jobId}-errors.csv`
    link.click()
    URL.revokeObjectURL(blobUrl)
  }
}

export const tagsApi = {
  list: (workspaceId: string) => {
    return request<Tag[]>(`/tags?workspace_id=${workspaceId}`)
  },
  create: (workspaceId: string, data: { name: string, color?: string }) => {
    return request<Tag>('/tags', {
      method: 'POST',
      body: JSON.stringify({ workspace_id: workspaceId, ...data })
    })
  },
  update: (tagId: string, workspaceId: string, data: { name?: string, color?: string | null }) => {
    return request<Tag>(`/tags/${tagId}?workspace_id=${workspaceId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  delete: (tagId: string, workspaceId: string) => {
    return request<void>(`/tags/${tagId}?workspace_id=${workspaceId}`, { method: 'DELETE' })
  }
}

export const notificationsApi = {
  list: (workspaceId: string) => request<any[]>(`/notifications?workspace_id=${workspaceId}`),
  markRead: (id: string, workspaceId: string) => request<any>(`/notifications/${id}/read?workspace_id=${workspaceId}`, { method: 'POST' }),
  markAllRead: (workspaceId: string) => request<void>(`/notifications/read-all?workspace_id=${workspaceId}`, { method: 'POST' }),
}

// Duplicates API
export const duplicatesApi = {
  find: (workspaceId: string) =>
    request<any[]>(`/people/duplicates?workspace_id=${workspaceId}`),
  merge: (data: any, workspaceId: string) =>
    request<any>(`/people/duplicates/merge?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
}

// CSV Export API
export const exportsApi = {
  peopleCsv: (params: Record<string, string>) => {
    const query = new URLSearchParams(params).toString()
    return requestBlob(`/exports/people.csv?${query}`)
  },
}

export const activitiesApi = {
  list: (personId: string, workspaceId: string, params: Record<string, string> = {}) => {
    const query = new URLSearchParams({ workspace_id: workspaceId, ...params }).toString()
    return request<any[]>(`/people/${personId}/activities?${query}`)
  },
  create: (personId: string, data: any, workspaceId: string) =>
    request<any>(`/people/${personId}/activities?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (activityId: string, data: any, workspaceId: string) =>
    request<any>(`/activities/${activityId}?workspace_id=${workspaceId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (activityId: string, workspaceId: string) =>
    request<void>(`/activities/${activityId}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
  restore: (activityId: string, workspaceId: string) =>
    request<any>(`/activities/${activityId}/restore?workspace_id=${workspaceId}`, { method: 'POST' }),
  uploadAttachment: (activityId: string, file: File, workspaceId: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return request<any>(`/activities/${activityId}/attachments?workspace_id=${workspaceId}`, {
      method: 'POST',
      body: formData,
    })
  },
  getAttachmentDownloadUrl: (attachmentId: string, workspaceId: string) =>
    request<{ url: string; expires_in: number }>(
      `/attachments/${attachmentId}/download-url?workspace_id=${workspaceId}`,
    ),
  deleteAttachment: (attachmentId: string, workspaceId: string) =>
    request<void>(`/attachments/${attachmentId}?workspace_id=${workspaceId}`, {
      method: 'DELETE',
    }),
}

export const tasksApi = {
  list: (workspaceId: string, params: Record<string, string> = {}) => {
    const query = new URLSearchParams({ workspace_id: workspaceId, ...params }).toString()
    return request<any>(`/tasks?${query}`)
  },
  create: (workspaceId: string, data: any) =>
    request<any>(`/tasks?workspace_id=${workspaceId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (workspaceId: string, taskId: string, data: any) =>
    request<any>(`/tasks/${taskId}?workspace_id=${workspaceId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  delete: (workspaceId: string, taskId: string) =>
    request<void>(`/tasks/${taskId}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
}

// Dashboard API
export const dashboardApi = {
  getSummary: (workspaceId: string) =>
    request<any>(`/dashboard/summary?workspace_id=${workspaceId}`),
  getDue: (workspaceId: string, params?: Record<string, string>) => {
    const query = new URLSearchParams({ workspace_id: workspaceId, ...params }).toString()
    return request<any[]>(`/dashboard/due?${query}`)
  },
  getTags: (workspaceId: string) =>
    request<any[]>(`/dashboard/tags?workspace_id=${workspaceId}`),
  getWidgets: (workspaceId: string) =>
    request<any>(`/dashboard/widgets?workspace_id=${workspaceId}&limit=20`),
}

// Templates API
export const templatesApi = {
  list: (workspaceId: string, category?: string) => {
    const params = new URLSearchParams({ workspace_id: workspaceId })
    if (category) params.set('category', category)
    return request<any[]>(`/templates?${params}`)
  },
  create: (data: any, workspaceId: string) =>
    request<any>(`/templates?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any, workspaceId: string) =>
    request<any>(`/templates/${id}?workspace_id=${workspaceId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string, workspaceId: string) =>
    request<void>(`/templates/${id}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
}

// Calendar API
export const calendarApi = {
  getReminderLink: (workspaceId: string) =>
    request<any>(`/calendar/daily-reminder-link?workspace_id=${workspaceId}`),
}

// Workspace activity feed API
export const workspaceActivitiesApi = {
  list: (workspaceId: string, limit = 50) => request<any>(`/activities?workspace_id=${workspaceId}&limit=${limit}`),
}

export const pipelineStagesApi = {
  list: (workspaceId: string) => request<any[]>(`/pipeline-stages/?workspace_id=${workspaceId}`),
  create: (data: any, workspaceId: string) => request<any>(`/pipeline-stages/?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any, workspaceId: string) => request<any>(`/pipeline-stages/${id}?workspace_id=${workspaceId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  reorder: (stageIds: string[], workspaceId: string) => request<any[]>(`/pipeline-stages/reorder?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify({ stage_ids: stageIds }) }),
  delete: (id: string, workspaceId: string) => request<void>(`/pipeline-stages/${id}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
}

export const customFieldsApi = {
  list: (workspaceId: string) => request<any[]>(`/custom-fields/?workspace_id=${workspaceId}`),
  create: (data: any, workspaceId: string) => request<any>(`/custom-fields/?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any, workspaceId: string) => request<any>(`/custom-fields/${id}?workspace_id=${workspaceId}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string, workspaceId: string) => request<void>(`/custom-fields/${id}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
}

export const savedViewsApi = {
  list: (workspaceId: string) =>
    request<any[]>(`/saved-views?workspace_id=${workspaceId}`),
  create: (data: any, workspaceId: string) =>
    request<any>(`/saved-views?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any, workspaceId: string) =>
    request<any>(`/saved-views/${id}?workspace_id=${workspaceId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string, workspaceId: string) =>
    request<void>(`/saved-views/${id}?workspace_id=${workspaceId}`, { method: 'DELETE' }),
}

// Analytics API
export const analyticsApi = {
  getFunnel: (workspaceId: string) => request<any>(`/workspaces/${workspaceId}/analytics/funnel`),
  getPerformance: (workspaceId: string, params?: Record<string, string>) => {
    const query = new URLSearchParams(params).toString()
    return request<any[]>(`/workspaces/${workspaceId}/analytics/performance${query ? `?${query}` : ''}`)
  },
  getGoals: (workspaceId: string) => request<any>(`/workspaces/${workspaceId}/analytics/goals`),
  exportCsv: (workspaceId: string, params?: Record<string, string>) => requestBlob(`/workspaces/${workspaceId}/analytics/export.csv?${new URLSearchParams(params).toString()}`),
  exportPdf: (workspaceId: string, params?: Record<string, string>) => requestBlob(`/workspaces/${workspaceId}/analytics/export.pdf?${new URLSearchParams(params).toString()}`),
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/api/httpClient.ts')
