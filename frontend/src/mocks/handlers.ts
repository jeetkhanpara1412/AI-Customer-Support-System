import { http, HttpResponse } from 'msw'

import type { ChatResult, KnowledgeEntry, Ticket, User } from '../api/client'

const user: User = { id: 1, name: 'Alex Morgan', email: 'alex@example.com', role: 'user' }
const admin: User = { id: 2, name: 'Support Admin', email: 'admin@example.com', role: 'admin' }
const examples: KnowledgeEntry[] = [
  { id: 1, message: 'How do I reset my password?', category: 'Account Access', response: 'Use the password reset link on the sign-in page.', enabled: true },
]
const tickets: Ticket[] = []
const conversations: { id: number; title: string; updated_at: string }[] = []
const ticketReplies = new Map<number, Ticket['replies']>()
let nextId = 1

function currentUser(request: Request) {
  return request.headers.get('authorization')?.includes('admin-token') ? admin : user
}

function createReply(text: string): ChatResult {
  const lowered = text.toLowerCase()
  const fraud = /fraud|unauthori[sz]ed|suspicious|hacked|stolen|don't recognize|unrecognized/.test(lowered)
  const category = fraud ? 'Security / Fraud' : lowered.includes('refund') ? 'Refund' : 'General Inquiry'
  const escalated = fraud || lowered.includes('human')
  const conversationId = nextId++
  conversations.unshift({ id: conversationId, title: text.slice(0, 60), updated_at: new Date().toISOString() })
  const result: ChatResult = {
    conversation_id: conversationId,
    message_id: nextId++,
    reply: fraud ? 'Your security concern has been escalated to a human support specialist.' : 'Thanks for reaching out. Our support team is happy to help.',
    category,
    confidence: 0.91,
    similarity: 0.42,
    mode: fraud ? 'fallback' : 'matched',
    escalated,
    ticket_id: null,
  }
  if (escalated) {
    const ticketId = nextId++
    result.ticket_id = ticketId
    tickets.unshift({
      id: ticketId,
      subject: text.slice(0, 160),
      conversation_id: conversationId,
      category,
      priority: fraud ? 'high' : 'low',
      status: 'open',
      replies: [],
      created_at: new Date().toISOString(),
    })
  }
  return result
}

export const handlers = [
  http.post('*/api/auth/register', async ({ request }) => {
    const body = await request.json() as { name?: string; email?: string }
    return HttpResponse.json({ id: nextId++, name: body.name || 'Customer', email: body.email || user.email, role: 'user' }, { status: 201 })
  }),
  http.post('*/api/auth/login', async ({ request }) => {
    const body = await request.json() as { email?: string }
    const signedInUser = body.email?.includes('admin') ? admin : user
    return HttpResponse.json({ access_token: signedInUser.role === 'admin' ? 'admin-token' : 'mock-access-token', token_type: 'bearer', user: signedInUser })
  }),
  http.post('*/api/auth/refresh', () => HttpResponse.json({ access_token: 'mock-access-token' })),
  http.post('*/api/auth/logout', () => new HttpResponse(null, { status: 204 })),
  http.get('*/api/auth/me', ({ request }) => HttpResponse.json(currentUser(request))),
  http.post('*/api/chat', async ({ request }) => {
    const body = await request.json() as { message: string }
    return HttpResponse.json(createReply(body.message))
  }),
  http.get('*/api/conversations', () => HttpResponse.json(conversations)),
  http.get('*/api/conversations/:id', ({ params }) => HttpResponse.json({
    id: Number(params.id),
    title: conversations.find((item) => item.id === Number(params.id))?.title || 'Conversation',
    updated_at: new Date().toISOString(),
    messages: [],
  })),
  http.get('*/api/tickets', () => HttpResponse.json(tickets)),
  http.get('*/api/tickets/:id', ({ params }) => {
    const ticket = tickets.find((item) => item.id === Number(params.id))
    return ticket ? HttpResponse.json({ ...ticket, replies: ticketReplies.get(ticket.id) || [] }) : HttpResponse.json({ error: { code: 'not_found', message: 'Ticket not found' } }, { status: 404 })
  }),
  http.get('*/api/admin/stats', () => HttpResponse.json({
    open_tickets: tickets.filter((ticket) => ticket.status === 'open').length,
    resolved_today: 0,
    escalation_rate: tickets.length / Math.max(conversations.length, 1),
    avg_confidence: 0.88,
    by_category: Object.entries(tickets.reduce<Record<string, number>>((result, ticket) => {
      result[ticket.category] = (result[ticket.category] || 0) + 1
      return result
    }, {})).map(([category, count]) => ({ category, count })),
  })),
  http.get('*/api/admin/tickets', () => HttpResponse.json(tickets)),
  http.patch('*/api/admin/tickets/:id', async ({ params, request }) => {
    const ticket = tickets.find((item) => item.id === Number(params.id))
    if (!ticket) return HttpResponse.json({ error: { code: 'not_found', message: 'Not found' } }, { status: 404 })
    const body = await request.json() as { status: Ticket['status'] }
    ticket.status = body.status
    return HttpResponse.json(ticket)
  }),
  http.post('*/api/admin/tickets/:id/reply', async ({ params, request }) => {
    const body = await request.json() as { text: string }
    const ticketId = Number(params.id)
    const replies = ticketReplies.get(ticketId) || []
    replies.push({ id: nextId++, text: body.text, created_at: new Date().toISOString() })
    ticketReplies.set(ticketId, replies)
    const ticket = tickets.find((item) => item.id === ticketId)
    if (ticket) ticket.replies = replies
    return HttpResponse.json({ id: nextId++, text: body.text, role: 'agent' })
  }),
  http.get('*/api/admin/knowledge', () => HttpResponse.json(examples)),
  http.post('*/api/admin/knowledge', async ({ request }) => {
    const body = await request.json() as Omit<KnowledgeEntry, 'id' | 'enabled'>
    const entry: KnowledgeEntry = { ...body, id: nextId++, enabled: true }
    examples.push(entry)
    return HttpResponse.json(entry, { status: 201 })
  }),
  http.put('*/api/admin/knowledge/:id', async ({ params, request }) => {
    const index = examples.findIndex((entry) => entry.id === Number(params.id))
    const body = await request.json() as Omit<KnowledgeEntry, 'id' | 'enabled'>
    if (index < 0) return HttpResponse.json({ error: { code: 'not_found', message: 'Not found' } }, { status: 404 })
    examples[index] = { ...examples[index], ...body }
    return HttpResponse.json(examples[index])
  }),
  http.delete('*/api/admin/knowledge/:id', ({ params }) => {
    const index = examples.findIndex((entry) => entry.id === Number(params.id))
    if (index >= 0) examples.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),
  http.post('*/api/admin/retrain', () => HttpResponse.json({ accuracy: 0.87, samples: examples.length })),
  http.get('*/api/admin/users', () => HttpResponse.json([user, admin])),
]
