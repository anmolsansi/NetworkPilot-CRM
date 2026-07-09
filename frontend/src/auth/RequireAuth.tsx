import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { logInfo, maskId } from '../utils/logger'

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuthStore()

  useEffect(() => {
    logInfo('RequireAuth', 'Route guard evaluated', {
      loading,
      hasSession: Boolean(session),
      userId: maskId(session?.user.id),
    })
  }, [loading, session])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!session) {
    logInfo('RequireAuth', 'Redirecting unauthenticated user to login')
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/auth/RequireAuth.tsx')
