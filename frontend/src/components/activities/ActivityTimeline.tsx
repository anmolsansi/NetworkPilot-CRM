import { Badge } from '../common/Badge'

interface Activity {
  id: string
  action_type: string
  source: string
  previous_stage: string | null
  new_stage: string | null
  message: string | null
  notes: string | null
  created_at: string
}

const sourceVariant = {
  web_app: 'primary',
  chrome_extension: 'success',
  system: 'default',
} as const

export function ActivityTimeline({ activities }: { activities: Activity[] }) {
  if (activities.length === 0) {
    return (
      <p className="text-sm text-gray-500 text-center py-4">No activities yet</p>
    )
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {activities.map((activity, idx) => (
          <li key={activity.id}>
            <div className="relative pb-8">
              {idx !== activities.length - 1 && (
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" />
              )}
              <div className="relative flex space-x-3">
                <div>
                  <span className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center ring-8 ring-white">
                    <span className="text-primary-600 text-sm">
                      {activity.action_type === 'message_sent' ? '💬' :
                       activity.action_type === 'accepted' ? '✓' :
                       activity.action_type === 'reply_received' ? '↩' : '•'}
                    </span>
                  </span>
                </div>
                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1">
                  <div>
                    <p className="text-sm text-gray-900">
                      <span className="font-medium">{activity.action_type.replace(/_/g, ' ')}</span>
                      {activity.new_stage && (
                        <span className="text-gray-500">
                          {' → '}
                          <Badge variant="primary">{activity.new_stage.replace(/_/g, ' ')}</Badge>
                        </span>
                      )}
                    </p>
                    {activity.notes && (
                      <p className="mt-1 text-sm text-gray-500">{activity.notes}</p>
                    )}
                  </div>
                  <div className="whitespace-nowrap text-right text-sm text-gray-500">
                    <time>{new Date(activity.created_at).toLocaleDateString()}</time>
                    <div className="mt-1">
                      <Badge variant={sourceVariant[activity.source as keyof typeof sourceVariant] || 'default'}>
                        {activity.source.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/components/activities/ActivityTimeline.tsx')
