import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import type { SystemRole } from '@/types/api'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: SystemRole[]
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { session, loading, role } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-border border-t-primary motion-reduce:animate-none" />
      </div>
    )
  }

  if (!session) return <Navigate to="/login" replace />

  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
