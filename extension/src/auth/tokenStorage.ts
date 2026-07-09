import { Session } from '@supabase/supabase-js'
import { hasSupabaseConfig, supabase } from './supabaseClient'

interface TokenData {
  token: string
  apiUrl: string
  workspaceId: string
  email?: string
}

const API_URL_KEY = 'api_url'
const WORKSPACE_ID_KEY = 'workspace_id'

export async function getToken(): Promise<TokenData | null> {
  console.debug('[NetworkPilot Extension Auth]', 'Loading session and workspace settings')
  const [{ data: { session } }, result] = await Promise.all([
    supabase.auth.getSession(),
    chrome.storage.local.get([API_URL_KEY, WORKSPACE_ID_KEY]),
  ])

  if (session?.access_token && result.api_url && result.workspace_id) {
    console.debug('[NetworkPilot Extension Auth]', 'Session and workspace settings available', {
      workspaceId: String(result.workspace_id).slice(-8),
      apiConfigured: Boolean(result.api_url),
    })
    return {
      token: session.access_token,
      apiUrl: result.api_url,
      workspaceId: result.workspace_id,
      email: session.user.email,
    }
  }
  console.debug('[NetworkPilot Extension Auth]', 'Session or workspace settings missing', {
    hasSession: Boolean(session?.access_token),
    hasApiUrl: Boolean(result.api_url),
    hasWorkspaceId: Boolean(result.workspace_id),
  })
  return null
}

export async function setWorkspaceSettings(apiUrl: string, workspaceId: string): Promise<void> {
  console.info('[NetworkPilot Extension Auth]', 'Saving workspace settings', {
    workspaceId: workspaceId.slice(-8),
    apiConfigured: Boolean(apiUrl),
  })
  await chrome.storage.local.set({
    [API_URL_KEY]: normalizeApiUrl(apiUrl),
    [WORKSPACE_ID_KEY]: workspaceId,
  })
}

export async function clearToken(): Promise<void> {
  console.info('[NetworkPilot Extension Auth]', 'Clearing auth and workspace settings')
  await supabase.auth.signOut()
  await chrome.storage.local.remove([API_URL_KEY, WORKSPACE_ID_KEY])
}

export async function isAuthenticated(): Promise<boolean> {
  const token = await getToken()
  console.debug('[NetworkPilot Extension Auth]', 'Authentication check completed', {
    authenticated: token !== null,
  })
  return token !== null
}

export async function signInWithGoogle(apiUrl: string): Promise<Session> {
  if (!hasSupabaseConfig()) {
    console.error('[NetworkPilot Extension Auth]', 'Supabase config missing for extension')
    throw new Error('Supabase URL and anon key are not configured for the extension')
  }

  const redirectTo = chrome.identity.getRedirectURL('auth')
  console.info('[NetworkPilot Extension Auth]', 'Starting Google OAuth flow', {
    redirectTo,
    apiConfigured: Boolean(apiUrl),
  })
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo,
      skipBrowserRedirect: true,
    },
  })

  if (error) throw error
  if (!data.url) throw new Error('Supabase did not return a Google sign-in URL')

  const redirectUrl = await chrome.identity.launchWebAuthFlow({
    url: data.url,
    interactive: true,
  })

  if (!redirectUrl) {
    console.warn('[NetworkPilot Extension Auth]', 'Google OAuth flow cancelled')
    throw new Error('Google sign-in was cancelled')
  }

  const params = parseOAuthRedirect(redirectUrl)
  const oauthError = params.get('error_description') || params.get('error')
  if (oauthError) {
    console.error('[NetworkPilot Extension Auth]', 'Google OAuth redirect returned error', {
      message: oauthError,
    })
    throw new Error(oauthError)
  }

  const accessToken = params.get('access_token')
  const refreshToken = params.get('refresh_token')
  if (!accessToken || !refreshToken) {
    console.error('[NetworkPilot Extension Auth]', 'OAuth redirect missing Supabase session tokens')
    throw new Error('Google sign-in did not return a Supabase session')
  }

  const { data: sessionData, error: sessionError } = await supabase.auth.setSession({
    access_token: accessToken,
    refresh_token: refreshToken,
  })

  if (sessionError) throw sessionError
  if (!sessionData.session) throw new Error('Could not persist Supabase session')

  await chrome.storage.local.set({ [API_URL_KEY]: normalizeApiUrl(apiUrl) })
  console.info('[NetworkPilot Extension Auth]', 'Google OAuth flow completed', {
    userId: sessionData.session.user.id.slice(-8),
  })
  return sessionData.session
}

function parseOAuthRedirect(redirectUrl: string): URLSearchParams {
  const url = new URL(redirectUrl)
  const rawParams = url.hash.startsWith('#') ? url.hash.slice(1) : url.search.slice(1)
  return new URLSearchParams(rawParams)
}

function normalizeApiUrl(apiUrl: string): string {
  return apiUrl.trim().replace(/\/$/, '')
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/auth/tokenStorage.ts')
