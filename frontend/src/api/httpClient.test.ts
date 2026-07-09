import { describe, expect, it } from 'vitest'
import { resolveApiBaseUrl } from './httpClient'

describe('resolveApiBaseUrl', () => {
  it('defaults to the relative API prefix', () => {
    expect(resolveApiBaseUrl()).toBe('/api/v1')
  })

  it('keeps a configured API URL that already includes the version prefix', () => {
    expect(resolveApiBaseUrl('https://networkpilot-crm.onrender.com/api/v1')).toBe(
      'https://networkpilot-crm.onrender.com/api/v1'
    )
  })

  it('adds the API version prefix when only a backend origin is configured', () => {
    expect(resolveApiBaseUrl('https://networkpilot-crm.onrender.com')).toBe(
      'https://networkpilot-crm.onrender.com/api/v1'
    )
  })

  it('converts an /api root to the v1 API root', () => {
    expect(resolveApiBaseUrl('https://networkpilot-crm.onrender.com/api/')).toBe(
      'https://networkpilot-crm.onrender.com/api/v1'
    )
  })
})
