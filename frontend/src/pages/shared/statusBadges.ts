import { badgeVariantClasses, type BadgeVariant } from '@/components/ui/badgeVariants'

type ReadinessVariant = Extract<BadgeVariant, 'ready' | 'blocked' | 'review' | 'neutral'>

const STATUS_VARIANT: Record<string, ReadinessVariant> = {
  ready: 'ready',
  blocked_by_dependency: 'blocked',
  blocked_by_documents: 'blocked',
  review_required: 'review',
  insufficient_data: 'neutral',
}

export function statusBadge(status: string): string {
  const variant = STATUS_VARIANT[status.toLowerCase()] ?? 'neutral'
  return badgeVariantClasses[variant]
}

const CLASSIFICATION_VARIANT: Record<string, ReadinessVariant> = {
  RESULT_CHANGED: 'blocked',
  SOURCE_RELEVANT: 'review',
}

export function classificationBadge(classification: string): string {
  return badgeVariantClasses[CLASSIFICATION_VARIANT[classification] ?? 'neutral']
}
