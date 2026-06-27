interface TokenData {
  token: string
  apiUrl: string
  workspaceId: string
}

export async function getToken(): Promise<TokenData | null> {
  const result = await chrome.storage.local.get(['auth_token', 'api_url', 'workspace_id'])
  if (result.auth_token && result.api_url && result.workspace_id) {
    return { token: result.auth_token, apiUrl: result.api_url, workspaceId: result.workspace_id }
  }
  return null
}

export async function setToken(token: string, apiUrl: string, workspaceId: string): Promise<void> {
  await chrome.storage.local.set({
    auth_token: token,
    api_url: apiUrl,
    workspace_id: workspaceId,
  })
}

export async function clearToken(): Promise<void> {
  await chrome.storage.local.remove(['auth_token', 'api_url', 'workspace_id'])
}

export async function isAuthenticated(): Promise<boolean> {
  const token = await getToken()
  return token !== null
}
