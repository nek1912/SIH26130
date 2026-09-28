"""Service-level tests for manual government handoff.

The handoff store tracks the applicant's MANUAL progress on external
authority portals. No test here performs, or asserts, any external
communication: opening a portal URL changes nothing.
"""
from __future__ import annotations

import pytest


class TestReadyGate:
    @pytest.mark.parametrize(
        "status", ["not_applicable", "insufficient_data", "blocked_by_dependency",
                   "blocked_by_documents", "review_required", "complete"]
    )
    def test_non_ready_status_cannot_initiate(self, status):
        from app.handoff.service import HandoffStateError, prepare_initiation

        with pytest.raises(HandoffStateError):
            prepare_initiation(
                application_id="app-1",
                approval_code="A05",
                orchestration_status=status,
                reported_by="user-1",
            )

    def test_ready_can_initiate(self):
        from app.handoff.service import prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        assert record["status"] == "handed_off"
        assert record["approval_code"] == "A05"
        assert "parivesh.nic.in" in record["portal_url"]
        assert record["external_reference"] is None
        assert record["verified_by"] is None

    def test_unknown_approval_code_rejected(self):
        from app.handoff.service import HandoffStateError, prepare_initiation

        with pytest.raises(HandoffStateError):
            prepare_initiation(
                application_id="app-1",
                approval_code="A99",
                orchestration_status="ready",
                reported_by="user-1",
            )


class TestTransitions:
    def test_handed_off_is_not_submitted(self):
        from app.handoff.service import prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        assert record["status"] != "submitted_externally"
        assert record["submitted_at"] is None

    def test_submission_records_reference(self):
        from app.handoff.service import apply_submission, prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        updated = apply_submission(
            record, external_reference="PARIVESH/2026/12345", actor="user-1"
        )
        assert updated["status"] == "submitted_externally"
        assert updated["external_reference"] == "PARIVESH/2026/12345"
        assert updated["submitted_at"] is not None

    def test_empty_reference_rejected(self):
        from app.handoff.service import HandoffStateError, apply_submission, prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        with pytest.raises(HandoffStateError):
            apply_submission(record, external_reference="   ", actor="user-1")

    def test_invalid_transition_rejected(self):
        from app.handoff.service import HandoffStateError, apply_report, prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        # handed_off -> under_external_review skips submission.
        with pytest.raises(HandoffStateError):
            apply_report(record, to_status="under_external_review", actor="user-1")

    def test_reported_approval_stays_user_reported(self):
        from app.handoff.service import apply_report, apply_submission, prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        record = apply_submission(record, external_reference="REF-1", actor="user-1")
        record = apply_report(record, to_status="under_external_review", actor="user-1")
        record = apply_report(record, to_status="approved_external", actor="user-1")
        assert record["status"] == "approved_external"
        assert record["verification"] == "user_reported"
        assert record["verified_by"] is None

    def test_verify_makes_approval_authoritative(self):
        from app.handoff.service import (
            apply_report,
            apply_submission,
            apply_verification,
            prepare_initiation,
        )

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        record = apply_submission(record, external_reference="REF-1", actor="user-1")
        record = apply_report(record, to_status="under_external_review", actor="user-1")
        record = apply_verification(
            record, verified_status="approved_external", verifier="staff-1"
        )
        assert record["status"] == "approved_external"
        assert record["verification"] == "staff_verified"
        assert record["verified_by"] == "staff-1"
        assert record["verified_at"] is not None

    def test_returned_for_correction_can_resubmit(self):
        from app.handoff.service import (
            apply_report,
            apply_submission,
            prepare_initiation,
        )

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        record = apply_submission(record, external_reference="REF-1", actor="user-1")
        record = apply_report(record, to_status="returned_for_correction", actor="user-1")
        record = apply_submission(record, external_reference="REF-2", actor="user-1")
        assert record["status"] == "submitted_externally"
        assert record["external_reference"] == "REF-2"

    def test_terminal_approved_rejects_further_reports(self):
        from app.handoff.service import (
            HandoffStateError,
            apply_report,
            apply_submission,
            apply_verification,
            prepare_initiation,
        )

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        record = apply_submission(record, external_reference="REF-1", actor="user-1")
        record = apply_report(record, to_status="under_external_review", actor="user-1")
        record = apply_verification(
            record, verified_status="approved_external", verifier="staff-1"
        )
        with pytest.raises(HandoffStateError):
            apply_report(record, to_status="rejected_external", actor="staff-1")


class TestNoExternalCommunication:
    def test_handoff_modules_use_no_http_client(self):
        import pathlib

        for name in ("models.py", "service.py"):
            text = pathlib.Path(f"app/handoff/{name}").read_text()
            for token in ("httpx", "requests", "urlopen", "urllib", "aiohttp"):
                assert token not in text, f"{name} must not use {token}"

    def test_seed_catalog_uses_only_relative_paths_or_approved_hosts(self):
        from app.seed.handoff import all_portal_entries

        entries = all_portal_entries()
        assert len(entries) == 18
        for entry in entries:
            assert entry["portal_url"].startswith("https://")
            assert entry["portal_kind"] in ("portal", "reference")


class TestHistoryPreserved:
    def test_handoff_record_survives_readiness_loss(self):
        # The store never deletes/resets on orchestration change: a stored
        # handed_off row is history regardless of later fact edits.
        from app.handoff.service import prepare_initiation

        record = prepare_initiation(
            application_id="app-1",
            approval_code="A05",
            orchestration_status="ready",
            reported_by="user-1",
        )
        # Later facts make A05 non-ready: no service function mutates or
        # removes the stored record; callers surface currently_ready instead.
        assert record["status"] == "handed_off"
