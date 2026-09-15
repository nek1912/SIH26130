# Tasks 6+7: Frontend Types, API Client, and Document Checklist UI

## Task 6: Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/lib/api.ts`

### Step 1: Add TypeScript types

Add to `frontend/src/types/api.ts` at the end:

```typescript
export interface DocumentRequirement {
  id: string
  application_id: string
  requirement_key: string
  document_name: string
  approval_id: string
  domain: string
  requirement_level: 'required' | 'mandatory' | 'conditional'
  readiness: 'pending' | 'uploaded' | 'valid' | 'invalid' | 'review_required'
  accepted_mime_types: string[] | null
  max_size_mb: number | null
  description: string | null
  source_basis: string | null
  source_url: string | null
  document_role: string | null
  uploaded_document_id: string | null
  rejection_reason: string | null
  created_at: string
  updated_at: string
}

export interface UploadedDocument {
  id: string
  application_id: string
  requirement_key: string
  original_filename: string
  storage_path: string
  mime_type: string
  file_size_bytes: number
  status: 'pending_upload' | 'uploaded' | 'verified' | 'rejected' | 'virus_detected' | 'expired'
  rejection_reason: string | null
  uploaded_by_user_id: string | null
  created_at: string
}

export interface UploadResult {
  document: UploadedDocument
  requirement: DocumentRequirement
}
```

### Step 2: Add API methods

Add to `frontend/src/lib/api.ts` inside the `api` object (after the `workflow` namespace):

```typescript
  documents: {
    listRequirements: (appId: string) =>
      request<DocumentRequirement[]>(`/applications/${appId}/document-requirements`),
    list: (appId: string) =>
      request<UploadedDocument[]>(`/applications/${appId}/documents`),
    upload: async (appId: string, reqKey: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data: { session } } = await supabase.auth.getSession()
      const headers: Record<string, string> = {}
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }
      const res = await fetch(
        `${API_BASE}/applications/${appId}/documents/${reqKey}/upload`,
        { method: 'POST', headers, body: formData },
      )
      if (res.status === 401) {
        window.location.href = '/login'
        throw new ApiError(401, 'Unauthorized')
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }))
        throw new ApiError(res.status, body.detail ?? res.statusText)
      }
      return res.json() as Promise<UploadResult>
    },
    get: (appId: string, docId: string) =>
      request<UploadedDocument>(`/applications/${appId}/documents/${docId}`),
    delete: (appId: string, docId: string) =>
      request<{ deleted: boolean }>(`/applications/${appId}/documents/${docId}`, { method: 'DELETE' }),
  },
```

### Step 3: Run frontend checks

Run: `cd D:\SIH\frontend && npx tsc --noEmit && npx oxlint`
Expected: 0 TypeScript errors, no new lint errors

## Task 7: Frontend Document Checklist UI

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

### Step 1: Add imports and state

At the top of `ApplicationDetailPage.tsx`, add to imports:

```typescript
import type { DocumentRequirement, UploadedDocument } from '@/types/api'
```

Inside the component, after existing state variables, add:

```typescript
const [docRequirements, setDocRequirements] = useState<DocumentRequirement[]>([])
const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
const [docLoading, setDocLoading] = useState(false)
const [docError, setDocError] = useState('')
const [uploadingKey, setUploadingKey] = useState('')
```

### Step 2: Add effect to load documents

After the existing `useEffect` that loads the application, add:

```typescript
useEffect(() => {
  if (!id) return
  setDocLoading(true)
  Promise.all([
    api.documents.listRequirements(id),
    api.documents.list(id),
  ])
    .then(([reqs, docs]) => {
      setDocRequirements(reqs as DocumentRequirement[])
      setUploadedDocs(docs as UploadedDocument[])
    })
    .catch((err) => setDocError(err.message))
    .finally(() => setDocLoading(false))
}, [id])
```

### Step 3: Add upload and delete handlers

After the existing `handleAction` function, add:

```typescript
const handleUpload = async (reqKey: string, file: File) => {
  if (!id) return
  setUploadingKey(reqKey)
  setDocError('')
  try {
    const result = await api.documents.upload(id, reqKey, file)
    setUploadedDocs((prev) => {
      const filtered = prev.filter((d) => d.requirement_key !== reqKey)
      return [result.document, ...filtered]
    })
    setDocRequirements((prev) =>
      prev.map((r) => (r.requirement_key === reqKey ? result.requirement : r)),
    )
  } catch (err) {
    if (err instanceof ApiError) setDocError(err.message)
    else setDocError(err instanceof Error ? err.message : 'Upload failed')
  } finally {
    setUploadingKey('')
  }
}

const handleDeleteDoc = async (docId: string, reqKey: string) => {
  if (!id) return
  try {
    await api.documents.delete(id, docId)
    setUploadedDocs((prev) => prev.filter((d) => d.id !== docId))
    setDocRequirements((prev) =>
      prev.map((r) =>
        r.requirement_key === reqKey
          ? { ...r, readiness: 'pending' as const, uploaded_document_id: null }
          : r,
      ),
    )
  } catch (err) {
    if (err instanceof ApiError) setDocError(err.message)
    else setDocError(err instanceof Error ? err.message : 'Delete failed')
  }
}
```

### Step 4: Add JSX section

Before the closing `</div>` of the component, add the document checklist section:

```tsx
      {/* Document Checklist */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Document Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          {docLoading ? (
            <LoadingSpinner className="py-4" />
          ) : docError ? (
            <div className="text-sm text-destructive">{docError}</div>
          ) : docRequirements.length === 0 ? (
            <p className="text-sm text-muted-foreground">No document requirements for this application.</p>
          ) : (
            <div className="space-y-3">
              {docRequirements.map((req) => {
                const uploaded = uploadedDocs.find((d) => d.requirement_key === req.requirement_key)
                return (
                  <div
                    key={req.requirement_key}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{req.requirement_key}</span>
                        <span className="text-sm font-medium truncate">{req.document_name}</span>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            req.requirement_level === 'mandatory'
                              ? 'bg-red-100 text-red-800'
                              : req.requirement_level === 'conditional'
                                ? 'bg-yellow-100 text-yellow-800'
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
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteDoc(uploaded.id, req.requirement_key)}
                        >
                          Remove
                        </Button>
                      ) : (
                        <label className="cursor-pointer">
                          <input
                            type="file"
                            className="hidden"
                            accept={req.accepted_mime_types?.join(',')}
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) handleUpload(req.requirement_key, file)
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={uploadingKey === req.requirement_key}
                            asChild
                          >
                            <span>
                              {uploadingKey === req.requirement_key ? 'Uploading...' : 'Upload'}
                            </span>
                          </Button>
                        </label>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
```

### Step 5: Run frontend checks

Run: `cd D:\SIH\frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: 0 TypeScript errors, build succeeds

### Step 6: Commit

```bash
git add frontend/src/types/api.ts frontend/src/lib/api.ts frontend/src/pages/applicant/ApplicationDetailPage.tsx
git commit -m "feat: add document types, API client, and checklist UI"
```
