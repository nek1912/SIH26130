## Task 11: Frontend Extraction Status Display

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `extraction_status` from UploadedDocument
- Produces: Extraction status badges in document checklist

- [ ] **Step 1: Update extraction status badge in applicant page**

In the document checklist section, replace the existing extraction status display with:

```tsx
{/* Extraction Status */}
{uploaded && (
  <div className="mt-2 flex items-center gap-3 text-xs">
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
        (uploaded.extraction_status ?? extractionStatus) === 'succeeded'
          ? 'bg-green-100 text-green-800'
          : (uploaded.extraction_status ?? extractionStatus) === 'failed'
            ? 'bg-red-100 text-red-800'
            : (uploaded.extraction_status ?? extractionStatus) === 'running'
              ? 'bg-blue-100 text-blue-800'
              : (uploaded.extraction_status ?? extractionStatus) === 'unsupported'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-700'
      }`}
    >
      Extraction: {uploaded.extraction_status ?? extractionStatus ?? 'pending'}
      {(uploaded.extraction_status ?? extractionStatus) === 'running' && (
        <svg className="ml-1 h-3 w-3 animate-spin" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
    </span>
    {validationOutcome && (
      <span
        className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
          validationOutcome === 'VALID'
            ? 'bg-green-100 text-green-800'
            : validationOutcome === 'INVALID'
              ? 'bg-red-100 text-red-800'
              : validationOutcome === 'REVIEW_REQUIRED'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-700'
        }`}
      >
        Validation: {validationOutcome}
      </span>
    )}
  </div>
)}
```

- [ ] **Step 2: Add polling for extraction status after upload**

After a successful upload, add a polling mechanism to refetch extraction summary:

```typescript
// In handleUpload, after setting state, poll for extraction status
const handleUpload = async (reqKey: string, file: File) => {
  // ... existing upload logic ...
  try {
    const result = await api.documents.upload(id, reqKey, file)
    // ... existing state updates ...

    // Poll extraction status after a short delay
    setTimeout(async () => {
      try {
        const summary = await api.documents.getExtractionSummary(id)
        setExtractionSummary(summary as ExtractionSummary[])
      } catch {
        // Ignore poll errors
      }
    }, 2000)
  } catch (err) {
    // ... existing error handling ...
  }
}
```

- [ ] **Step 3: Apply same changes to staff page**

Apply the same extraction status badge and polling logic to `frontend/src/pages/staff/ApplicationDetailPage.tsx`.

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Verify build**

Run: `cd frontend && npx vite build`
Expected: Build success

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx frontend/src/pages/staff/ApplicationDetailPage.tsx
git commit -m "feat: add extraction status badges with running/succeeded/failed/unsupported states"
```

---

