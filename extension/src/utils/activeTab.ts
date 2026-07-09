const LINKEDIN_PROFILE_REGEX = /^\/in\/[a-zA-Z0-9_-]+\/?$/

export async function getActiveTab(): Promise<{ url: string; title: string } | null> {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (tab?.url) {
      return { url: tab.url, title: tab.title || '' }
    }
  } catch (error) {
    console.error('Failed to get active tab:', error)
  }
  return null
}

export function isLinkedInProfileUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    const hostname = parsed.hostname.replace('www.', '')
    if (hostname !== 'linkedin.com') return false

    return LINKEDIN_PROFILE_REGEX.test(parsed.pathname)
  } catch {
    return false
  }
}

export function normalizeLinkedInUrl(url: string): { normalized: string; slug: string } | null {
  try {
    const parsed = new URL(url)
    const slug = parsed.pathname.split('/in/')[1]?.split('/')[0]
    if (!slug) return null

    return {
      normalized: `linkedin.com/in/${slug.toLowerCase()}`,
      slug: slug.toLowerCase(),
    }
  } catch {
    return null
  }
}

export function extractNameFromTitle(title: string): string {
  // LinkedIn profile titles are usually "First Last - Title at Company | LinkedIn"
  const name = title.split(' - ')[0]?.split(' | ')[0]?.trim()
  return name || title
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/utils/activeTab.ts')
