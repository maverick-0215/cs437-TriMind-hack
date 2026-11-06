import { BrowserRouter, Route, Routes } from 'react-router'
import { AuthProvider, RequireAdmin, RequireLogin, RequireStudent } from './auth'
import Layout from './Layout'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminHandoversPage from './pages/admin/AdminHandoversPage'
import AdminItemNewPage from './pages/admin/AdminItemNewPage'
import AdminItemPage from './pages/admin/AdminItemPage'
import ClaimPage from './pages/ClaimPage'
import ClaimsPage from './pages/ClaimsPage'
import FoundListPage from './pages/FoundListPage'
import LoginPage from './pages/LoginPage'
import NotificationsPage from './pages/NotificationsPage'
import ReportDetailPage from './pages/ReportDetailPage'
import ReportNewPage from './pages/ReportNewPage'
import ReportsPage from './pages/ReportsPage'

export function AppRoutes() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireLogin />}>
          <Route element={<Layout />}>
            <Route index element={<FoundListPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route element={<RequireStudent />}>
              <Route path="items/:id/claim" element={<ClaimPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="reports/new" element={<ReportNewPage />} />
              <Route path="reports/:id" element={<ReportDetailPage />} />
              <Route path="claims" element={<ClaimsPage />} />
            </Route>
            <Route path="admin" element={<RequireAdmin />}>
              <Route index element={<AdminDashboardPage />} />
              <Route path="items/new" element={<AdminItemNewPage />} />
              <Route path="items/:id" element={<AdminItemPage />} />
              <Route path="handovers" element={<AdminHandoversPage />} />
            </Route>
            <Route path="*" element={<h1>Page not found</h1>} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
