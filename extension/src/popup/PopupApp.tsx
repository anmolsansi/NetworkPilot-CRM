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
    console.info('[NetworkPilot Extension Popup]', 'Initializing popup')
    // Check authentication
    const authed = await isAuthenticated()
    if (!authed) {
      console.info('[NetworkPilot Extension Popup]', 'Popup unauthenticated')
      setViewState('unauthenticated')
      return
    }

    // Get active tab
    const tab = await getActiveTab()
    if (!tab) {
      console.error('[NetworkPilot Extension Popup]', 'Could not access current tab')
      setError('Could not access current tab')
      setViewState('error')
      return
    }

    setTabInfo(tab)

    // Validate LinkedIn profile URL
    if (!isLinkedInProfileUrl(tab.url)) {
      console.info('[NetworkPilot Extension Popup]', 'Active tab is not a LinkedIn profile', {
        urlLength: tab.url.length,
      })
      setViewState('invalid_page')
      return
    }

    // Get workspace ID from storage
    const authData = await getToken()
    if (!authData) {
      console.info('[NetworkPilot Extension Popup]', 'Auth data missing after auth check')
      setViewState('unauthenticated')
      return
    }

    const wsId = authData.workspaceId
    if (!wsId) {
      console.error('[NetworkPilot Extension Popup]', 'Workspace ID missing in extension settings')
      setError('Please set workspace ID in extension settings')
      setViewState('error')
      return
    }

    // Lookup profile
    try {
      const normalized = normalizeLinkedInUrl(tab.url)
      if (!normalized) {
        console.info('[NetworkPilot Extension Popup]', 'LinkedIn URL normalization failed')
        setViewState('invalid_page')
        return
      }

      console.info('[NetworkPilot Extension Popup]', 'Looking up active LinkedIn profile', {
        workspaceId: wsId.slice(-8),
        slug: normalized.slug,
      })
      const lookup = await extensionApi.lookup(tab.url)
      setLookupResult(lookup)

      if (lookup.found) {
        console.info('[NetworkPilot Extension Popup]', 'Existing profile found', {
          workspaceId: wsId.slice(-8),
          personId: lookup.person_id?.slice(-8) || null,
        })
        setViewState('existing_profile')
      } else {
        console.info('[NetworkPilot Extension Popup]', 'New profile flow selected', {
          workspaceId: wsId.slice(-8),
          slug: normalized.slug,
        })
        setViewState('new_profile')
      }
    } catch (err: any) {
      console.error('[NetworkPilot Extension Popup]', 'Popup initialization failed', {
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to lookup profile')
      setViewState('error')
    }
  }

  const handleSuccess = () => {
    console.info('[NetworkPilot Extension Popup]', 'Action succeeded; refreshing popup state')
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

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/PopupApp.tsx')
