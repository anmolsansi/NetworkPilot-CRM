export function LoadingView() {
  return (
    <div className="p-4 flex items-center justify-center min-h-[200px]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
        <p className="text-sm text-gray-600">Loading...</p>
      </div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/LoadingView.tsx')
