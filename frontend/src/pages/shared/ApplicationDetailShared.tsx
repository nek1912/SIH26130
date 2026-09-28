import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/shared/PageHeader'
import { DocumentChecklist } from '@/pages/shared/DocumentChecklist'
import { ConsistencyPanel } from '@/pages/shared/ConsistencyPanel'
import { RegulatoryAssistant } from '@/pages/shared/RegulatoryAssistant'
import { IncentiveSchemes } from '@/pages/shared/IncentiveSchemes'
import type {
  ConsistencyResult,
  DocumentRequirement,
  UploadedDocument,
  ExtractionSummary,
} from '@/types/api'

interface DetailPageHeaderProps {
  referenceNumber: string
  objectId: string
  onBack: () => void
}

// Shared title row for both detail pages. Same hierarchy as the previous
// copy-pasted blocks (h1 + mono id + outline Back), centralized on PageHeader.
export function DetailPageHeader({ referenceNumber, objectId, onBack }: DetailPageHeaderProps) {
  return (
    <PageHeader
      title={`Application ${referenceNumber}`}
      description={<p className="break-all font-mono text-xs text-muted-foreground">{objectId}</p>}
      actions={
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
      }
    />
  )
}

interface DetailBottomSectionsProps {
  applicationId: string
  approvalId: string
  projectFacts: Record<string, unknown> | null
  docRequirements: DocumentRequirement[]
  uploadedDocs: UploadedDocument[]
  extractionSummary: ExtractionSummary[]
  docLoading: boolean
  docError: string
  onRefreshDocs: () => void
  consistency: ConsistencyResult | null
  consistencyLoading: boolean
  consistencyError: string
  onRunConsistency: () => void
}

// Bottom four panels are rendered identically (same order, same props) in both
// role pages. Role-specific panels (WhatIf/Handoff/ChangeImpact, actions,
// timeline, status grid) stay in the pages and are composed around this.
export function DetailBottomSections({
  applicationId,
  approvalId,
  projectFacts,
  docRequirements,
  uploadedDocs,
  extractionSummary,
  docLoading,
  docError,
  onRefreshDocs,
  consistency,
  consistencyLoading,
  consistencyError,
  onRunConsistency,
}: DetailBottomSectionsProps) {
  return (
    <>
      <DocumentChecklist
        applicationId={applicationId}
        requirements={docRequirements}
        uploadedDocs={uploadedDocs}
        extractionSummary={extractionSummary}
        loading={docLoading}
        error={docError}
        onRefresh={onRefreshDocs}
      />

      <ConsistencyPanel
        consistency={consistency}
        loading={consistencyLoading}
        error={consistencyError}
        onRunCheck={onRunConsistency}
      />

      <RegulatoryAssistant approvalId={approvalId} applicationId={applicationId} />

      {projectFacts && <IncentiveSchemes projectFacts={projectFacts} />}
    </>
  )
}
