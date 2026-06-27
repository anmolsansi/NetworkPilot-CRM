import { create } from 'zustand'
import { workspaceApi } from '../api/httpClient'

interface Workspace {
  id: string
  name: string
  owner_id: string
  default_follow_up_delay_days: number
  default_acceptance_check_delay_days: number
  daily_reminder_time: string
  timezone: string
}

interface WorkspaceState {
  workspaces: Workspace[]
  currentWorkspace: Workspace | null
  loading: boolean
  fetchWorkspaces: () => Promise<void>
  setCurrentWorkspace: (workspace: Workspace | null) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  currentWorkspace: null,
  loading: false,
  fetchWorkspaces: async () => {
    set({ loading: true })
    try {
      const workspaces = await workspaceApi.list()
      set({ workspaces, loading: false })
      // Auto-select first workspace
      if (workspaces.length > 0 && !useWorkspaceStore.getState().currentWorkspace) {
        set({ currentWorkspace: workspaces[0] })
      }
    } catch (error) {
      set({ loading: false })
    }
  },
  setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
}))
