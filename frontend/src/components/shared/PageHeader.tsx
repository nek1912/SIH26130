import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: ReactNode
  actions?: ReactNode
  className?: string
}

// Shared page heading row. Callers pass their existing description and action
// markup unchanged; this component only centralizes the row structure and the
// title treatment. No eyebrow slot: no page in the product currently uses one.
export function PageHeader({ title, description, actions, className = '' }: PageHeaderProps) {
  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {description}
      </div>
      {actions ? <div className="flex gap-3">{actions}</div> : null}
    </div>
  )
}
