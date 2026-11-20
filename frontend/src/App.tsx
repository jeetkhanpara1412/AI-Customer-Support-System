import { Component, lazy, Suspense, useEffect, type ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { api, type User } from './api/client'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthPage } from './pages/AuthPage'
import { useAuthStore } from './store/auth'

const queryClient = new QueryClient()
const AdminPage = lazy(() =>
  import('./pages/AdminPage').then((module) => ({ default: module.AdminPage })),
)
const ChatPage = lazy(() =>
  import('./pages/ChatPage').then((module) => ({ default: module.ChatPage })),
)
const TicketsPage = lazy(() =>
  import('./pages/TicketsPage').then((module) => ({
    default: module.TicketsPage,
  })),
)

class AppErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (this.state.failed)
      return (
        <main className="error-page" role="alert">
          <h1>Something went wrong</h1>
          <p>The support app could not display this page.</p>
          <button className="button-primary" type="button" onClick={() => window.location.reload()}>
            Reload
          </button>
        </main>
      )
    return this.props.children
  }
}

function SessionBootstrap() {
  useEffect(() => {
    let active = true
    async function bootstrap() {
      try {
        const { accessToken } = useAuthStore.getState()
        if (accessToken) {
          useAuthStore.getState().setBootstrapped(true)
          return
        }
        const { data } = await api.post<{ access_token: string }>(
          '/auth/refresh',
          {},
          {
            headers: { 'X-Requested-With': 'fetch' },
          },
        )
        if (!active) return
        useAuthStore.getState().setAccessToken(data.access_token)
        const user = await api.get<User>('/auth/me')
        if (active) useAuthStore.getState().setUser(user.data)
      } catch {
        if (active) {
          useAuthStore.getState().clearAuth()
        }
      } finally {
        if (active) useAuthStore.getState().setBootstrapped(true)
      }
    }
    void bootstrap()
    return () => {
      active = false
    }
  }, [])

  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <p className="p-8 text-center" role="status">
            Loading page…
          </p>
        }
      >
        <Routes>
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/tickets" element={<TicketsPage />} />
              <Route path="/tickets/:ticketId" element={<TicketsPage />} />
              <Route element={<ProtectedRoute admin />}>
                <Route path="/admin/*" element={<AdminPage />} />
              </Route>
            </Route>
          </Route>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route
            path="*"
            element={
              <main className="error-page">
                <h1>Page not found</h1>
                <p>The page you requested does not exist.</p>
                <a className="button-primary" href="/chat">Back to support</a>
              </main>
            }
          />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default function App() {
  return (
    <AppErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <SessionBootstrap />
      </QueryClientProvider>
    </AppErrorBoundary>
  )
}
