interface Props {
  url?: string
}

export function InvalidPageView({ url }: Props) {
  return (
    <div className="p-4 text-center">
      <div className="text-4xl mb-4">📄</div>
      <h2 className="text-lg font-semibold text-gray-900 mb-2">Not a LinkedIn Profile</h2>
      <p className="text-sm text-gray-600 mb-4">
        Navigate to a LinkedIn profile page to use this extension.
      </p>
      {url && (
        <p className="text-xs text-gray-400 break-all">{url}</p>
      )}
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/InvalidPageView.tsx')
