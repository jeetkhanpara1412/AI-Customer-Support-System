import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'

import { api, type ChatResult } from '../api/client'
import { useAuthStore } from '../store/auth'

const chatSchema = z.object({
  message: z.string().trim().min(1, 'Enter a message').max(1000, 'Maximum 1000 characters'),
})

type ChatValues = z.infer<typeof chatSchema>
type ChatLine = {
  id: string
  role: 'user' | 'assistant' | 'agent'
  text: string
  category?: string
  confidence?: number
  escalated?: boolean
}
type SocketEvent = ChatResult & {
  type: 'typing' | 'assistant_message' | 'agent_message' | 'error'
  text?: string
  ticket_id?: number
  message?: string
}

export function ChatPage() {
  const token = useAuthStore((state) => state.accessToken)
  const user = useAuthStore((state) => state.user)
  const [lines, setLines] = useState<ChatLine[]>([])
  const [conversationId, setConversationId] = useState<number>()
  const [connection, setConnection] = useState<'connecting' | 'connected' | 'offline'>('connecting')
  const [typing, setTyping] = useState(false)
  const [socketError, setSocketError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const socket = useRef<WebSocket | null>(null)
  const pendingSocketMessage = useRef<string | null>(null)
  const queryClient = useQueryClient()
  const form = useForm<ChatValues>({
    resolver: zodResolver(chatSchema),
    defaultValues: { message: '' },
  })
  const conversations = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => (await api.get<{ id: number; title: string; updated_at: string }[]>('/conversations')).data,
  })
  const mutation = useMutation({
    mutationFn: async (request: { message: string; alreadyRendered: boolean }) => (
      await api.post<ChatResult>('/chat', {
        message: request.message,
        conversation_id: conversationId,
      })
    ).data,
    onSuccess: (result, { message, alreadyRendered }) => {
      setConversationId(result.conversation_id)
      pendingSocketMessage.current = null
      setLines((previous) => [
        ...previous,
        ...(alreadyRendered ? [] : [{ id: `u-${Date.now()}`, role: 'user' as const, text: message }]),
        {
          id: `a-${result.message_id}`,
          role: 'assistant',
          text: result.reply,
          category: result.category,
          confidence: result.confidence,
          escalated: result.escalated,
        },
      ])
      setTyping(false)
      setSocketError('')
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
  const sendRest = mutation.mutate

  useEffect(() => {
    if (!token) return
    let disposed = false
    let retryTimer: ReturnType<typeof setTimeout> | undefined
    const connect = () => {
      if (disposed) return
      setConnection('connecting')
      const wsBase = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat`
      const ws = new WebSocket(wsBase)
      socket.current = ws
      ws.onopen = () => {
        ws.send(JSON.stringify({ type: 'auth', access_token: token }))
        setConnection('connected')
        setSocketError('')
      }
      ws.onmessage = (event: MessageEvent<string>) => {
        const data = JSON.parse(event.data) as SocketEvent
        if (data.type === 'typing') {
          setTyping(true)
          return
        }
        if (data.type === 'error') {
          pendingSocketMessage.current = null
          setTyping(false)
          setSocketError(data.message || 'Live chat reported an error.')
          return
        }
        if (data.type === 'agent_message') {
          setTyping(false)
          setLines((previous) => [...previous, {
            id: `agent-${Date.now()}`,
            role: 'agent',
            text: data.text || '',
          }])
          return
        }
        if (data.type === 'assistant_message') {
          pendingSocketMessage.current = null
          setConversationId(data.conversation_id)
          setTyping(false)
          setLines((previous) => [...previous, {
            id: `assistant-${data.message_id}`,
            role: 'assistant',
            text: data.reply,
            category: data.category,
            confidence: data.confidence,
            escalated: data.escalated,
          }])
          queryClient.invalidateQueries({ queryKey: ['tickets'] })
          queryClient.invalidateQueries({ queryKey: ['conversations'] })
        }
      }
      ws.onerror = () => setConnection('offline')
      ws.onclose = () => {
        socket.current = null
        setConnection('offline')
        if (!disposed && pendingSocketMessage.current) {
          const message = pendingSocketMessage.current
          pendingSocketMessage.current = null
          sendRest({ message, alreadyRendered: true })
        }
        if (!disposed) retryTimer = setTimeout(connect, 2000)
      }
    }
    connect()
    return () => {
      disposed = true
      if (retryTimer) clearTimeout(retryTimer)
      socket.current?.close()
      socket.current = null
    }
  }, [token, queryClient, sendRest])

  function newConversation() {
    setConversationId(undefined)
    setLines([])
    setSocketError('')
  }

  async function openConversation(id: number) {
    setConversationId(id)
    setSocketError('')
    try {
      const { data } = await api.get<{
        messages: { id: number; role: ChatLine['role']; text: string; category?: string; confidence?: number; escalated?: boolean }[]
      }>(`/conversations/${id}`)
      setLines(data.messages.map((line) => ({ ...line, id: String(line.id) })))
    } catch {
      setSocketError('This conversation could not be loaded.')
    }
  }

  function submit({ message }: ChatValues) {
    if (socket.current?.readyState === WebSocket.OPEN) {
      setLines((previous) => [...previous, { id: `user-${Date.now()}`, role: 'user', text: message }])
      setTyping(true)
      setSocketError('')
      pendingSocketMessage.current = message
      socket.current.send(JSON.stringify({
        type: 'user_message',
        text: message,
        conversation_id: conversationId,
      }))
    } else {
      mutation.mutate({ message, alreadyRendered: false })
    }
    form.reset()
  }

  return (
    <div className="chat-shell">
      <aside className={`chat-sidebar ${sidebarOpen ? 'chat-sidebar-open' : ''}`} aria-label="Conversation history">
        <div className="flex items-center justify-between gap-2">
          <strong className="text-lg text-indigo-800 dark:text-indigo-200">SupportAI</strong>
          <button type="button" className="button-primary" onClick={newConversation}>New chat</button>
        </div>
        <p className="mt-8 text-xs font-semibold uppercase tracking-wider text-slate-500">Recent</p>
        {conversations.isLoading ? <p role="status" className="mt-3 text-sm">Loading conversations…</p>
          : conversations.isError ? <p role="alert" className="mt-3 text-sm">History could not be loaded.</p>
            : <ul className="mt-2 space-y-1">
              {conversations.data?.map((item) => (
                <li key={item.id}>
                  <button
                    className={`conversation-link ${conversationId === item.id ? 'conversation-active' : ''}`}
                    type="button"
                    onClick={() => {
                      setSidebarOpen(false)
                      void openConversation(item.id)
                    }}
                  >
                    {item.title || 'Conversation'}
                  </button>
                </li>
              ))}
            </ul>}
        <div className="mt-auto border-t border-slate-200 pt-4 dark:border-slate-700">
          <p className="font-medium">{user?.name}</p>
          <Link className="mt-2 inline-block text-sm text-indigo-700 underline dark:text-indigo-300" to="/tickets">My tickets</Link>
        </div>
      </aside>
      <section className="min-w-0 flex-1">
        <header className="chat-header">
          <div className="flex min-w-0 items-center gap-3">
            <button type="button" className="button-secondary mobile-sidebar-toggle" aria-label="Toggle conversation history" aria-expanded={sidebarOpen} onClick={() => setSidebarOpen((open) => !open)}>History</button>
            <h1 className="truncate font-semibold">{conversationId ? 'Support conversation' : 'New conversation'}</h1>
          </div>
          <span className={connection === 'connected' ? 'live-pill' : 'offline-pill'}>{connection === 'connected' ? 'Live' : 'Reconnecting'}</span>
        </header>
        <div className="chat-content">
          <div className="chat-messages" aria-live="polite">
            {lines.length === 0 && <div className="empty-chat"><h2>How can we help?</h2><p>Send a message and our support assistant will get started.</p></div>}
            {lines.map((line) => <ChatBubble line={line} key={line.id} />)}
            {(typing || mutation.isPending) && <p className="typing-indicator" role="status">Support is typing…</p>}
          </div>
          {socketError && <p className="mb-2 text-sm text-red-700" role="alert">{socketError} {connection !== 'connected' && 'Your next message will use the secure REST fallback.'}</p>}
          {mutation.isError && <p className="mb-2 text-sm text-red-700" role="alert">Message could not be sent. Please retry.</p>}
          <form className="chat-composer" onSubmit={(event) => {
            event.preventDefault()
            void form.handleSubmit(submit)(event)
          }}>
            <label className="sr-only" htmlFor="chat-message">Message</label>
            <input id="chat-message" className="min-w-0 flex-1" maxLength={1000} aria-invalid={Boolean(form.formState.errors.message)} placeholder="Write your message…" {...form.register('message')} />
            <button className="button-primary min-h-11" type="submit" disabled={mutation.isPending || typing}>Send</button>
          </form>
          {form.formState.errors.message && <p className="mt-2 text-sm text-red-700" role="alert">{form.formState.errors.message.message}</p>}
        </div>
      </section>
    </div>
  )
}

export function ChatBubble({ line }: { line: ChatLine }) {
  const bubbleClass = line.role === 'user'
    ? 'chat-bubble chat-bubble-user'
    : line.role === 'agent'
      ? 'chat-bubble chat-bubble-agent'
      : 'chat-bubble chat-bubble-assistant'
  return (
    <article className={`chat-line ${line.role === 'user' ? 'chat-line-user' : ''}`}>
      <div className={bubbleClass}>
        {line.role === 'agent' && <p className="mb-1 text-xs font-semibold">Support agent</p>}
        <p className="whitespace-pre-wrap">{line.text}</p>
      </div>
      {line.category && <div className="mt-2 flex flex-wrap gap-2">
        <span className="badge badge-primary">{line.category}</span>
        <span className="badge badge-neutral">{Math.round((line.confidence ?? 0) * 100)}% confidence</span>
        {line.escalated && <span className="badge badge-warning">Escalated to human</span>}
      </div>}
    </article>
  )
}
