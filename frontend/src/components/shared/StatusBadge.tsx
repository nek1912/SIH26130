import { Badge } from '@/components/ui/badge'
import type { ApplicationStatus } from '@/types/api'

const statusConfig: Record<ApplicationStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info' }> = {
  draft: { label: 'Draft', variant: 'secondary' },
  submitted: { label: 'Submitted', variant: 'info' },
  under_review: { label: 'Under Review', variant: 'info' },
  awaiting_inspection: { label: 'Awaiting Inspection', variant: 'warning' },
  awaiting_consultation: { label: 'Awaiting Consultation', variant: 'warning' },
  awaiting_hearing: { label: 'Awaiting Hearing', variant: 'warning' },
  awaiting_documents: { label: 'Awaiting Documents', variant: 'warning' },
  awaiting_payment: { label: 'Awaiting Payment', variant: 'warning' },
  approved: { label: 'Approved', variant: 'success' },
  refused: { label: 'Refused', variant: 'destructive' },
  withdrawn: { label: 'Withdrawn', variant: 'secondary' },
  incomplete: { label: 'Incomplete', variant: 'warning' },
  returned: { label: 'Returned', variant: 'warning' },
  cancelled: { label: 'Cancelled', variant: 'secondary' },
}

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const config = statusConfig[status] ?? { label: status, variant: 'outline' as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}
