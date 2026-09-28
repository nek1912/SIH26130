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
        return self.client.insert_one(
            "consistency_results",
            {
                "application_id": application_id,
                "outcome": outcome,
                "checked_at": checked_at,
                "rule_version": rule_version,
            },
        )

    def create_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create multiple consistency findings in one call."""
        if not findings:
            return []
        return self.client.insert_many("consistency_findings", findings)

    def get_latest_result(self, application_id: str) -> dict[str, Any] | None:
        """Get the most recent consistency result for an application."""
        return self.client.fetch_one(
            "SELECT * FROM consistency_results WHERE application_id = %s "
            "ORDER BY checked_at DESC LIMIT 1",
            (application_id,),
        )

    def list_findings_for_result(self, result_id: str) -> list[dict[str, Any]]:
        """List all findings for a consistency result."""
        return self.client.fetch_all(
            "SELECT * FROM consistency_findings WHERE result_id = %s",
            (result_id,),
        )

    def delete_findings_for_result(self, result_id: str) -> None:
        """Delete all findings for a consistency result."""
        self.client.delete_where(
            "consistency_findings", "result_id = %s", (result_id,)
        )

    def delete_previous_results(self, application_id: str) -> None:
        """Delete all previous consistency results for an application (for re-run)."""
        existing = self.client.fetch_all(
            "SELECT id FROM consistency_results WHERE application_id = %s",
            (application_id,),
        )
        for row in existing:
            self.delete_findings_for_result(row["id"])
        self.client.delete_where(
            "consistency_results", "application_id = %s", (application_id,)
        )

    def get_extracted_fields_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """Get all extracted fields for an application."""
        return self.client.fetch_all(
            "SELECT * FROM extracted_fields WHERE application_id = %s",
            (application_id,),
        )

    def get_document_req_map(self, application_id: str) -> dict[str, str]:
        """Get mapping from document_id to requirement_key for an application."""
        rows = self.client.fetch_all(
            "SELECT id, requirement_key FROM documents WHERE application_id = %s",
            (application_id,),
        )
        return {row["id"]: row["requirement_key"] for row in rows}
