import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { ProjectListPage } from '@/pages/applicant/ProjectListPage'
import { ProjectCreatePage } from '@/pages/applicant/ProjectCreatePage'
import { ProjectDetailPage } from '@/pages/applicant/ProjectDetailPage'
import { ApplicationListPage } from '@/pages/applicant/ApplicationListPage'
import { ApplicationSubmitPage } from '@/pages/applicant/ApplicationSubmitPage'
import { ApplicantApplicationDetailPage } from '@/pages/applicant/ApplicationDetailPage'
import { QueuePage } from '@/pages/staff/QueuePage'
import { ApplicationDetailPage } from '@/pages/staff/ApplicationDetailPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

function ApplicationDetailRouter() {
  const { role } = useAuth()
  if (role === 'APPLICANT') {
    return <ApplicantApplicationDetailPage />
  }
  return <ApplicationDetailPage />
}

function HomeRedirect() {
  const { role } = useAuth()
  return <Navigate to={role === 'APPLICANT' ? '/projects' : '/queue'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<HomeRedirect />} />

        {/* Applicant routes */}
        <Route
          path="/projects"
          element={
            <ProtectedRoute allowedRoles={['APPLICANT', 'MANAGER', 'ADMIN']}>
              <ProjectListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/new"
          element={
            <ProtectedRoute allowedRoles={['APPLICANT', 'MANAGER', 'ADMIN']}>
              <ProjectCreatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id"
          element={
            <ProtectedRoute allowedRoles={['APPLICANT', 'MANAGER', 'ADMIN']}>
              <ProjectDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id/applications"
          element={
            <ProtectedRoute allowedRoles={['APPLICANT', 'MANAGER', 'ADMIN']}>
              <ApplicationListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id/submit"
          element={
            <ProtectedRoute allowedRoles={['APPLICANT', 'MANAGER', 'ADMIN']}>
              <ApplicationSubmitPage />
            </ProtectedRoute>
          }
        />

        {/* Staff routes */}
        <Route
          path="/queue"
          element={
            <ProtectedRoute allowedRoles={['REVIEWER', 'MANAGER', 'ADMIN']}>
              <QueuePage />
            </ProtectedRoute>
          }
        />

        {/* Application detail - role-based routing */}
        <Route
          path="/applications/:id"
          element={
            <ProtectedRoute allowedRoles={['APPLICANT', 'REVIEWER', 'MANAGER', 'ADMIN']}>
              <ApplicationDetailRouter />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
