import { useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { DocumentRequirement, UploadedDocument, ExtractionSummary } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { badgeVariantClasses } from '@/components/ui/badgeVariants'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

interface DocumentChecklistProps {
  applicationId: string
  requirements: DocumentRequirement[]
  uploadedDocs: UploadedDocument[]
  extractionSummary: ExtractionSummary[]
  loading: boolean
  error: string
  onRefresh: () => void
}

// The default requirement level keeps its informational blue inline on
// purpose: blue here is a heterogeneous informational treatment, not a
// state, and has no status alias. Deferred, not silently remapped.

const EXTRACTION_VARIANT: Record<string, 'ready' | 'blocked' | 'pending' | 'review' | 'neutralMuted'> = {
  completed: 'ready',
  failed: 'blocked',
  running: 'pending',
  unsupported: 'review',
}

const VALIDATION_VARIANT: Record<string, 'ready' | 'blocked' | 'review' | 'neutralMuted'> = {
  VALID: 'ready',
  INVALID: 'blocked',
  REVIEW_REQUIRED: 'review',
}

const FINDING_VARIANT: Record<string, 'readySoft' | 'blockedSoft' | 'reviewSoft' | 'neutralSoft'> = {
  VALID: 'readySoft',
  INVALID: 'blockedSoft',
  REVIEW_REQUIRED: 'reviewSoft',
}

export function DocumentChecklist({
  applicationId,
  requirements,
  uploadedDocs,
  extractionSummary,
  loading,
  error,
  onRefresh,
}: DocumentChecklistProps) {
  const [uploadingKey, setUploadingKey] = useState('')
  const [extractingDocId, setExtractingDocId] = useState('')
  const [validatingDocId, setValidatingDocId] = useState('')
  const [docError, setDocError] = useState('')

  const handleUpload = async (reqKey: string, file: File) => {
    setUploadingKey(reqKey)
    setDocError('')
    try {
      await api.documents.upload(applicationId, reqKey, file)
      onRefresh()
      setTimeout(async () => {
        try {
          await api.documents.getExtractionSummary(applicationId)
          onRefresh()
        } catch { /* Ignore poll errors */ }
      }, 2000)
    } catch (err) {
      setDocError(getErrorMessage(err, 'Upload failed'))
    } finally {
      setUploadingKey('')
    }
  }

  const handleDeleteDoc = async (docId: string) => {
    try {
      await api.documents.delete(applicationId, docId)
      onRefresh()
    } catch (err) {
      setDocError(getErrorMessage(err, 'Delete failed'))
    }
  }

  const handleExtract = async (docId: string) => {
    setExtractingDocId(docId)
    setDocError('')
    try {
      await api.documents.extract(applicationId, docId)
      onRefresh()
    } catch (err) {
      setDocError(getErrorMessage(err, 'Extraction failed'))
    } finally {
      setExtractingDocId('')
    }
  }

  const handleValidate = async (docId: string) => {
    setValidatingDocId(docId)
    setDocError('')
    try {
      await api.documents.validate(applicationId, docId)
      onRefresh()
    } catch (err) {
      setDocError(getErrorMessage(err, 'Validation failed'))
    } finally {
      setValidatingDocId('')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Document Checklist</CardTitle>
      </CardHeader>
      <CardContent>
        {(error || docError) ? (
          <div className="text-sm text-destructive">{error || docError}</div>
        ) : loading ? (
          <LoadingSpinner className="py-4" />
        ) : requirements.length === 0 ? (
          <p className="text-sm text-muted-foreground">No document requirements for this application.</p>
        ) : (
          <div className="space-y-3">
            {requirements.map((req) => {
              const uploaded = uploadedDocs.find((d) => d.requirement_key === req.requirement_key)
              const summary = extractionSummary.find((s) => s.requirement_key === req.requirement_key)
              const extractionStatus = summary?.extraction_status
              const validationOutcome = summary?.validation_outcome
              return (
                <div key={req.requirement_key} className="rounded-md border p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{req.requirement_key}</span>
                        <span className="text-sm font-medium truncate">{req.document_name}</span>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            req.requirement_level === 'mandatory'
                              ? badgeVariantClasses.blocked
                              : req.requirement_level === 'conditional'
                                ? badgeVariantClasses.review
                                : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {req.requirement_level}
                        </span>
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                          {req.domain}
                        </span>
                      </div>
                      {uploaded ? (
                        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{uploaded.original_filename}</span>
                          <span>({(uploaded.file_size_bytes / 1024).toFixed(1)} KB)</span>
                          <StatusBadge status={uploaded.status === 'verified' ? 'approved' : uploaded.status === 'rejected' ? 'refused' : 'submitted'} />
                        </div>
                      ) : (
                        <p className="mt-1 text-xs text-muted-foreground">Not uploaded</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {uploaded ? (
                        <>
                          <Button variant="outline" size="sm" onClick={() => handleExtract(uploaded.id)} disabled={extractingDocId === uploaded.id}>
                            {extractingDocId === uploaded.id ? 'Extracting...' : 'Extract'}
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => handleValidate(uploaded.id)} disabled={validatingDocId === uploaded.id}>
                            {validatingDocId === uploaded.id ? 'Validating...' : 'Validate'}
                          </Button>
                          <Button variant="destructive" size="sm" onClick={() => handleDeleteDoc(uploaded.id)}>
                            Remove
                          </Button>
                        </>
                      ) : (
                        <label className="cursor-pointer">
                          <input
                            type="file"
                            className="peer sr-only"
                            accept={req.accepted_mime_types?.join(',')}
                            aria-label={`Upload ${req.document_name}`}
                            disabled={uploadingKey === req.requirement_key}
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) handleUpload(req.requirement_key, file)
                            }}
                          />
                          <span
                            className={`inline-flex h-9 items-center justify-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2 ${
                              uploadingKey === req.requirement_key ? 'pointer-events-none opacity-50' : ''
                            }`}
                          >
                            {uploadingKey === req.requirement_key ? 'Uploading...' : 'Upload'}
                          </span>
                        </label>
                      )}
                    </div>
                  </div>

                  {uploaded && (
                    <div className="mt-2 flex items-center gap-3 text-xs">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
                          badgeVariantClasses[EXTRACTION_VARIANT[uploaded.extraction_status ?? extractionStatus ?? ''] ?? 'neutralMuted']
                        }`}
                      >
                        Extraction: {(uploaded.extraction_status ?? extractionStatus) === 'completed'
                          ? 'Extracted'
                          : (uploaded.extraction_status ?? extractionStatus) === 'running'
                            ? 'Extracting...'
                            : (uploaded.extraction_status ?? extractionStatus) ?? 'pending'}
                        {(uploaded.extraction_status ?? extractionStatus) === 'running' && (
                          <svg className="ml-1 h-3 w-3 animate-spin motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                        )}
                      </span>
                      {validationOutcome && (
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
                            badgeVariantClasses[VALIDATION_VARIANT[validationOutcome ?? ''] ?? 'neutralMuted']
                          }`}
                        >
                          Validation: {validationOutcome}
                        </span>
                      )}
                      {summary?.finding_count ? (
                        <span className="text-muted-foreground">
                          {summary.finding_count} finding{summary.finding_count !== 1 ? 's' : ''}
                        </span>
                      ) : null}
                    </div>
                  )}

                  {summary?.findings && summary.findings.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {summary.findings.map((finding, idx) => (
                        <div
                          key={idx}
                          className={`text-xs p-2 rounded ${badgeVariantClasses[FINDING_VARIANT[finding.outcome] ?? 'neutralSoft']}`}
                        >
                          <span className="font-medium font-mono">{finding.rule_id}:</span> {finding.message}
                          {finding.source_ref && (
                            <span className="ml-1 text-muted-foreground">({finding.source_ref})</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
