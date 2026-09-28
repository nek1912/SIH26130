import type { ReactNode } from 'react'

interface ErrorStateProps {
  message?: string
  className?: string
  children?: ReactNode
}

// Single shared error block. Same destructive-token styling as the previous
// copy-pasted blocks; role="alert" announces it to assistive technology.
export function ErrorState({ message, className = '', children }: ErrorStateProps) {
  if (!message && !children) return null
  return (
    <div role="alert" className={`rounded-md bg-destructive/10 p-3 text-sm text-destructive ${className}`}>
      {children ?? message}
    </div>
  )
}
