"""Document extraction and validation endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_documents_repository
from app.audit.service import AuditEntry, create_audit_record
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.extraction.models import ExtractionStatus
from app.extraction.service import extract_document
from app.extraction.validation import validate_document
from app.repositories.documents import DocumentsRepository

router = APIRouter()


def _get_app_withOwnership(
    application_id: str,
    repo: DocumentsRepository,
    user: UserContext,
) -> dict[str, Any]:
    """Get application and verify ownership. Raises 404/403."""
    from uuid import UUID

    from app.repositories.applications import ApplicationsRepository

    app_repo = ApplicationsRepository(repo.client)
    application = app_repo.get_by_id(UUID(application_id))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    return application


@router.post(
    "/applications/{application_id}/documents/{document_id}/extract"
)
async def extract_document_fields(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Extract structured fields from an uploaded document.

    Performs deterministic extraction based on MIME type:
    - PDF: metadata (title, author, pages)
    - CSV: headers, row/column counts
    - Excel: sheet names, headers, row/column counts

    No LLM or OCR is used.
    """
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(
            status_code=404, detail="Document not found for this application"
        )

    # Get file content from storage
    from app.core.config import get_settings
    from app.db.client import get_supabase

    settings = get_settings()
    client = get_supabase()
    storage_path = document.get("storage_path", "")

    try:
        file_data = client.storage.from_(settings.supabase_storage_bucket).download(
            storage_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download document: {str(e)}"
        )

    # Perform extraction
    mime_type = document.get("mime_type", "application/octet-stream")
    extraction_result = extract_document(
        content=file_data,
        mime_type=mime_type,
        document_id=document_id,
        application_id=application_id,
    )

    # Delete existing extraction data for this document
    repo.delete_extracted_fields_for_document(document_id)
    repo.delete_extracted_fields_for_document(document_id)  # idempotent

    # Store extraction result
    extraction_data = {
        "document_id": document_id,
        "application_id": application_id,
        "status": extraction_result.status.value,
        "errors": extraction_result.errors,
        "metadata": extraction_result.metadata,
    }

    # Check if result already exists
    existing = repo.get_extraction_result_for_document(document_id)
    if existing:
        repo.update_extraction_result(document_id, extraction_data)
    else:
        repo.create_extraction_result(extraction_data)

    # Store extracted fields
    if extraction_result.fields:
        fields_data = []
        for field in extraction_result.fields:
            fields_data.append({
                "document_id": document_id,
                "application_id": application_id,
                "field_name": field.field_name,
                "field_value": field.field_value,
                "field_type": field.field_type,
                "extraction_method": field.extraction_method,
                "confidence": field.confidence,
                "metadata": field.metadata,
            })
        repo.create_extracted_fields_bulk(fields_data)

    # Update requirement extraction status
    requirement_key = document.get("requirement_key")
    if requirement_key:
        repo.update_requirement_extraction_status(
            application_id, requirement_key, extraction_result.status.value
        )

    # Audit
    create_audit_record(
        AuditEntry(
            action="document:extract",
            entity_type="document",
            entity_id=document_id,
            user_id=str(user.user_id),
            application_id=application_id,
            new_values={
                "extraction_status": extraction_result.status.value,
                "field_count": len(extraction_result.fields),
            },
        )
    )

    return {
        "document_id": document_id,
        "extraction_status": extraction_result.status.value,
        "field_count": len(extraction_result.fields),
        "errors": extraction_result.errors,
        "metadata": extraction_result.metadata,
    }


@router.post(
    "/applications/{application_id}/documents/{document_id}/validate"
)
async def validate_document_fields(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Validate extracted fields against deterministic rules.

    Returns explicit outcomes: VALID, INVALID, REVIEW_REQUIRED, or INSUFFICIENT_DATA.
    Every result includes source/rule traceability.
    """
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(
            status_code=404, detail="Document not found for this application"
        )

    requirement_key = document.get("requirement_key")
    if not requirement_key:
        raise HTTPException(
            status_code=400, detail="Document has no associated requirement"
        )

    # Get requirement for domain info
    requirement = repo.get_requirement(application_id, requirement_key)
    if not requirement:
        raise HTTPException(
            status_code=404, detail=f"Requirement '{requirement_key}' not found"
        )

    # Get extraction result
    extraction_result_data = repo.get_extraction_result_for_document(document_id)
    if not extraction_result_data:
        # Run extraction first if not done
        from app.core.config import get_settings
        from app.db.client import get_supabase

        settings = get_settings()
        client = get_supabase()
        storage_path = document.get("storage_path", "")

        try:
            file_data = client.storage.from_(
                settings.supabase_storage_bucket
            ).download(storage_path)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to download document: {str(e)}"
            )

        mime_type = document.get("mime_type", "application/octet-stream")
        extraction_result = extract_document(
            content=file_data,
            mime_type=mime_type,
            document_id=document_id,
            application_id=application_id,
        )

        # Store extraction result
        extraction_data = {
            "document_id": document_id,
            "application_id": application_id,
            "status": extraction_result.status.value,
            "errors": extraction_result.errors,
            "metadata": extraction_result.metadata,
        }
        existing = repo.get_extraction_result_for_document(document_id)
        if existing:
            repo.update_extraction_result(document_id, extraction_data)
        else:
            repo.create_extraction_result(extraction_data)

        # Store fields
        if extraction_result.fields:
            fields_data = []
            for field in extraction_result.fields:
                fields_data.append({
                    "document_id": document_id,
                    "application_id": application_id,
                    "field_name": field.field_name,
                    "field_value": field.field_value,
                    "field_type": field.field_type,
                    "extraction_method": field.extraction_method,
                    "confidence": field.confidence,
                    "metadata": field.metadata,
                })
            repo.create_extracted_fields_bulk(fields_data)

        # Update requirement status
        repo.update_requirement_extraction_status(
            application_id, requirement_key, extraction_result.status.value
        )
    else:
        # Reconstruct extraction result from stored data
        from app.extraction.models import ExtractedField, ExtractionResult

        stored_fields = repo.list_extracted_fields_for_document(document_id)
        fields = []
        for sf in stored_fields:
            fields.append(ExtractedField(
                id=sf.get("id"),
                document_id=sf["document_id"],
                application_id=sf["application_id"],
                field_name=sf["field_name"],
                field_value=sf.get("field_value"),
                field_type=sf.get("field_type", "string"),
                extraction_method=sf.get("extraction_method", ""),
                confidence=sf.get("confidence", 1.0),
                metadata=sf.get("metadata", {}),
            ))

        extraction_result = ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus(extraction_result_data["status"]),
            fields=fields,
            errors=extraction_result_data.get("errors", []),
            metadata=extraction_result_data.get("metadata", {}),
        )

    # Run validation
    domain = requirement.get("domain", "")
    mime_type = document.get("mime_type", "application/octet-stream")
    accepted_mime = requirement.get("accepted_mime_types")

    validation_result = validate_document(
        extraction_result=extraction_result,
        requirement_key=requirement_key,
        domain=domain,
        mime_type=mime_type,
        accepted_mime_types=accepted_mime,
    )

    # Delete existing validation data for this document
    repo.delete_validation_findings_for_document(document_id)
    repo.delete_validation_results_for_document(document_id)

    # Store validation result
    validation_data = {
        "document_id": document_id,
        "application_id": application_id,
        "requirement_key": requirement_key,
        "outcome": validation_result.outcome.value,
        "rule_version": validation_result.rule_version,
        "source_refs": validation_result.source_refs,
    }
    repo.create_validation_result(validation_data)

    # Store findings
    if validation_result.findings:
        findings_data = []
        for finding in validation_result.findings:
            findings_data.append({
                "document_id": document_id,
                "application_id": application_id,
                "field_name": finding.field_name,
                "rule_id": finding.rule_id,
                "rule_description": finding.rule_description,
                "outcome": finding.outcome.value,
                "expected": finding.expected,
                "actual": finding.actual,
                "message": finding.message,
                "source_ref": finding.source_ref,
            })
        repo.create_validation_findings_bulk(findings_data)

    # Update requirement validation outcome
    repo.update_requirement_validation_outcome(
        application_id, requirement_key, validation_result.outcome.value
    )

    # Audit
    create_audit_record(
        AuditEntry(
            action="document:validate",
            entity_type="document",
            entity_id=document_id,
            user_id=str(user.user_id),
            application_id=application_id,
            new_values={
                "validation_outcome": validation_result.outcome.value,
                "finding_count": len(validation_result.findings),
            },
        )
    )

    return {
        "document_id": document_id,
        "requirement_key": requirement_key,
        "outcome": validation_result.outcome.value,
        "finding_count": len(validation_result.findings),
        "findings": [
            {
                "field_name": f.field_name,
                "rule_id": f.rule_id,
                "rule_description": f.rule_description,
                "outcome": f.outcome.value,
                "expected": f.expected,
                "actual": f.actual,
                "message": f.message,
                "source_ref": f.source_ref,
            }
            for f in validation_result.findings
        ],
        "source_refs": validation_result.source_refs,
    }


@router.get(
    "/applications/{application_id}/documents/{document_id}/extraction"
)
async def get_extraction_status(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get extraction status and fields for a document."""
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(
            status_code=404, detail="Document not found for this application"
        )

    extraction_result = repo.get_extraction_result_for_document(document_id)
    fields = repo.list_extracted_fields_for_document(document_id)

    return {
        "document_id": document_id,
        "extraction": extraction_result,
        "fields": fields,
    }


@router.get(
    "/applications/{application_id}/documents/{document_id}/validation"
)
async def get_validation_status(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get validation result and findings for a document."""
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(
            status_code=404, detail="Document not found for this application"
        )

    validation_result = repo.get_validation_result_for_document(document_id)
    findings = repo.list_validation_findings_for_document(document_id)

    return {
        "document_id": document_id,
        "validation": validation_result,
        "findings": findings,
    }


@router.get(
    "/applications/{application_id}/extraction-summary"
)
async def get_extraction_summary(
    application_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get extraction and validation summary for all documents in an application."""
    _get_app_withOwnership(application_id, repo, user)

    requirements = repo.list_requirements_for_application(application_id)
    documents = repo.list_documents_for_application(application_id)

    summary = []
    for req in requirements:
        req_key = req["requirement_key"]
        doc = next(
            (d for d in documents if d.get("requirement_key") == req_key), None
        )

        entry = {
            "requirement_key": req_key,
            "document_name": req.get("document_name", ""),
            "domain": req.get("domain", ""),
            "readiness": req.get("readiness", "pending"),
            "extraction_status": req.get("extraction_status"),
            "validation_outcome": req.get("validation_outcome"),
            "has_document": doc is not None,
        }

        if doc:
            doc_id = doc["id"]
            extraction = repo.get_extraction_result_for_document(doc_id)
            validation = repo.get_validation_result_for_document(doc_id)
            findings = repo.list_validation_findings_for_document(doc_id)

            entry["extraction"] = extraction
            entry["validation"] = validation
            entry["finding_count"] = len(findings)
            entry["findings"] = findings
        else:
            entry["extraction"] = None
            entry["validation"] = None
            entry["finding_count"] = 0
            entry["findings"] = []

        summary.append(entry)

    return summary
