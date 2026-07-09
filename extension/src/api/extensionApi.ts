import { getToken } from '../auth/tokenStorage'

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const authData = await getToken()
  if (!authData) {
    console.warn('[NetworkPilot Extension API]', 'Request blocked; missing auth data', { path })
    throw { code: 'UNAUTHORIZED', message: 'Not authenticated' }
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authData.token}`,
    ...(options.headers as Record<string, string>),
  }

  const startedAt = Date.now()
  console.debug('[NetworkPilot Extension API]', 'Request started', {
    method: options.method || 'GET',
    path,
    workspaceId: authData.workspaceId.slice(-8),
  })
  const response = await fetch(`${authData.apiUrl}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    console.warn('[NetworkPilot Extension API]', 'Unauthorized response', {
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
    })
    throw { code: 'UNAUTHORIZED', message: 'Invalid or expired token' }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    console.error('[NetworkPilot Extension API]', 'Request failed', {
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
      error: errorData?.error || null,
    })
    throw errorData?.error || { code: 'HTTP_ERROR', message: `Request failed: ${response.status}` }
  }

  if (response.status === 204) {
    console.debug('[NetworkPilot Extension API]', 'Request completed with no content', {
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
    })
    return undefined as T
  }

  console.debug('[NetworkPilot Extension API]', 'Request completed', {
    path,
    status: response.status,
    durationMs: Date.now() - startedAt,
  })
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
  const startedAt = Date.now()
  console.debug('[NetworkPilot Extension SetupAPI]', 'Setup request started', {
    method: options.method || 'GET',
    path,
  })
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
    console.error('[NetworkPilot Extension SetupAPI]', 'Setup request failed', {
      path,
      status: response.status,
      durationMs: Date.now() - startedAt,
      error: errorData?.error || null,
    })
    throw errorData?.error || { code: 'HTTP_ERROR', message: `Request failed: ${response.status}` }
  }

  console.debug('[NetworkPilot Extension SetupAPI]', 'Setup request completed', {
    path,
    status: response.status,
    durationMs: Date.now() - startedAt,
  })
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
    console.info('[NetworkPilot Extension API]', 'Looking up LinkedIn profile', {
      workspaceId: authData.workspaceId.slice(-8),
      urlLength: linkedinUrl.length,
    })
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
    console.info('[NetworkPilot Extension API]', 'Creating profile from extension', {
      workspaceId: authData.workspaceId.slice(-8),
      priority: data.priority,
      initialAction: data.initial_action,
    })
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
    console.info('[NetworkPilot Extension API]', 'Recording quick action from extension', {
      workspaceId: authData.workspaceId.slice(-8),
      personId: data.person_id.slice(-8),
      actionType: data.action_type,
    })
    return request<QuickActionResponse>('/extension/quick-action', {
      method: 'POST',
      body: JSON.stringify({ ...data, workspace_id: authData.workspaceId }),
    })
  },

  getTemplates: async () => {
    const authData = await getToken()
    if (!authData?.workspaceId) throw new Error('No workspace ID')
    console.info('[NetworkPilot Extension API]', 'Loading templates from extension', {
      workspaceId: authData.workspaceId.slice(-8),
    })
    return request<Template[]>(`/templates?workspace_id=${authData.workspaceId}`)
  },
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/api/extensionApi.ts')
