import { supabase } from '../auth/supabaseClient'

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
  bulkAction: (data: any) =>
    request<any>('/people/bulk-actions', { method: 'POST', body: JSON.stringify(data) }),
}

// CSV Import API
export const importsApi = {
  previewPeople: (data: FormData) =>
    request<any>('/imports/people/preview', { method: 'POST', body: data }),
  commitPeople: (data: any) =>
    request<any>('/imports/people/commit', { method: 'POST', body: JSON.stringify(data) }),
}

// CSV Export API
export const exportsApi = {
  peopleCsv: (params: Record<string, string>) => {
    const query = new URLSearchParams(params).toString()
    return requestBlob(`/exports/people.csv?${query}`)
  },
}

// Activities API
export const activitiesApi = {
  list: (personId: string, workspaceId: string) =>
    request<any[]>(`/people/${personId}/activities?workspace_id=${workspaceId}`),
  create: (personId: string, data: any, workspaceId: string) =>
    request<any>(`/people/${personId}/activities?workspace_id=${workspaceId}`, { method: 'POST', body: JSON.stringify(data) }),
}

// Dashboard API
export const dashboardApi = {
  getSummary: (workspaceId: string) =>
    request<any>(`/dashboard/summary?workspace_id=${workspaceId}`),
  getDue: (workspaceId: string, params?: Record<string, string>) => {
    const query = new URLSearchParams({ workspace_id: workspaceId, ...params }).toString()
    return request<any[]>(`/dashboard/due?${query}`)
  },
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

// Saved Views API
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

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/api/httpClient.ts')
