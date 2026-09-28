export type BadgeVariant =
  | 'default'
  | 'secondary'
  | 'destructive'
  | 'outline'
  | 'success'
  | 'warning'
  | 'info'
  | 'ready'
  | 'blocked'
  | 'review'
  | 'insufficient'
  | 'neutral'
  | 'pending'
  | 'neutralMuted'
  | 'readySoft'
  | 'blockedSoft'
  | 'reviewSoft'
  | 'neutralSoft'

// Single source of truth for pill styling. The ready/blocked/review/
// insufficient/neutral aliases intentionally reuse the exact legacy palette
// classes for now; migrating them onto semantic OKLCH tokens is an explicit
// later visual-token batch (Batch 7), not this structural batch.
export const badgeVariantClasses: Record<BadgeVariant, string> = {
  default: 'bg-primary text-primary-foreground',
  secondary: 'bg-secondary text-secondary-foreground',
  destructive: 'bg-destructive text-destructive-foreground',
  outline: 'border border-border text-foreground',
  success: 'bg-success text-success-foreground',
  warning: 'bg-warning text-warning-foreground',
  info: 'bg-info text-info-foreground',
  ready: 'bg-green-100 text-green-800',
  blocked: 'bg-red-100 text-red-800',
  review: 'bg-yellow-100 text-yellow-800',
  insufficient: 'bg-gray-100 text-gray-800',
  neutral: 'bg-gray-100 text-gray-800',
  // In-flight/pending blue. Distinct from neutral: marks work underway,
  // not absence of state. Same legacy string, centralized.
  pending: 'bg-blue-100 text-blue-800',
  // Muted gray fallback. Distinct from neutral gray-800: a dimmer treatment
  // used by a few legacy fallback branches. Centralized verbatim.
  neutralMuted: 'bg-gray-100 text-gray-700',
  // Soft inline-finding treatments (bg-*-50 / text-*-700) used by finding
  // rows in DocumentChecklist and ConsistencyPanel. Verbatim centralization;
  // not interchangeable with the stronger pill aliases above.
  readySoft: 'bg-green-50 text-green-700',
  blockedSoft: 'bg-red-50 text-red-700',
  reviewSoft: 'bg-yellow-50 text-yellow-700',
  neutralSoft: 'bg-gray-50 text-gray-700',
}
