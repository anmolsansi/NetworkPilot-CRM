import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { workspaceApi, calendarApi } from '../api/httpClient'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Select } from '../components/common/Select'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { EmptyState } from '../components/common/EmptyState'
import { PipelineStagesSettings } from '../components/settings/PipelineStagesSettings'
import { CustomFieldsSettings } from '../components/settings/CustomFieldsSettings'

const timezones = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time' },
  { value: 'America/Chicago', label: 'Central Time' },
  { value: 'America/Denver', label: 'Mountain Time' },
  { value: 'America/Los_Angeles', label: 'Pacific Time' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
]

export function SettingsPage() {
  const navigate = useNavigate()
  const { currentWorkspace, fetchWorkspaces } = useWorkspaceStore()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: '',
    timezone: 'UTC',
    default_follow_up_delay_days: 3,
    default_acceptance_check_delay_days: 1,
  })
  const [calendarLink, setCalendarLink] = useState<string | null>(null)
  const [loadingCalendar, setLoadingCalendar] = useState(false)

  useEffect(() => {
    if (currentWorkspace) {
      setForm({
        name: currentWorkspace.name,
        timezone: currentWorkspace.timezone,
        default_follow_up_delay_days: currentWorkspace.default_follow_up_delay_days,
        default_acceptance_check_delay_days: currentWorkspace.default_acceptance_check_delay_days,
      })
    }
  }, [currentWorkspace])

  const handleSave = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot Settings]', 'Saving workspace settings', {
      workspaceId: currentWorkspace.id.slice(-8),
      timezone: form.timezone,
    })
    setSaving(true)
    setError(null)
    try {
      await workspaceApi.update(currentWorkspace.id, form)
      await fetchWorkspaces()
      console.info('[NetworkPilot Settings]', 'Workspace settings saved', {
        workspaceId: currentWorkspace.id.slice(-8),
      })
    } catch (err: any) {
      console.error('[NetworkPilot Settings]', 'Failed to save workspace settings', {
        workspaceId: currentWorkspace.id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleGenerateCalendarLink = async () => {
    if (!currentWorkspace) return

    console.info('[NetworkPilot Settings]', 'Generating calendar link', {
      workspaceId: currentWorkspace.id.slice(-8),
    })
    setLoadingCalendar(true)
    try {
      const response = await calendarApi.getReminderLink(currentWorkspace.id)
      setCalendarLink(response.url)
      console.info('[NetworkPilot Settings]', 'Calendar link generated', {
        workspaceId: currentWorkspace.id.slice(-8),
      })
    } catch (err: any) {
      console.error('[NetworkPilot Settings]', 'Failed to generate calendar link', {
        workspaceId: currentWorkspace.id.slice(-8),
        message: err.message,
        code: err.code,
      })
      setError(err.message || 'Failed to generate calendar link')
    } finally {
      setLoadingCalendar(false)
    }
  }

  if (!currentWorkspace) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <EmptyState
          title="Create a workspace first"
          description="Create a workspace before configuring workspace settings and reminders."
          action={<Button onClick={() => navigate('/')}>Go to Dashboard</Button>}
        />
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
      <p className="mt-2 text-sm text-gray-600">
        Configure your workspace preferences
      </p>

      {error && <div className="mt-4"><ErrorAlert message={error} /></div>}

      <div className="mt-6 max-w-2xl space-y-6">
        {/* Workspace Settings */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Workspace</h2>
          <div className="space-y-4">
            <Input
              label="Workspace Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <Select
              label="Timezone"
              options={timezones}
              value={form.timezone}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
            />
          </div>
        </div>

        {/* Reminder Settings */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Follow-up Reminders</h2>
          <div className="space-y-4">
            <Input
              label="Default Follow-up Delay (days)"
              type="number"
              min={1}
              max={30}
              value={form.default_follow_up_delay_days}
              onChange={(e) => setForm({ ...form, default_follow_up_delay_days: parseInt(e.target.value) || 3 })}
            />
            <Input
              label="Acceptance Check Delay (days)"
              type="number"
              min={1}
              max={14}
              value={form.default_acceptance_check_delay_days}
              onChange={(e) => setForm({ ...form, default_acceptance_check_delay_days: parseInt(e.target.value) || 1 })}
            />
          </div>
        </div>

        {/* Calendar Link */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Daily Calendar Reminder</h2>
          <p className="text-sm text-gray-600 mb-4">
            Generate a Google Calendar link for a daily reminder to check your follow-ups.
          </p>
          <Button
            variant="secondary"
            onClick={handleGenerateCalendarLink}
            disabled={loadingCalendar}
          >
            {loadingCalendar ? 'Generating...' : 'Generate Calendar Link'}
          </Button>
          {calendarLink && (
            <div className="mt-4 p-3 bg-gray-50 rounded-md">
              <a
                href={calendarLink}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-700 text-sm break-all"
              >
                {calendarLink}
              </a>
            </div>
          )}
        </div>

        {/* Pipeline Stages */}
        <PipelineStagesSettings workspaceId={currentWorkspace.id} />

        {/* Custom Fields */}
        <CustomFieldsSettings />

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>
    </div>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/pages/SettingsPage.tsx')
