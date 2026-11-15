import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { z } from 'zod'
import { useAuthStore } from '../store/auth'

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean }

const userSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  role: z.enum(['user', 'admin']),
})
const ticketSchema = z.object({
  id: z.number(),
  subject: z.string(),
  conversation_id: z.number(),
  category: z.string(),
  priority: z.enum(['low', 'medium', 'high']),
  status: z.enum(['open', 'in_progress', 'resolved']),
  replies: z
    .array(
      z.object({ id: z.number(), text: z.string(), created_at: z.string() }),
    )
    .default([]),
  created_at: z.string(),
})
const chatSchema = z.object({
  conversation_id: z.number(),
  message_id: z.number(),
  reply: z.string(),
  category: z.string(),
  confidence: z.number().min(0).max(1),
  similarity: z.number().min(0).max(1),
  mode: z.enum(['matched', 'default', 'fallback']),
  escalated: z.boolean(),
  ticket_id: z.number().nullable().optional(),
})
const conversationSummarySchema = z.object({
  id: z.number(),
  title: z.string(),
  updated_at: z.string(),
})
const conversationDetailSchema = conversationSummarySchema.extend({
  messages: z.array(
    z.object({
      id: z.number(),
      role: z.enum(['user', 'assistant', 'agent']),
      text: z.string(),
      category: z.string().nullable().optional(),
      confidence: z.number().nullable().optional(),
      escalated: z.boolean().optional(),
      created_at: z.string(),
    }),
  ),
})
const knowledgeSchema = z.object({
  id: z.number(),
  message: z.string(),
  category: z.string(),
  response: z.string(),
  enabled: z.boolean(),
})

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use((response) => {
  const url = (response.config.url || '').split('?')[0]
  if (url.endsWith('/auth/register') || url.endsWith('/auth/me'))
    userSchema.parse(response.data)
  else if (url.endsWith('/auth/login')) {
    z.object({
      access_token: z.string(),
      token_type: z.literal('bearer'),
      user: userSchema,
    }).parse(response.data)
  } else if (url.endsWith('/auth/refresh'))
    z.object({ access_token: z.string() }).parse(response.data)
  else if (url.endsWith('/chat')) chatSchema.parse(response.data)
  else if (url.endsWith('/conversations'))
    z.array(conversationSummarySchema).parse(response.data)
  else if (/\/conversations\/\d+$/.test(url))
    conversationDetailSchema.parse(response.data)
  else if (/\/tickets\/\d+$/.test(url) || /\/admin\/tickets\/\d+$/.test(url))
    ticketSchema.parse(response.data)
  else if (url.endsWith('/tickets') || url.endsWith('/admin/tickets'))
    z.array(ticketSchema).parse(response.data)
  else if (url.endsWith('/admin/stats')) {
    z.object({
      open_tickets: z.number(),
      resolved_today: z.number(),
      escalation_rate: z.number(),
      avg_confidence: z.number(),
      by_category: z.array(
        z.object({ category: z.string(), count: z.number() }),
      ),
    }).parse(response.data)
  } else if (url.endsWith('/admin/knowledge'))
    z.array(knowledgeSchema).parse(response.data)
  else if (/\/admin\/knowledge\/\d+$/.test(url))
    knowledgeSchema.parse(response.data)
  else if (url.endsWith('/admin/users'))
    z.array(userSchema).parse(response.data)
  else if (url.endsWith('/admin/retrain'))
    z.object({ accuracy: z.number(), samples: z.number() }).parse(response.data)
  return response
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshRequest: Promise<string> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined
    if (
      error.response?.status !== 401 ||
      !config ||
      config._retry ||
      config.url?.includes('/auth/login') ||
      config.url?.includes('/auth/register') ||
      config.url?.includes('/auth/refresh')
    ) {
      return Promise.reject(error)
    }

    config._retry = true
    refreshRequest ??= axios
      .post<{ access_token: string }>(
        `${api.defaults.baseURL}/auth/refresh`,
        {},
        { withCredentials: true, headers: { 'X-Requested-With': 'fetch' } },
      )
      .then(
        ({ data }) =>
          z.object({ access_token: z.string() }).parse(data).access_token,
      )
      .finally(() => {
        refreshRequest = null
      })

    try {
      const token = await refreshRequest
      useAuthStore.getState().setAccessToken(token)
      config.headers.Authorization = `Bearer ${token}`
      return api(config)
    } catch (refreshError) {
      useAuthStore.getState().clearAuth()
      return Promise.reject(refreshError)
    }
  },
)

export interface User {
  id: number
  email: string
  name: string
  role: 'user' | 'admin'
}

export interface ChatResult {
  conversation_id: number
  message_id: number
  mode: 'matched' | 'default' | 'fallback'
  category: string
  confidence: number
  similarity: number
  reply: string
  escalated: boolean
  ticket_id: number | null
}

export interface Ticket {
  id: number
  subject: string
  conversation_id: number
  category: string
  priority: 'low' | 'medium' | 'high'
  status: 'open' | 'in_progress' | 'resolved'
  replies: { id: number; text: string; created_at: string }[]
  created_at: string
}

export interface KnowledgeEntry {
  id: number
  message: string
  category: string
  response: string
  enabled: boolean
}
