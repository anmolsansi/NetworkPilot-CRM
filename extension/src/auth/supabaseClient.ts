import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:54321'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'missing-anon-key'

const chromeStorage = {
  getItem: async (key: string) => {
    const result = await chrome.storage.local.get(key)
    return result[key] ?? null
  },
  setItem: async (key: string, value: string) => {
    await chrome.storage.local.set({ [key]: value })
  },
  removeItem: async (key: string) => {
    await chrome.storage.local.remove(key)
  },
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    detectSessionInUrl: false,
    flowType: 'implicit',
    persistSession: true,
    storage: chromeStorage,
  },
})

export function hasSupabaseConfig(): boolean {
  return Boolean(import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY)
}
