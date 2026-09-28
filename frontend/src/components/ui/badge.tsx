import type { ReactNode } from 'react'
import { badgeVariantClasses, type BadgeVariant } from './badgeVariants'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  className?: string
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${badgeVariantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  )
}
