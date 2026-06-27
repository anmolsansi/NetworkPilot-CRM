import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { RequireAuth } from '../auth/RequireAuth'
import { LoginPage } from '../pages/LoginPage'
import { DashboardPage } from '../pages/DashboardPage'
import { PeopleListPage } from '../pages/PeopleListPage'
import { PersonDetailPage } from '../pages/PersonDetailPage'
import { TemplatesPage } from '../pages/TemplatesPage'
import { SettingsPage } from '../pages/SettingsPage'
import { AppLayout } from '../components/layout/AppLayout'

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
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
          <Route path="people/:id" element={<PersonDetailPage />} />
          <Route path="templates" element={<TemplatesPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
