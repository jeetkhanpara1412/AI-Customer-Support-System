import { useEffect, useState } from 'react'
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore, useUiStore } from '../store/auth'

export function Layout() {
  const { user, clearAuth } = useAuthStore()
  const { darkMode, toggleDarkMode } = useUiStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [logoutError, setLogoutError] = useState('')

  useEffect(() => {
    window.localStorage.setItem('support-dark-mode', String(darkMode))
  }, [darkMode])

  async function logout() {
    try {
      await api.post('/auth/logout')
      setLogoutError('')
      clearAuth()
      navigate('/login')
    } catch {
      setLogoutError('Sign out could not be completed. Please retry.')
    }
  }

  return (
    <div className={darkMode ? 'dark min-h-screen' : 'min-h-screen'}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <nav
          className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4"
          aria-label="Main navigation"
        >
          <Link
            className="font-bold text-indigo-700 dark:text-indigo-300"
            to="/chat"
          >
            SupportDesk
          </Link>
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <NavLink to="/chat">Chat</NavLink>
            <NavLink to="/tickets">My tickets</NavLink>
            {user?.role === 'admin' && <NavLink to="/admin">Admin</NavLink>}
            <button
              type="button"
              className="button-secondary"
              onClick={toggleDarkMode}
              aria-label="Toggle dark mode"
            >
              {darkMode ? 'Light mode' : 'Dark mode'}
            </button>
            <button type="button" className="button-secondary" onClick={logout}>
              Sign out
            </button>
          </div>
        </nav>
      </header>
      {logoutError && (
        <p
          className="mx-auto max-w-6xl px-4 pt-3 text-sm text-red-700"
          role="alert"
        >
          {logoutError}
        </p>
      )}
      <main
        id="main-content"
        className={
          location.pathname === '/chat'
            ? 'mx-auto max-w-7xl px-4 py-5'
            : 'mx-auto max-w-6xl px-4 py-8'
        }
      >
        <Outlet />
      </main>
    </div>
  )
}
