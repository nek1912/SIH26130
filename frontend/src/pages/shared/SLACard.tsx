import type { SlaInfo } from '@/types/api'
import { badgeVariantClasses } from '@/components/ui/badgeVariants'
import { formatDate } from '@/lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface SLACardProps {
  sla: SlaInfo
}

const SLA_STATUS_VARIANT: Record<SlaInfo['state'], 'ready' | 'blocked' | 'review'> = {
  on_track: 'ready',
  due_soon: 'review',
  due_today: 'review',
  breached: 'blocked',
}

const SLA_STATUS_LABEL: Record<SlaInfo['state'], string> = {
  on_track: 'On Track',
  due_soon: 'Due Soon',
  due_today: 'Due Today',
  breached: 'Breached',
}

export function SLACard({ sla }: SLACardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>SLA Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <p className="text-sm font-medium">{sla.stage_label}</p>
            <p className="text-xs text-muted-foreground">
              Target: {sla.sla_business_days} business days
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm">
              Due: {formatDate(sla.due_date)}
            </p>
            <p className="text-xs text-muted-foreground">
              {sla.remaining_business_days > 0
                ? `${sla.remaining_business_days} days remaining`
                : `${sla.overdue_business_days} days overdue`}
            </p>
          </div>
          <span
            className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${badgeVariantClasses[SLA_STATUS_VARIANT[sla.state]]}`}
          >
            {SLA_STATUS_LABEL[sla.state]}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
