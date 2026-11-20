import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import type { ReactNode } from 'react'
import { useState } from 'react'
import { api, type User } from '../api/client'
import { useAuthStore } from '../store/auth'

const createAuthSchema = (isRegistration: boolean) =>
  z
    .object({
      name: z.string().trim().optional(),
      email: z.string().email('Enter a valid email address'),
      password: z
        .string()
        .min(10, 'Use at least 10 characters')
        .regex(/[A-Z]/, 'Include an uppercase letter')
        .regex(/[a-z]/, 'Include a lowercase letter')
        .regex(/\d/, 'Include a number'),
      confirm_password: z.string().optional(),
    })
    .superRefine((values, context) => {
      if (isRegistration && !values.name?.trim())
        context.addIssue({
          code: 'custom',
          path: ['name'],
          message: 'Name is required',
        })
      if (isRegistration && values.confirm_password !== values.password) {
        context.addIssue({
          code: 'custom',
          path: ['confirm_password'],
          message: 'Passwords must match',
        })
      }
    })

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const isRegister = mode === 'register'
  const [showPassword, setShowPassword] = useState(false)
  const authSchema = createAuthSchema(isRegister)
  type FormValues = z.infer<typeof authSchema>
  const navigate = useNavigate()
  const setSession = useAuthStore((state) => state.setSession)
  const form = useForm<FormValues>({
    resolver: zodResolver(authSchema),
    defaultValues: { email: '', password: '', name: '', confirm_password: '' },
  })
  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (isRegister)
        await api.post('/auth/register', {
          name: values.name,
          email: values.email,
          password: values.password,
        })
      const { data } = await api.post<{ access_token: string; user: User }>(
        '/auth/login',
        {
          email: values.email,
          password: values.password,
        },
      )
      return data
    },
    onSuccess: ({ access_token, user }) => {
      setSession(access_token, user)
      navigate(user.role === 'admin' ? '/admin' : '/chat')
    },
  })

  return (
    <main className="auth-layout">
      <aside className="auth-brand-panel">
        <div className="mb-10 flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-xl bg-white text-xl font-bold text-indigo-700">
            S
          </span>
          <strong className="text-xl">SupportAI</strong>
        </div>
        <h1 className="max-w-md text-4xl font-bold leading-tight">
          Support that answers in seconds.
        </h1>
        <p className="mt-5 max-w-md text-lg text-indigo-100">
          Instant replies for common questions. Real people for everything that
          needs care.
        </p>
      </aside>
      <section className="auth-form-panel">
        <div className="panel w-full max-w-[380px]">
          <h1 className="mb-2 text-2xl font-bold">
            {isRegister ? 'Create your account' : 'Welcome back'}
          </h1>
          <p className="mb-6 text-slate-600 dark:text-slate-300">
            {isRegister
              ? 'Create an account to start a support conversation.'
              : 'Sign in to continue to your support chat.'}
          </p>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
            noValidate
          >
            {isRegister && (
              <Field label="Name" error={form.formState.errors.name?.message}>
                <input
                  id="name"
                  aria-invalid={Boolean(form.formState.errors.name)}
                  autoComplete="name"
                  {...form.register('name')}
                />
              </Field>
            )}
            <Field label="Email" error={form.formState.errors.email?.message}>
              <input
                id="email"
                aria-invalid={Boolean(form.formState.errors.email)}
                type="email"
                autoComplete="email"
                {...form.register('email')}
              />
            </Field>
            <Field
              label="Password"
              error={form.formState.errors.password?.message}
            >
              <div className="password-field">
                <input
                  id="password"
                  aria-invalid={Boolean(form.formState.errors.password)}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  {...form.register('password')}
                />
                <button
                  type="button"
                  className="password-toggle"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((value) => !value)}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </Field>
            {isRegister && (
              <Field
                label="Confirm password"
                error={form.formState.errors.confirm_password?.message}
              >
                <input
                  id="confirm-password"
                  aria-invalid={Boolean(form.formState.errors.confirm_password)}
                  type="password"
                  autoComplete="new-password"
                  {...form.register('confirm_password')}
                />
              </Field>
            )}
            {mutation.isError && (
              <p className="text-sm text-red-700" role="alert">
                Unable to {mode}. Check your details and try again.
              </p>
            )}
            <button
              className="button-primary w-full"
              type="submit"
              disabled={mutation.isPending}
            >
              {mutation.isPending
                ? 'Please wait…'
                : isRegister
                  ? 'Create account'
                  : 'Sign in'}
            </button>
          </form>
          <p className="mt-5 text-sm">
            {isRegister ? 'Already have an account? ' : 'New here? '}
            <Link
              className="text-indigo-700 underline dark:text-indigo-300"
              to={isRegister ? '/login' : '/register'}
            >
              {isRegister ? 'Sign in' : 'Create an account'}
            </Link>
          </p>
        </div>
      </section>
    </main>
  )
}

function Field({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: ReactNode
}) {
  const id = label.toLowerCase().replaceAll(' ', '-')
  return (
    <div>
      <label className="mb-1 block text-sm font-medium" htmlFor={id}>
        {label}
      </label>
      {children}
      {error && <p className="mt-1 text-sm text-red-700">{error}</p>}
    </div>
  )
}
