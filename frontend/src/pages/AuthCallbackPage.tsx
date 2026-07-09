import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../auth/supabaseClient'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { logError, logInfo, maskId } from '../utils/logger'

export function AuthCallbackPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const finishSignIn = async () => {
      const callbackParams = getCallbackParams()
      const accessToken = callbackParams.get('access_token')
      const refreshToken = callbackParams.get('refresh_token')
      const callbackKeys = Array.from(callbackParams.keys()).filter((key) => !key.includes('token'))

      logInfo('AuthCallback', 'Processing OAuth callback', {
        accessCredentialPresent: Boolean(accessToken),
        refreshCredentialPresent: Boolean(refreshToken),
        callbackKeys,
      })

      if (accessToken && refreshToken) {
        const { error: sessionError } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        })

        if (sessionError) throw sessionError
        logInfo('AuthCallback', 'OAuth callback session persisted')
      }

      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      if (sessionError) throw sessionError
      if (!session) throw new Error('Google sign-in did not create a session')

      logInfo('AuthCallback', 'OAuth session available; entering app', {
        userId: maskId(session.user.id),
        provider: session.user.app_metadata?.provider,
        expiresAt: session.expires_at,
      })

      window.history.replaceState(null, document.title, '/auth/callback')
      navigate('/', { replace: true })
    }

    finishSignIn().catch((err: any) => {
      logError('AuthCallback', 'OAuth callback failed', {
        message: err.message || 'Could not finish Google sign-in',
        name: err.name,
      })
      if (mounted) {
        setError(err.message || 'Could not finish Google sign-in')
      }
    })

    return () => {
      mounted = false
    }
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        {error ? (
          <ErrorAlert message={error} />
        ) : (
          <div className="text-center">
            <div className="mx-auto animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            <p className="mt-4 text-sm text-gray-600">Finishing sign-in...</p>
          </div>
        )}
      </div>
    </div>
  )
}

function getCallbackParams(): URLSearchParams {
  const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const searchParams = new URLSearchParams(window.location.search)

  searchParams.forEach((value, key) => {
    if (!hashParams.has(key)) hashParams.set(key, value)
  })

  return hashParams
}
