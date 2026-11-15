import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation } from 'react-router-dom'
import { z } from 'zod'

import { api, type KnowledgeEntry, type Ticket, type User } from '../api/client'

const entrySchema = z.object({
  message: z.string().trim().min(3, 'Enter at least 3 characters').max(1000),
  category: z.string().min(1),
  response: z.string().trim().min(3, 'Enter at least 3 characters').max(2000),
})
const replySchema = z.object({
  text: z.string().trim().min(1, 'Enter a reply').max(1000),
})
const categories = [
  'Account Access',
  'Billing',
  'Refund',
  'Technical Issue',
  'Payment Issue',
  'Order / Delivery',
  'Account Management',
  'Security / Fraud',
  'General Inquiry',
]

interface AdminStats {
  open_tickets: number
  resolved_today: number
  escalation_rate: number
  avg_confidence: number
  by_category: { category: string; count: number }[]
}

export function AdminPage() {
  const { pathname } = useLocation()
  const queryClient = useQueryClient()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const retrain = useMutation({
    mutationFn: () =>
      api.post<{ accuracy: number; samples: number }>('/admin/retrain'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
  const view = pathname.includes('/tickets')
    ? 'tickets'
    : pathname.includes('/knowledge')
      ? 'knowledge'
      : pathname.includes('/users')
        ? 'users'
        : 'dashboard'

  function runRetrain() {
    if (
      window.confirm(
        'Retrain the support model using the current knowledge base?',
      )
    )
      retrain.mutate()
  }

  return (
    <div className="admin-shell">
      <aside
        className={`admin-sidebar ${sidebarOpen ? 'admin-sidebar-open' : ''}`}
      >
        <strong className="text-xl text-indigo-800 dark:text-indigo-200">
          SupportAI Admin
        </strong>
        <nav className="mt-8 space-y-1" aria-label="Admin navigation">
          {[
            ['/admin', 'Dashboard'],
            ['/admin/tickets', 'Tickets'],
            ['/admin/knowledge', 'Knowledge base'],
            ['/admin/users', 'Users'],
          ].map(([to, label]) => (
            <Link
              className={`admin-nav-link ${pathname === to ? 'admin-nav-active' : ''}`}
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
            >
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <section className="min-w-0 flex-1">
        <header className="admin-header">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="button-secondary mobile-sidebar-toggle"
              aria-label="Toggle admin navigation"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen((open) => !open)}
            >
              Menu
            </button>
            <h1 className="text-xl font-semibold">
              {view === 'dashboard'
                ? 'Dashboard'
                : view === 'tickets'
                  ? 'Tickets'
                  : view === 'knowledge'
                    ? 'Knowledge base'
                    : 'Users'}
            </h1>
          </div>
          <button
            className="button-primary"
            type="button"
            onClick={runRetrain}
            disabled={retrain.isPending}
          >
            {retrain.isPending ? 'Retraining…' : 'Retrain model'}
          </button>
        </header>
        <div className="p-5 sm:p-7">
          {retrain.isError && (
            <p className="mb-4 text-sm text-red-700" role="alert">
              Retraining failed. Review the knowledge base and retry.
            </p>
          )}
          {retrain.isSuccess && (
            <p className="mb-4 text-sm text-green-800" role="status">
              Model retrained with {retrain.data.data.samples} examples (
              {Math.round(retrain.data.data.accuracy * 100)}% validation
              accuracy).
            </p>
          )}
          {view === 'dashboard' && <Dashboard />}
          {view === 'tickets' && <AdminTickets />}
          {view === 'knowledge' && <KnowledgeManager />}
          {view === 'users' && <UserTable />}
        </div>
      </section>
    </div>
  )
}

function Dashboard() {
  const stats = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => (await api.get<AdminStats>('/admin/stats')).data,
  })
  const tickets = useQuery({
    queryKey: ['admin-tickets', 'recent'],
    queryFn: async () =>
      (await api.get<Ticket[]>('/admin/tickets?page=1')).data,
  })
  if (stats.isLoading || tickets.isLoading)
    return <p role="status">Loading dashboard…</p>
  if (stats.isError || tickets.isError)
    return <p role="alert">Dashboard data could not be loaded. Please retry.</p>
  const data = stats.data
  if (!data) return <p role="alert">Dashboard statistics are unavailable.</p>
  const max = Math.max(1, ...data.by_category.map((item) => item.count))
  return (
    <div className="space-y-7">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Open tickets" value={data.open_tickets} />
        <StatCard label="Resolved today" value={data.resolved_today} />
        <StatCard
          label="Escalation rate"
          value={`${Math.round(data.escalation_rate * 100)}%`}
        />
        <StatCard
          label="Average confidence"
          value={`${Math.round(data.avg_confidence * 100)}%`}
        />
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <section className="panel">
          <h2 className="mb-5 text-lg font-semibold">Tickets by category</h2>
          {data.by_category.length === 0 ? (
            <p className="text-slate-600">No ticket data yet.</p>
          ) : (
            <div className="space-y-3">
              {data.by_category.map((item) => (
                <div
                  className="grid grid-cols-[minmax(120px,1fr)_2fr_auto] items-center gap-3"
                  key={item.category}
                >
                  <span className="truncate text-sm">{item.category}</span>
                  <div
                    className="h-3 rounded-full bg-slate-100 dark:bg-slate-800"
                    role="img"
                    aria-label={`${item.count} tickets in ${item.category}`}
                  >
                    <div
                      className="h-full rounded-full bg-indigo-600"
                      style={{ width: `${(item.count / max) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">{item.count}</span>
                </div>
              ))}
            </div>
          )}
        </section>
        <section className="panel">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent tickets</h2>
            <Link
              className="text-sm text-indigo-700 underline"
              to="/admin/tickets"
            >
              View all
            </Link>
          </div>
          {tickets.data?.length ? (
            <TicketTable tickets={tickets.data.slice(0, 8)} />
          ) : (
            <p className="text-slate-600">No recent tickets.</p>
          )}
        </section>
      </div>
    </div>
  )
}

function AdminTickets() {
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [priority, setPriority] = useState('')
  const query = useQuery({
    queryKey: ['admin-tickets', status, category, priority],
    queryFn: async () => {
      const search = new URLSearchParams()
      if (status) search.set('status', status)
      if (category) search.set('category', category)
      if (priority) search.set('priority', priority)
      return (await api.get<Ticket[]>(`/admin/tickets?${search}`)).data
    },
  })
  return (
    <section>
      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <label className="text-sm">
          Status
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </label>
        <label className="text-sm">
          Category
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Priority
          <select
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
          >
            <option value="">All priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
      </div>
      {query.isLoading ? (
        <p role="status">Loading tickets…</p>
      ) : query.isError ? (
        <p role="alert">Tickets could not be loaded.</p>
      ) : query.data?.length ? (
        <div className="space-y-3">
          {query.data.map((ticket) => (
            <AdminTicket key={ticket.id} ticket={ticket} />
          ))}
        </div>
      ) : (
        <p className="panel">No tickets match these filters.</p>
      )}
    </section>
  )
}

function AdminTicket({ ticket }: { ticket: Ticket }) {
  const queryClient = useQueryClient()
  const form = useForm<z.infer<typeof replySchema>>({
    resolver: zodResolver(replySchema),
    defaultValues: { text: '' },
  })
  const update = useMutation({
    mutationFn: (status: Ticket['status']) =>
      api.patch(`/admin/tickets/${ticket.id}`, { status }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['admin-tickets'] }),
  })
  const reply = useMutation({
    mutationFn: (values: z.infer<typeof replySchema>) =>
      api.post(`/admin/tickets/${ticket.id}/reply`, values),
    onSuccess: () => {
      form.reset()
      queryClient.invalidateQueries({ queryKey: ['admin-tickets'] })
    },
  })
  return (
    <article className="panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">
            #{ticket.id} · {ticket.subject}
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {ticket.category} · {ticket.priority} priority
          </p>
        </div>
        <label className="text-sm">
          Status
          <select
            aria-label={`Ticket ${ticket.id} status`}
            value={ticket.status}
            onChange={(event) =>
              update.mutate(event.target.value as Ticket['status'])
            }
          >
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </label>
      </div>
      {ticket.replies.map((item) => (
        <p
          className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-950"
          key={item.id}
        >
          {item.text}
        </p>
      ))}
      <form
        className="mt-4 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          void form.handleSubmit((values) => reply.mutate(values))(event)
        }}
      >
        <label className="sr-only" htmlFor={`reply-${ticket.id}`}>
          Reply to ticket {ticket.id}
        </label>
        <input
          id={`reply-${ticket.id}`}
          className="min-w-0 flex-1"
          placeholder="Write an agent reply…"
          {...form.register('text')}
        />
        <button
          className="button-secondary"
          type="submit"
          disabled={reply.isPending}
        >
          Reply
        </button>
      </form>
      {form.formState.errors.text && (
        <p className="mt-1 text-sm text-red-700" role="alert">
          {form.formState.errors.text.message}
        </p>
      )}
      {reply.isError && (
        <p className="mt-1 text-sm text-red-700" role="alert">
          Reply could not be sent.
        </p>
      )}
    </article>
  )
}

function KnowledgeManager() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<number | null>(null)
  const query = useQuery({
    queryKey: ['knowledge'],
    queryFn: async () =>
      (await api.get<KnowledgeEntry[]>('/admin/knowledge')).data,
  })
  const form = useForm<z.infer<typeof entrySchema>>({
    resolver: zodResolver(entrySchema),
    defaultValues: { message: '', category: 'General Inquiry', response: '' },
  })
  const save = useMutation({
    mutationFn: (entry: z.infer<typeof entrySchema>) =>
      editingId
        ? api.put(`/admin/knowledge/${editingId}`, entry)
        : api.post('/admin/knowledge', entry),
    onSuccess: () => {
      form.reset()
      setEditingId(null)
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/knowledge/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledge'] }),
  })
  return (
    <section className="space-y-5">
      <form
        className="panel grid gap-3 md:grid-cols-3"
        onSubmit={(event) => {
          event.preventDefault()
          void form.handleSubmit((values) => save.mutate(values))(event)
        }}
      >
        <label className="text-sm">
          Customer example
          <input {...form.register('message')} />
        </label>
        <label className="text-sm">
          Category
          <select {...form.register('category')}>
            {categories.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Suggested response
          <input {...form.register('response')} />
        </label>
        <div className="flex gap-2 md:col-span-3">
          <button
            className="button-primary"
            type="submit"
            disabled={save.isPending}
          >
            {editingId ? 'Save changes' : 'Add example'}
          </button>
          {editingId && (
            <button
              className="button-secondary"
              type="button"
              onClick={() => {
                form.reset()
                setEditingId(null)
              }}
            >
              Cancel edit
            </button>
          )}
        </div>
        {save.isError && (
          <p className="text-sm text-red-700" role="alert">
            The example could not be saved.
          </p>
        )}
      </form>
      {query.isLoading ? (
        <p role="status">Loading knowledge base…</p>
      ) : query.isError ? (
        <p role="alert">Knowledge base could not be loaded.</p>
      ) : query.data?.length ? (
        <div className="space-y-3">
          {query.data.map((entry) => (
            <article
              className="panel flex flex-wrap items-start justify-between gap-3"
              key={entry.id}
            >
              <div>
                <p className="font-semibold">{entry.message}</p>
                <p className="text-xs text-indigo-800">{entry.category}</p>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                  {entry.response}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => {
                    setEditingId(entry.id)
                    form.reset({
                      message: entry.message,
                      category: entry.category,
                      response: entry.response,
                    })
                  }}
                >
                  Edit
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => {
                    if (window.confirm(`Delete knowledge example ${entry.id}?`))
                      remove.mutate(entry.id)
                  }}
                  disabled={remove.isPending}
                  aria-label={`Delete knowledge example ${entry.id}`}
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="panel">The knowledge base is empty.</p>
      )}
      {remove.isError && (
        <p role="alert">The knowledge example could not be deleted.</p>
      )}
    </section>
  )
}

function UserTable() {
  const query = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => (await api.get<User[]>('/admin/users')).data,
  })
  if (query.isLoading) return <p role="status">Loading users…</p>
  if (query.isError) return <p role="alert">Users could not be loaded.</p>
  if (!query.data?.length) return <p className="panel">No users found.</p>
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <table className="w-full text-left text-sm">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          {query.data.map((user) => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TicketTable({ tickets }: { tickets: Ticket[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr>
            <th>Ticket</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr key={ticket.id}>
              <td>
                <Link
                  className="text-indigo-700 underline"
                  to={`/admin/tickets`}
                >
                  #{ticket.id} {ticket.subject}
                </Link>
              </td>
              <td>{ticket.category}</td>
              <td>{ticket.priority}</td>
              <td>{ticket.status.replace('_', ' ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function StatCard({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <article className="panel">
      <p className="text-sm text-slate-600 dark:text-slate-300">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
    </article>
  )
}
