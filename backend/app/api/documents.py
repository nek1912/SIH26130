"""Document management endpoints."""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.api.deps import get_documents_repository
from app.audit.service import AuditEntry, create_audit_record
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.documents import DocumentsRepository

router = APIRouter()


# -- Helpers --

def _sanitize_filename(filename: str) -> str:
    """Remove path traversal and dangerous characters from filename."""
    name = filename.replace("\x00", "")
    # Extract basename to prevent path traversal
    name = name.split("/")[-1].split("\\")[-1]
    name = name.lstrip(".")
    name = re.sub(r"[^\w.\-]", "_", name)
    if not name:
        name = "unnamed_file"
    return name


def _validate_upload(
    filename: str,
    content_type: str,
    file_size: int,
    accepted_types: list[str] | None,
    max_size_mb: int | None,
) -> tuple[bool, str]:
    """Validate file upload. Returns (is_valid, error_message)."""
    if file_size <= 0:
        return False, "File is empty"

    if max_size_mb and file_size > max_size_mb * 1024 * 1024:
        return False, f"File exceeds maximum size of {max_size_mb} MB"

    if accepted_types:
        type_match = False
        for accepted in accepted_types:
            if accepted.endswith("/*"):
                prefix = accepted[:-2]
                if content_type.startswith(prefix):
                    type_match = True
                    break
            elif content_type == accepted:
                type_match = True
                break
        if not type_match:
            return False, f"File type '{content_type}' not accepted. Allowed: {accepted_types}"

    return True, ""


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


# -- Endpoints --

@router.get("/applications/{application_id}/document-requirements")
async def list_document_requirements(
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
    """List document requirements checklist for an application."""
    _get_app_withOwnership(application_id, repo, user)
    return repo.list_requirements_for_application(application_id)


@router.get("/applications/{application_id}/documents")
async def list_documents(
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
    """List uploaded documents for an application."""
    _get_app_withOwnership(application_id, repo, user)
    return repo.list_documents_for_application(application_id)


@router.post("/applications/{application_id}/documents/{requirement_key}/upload")
async def upload_document(
    application_id: str,
    requirement_key: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
        )
    ),
):
    """Upload a document for a specific requirement."""
    _get_app_withOwnership(application_id, repo, user)

    # Verify requirement exists
    requirement = repo.get_requirement(application_id, requirement_key)
    if not requirement:
        raise HTTPException(
            status_code=404,
            detail=f"Document requirement '{requirement_key}' not found for this application",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)
    content_type = file.content_type or "application/octet-stream"
    filename = _sanitize_filename(file.filename or "unnamed_file")

    # Validate
    accepted = requirement.get("accepted_mime_types")
    max_size = requirement.get("max_size_mb")
    is_valid, error = _validate_upload(filename, content_type, file_size, accepted, max_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Upload to Supabase Storage
    from app.core.config import get_settings
    from app.db.client import get_supabase

    settings = get_settings()
    storage_path = f"applications/{application_id}/{requirement_key}/{filename}"

    try:
        client = get_supabase()
        client.storage.from_(settings.supabase_storage_bucket).upload(
            storage_path, content, {"content-type": content_type}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storage upload failed: {str(e)}",
        )

    # Create document record
    doc_data = {
        "application_id": application_id,
        "requirement_key": requirement_key,
        "original_filename": filename,
        "storage_path": storage_path,
        "mime_type": content_type,
        "file_size_bytes": file_size,
        "status": "uploaded",
        "uploaded_by_user_id": str(user.user_id),
    }
    document = repo.create_document(doc_data)

    # Update requirement readiness
    repo.update_requirement_readiness(
        application_id, requirement_key, "uploaded", document["id"]
    )

    # Audit
    create_audit_record(
        AuditEntry(
            action="document:upload",
            entity_type="document",
            entity_id=document["id"],
            user_id=str(user.user_id),
            application_id=application_id,
            new_values={
                "filename": filename,
                "mime_type": content_type,
                "file_size": file_size,
                "requirement_key": requirement_key,
            },
        )
    )

    # Trigger background extraction
    from app.extraction.background import run_extraction_background
    background_tasks.add_task(
        run_extraction_background, document["id"], application_id
    )

    return {
        "document": document,
        "requirement": repo.get_requirement(application_id, requirement_key),
    }


@router.get("/applications/{application_id}/documents/{document_id}")
async def get_document(
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
    """Get document metadata."""
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(status_code=404, detail="Document not found for this application")

    return document


@router.delete("/applications/{application_id}/documents/{document_id}")
async def delete_document(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
        )
    ),
):
    """Delete an uploaded document."""
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(status_code=404, detail="Document not found for this application")

    # Delete from storage
    from app.core.config import get_settings
    from app.db.client import get_supabase

    settings = get_settings()
    client = get_supabase()
    storage_path = document.get("storage_path", "")
    if storage_path:
        try:
            client.storage.from_(settings.supabase_storage_bucket).remove([storage_path])
        except Exception:
            pass  # Best-effort storage cleanup

    # Update requirement readiness back to pending
    requirement_key = document.get("requirement_key")
    if requirement_key:
        repo.update_requirement_readiness(
            application_id, requirement_key, "pending", None, None
        )

    # Delete document record
    repo.delete_document(document_id)

    # Audit
    create_audit_record(
        AuditEntry(
            action="document:delete",
            entity_type="document",
            entity_id=document_id,
            user_id=str(user.user_id),
            application_id=application_id,
            previous_values={
                "filename": document.get("original_filename"),
                "requirement_key": requirement_key,
            },
        )
    )

    return {"deleted": True}
