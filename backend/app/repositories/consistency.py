"""Consistency repository — CRUD for consistency_results and consistency_findings."""
from __future__ import annotations

from typing import Any

from app.repositories.base import BaseRepository


class ConsistencyRepository(BaseRepository):
    """Repository for cross-document consistency operations."""

    def __init__(self, client):
        super().__init__(client, "consistency_results")

    def create_result(
        self,
        application_id: str,
        outcome: str,
        checked_at: str,
        rule_version: str,
    ) -> dict[str, Any]:
        """Create a consistency result record."""
        result = (
            self.client.table("consistency_results")
            .insert({
                "application_id": application_id,
                "outcome": outcome,
                "checked_at": checked_at,
                "rule_version": rule_version,
            })
            .execute()
        )
        return result.data[0]

    def create_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create multiple consistency findings in one call."""
        if not findings:
            return []
        result = (
            self.client.table("consistency_findings")
            .insert(findings)
            .execute()
        )
        return result.data or []

    def get_latest_result(self, application_id: str) -> dict[str, Any] | None:
        """Get the most recent consistency result for an application."""
        result = (
            self.client.table("consistency_results")
            .select("*")
            .eq("application_id", application_id)
            .order("checked_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_findings_for_result(self, result_id: str) -> list[dict[str, Any]]:
        """List all findings for a consistency result."""
        result = (
            self.client.table("consistency_findings")
            .select("*")
            .eq("result_id", result_id)
            .execute()
        )
        return result.data or []

    def delete_findings_for_result(self, result_id: str) -> None:
        """Delete all findings for a consistency result."""
        self.client.table("consistency_findings").delete().eq(
            "result_id", result_id
        ).execute()

    def delete_previous_results(self, application_id: str) -> None:
        """Delete all previous consistency results for an application (for re-run)."""
        existing = (
            self.client.table("consistency_results")
            .select("id")
            .eq("application_id", application_id)
            .execute()
        )
        for row in (existing.data or []):
            self.delete_findings_for_result(row["id"])
        self.client.table("consistency_results").delete().eq(
            "application_id", application_id
        ).execute()

    def get_extracted_fields_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """Get all extracted fields for an application."""
        result = (
            self.client.table("extracted_fields")
            .select("*")
            .eq("application_id", application_id)
            .execute()
        )
        return result.data or []

    def get_document_req_map(self, application_id: str) -> dict[str, str]:
        """Get mapping from document_id to requirement_key for an application."""
        result = (
            self.client.table("documents")
            .select("id, requirement_key")
            .eq("application_id", application_id)
            .execute()
        )
        return {row["id"]: row["requirement_key"] for row in (result.data or [])}
