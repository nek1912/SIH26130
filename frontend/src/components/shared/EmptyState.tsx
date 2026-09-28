import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'

interface EmptyStateProps {
  message: ReactNode
  actions?: ReactNode
  className?: string
}

// Absence-of-content state for list-style pages: centered muted message in a
// card. Not a universal state component — loading, error, and inline panel
// placeholders keep their existing local forms.
export function EmptyState({ message, actions, className = '' }: EmptyStateProps) {
  return (
    <Card className={className}>
      <CardContent className="py-12 text-center text-muted-foreground">
        <p>{message}</p>
        {actions ? <div className="mt-4">{actions}</div> : null}
      </CardContent>
    </Card>
  )
}
