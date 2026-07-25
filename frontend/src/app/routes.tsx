import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { RequireAuth } from '../auth/RequireAuth'
import { LoginPage } from '../pages/LoginPage'
import { AuthCallbackPage } from '../pages/AuthCallbackPage'
import { AppLayout } from '../components/layout/AppLayout'

const DashboardPage = lazy(() =>
  import('../pages/DashboardPage').then(({ DashboardPage }) => ({ default: DashboardPage }))
)
const PeopleListPage = lazy(() =>
  import('../pages/PeopleListPage').then(({ PeopleListPage }) => ({ default: PeopleListPage }))
)
const PersonCreatePage = lazy(() =>
  import('../pages/PersonCreatePage').then(({ PersonCreatePage }) => ({ default: PersonCreatePage }))
)
const PersonDetailPage = lazy(() =>
  import('../pages/PersonDetailPage').then(({ PersonDetailPage }) => ({ default: PersonDetailPage }))
)
const TemplatesPage = lazy(() =>
  import('../pages/TemplatesPage').then(({ TemplatesPage }) => ({ default: TemplatesPage }))
)
const SettingsPage = lazy(() =>
  import('../pages/SettingsPage').then(({ SettingsPage }) => ({ default: SettingsPage }))
)
const ImportsPage = lazy(() =>
  import('../features/imports/ImportsPage').then(({ ImportsPage }) => ({ default: ImportsPage }))
)
const NotificationsPage = lazy(() =>
  import('../pages/NotificationsPage').then(({ NotificationsPage }) => ({ default: NotificationsPage }))
)
const AnalyticsPage = lazy(() =>
  import('../pages/AnalyticsPage').then(({ AnalyticsPage }) => ({ default: AnalyticsPage }))
)
const TasksPage = lazy(() =>
  import('../pages/TasksPage').then(({ TasksPage }) => ({ default: TasksPage }))
)
const InviteAcceptPage = lazy(() =>
  import('../pages/InviteAcceptPage').then(({ InviteAcceptPage }) => ({ default: InviteAcceptPage }))
)

function RouteFallback() {
  return (
    <div className="space-y-4" aria-label="Loading page">
      <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
      <div className="h-64 animate-pulse rounded-lg bg-gray-200" />
    </div>
  )
}

function lazyRoute(page: React.ReactNode) {
  return <Suspense fallback={<RouteFallback />}>{page}</Suspense>
}

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
          <Route index element={lazyRoute(<DashboardPage />)} />
          <Route path="people" element={lazyRoute(<PeopleListPage />)} />
          <Route path="people/new" element={lazyRoute(<PersonCreatePage />)} />
          <Route path="people/:id" element={lazyRoute(<PersonDetailPage />)} />
          <Route path="templates" element={lazyRoute(<TemplatesPage />)} />
          <Route path="settings" element={lazyRoute(<SettingsPage />)} />
          <Route path="imports" element={lazyRoute(<ImportsPage />)} />
          <Route path="notifications" element={lazyRoute(<NotificationsPage />)} />
          <Route path="analytics" element={lazyRoute(<AnalyticsPage />)} />
          <Route path="tasks" element={lazyRoute(<TasksPage />)} />
          <Route path="invites/accept" element={lazyRoute(<InviteAcceptPage />)} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/app/routes.tsx')
