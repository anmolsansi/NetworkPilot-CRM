import { useEffect, useState } from 'react'
import { peopleApi, workspaceMembersApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { Select } from '../common/Select'

interface Member {
  user_id: string
  email: string
  display_name: string | null
}

export function PersonOwnerControl({
  personId,
  ownerId,
  onUpdated,
}: {
  personId: string
  ownerId: string | null
  onUpdated: () => void
}) {
  const { currentWorkspace } = useWorkspaceStore()
  const [members, setMembers] = useState<Member[]>([])

  useEffect(() => {
    if (!currentWorkspace) return
    workspaceMembersApi.list(currentWorkspace.id).then(setMembers)
  }, [currentWorkspace])

  if (!currentWorkspace) return null

  return (
    <Select
      label="Contact owner"
      options={[
        { value: '', label: 'Unassigned' },
        ...members.map(member => ({
          value: member.user_id,
          label: member.display_name || member.email,
        })),
      ]}
      value={ownerId || ''}
      onChange={async (event) => {
        await peopleApi.update(
          personId,
          { owner_id: event.target.value || null },
          currentWorkspace.id,
        )
        onUpdated()
      }}
    />
  )
}
