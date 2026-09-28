import type { ReactNode } from 'react'

interface DisclosureProps {
  summary: ReactNode
  children: ReactNode
  defaultOpen?: boolean
  className?: string
}

// Shared native disclosure. No JavaScript state, no animation: open/close and
// keyboard behavior come from <details>/<summary>. Panels with stateful
// disclosure behavior (e.g. lazy loading on open) keep their local
// implementation and must not migrate here.
export function Disclosure({ summary, children, defaultOpen = false, className = '' }: DisclosureProps) {
  return (
    <details open={defaultOpen ? true : undefined} className={className}>
      <summary className="cursor-pointer rounded-sm text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">{summary}</summary>
      {children}
    </details>
  )
}
