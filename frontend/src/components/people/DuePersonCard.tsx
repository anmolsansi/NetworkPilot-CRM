import { Badge } from '../common/Badge'
import { Button } from '../common/Button'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { peopleApi } from '../../api/httpClient'

interface DuePersonCardProps {
  person: {
    id: string
    name: string
    company: string | null
    role: string | null
    linkedin_url: string
    stage: string
    priority: string
    next_action_type: string | null
    next_action_date: string | null
    last_action_type: string | null
  }
  onUpdate: () => void
}

const priorityVariant = {
  A: 'danger',
  B: 'warning',
  C: 'default',
} as const

const stageLabels: Record<string, string> = {
  invite_sent: 'Invite Sent',
  invite_pending: 'Invite Pending',
  accepted: 'Accepted',
  waiting_for_reply: 'Waiting for Reply',
  follow_up_1_sent: 'Follow-up 1 Sent',
  follow_up_2_sent: 'Follow-up 2 Sent',
  replied: 'Replied',
  archived: 'Archived',
}

export function DuePersonCard({ person, onUpdate }: DuePersonCardProps) {
  const { currentWorkspace } = useWorkspaceStore()

  const handleSnooze = async () => {
    if (!currentWorkspace) return

    try {
      await peopleApi.snooze(
        person.id,
        { until_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] },
        currentWorkspace.id
      )
      onUpdate()
    } catch (error) {
      console.error('Failed to snooze:', error)
    }
  }

  const isOverdue = person.next_action_date && new Date(person.next_action_date) < new Date()

  return (
    <div className={`bg-white shadow rounded-lg p-4 ${isOverdue ? 'border-l-4 border-red-500' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-3">
            <h3 className="text-sm font-medium text-gray-900 truncate">{person.name}</h3>
            <Badge variant={priorityVariant[person.priority as keyof typeof priorityVariant]}>
              {person.priority}
            </Badge>
            <Badge variant="primary">{stageLabels[person.stage] || person.stage}</Badge>
          </div>
          {(person.company || person.role) && (
            <p className="mt-1 text-sm text-gray-500 truncate">
              {[person.role, person.company].filter(Boolean).join(' at ')}
            </p>
          )}
          {person.next_action_type && (
            <p className="mt-1 text-sm text-gray-600">
              Next: <span className="font-medium">{person.next_action_type.replace(/_/g, ' ')}</span>
              {person.next_action_date && (
                <span className={`ml-2 ${isOverdue ? 'text-red-600 font-medium' : ''}`}>
                  {new Date(person.next_action_date).toLocaleDateString()}
                </span>
              )}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2 ml-4">
          <a
            href={person.linkedin_url.startsWith('http') ? person.linkedin_url : `https://${person.linkedin_url}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-sm"
          >
            LinkedIn
          </a>
          <Button variant="ghost" size="sm" onClick={handleSnooze}>
            Snooze 7d
          </Button>
        </div>
      </div>
    </div>
  )
}
