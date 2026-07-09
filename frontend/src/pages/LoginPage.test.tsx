import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from '../pages/LoginPage'
import { supabase } from '../auth/supabaseClient'

vi.mock('../auth/supabaseClient', () => ({
  supabase: {
    auth: {
      signInWithOAuth: vi.fn(),
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
    },
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByText('NetworkPilot CRM')).toBeInTheDocument()
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()
  })

  it('renders email input', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByPlaceholderText('Email address')).toBeInTheDocument()
  })

  it('renders password input', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
  })

  it('renders sign in button', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('starts Google OAuth from the login form', async () => {
    vi.mocked(supabase.auth.signInWithOAuth).mockResolvedValue({ data: { provider: 'google', url: 'https://example.com/oauth' }, error: null })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /continue with google/i }))

    await waitFor(() => {
      expect(supabase.auth.signInWithOAuth).toHaveBeenCalledWith({
        provider: 'google',
        options: {
          redirectTo: window.location.origin,
        },
      })
    })
  })
})
