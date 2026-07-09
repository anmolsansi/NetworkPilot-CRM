import { useAuthStore } from '../../stores/authStore'
import { useWorkspaceStore } from '../../stores/workspaceStore'

export function Topbar() {
  const { user, signOut } = useAuthStore()
  const { currentWorkspace } = useWorkspaceStore()

  return (
    <div className="sticky top-0 z-10 bg-white border-b border-gray-200 h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8">
      <div className="flex items-center">
        <h1 className="text-lg font-semibold text-gray-900 lg:hidden">NetworkPilot</h1>
        {currentWorkspace && (
          <span className="ml-4 text-sm text-gray-500 hidden lg:block">
            {currentWorkspace.name}
          </span>
        )}
      </div>
      <div className="flex items-center space-x-4">
        <span className="text-sm text-gray-600">{user?.email}</span>
        <button
          onClick={signOut}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Sign out
        </button>
      </div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/components/layout/Topbar.tsx')
