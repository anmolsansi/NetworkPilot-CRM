import { getToken } from '../auth/tokenStorage'

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const authData = await getToken()
  if (!authData) {
    throw { code: 'UNAUTHORIZED', message: 'Not authenticated' }
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authData.token}`,
    ...(options.headers as Record<string, string>),
  }

  const response = await fetch(`${authData.apiUrl}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    throw { code: 'UNAUTHORIZED', message: 'Invalid or expired token' }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw errorData?.error || { code: 'HTTP_ERROR', message: `Request failed: ${response.status}` }
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export interface LookupResponse {
  found: boolean
  person_id?: string
  name?: string
  linkedin_url?: string
  linkedin_slug?: string
  stage?: string
  priority?: string
  next_action_type?: string
  next_action_date?: string
  last_action_type?: string
}

export interface QuickCreateResponse {
  person_id: string
  name: string
  linkedin_url: string
  stage: string
  next_action_type: string | null
  next_action_date: string | null
  activity_id: string
}

export interface QuickActionResponse {
  person_id: string
  stage: string
  next_action_type: string | null
  next_action_date: string | null
  activity_id: string
}

export interface Template {
  id: string
  name: string
  category: string
  body: string
  variables: string[] | null
}

export interface Workspace {
  id: string
  name: string
}

async function setupRequest<T>(
  apiUrl: string,
  token: string,
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${apiUrl.replace(/\/$/, '')}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...(options.headers as Record<string, string>),
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw errorData?.error || { code: 'HTTP_ERROR', message: `Request failed: ${response.status}` }
  }

  return response.json()
}

export const authSetupApi = {
  listWorkspaces: (apiUrl: string, token: string) =>
    setupRequest<Workspace[]>(apiUrl, token, '/workspaces'),
  createWorkspace: (apiUrl: string, token: string, name: string) =>
    setupRequest<Workspace>(apiUrl, token, '/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
}

export const extensionApi = {
  lookup: async (linkedinUrl: string) => {
    const authData = await getToken()
    if (!authData?.workspaceId) throw new Error('No workspace ID')
    return request<LookupResponse>(`/extension/lookup?workspace_id=${authData.workspaceId}&linkedin_url=${encodeURIComponent(linkedinUrl)}`)
  },

  quickCreate: async (data: {
    linkedin_url: string
    name: string
    role?: string
    company?: string
    location?: string
    priority?: string
    initial_action: string
    notes?: string
  }) => {
    const authData = await getToken()
    if (!authData?.workspaceId) throw new Error('No workspace ID')
    return request<QuickCreateResponse>('/extension/quick-create', {
      method: 'POST',
      body: JSON.stringify({ ...data, workspace_id: authData.workspaceId }),
    })
  },

  quickAction: async (data: {
    person_id: string
    action_type: string
    notes?: string
  }) => {
    const authData = await getToken()
    if (!authData?.workspaceId) throw new Error('No workspace ID')
    return request<QuickActionResponse>('/extension/quick-action', {
      method: 'POST',
      body: JSON.stringify({ ...data, workspace_id: authData.workspaceId }),
    })
  },

  getTemplates: async () => {
    const authData = await getToken()
    if (!authData?.workspaceId) throw new Error('No workspace ID')
    return request<Template[]>(`/templates?workspace_id=${authData.workspaceId}`)
  },
}
