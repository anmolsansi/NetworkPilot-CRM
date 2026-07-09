import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthCallbackPage } from './AuthCallbackPage'
import { supabase } from '../auth/supabaseClient'

const navigateMock = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock('../auth/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
      setSession: vi.fn(),
    },
  },
}))

describe('AuthCallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.history.pushState(null, '', '/')
  })

  it('persists an implicit OAuth callback session and enters the app', async () => {
    window.history.pushState(null, '', '/auth/callback#access_token=access-token&refresh_token=refresh-token')
    vi.mocked(supabase.auth.setSession).mockResolvedValue({
      data: {
        session: null,
        user: null,
      },
      error: null,
    })
    vi.mocked(supabase.auth.getSession).mockResolvedValue({
      data: {
        session: {
          access_token: 'access-token',
          refresh_token: 'refresh-token',
          expires_in: 3600,
          expires_at: 123,
          token_type: 'bearer',
          user: { id: 'user-1' },
        } as any,
      },
      error: null,
    })

    render(
      <MemoryRouter>
        <AuthCallbackPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(supabase.auth.setSession).toHaveBeenCalledWith({
        access_token: 'access-token',
        refresh_token: 'refresh-token',
      })
    })
    expect(navigateMock).toHaveBeenCalledWith('/', { replace: true })
  })

  it('shows an error when OAuth does not create a session', async () => {
    window.history.pushState(null, '', '/auth/callback')
    vi.mocked(supabase.auth.getSession).mockResolvedValue({
      data: { session: null },
      error: null,
    })

    render(
      <MemoryRouter>
        <AuthCallbackPage />
      </MemoryRouter>
    )

    expect(await screen.findByText('Google sign-in did not create a session')).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
