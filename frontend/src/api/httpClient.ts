import { supabase } from '../auth/supabaseClient'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

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

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    await supabase.auth.signOut()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw {
      code: errorData?.error?.code || 'HTTP_ERROR',
      message: errorData?.error?.message || `Request failed with status ${response.status}`,
      details: errorData?.error?.details,
    }
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

async function requestBlob(path: string): Promise<Blob> {
  const token = await getToken()
  const headers: Record<string, string> = {}

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { headers })

  if (response.status === 401) {
    await supabase.auth.signOut()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw {
      code: errorData?.error?.code || 'HTTP_ERROR',
      message: errorData?.error?.message || `Request failed with status ${response.status}`,
      details: errorData?.error?.details,
    }
  }

  return response.blob()
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
