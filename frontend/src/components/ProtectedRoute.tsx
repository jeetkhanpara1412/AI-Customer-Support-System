import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

export function ProtectedRoute({ admin = false }: { admin?: boolean }) {
  const { bootstrapped, accessToken, user } = useAuthStore()
  if (!bootstrapped) return <p className="p-8 text-center" role="status">Loading your session…</p>
  if (!accessToken || !user) return <Navigate to="/login" replace />
  if (admin && user.role !== 'admin') return <Navigate to="/chat" replace />
  return <Outlet />
}
