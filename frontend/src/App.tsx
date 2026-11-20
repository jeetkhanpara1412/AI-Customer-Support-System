import {
  Component,
  lazy,
  Suspense,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import axios from 'axios'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { api, type User } from './api/client'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Button, Skeleton } from './components/ui'
import { AuthPage } from './pages/AuthPage'
import { useAuthStore, useUiStore } from './store/auth'

const queryClient = new QueryClient()
let sessionBootstrapRequest: Promise<boolean> | null = null
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
          <Button type="button" onClick={() => window.location.reload()}>
            Try again
          </Button>
        </main>
      )
    return this.props.children
  }
}

function SessionBootstrap() {
  const [apiUnavailable, setApiUnavailable] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const darkMode = useUiStore((state) => state.darkMode)
  const bootstrapped = useAuthStore((state) => state.bootstrapped)

  useEffect(() => {
    let active = true
    useAuthStore.getState().setBootstrapped(false)
    sessionBootstrapRequest ??= restoreSession()
    const request = sessionBootstrapRequest
    void request.then((unavailable) => {
      if (!active) return
      setApiUnavailable(unavailable)
      useAuthStore.getState().setBootstrapped(true)
    }).finally(() => {
      if (sessionBootstrapRequest === request) sessionBootstrapRequest = null
    })
    return () => {
      active = false
    }
  }, [retryCount])

  return (
    <div className={`app-root${darkMode ? ' dark' : ''}`}>
      {!bootstrapped ? (
        <main className="session-screen" role="status" aria-label="Restoring session">
          <div className="session-card">
            <span className="brand-mark" aria-hidden="true">S</span>
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-64" />
            <p>Restoring your secure session…</p>
          </div>
        </main>
      ) : apiUnavailable ? (
        <main className="error-page session-screen" role="alert">
          <div>
            <h1>Support is temporarily unavailable</h1>
            <p>We couldn’t reach the support service. Check your connection and try again.</p>
            <Button
              type="button"
              onClick={() => {
                setApiUnavailable(false)
                setRetryCount((count) => count + 1)
              }}
            >
              Retry connection
            </Button>
          </div>
        </main>
      ) : (
        <BrowserRouter>
          <Suspense
            fallback={
              <main className="session-screen" role="status">
                <div className="session-card">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-64" />
                  <p>Loading page…</p>
                </div>
              </main>
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
      )}
    </div>
  )
}

async function restoreSession(): Promise<boolean> {
  try {
    const { accessToken, user } = useAuthStore.getState()
    if (accessToken && user) return false
    if (!accessToken) {
      const { data } = await api.post<{ access_token: string }>(
        '/auth/refresh',
        {},
        {
          headers: { 'X-Requested-With': 'fetch' },
        },
      )
      useAuthStore.getState().setAccessToken(data.access_token)
    }
    const currentUser = await api.get<User>('/auth/me')
    useAuthStore.getState().setUser(currentUser.data)
    return false
  } catch (error) {
    useAuthStore.getState().clearAuth()
    return (
      axios.isAxiosError(error) &&
      (!error.response || error.response.status >= 500)
    )
  }
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
