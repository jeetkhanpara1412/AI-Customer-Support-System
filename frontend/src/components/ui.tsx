import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary'
}) {
  return (
    <button
      className={`${variant === 'primary' ? 'button-primary' : 'button-secondary'} ${className}`}
      {...props}
    />
  )
}

export function ShieldIcon() {
  return (
    <svg
      aria-hidden="true"
      className="shield-icon"
      viewBox="0 0 20 20"
      fill="none"
    >
      <path
        d="M10 2.25 16 4.5v4.75c0 3.75-2.55 6.55-6 8.5-3.45-1.95-6-4.75-6-8.5V4.5l6-2.25Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path
        d="m7.5 9.75 1.65 1.65L12.75 7.8"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function IconButton({
  label,
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      type="button"
      className={`icon-button ${className}`}
      aria-label={label}
      title={label}
      {...props}
    />
  )
}

export function Card({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return <div className={`panel ${className}`}>{children}</div>
}

export function Badge({
  children,
  tone = 'neutral',
  className = '',
}: {
  children: ReactNode
  tone?: 'primary' | 'neutral' | 'warning' | 'success'
  className?: string
}) {
  return <span className={`badge badge-${tone} ${className}`}>{children}</span>
}

export function Avatar({ name }: { name: string }) {
  const initials = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
  return (
    <span className="avatar" aria-hidden="true">
      {initials || '?'}
    </span>
  )
}

export function Chip({
  children,
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={`chip ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Toast({
  children,
  tone = 'info',
}: {
  children: ReactNode
  tone?: 'success' | 'error' | 'info'
}) {
  const icon = tone === 'success' ? '✓' : tone === 'error' ? '!' : 'i'
  return (
    <p className={`toast toast-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <span className="toast-icon" aria-hidden="true">{icon}</span>
      {children}
    </p>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />
}

export function StatCard({
  label,
  value,
  tone = 'indigo',
  trend = 'Live support metrics',
  icon = '↗',
}: {
  label: string
  value: string | number
  tone?: 'indigo' | 'teal' | 'sky' | 'amber'
  trend?: string
  icon?: string
}) {
  return (
    <article className={`stat-card stat-${tone}`}>
      <div className="stat-icon" aria-hidden="true">{icon}</div>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      <p className="stat-trend"><span aria-hidden="true">↗</span> {trend}</p>
    </article>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state" role="status">
      <h2>{title}</h2>
      <p>{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
