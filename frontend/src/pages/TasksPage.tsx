import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { peopleApi, tasksApi, workspaceMembersApi } from '../api/httpClient'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { Input } from '../components/common/Input'
import { useWorkspaceStore } from '../stores/workspaceStore'

interface Task {
  id: string
  person_id: string
  person_name: string
  title: string
  description: string | null
  due_date: string | null
  status: 'open' | 'completed'
  assigned_to: string | null
  assignee_email: string | null
}

interface PersonOption {
  id: string
  name: string
}

export function TasksPage() {
  const { currentWorkspace } = useWorkspaceStore()
  const [tasks, setTasks] = useState<Task[]>([])
  const [people, setPeople] = useState<PersonOption[]>([])
  const [scope, setScope] = useState<'mine' | 'all'>('mine')
  const [status, setStatus] = useState<'open' | 'completed'>('open')
  const [form, setForm] = useState({ person_id: '', title: '', description: '', due_date: '' })

  const load = useCallback(async () => {
    if (!currentWorkspace) return
    const [membership, peopleResult] = await Promise.all([
      workspaceMembersApi.getMe(currentWorkspace.id),
      peopleApi.list({ workspace_id: currentWorkspace.id, limit: '100' }),
    ])
    const params: Record<string, string> = { status }
    if (scope === 'mine') params.assigned_to = membership.user_id
    const taskResult = await tasksApi.list(currentWorkspace.id, params)
    setTasks(taskResult.items)
    setPeople(peopleResult.items)
  }, [currentWorkspace, scope, status])

  useEffect(() => {
    load()
  }, [load])

  if (!currentWorkspace) {
    return <EmptyState title="Create a workspace first" description="Tasks belong to a workspace." />
  }

  const createTask = async (event: FormEvent) => {
    event.preventDefault()
    if (!form.person_id || !form.title.trim()) return
    const membership = await workspaceMembersApi.getMe(currentWorkspace.id)
    await tasksApi.create(currentWorkspace.id, {
      person_id: form.person_id,
      title: form.title.trim(),
      description: form.description.trim() || null,
      due_date: form.due_date || null,
      assigned_to: membership.user_id,
    })
    setForm({ person_id: '', title: '', description: '', due_date: '' })
    await load()
  }

  const toggleTask = async (task: Task) => {
    await tasksApi.update(currentWorkspace.id, task.id, {
      status: task.status === 'open' ? 'completed' : 'open',
    })
    await load()
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Tasks</h1>
          <p className="mt-1 text-sm text-gray-500">Track follow-ups and work assigned to people.</p>
        </div>
        <div className="flex gap-2">
          <Button variant={scope === 'mine' ? 'primary' : 'secondary'} onClick={() => setScope('mine')}>My tasks</Button>
          <Button variant={scope === 'all' ? 'primary' : 'secondary'} onClick={() => setScope('all')}>All tasks</Button>
          <Button variant={status === 'open' ? 'primary' : 'secondary'} onClick={() => setStatus(status === 'open' ? 'completed' : 'open')}>
            {status === 'open' ? 'Open' : 'Completed'}
          </Button>
        </div>
      </div>

      <form className="mt-6 grid gap-3 rounded-lg bg-white p-4 shadow sm:grid-cols-2" onSubmit={createTask}>
        <label className="text-sm font-medium text-gray-700">
          Person
          <select
            className="mt-1 block w-full rounded-md border-gray-300"
            value={form.person_id}
            onChange={(event) => setForm({ ...form, person_id: event.target.value })}
          >
            <option value="">Select a person</option>
            {people.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
          </select>
        </label>
        <Input label="Task" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        <Input label="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        <Input label="Due date" type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} />
        <Button type="submit">Create task</Button>
      </form>

      <div className="mt-6 space-y-3">
        {tasks.length === 0 ? (
          <EmptyState title="No tasks in this view" description="Create a task or change the current filters." />
        ) : tasks.map((task) => (
          <article key={task.id} className="flex items-start gap-3 rounded-lg bg-white p-4 shadow">
            <input type="checkbox" checked={task.status === 'completed'} onChange={() => toggleTask(task)} />
            <div className="min-w-0 flex-1">
              <div className={task.status === 'completed' ? 'text-gray-400 line-through' : 'font-medium text-gray-900'}>{task.title}</div>
              <Link className="text-sm text-primary-600" to={`/people/${task.person_id}`}>{task.person_name}</Link>
              {task.description && <p className="mt-1 text-sm text-gray-600">{task.description}</p>}
            </div>
            <div className="text-right text-xs text-gray-500">
              {task.due_date && <time>{task.due_date}</time>}
              <div>{task.assignee_email || 'Unassigned'}</div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
