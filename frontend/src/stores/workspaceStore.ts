import { create } from 'zustand'
import { workspaceApi } from '../api/httpClient'
import { logError, logInfo, maskId } from '../utils/logger'

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
    logInfo('WorkspaceStore', 'Loading workspaces')
    set({ loading: true, error: null })
    try {
      const workspaces = await workspaceApi.list()
      const currentWorkspace = useWorkspaceStore.getState().currentWorkspace
      const selectedWorkspace =
        workspaces.find((workspace) => workspace.id === currentWorkspace?.id) ??
        workspaces[0] ??
        null

      logInfo('WorkspaceStore', 'Workspaces loaded', {
        count: workspaces.length,
        previousWorkspaceId: maskId(currentWorkspace?.id),
        selectedWorkspaceId: maskId(selectedWorkspace?.id),
      })
      set({ workspaces, currentWorkspace: selectedWorkspace, loading: false })
    } catch (error: any) {
      const message = error?.message || 'Failed to load workspaces'
      logError('WorkspaceStore', 'Failed to load workspaces', {
        message,
        code: error?.code,
        details: error?.details,
      })
      set({ loading: false, error: message })
      throw error
    }
  },
  setCurrentWorkspace: (workspace) => {
    logInfo('WorkspaceStore', 'Current workspace changed', {
      selectedWorkspaceId: maskId(workspace?.id),
    })
    set({ currentWorkspace: workspace })
  },
}))

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/stores/workspaceStore.ts')
