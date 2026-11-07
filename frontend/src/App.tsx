import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AuthProvider, RequireAdmin, RequireLogin, RequireStudent } from './auth'
import Layout from './Layout'
import AdminAdminsPage from './pages/admin/AdminAdminsPage'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminHandoversPage from './pages/admin/AdminHandoversPage'
import AdminItemNewPage from './pages/admin/AdminItemNewPage'
import AdminItemPage from './pages/admin/AdminItemPage'
import ClaimsPage from './pages/ClaimsPage'
import GuidePage from './pages/GuidePage'
import LoginPage from './pages/LoginPage'
import NotificationsPage from './pages/NotificationsPage'
import ReportDetailPage from './pages/ReportDetailPage'
import ReportNewPage from './pages/ReportNewPage'
import ReportsPage from './pages/ReportsPage'

/** Home is the guide: the first page everyone sees after signing in. */
function Home() {
  return <Navigate to="/guide" replace />
}

export function AppRoutes() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireLogin />}>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="guide" element={<GuidePage />} />
            <Route element={<RequireStudent />}>
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
              <Route path="admins" element={<AdminAdminsPage />} />
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
