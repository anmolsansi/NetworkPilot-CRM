import { describe, it, expect } from 'vitest'
import { isLinkedInProfileUrl, normalizeLinkedInUrl, extractNameFromTitle } from '../activeTab'

describe('isLinkedInProfileUrl', () => {
  it('validates profile URLs', () => {
    expect(isLinkedInProfileUrl('https://www.linkedin.com/in/johndoe/')).toBe(true)
    expect(isLinkedInProfileUrl('https://linkedin.com/in/john-doe-123/')).toBe(true)
  })

  it('rejects non-profile URLs', () => {
    expect(isLinkedInProfileUrl('https://www.linkedin.com/company/google/')).toBe(false)
    expect(isLinkedInProfileUrl('https://www.google.com')).toBe(false)
    expect(isLinkedInProfileUrl('https://www.linkedin.com/feed/')).toBe(false)
  })
})

describe('normalizeLinkedInUrl', () => {
  it('normalizes valid URLs', () => {
    const result = normalizeLinkedInUrl('https://www.linkedin.com/in/JohnDoe/')
    expect(result).toEqual({ normalized: 'linkedin.com/in/johndoe', slug: 'johndoe' })
  })

  it('returns null for invalid URLs', () => {
    expect(normalizeLinkedInUrl('https://www.google.com')).toBeNull()
  })
})

describe('extractNameFromTitle', () => {
  it('extracts name from LinkedIn title', () => {
    const title = 'John Doe - Software Engineer at Google | LinkedIn'
    expect(extractNameFromTitle(title)).toBe('John Doe')
  })

  it('returns title if no separator', () => {
    const title = 'John Doe'
    expect(extractNameFromTitle(title)).toBe('John Doe')
  })
})
