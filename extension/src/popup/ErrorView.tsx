interface Props {
  message: string
  onRetry?: () => void
}

export function ErrorView({ message, onRetry }: Props) {
  return (
    <div className="p-4 text-center">
      <div className="text-4xl mb-4">⚠️</div>
      <h2 className="text-lg font-semibold text-gray-900 mb-2">Error</h2>
      <p className="text-sm text-gray-600 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700"
        >
          Try Again
        </button>
      )}
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/ErrorView.tsx')
