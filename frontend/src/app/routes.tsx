import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { RequireAuth } from '../auth/RequireAuth'
import { LoginPage } from '../pages/LoginPage'
import { AuthCallbackPage } from '../pages/AuthCallbackPage'
import { DashboardPage } from '../pages/DashboardPage'
import { PeopleListPage } from '../pages/PeopleListPage'
import { PersonCreatePage } from '../pages/PersonCreatePage'
import { PersonDetailPage } from '../pages/PersonDetailPage'
import { TemplatesPage } from '../pages/TemplatesPage'
import { SettingsPage } from '../pages/SettingsPage'
import { ImportsPage } from '../features/imports/ImportsPage'
import { NotificationsPage } from '../pages/NotificationsPage'
import { AnalyticsPage } from '../pages/AnalyticsPage'
import { TasksPage } from '../pages/TasksPage'
import { AppLayout } from '../components/layout/AppLayout'
import { InviteAcceptPage } from '../pages/InviteAcceptPage'

export function AppRoutes() {
  return (
    <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="people" element={<PeopleListPage />} />
          <Route path="people/new" element={<PersonCreatePage />} />
          <Route path="people/:id" element={<PersonDetailPage />} />
          <Route path="templates" element={<TemplatesPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="imports" element={<ImportsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="invites/accept" element={<InviteAcceptPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/app/routes.tsx')
