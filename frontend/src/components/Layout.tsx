import { useEffect, useState } from 'react'
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import { api } from '../api/client'
import { Avatar, Badge, ShieldIcon, Toast } from './ui'
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
      <header className="app-header">
        <nav
          className="app-nav"
          aria-label="Main navigation"
        >
          <Link
            className="brand-link"
            to="/chat"
          >
            <span className="brand-mark" aria-hidden="true">S</span>
            <span>SupportDesk</span>
          </Link>
          <div className="app-nav-links">
            <NavLink to="/chat">Chat</NavLink>
            <NavLink to="/tickets">My tickets</NavLink>
            {user?.role === 'admin' && (
              <NavLink className="admin-link" to="/admin">
                <ShieldIcon /> Admin
              </NavLink>
            )}
            <button
              type="button"
              className="button-secondary"
              onClick={toggleDarkMode}
              aria-label="Toggle dark mode"
            >
              {darkMode ? 'Light mode' : 'Dark mode'}
            </button>
            <details className="user-menu">
              <summary aria-label={`User menu for ${user?.name || 'account'}`}>
                <Avatar name={user?.name || 'User'} />
                <span className="user-menu-name">{user?.name}</span>
              </summary>
              <div className="user-menu-popover">
                <strong>{user?.name}</strong>
                <span className="user-menu-email">{user?.email}</span>
                <Badge className={`role-${user?.role || 'user'}`}>
                  {user?.role === 'admin' ? 'Administrator' : 'Customer'}
                </Badge>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => void logout()}
                >
                  Sign out
                </button>
              </div>
            </details>
          </div>
        </nav>
      </header>
      {logoutError && (
        <div className="mx-auto max-w-6xl px-4 pt-3">
          <Toast tone="error">
          {logoutError}
          </Toast>
        </div>
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
