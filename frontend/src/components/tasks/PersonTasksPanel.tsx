import { FormEvent, useCallback, useEffect, useState } from 'react'
import { tasksApi, workspaceMembersApi } from '../../api/httpClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { Button } from '../common/Button'
import { Input } from '../common/Input'

interface Task {
  id: string
  title: string
  due_date: string | null
  status: 'open' | 'completed'
}

export function PersonTasksPanel({ personId }: { personId: string }) {
  const { currentWorkspace } = useWorkspaceStore()
  const [tasks, setTasks] = useState<Task[]>([])
  const [title, setTitle] = useState('')
  const [dueDate, setDueDate] = useState('')

  const load = useCallback(async () => {
    if (!currentWorkspace) return
    const result = await tasksApi.list(currentWorkspace.id, { person_id: personId })
    setTasks(result.items)
  }, [currentWorkspace, personId])

  useEffect(() => {
    load()
  }, [load])

  const createTask = async (event: FormEvent) => {
    event.preventDefault()
    if (!currentWorkspace || !title.trim()) return
    const membership = await workspaceMembersApi.getMe(currentWorkspace.id)
    await tasksApi.create(currentWorkspace.id, {
      person_id: personId,
      title: title.trim(),
      due_date: dueDate || null,
      assigned_to: membership.user_id,
    })
    setTitle('')
    setDueDate('')
    await load()
  }

  const toggleTask = async (task: Task) => {
    if (!currentWorkspace) return
    await tasksApi.update(currentWorkspace.id, task.id, {
      status: task.status === 'open' ? 'completed' : 'open',
    })
    await load()
  }

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="mb-4 text-lg font-medium text-gray-900">Tasks</h2>
      <form className="grid gap-3 sm:grid-cols-[1fr_auto_auto]" onSubmit={createTask}>
        <Input
          aria-label="Task title"
          placeholder="Add a task"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <Input
          aria-label="Task due date"
          type="date"
          value={dueDate}
          onChange={(event) => setDueDate(event.target.value)}
        />
        <Button type="submit">Add task</Button>
      </form>
      <div className="mt-4 space-y-2">
        {tasks.length === 0 ? (
          <p className="text-sm text-gray-500">No tasks for this person.</p>
        ) : tasks.map((task) => (
          <label key={task.id} className="flex items-center gap-3 rounded-md border p-3">
            <input
              type="checkbox"
              checked={task.status === 'completed'}
              onChange={() => toggleTask(task)}
            />
            <span className={task.status === 'completed' ? 'text-gray-400 line-through' : ''}>
              {task.title}
            </span>
            {task.due_date && <time className="ml-auto text-xs text-gray-500">{task.due_date}</time>}
          </label>
        ))}
      </div>
    </section>
  )
}
