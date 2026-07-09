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
  error: string | null
  fetchWorkspaces: () => Promise<void>
  setCurrentWorkspace: (workspace: Workspace | null) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  currentWorkspace: null,
  loading: false,
  error: null,
  fetchWorkspaces: async () => {
    set({ loading: true, error: null })
    try {
      const workspaces = await workspaceApi.list()
      const currentWorkspace = useWorkspaceStore.getState().currentWorkspace
      const selectedWorkspace =
        workspaces.find((workspace) => workspace.id === currentWorkspace?.id) ??
        workspaces[0] ??
        null

      set({ workspaces, currentWorkspace: selectedWorkspace, loading: false })
    } catch (error: any) {
      const message = error?.message || 'Failed to load workspaces'
      set({ loading: false, error: message })
      throw error
    }
  },
  setCurrentWorkspace: (workspace) => {
    set({ currentWorkspace: workspace })
  },
}))
