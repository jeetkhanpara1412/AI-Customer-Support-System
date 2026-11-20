import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { api, type Ticket } from '../api/client'
import { categoryClassName } from '../components/categoryStyles'
import { Badge, Button, EmptyState, Skeleton } from '../components/ui'

export function TicketsPage() {
  const { ticketId } = useParams()
  const query = useQuery({
    queryKey: ['tickets', ticketId],
    queryFn: async () => {
      if (ticketId)
        return [(await api.get<Ticket>(`/tickets/${ticketId}`)).data]
      return (await api.get<Ticket[]>('/tickets')).data
    },
  })

  if (query.isLoading)
    return (
      <section className="space-y-3" role="status" aria-label="Loading tickets">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
      </section>
    )
  if (query.isError)
    return (
      <EmptyState
        title="Tickets could not be loaded"
        description="Check your connection and try again."
        action={<Button onClick={() => query.refetch()}>Retry</Button>}
      />
    )
  if (ticketId && query.data?.[0]) {
    const ticket = query.data[0]
    return (
      <section className="mx-auto max-w-3xl">
        <Link
          className="text-sm text-indigo-700 underline dark:text-indigo-300"
          to="/tickets"
        >
          Back to my tickets
        </Link>
        <article className="panel mt-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">{ticket.subject}</h1>
              <p className="mt-1 text-slate-600 dark:text-slate-300">
                Ticket #{ticket.id} ·{' '}
                <Badge className={categoryClassName(ticket.category)}>
                  {ticket.category}
                </Badge>
              </p>
            </div>
            <TicketBadge status={ticket.status} priority={ticket.priority} />
          </div>
          <h2 className="mt-8 text-lg font-semibold">Support replies</h2>
          {ticket.replies.length === 0 ? (
            <p className="mt-3 text-slate-600 dark:text-slate-300">
              A support specialist has not replied yet.
            </p>
          ) : (
            <ul className="mt-3 space-y-3">
              {ticket.replies.map((reply) => (
                <li className="chat-bubble chat-bubble-agent" key={reply.id}>
                  <p>{reply.text}</p>
                  <time className="mt-2 block text-xs">
                    {new Date(reply.created_at).toLocaleString()}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>
    )
  }
  if (!query.data?.length)
    return (
      <section>
        <h1 className="mb-6 text-2xl font-bold">My tickets</h1>
        <EmptyState
          title="No support tickets"
          description="Start a chat if you need help. A ticket may be created for human support."
          action={<Link className="button-primary" to="/chat">Start a chat</Link>}
        />
      </section>
    )
  return (
    <section>
      <h1 className="mb-6 text-2xl font-bold">My tickets</h1>
      <div className="grid gap-3">
        {query.data.map((ticket) => (
          <Link
            className="panel flex flex-wrap items-center justify-between gap-3 hover:border-indigo-400"
            to={`/tickets/${ticket.id}`}
            key={ticket.id}
          >
            <div>
              <h2 className="font-semibold">
                #{ticket.id} · {ticket.subject}
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                {ticket.category}
              </p>
            </div>
            <TicketBadge status={ticket.status} priority={ticket.priority} />
          </Link>
        ))}
      </div>
    </section>
  )
}

function TicketBadge({
  status,
  priority,
}: {
  status: Ticket['status']
  priority: Ticket['priority']
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge className={`status-${status}`}>{status.replace('_', ' ')}</Badge>
      <Badge className={`priority-${priority}`}>{priority} priority</Badge>
    </div>
  )
}
