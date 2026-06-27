import { useEffect, useState } from 'react'
import { getToken, isAuthenticated } from '../auth/tokenStorage'
import { getActiveTab, isLinkedInProfileUrl, normalizeLinkedInUrl, extractNameFromTitle } from '../utils/activeTab'
import { extensionApi, LookupResponse } from '../api/extensionApi'
import { UnauthenticatedView } from './UnauthenticatedView'
import { InvalidPageView } from './InvalidPageView'
import { LoadingView } from './LoadingView'
import { ErrorView } from './ErrorView'
import { NewProfileView } from './NewProfileView'
import { ExistingProfileView } from './ExistingProfileView'

type ViewState = 'loading' | 'unauthenticated' | 'invalid_page' | 'new_profile' | 'existing_profile' | 'error'

export function PopupApp() {
  const [viewState, setViewState] = useState<ViewState>('loading')
  const [tabInfo, setTabInfo] = useState<{ url: string; title: string } | null>(null)
  const [lookupResult, setLookupResult] = useState<LookupResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    init()
  }, [])

  const init = async () => {
    // Check authentication
    const authed = await isAuthenticated()
    if (!authed) {
      setViewState('unauthenticated')
      return
    }

    // Get active tab
    const tab = await getActiveTab()
    if (!tab) {
      setError('Could not access current tab')
      setViewState('error')
      return
    }

    setTabInfo(tab)

    // Validate LinkedIn profile URL
    if (!isLinkedInProfileUrl(tab.url)) {
      setViewState('invalid_page')
      return
    }

    // Get workspace ID from storage
    const authData = await getToken()
    if (!authData) {
      setViewState('unauthenticated')
      return
    }

    const wsId = authData.workspaceId
    if (!wsId) {
      setError('Please set workspace ID in extension settings')
      setViewState('error')
      return
    }

    // Lookup profile
    try {
      const normalized = normalizeLinkedInUrl(tab.url)
      if (!normalized) {
        setViewState('invalid_page')
        return
      }

      const lookup = await extensionApi.lookup(tab.url)
      setLookupResult(lookup)

      if (lookup.found) {
        setViewState('existing_profile')
      } else {
        setViewState('new_profile')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to lookup profile')
      setViewState('error')
    }
  }

  const handleSuccess = () => {
    init()
  }

  switch (viewState) {
    case 'loading':
      return <LoadingView />
    case 'unauthenticated':
      return <UnauthenticatedView onAuth={handleSuccess} />
    case 'invalid_page':
      return <InvalidPageView url={tabInfo?.url} />
    case 'error':
      return <ErrorView message={error || 'Unknown error'} onRetry={init} />
    case 'new_profile':
      return (
        <NewProfileView
          url={tabInfo?.url || ''}
          suggestedName={tabInfo ? extractNameFromTitle(tabInfo.title) : ''}
          onSuccess={handleSuccess}
        />
      )
    case 'existing_profile':
      return (
        <ExistingProfileView
          lookupResult={lookupResult!}
          onSuccess={handleSuccess}
        />
      )
    default:
      return <LoadingView />
  }
}
