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
  // Persisted regulatory identity chips (rendered verbatim from the row).
  approvalCode?: string | null
  jurisdiction?: string | null
}

// Shared title row for both detail pages. Same hierarchy as the previous
// copy-pasted blocks (h1 + mono id + outline Back), centralized on PageHeader.
export function DetailPageHeader({ referenceNumber, objectId, onBack, approvalCode, jurisdiction }: DetailPageHeaderProps) {
  return (
    <PageHeader
      title={`Application ${referenceNumber}`}
      description={
        <div className="space-y-1">
          <p className="break-all font-mono text-xs text-muted-foreground">{objectId}</p>
          {(approvalCode || jurisdiction) && (
            <p className="flex flex-wrap gap-1">
              {approvalCode && (
                <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-mono text-[10px] font-medium text-gray-700">
                  {approvalCode}
                </span>
              )}
              {jurisdiction && (
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] font-medium ${
                    jurisdiction === 'IN-MH' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {jurisdiction}
                </span>
              )}
            </p>
          )}
        </div>
      }
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
