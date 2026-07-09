import { create } from 'zustand'
import { Session, User } from '@supabase/supabase-js'
import { supabase } from '../auth/supabaseClient'
import { logError, logInfo, maskId } from '../utils/logger'

interface AuthState {
  session: Session | null
  user: User | null
  loading: boolean
  setSession: (session: Session | null) => void
  signOut: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  user: null,
  loading: true,
  setSession: (session) => {
    logInfo('AuthStore', 'Session state updated', {
      hasSession: Boolean(session),
      userId: maskId(session?.user.id),
      provider: session?.user.app_metadata?.provider,
      expiresAt: session?.expires_at,
    })
    set({ session, user: session?.user ?? null, loading: false })
  },
  signOut: async () => {
    logInfo('AuthStore', 'Signing out')
    await supabase.auth.signOut()
    set({ session: null, user: null })
  },
}))

// Initialize auth state
logInfo('AuthStore', 'Initializing auth session')
supabase.auth.getSession().then(({ data: { session } }) => {
  logInfo('AuthStore', 'Initial auth session loaded', {
    hasSession: Boolean(session),
    userId: maskId(session?.user.id),
    provider: session?.user.app_metadata?.provider,
  })
  useAuthStore.getState().setSession(session)
}).catch((error) => {
  logError('AuthStore', 'Failed to load initial auth session', {
    message: error.message,
    name: error.name,
  })
  useAuthStore.getState().setSession(null)
})

supabase.auth.onAuthStateChange((event, session) => {
  logInfo('AuthStore', 'Auth state change received', {
    event,
    hasSession: Boolean(session),
    userId: maskId(session?.user.id),
    provider: session?.user.app_metadata?.provider,
  })
  useAuthStore.getState().setSession(session)
})
