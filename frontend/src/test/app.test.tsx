import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'
import { AuthPage } from '../pages/AuthPage'
import { ChatBubble, ChatPage } from '../pages/ChatPage'
import { StatCard } from '../pages/AdminPage'
import { DataTable } from '../components/DataTable'
import { Layout } from '../components/Layout'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { useAuthStore } from '../store/auth'

vi.mock('../api/client', () => ({
  api: {
    post: vi.fn().mockImplementation((path: string) =>
      Promise.resolve({
        data:
          path === '/chat'
            ? {
                conversation_id: 3,
                message_id: 5,
                reply: 'We can help.',
                category: 'General Inquiry',
                confidence: 0.9,
                similarity: 0.4,
                mode: 'matched',
                escalated: false,
                ticket_id: null,
              }
            : {
                access_token: 'token',
                user: {
                  id: 1,
                  email: 'test@example.com',
                  name: 'Test',
                  role: 'user',
                },
              },
      }),
    ),
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

function renderWithRouter(children: ReactNode, initialEntries = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('customer support UI', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, user: null, bootstrapped: true })
  })

  it('validates required login fields', async () => {
    renderWithRouter(<AuthPage mode="login" />)
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(
      await screen.findByText('Enter a valid email address'),
    ).toBeInTheDocument()
  })

  it('validates registration name and password confirmation', async () => {
    renderWithRouter(<AuthPage mode="register" />)
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'new@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'StrongPassword123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Name is required')).toBeInTheDocument()
    expect(await screen.findByText('Passwords must match')).toBeInTheDocument()
  })

  it('renders chat composer with validation', async () => {
    renderWithRouter(<ChatPage />)
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Enter a message',
    )
  })

  it('sends a chat message through REST when the socket is unavailable', async () => {
    renderWithRouter(<ChatPage />)
    fireEvent.change(screen.getByLabelText('Message'), {
      target: { value: 'I need help' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    expect(await screen.findByText('We can help.')).toBeInTheDocument()
  })

  it('redirects a signed-out visitor to login', async () => {
    renderWithRouter(
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<p>Private</p>} />
        </Route>
        <Route path="/login" element={<p>Login page</p>} />
      </Routes>,
    )
    await waitFor(() =>
      expect(screen.getByText('Login page')).toBeInTheDocument(),
    )
  })

  it('redirects a non-admin user away from admin routes', async () => {
    useAuthStore.setState({
      accessToken: 'token',
      user: { id: 2, email: 'user@example.com', name: 'User', role: 'user' },
    })
    renderWithRouter(
      <Routes>
        <Route element={<ProtectedRoute admin />}>
          <Route path="/" element={<p>Admin</p>} />
        </Route>
        <Route path="/chat" element={<p>Chat page</p>} />
      </Routes>,
    )
    await waitFor(() =>
      expect(screen.getByText('Chat page')).toBeInTheDocument(),
    )
  })

  it('shows the admin shortcut and role badge only for administrators', async () => {
    useAuthStore.setState({
      accessToken: 'token',
      user: { id: 2, email: 'admin@example.com', name: 'Admin User', role: 'admin' },
    })
    const adminView = renderWithRouter(<Layout />)
    expect(screen.getByRole('link', { name: 'Admin' })).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('User menu for Admin User'))
    expect(screen.getByText('Administrator')).toBeInTheDocument()
    adminView.unmount()

    useAuthStore.setState({
      accessToken: 'token',
      user: { id: 3, email: 'user@example.com', name: 'Customer', role: 'user' },
    })
    renderWithRouter(<Layout />)
    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument()
  })

  it('shows category, confidence, and escalation badges on a chat bubble', () => {
    render(
      <ChatBubble
        line={{
          id: 'm1',
          role: 'assistant',
          text: 'Need help',
          category: 'Security / Fraud',
          confidence: 0.88,
          escalated: true,
        }}
      />,
    )
    expect(screen.getByText('Security / Fraud')).toBeInTheDocument()
    expect(screen.getByText('88% confidence')).toBeInTheDocument()
    expect(screen.getByText('Escalated to human')).toBeInTheDocument()
  })

  it('renders stat cards and table empty states', () => {
    render(
      <>
        <StatCard label="Open tickets" value={4} />
        <DataTable columns={[]} rows={[]} emptyMessage="No rows" />
      </>,
    )
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('No rows')).toBeInTheDocument()
  })
})
