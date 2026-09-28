"""Wire derive_mh_facts() into the IN-MH decision path (single path).

Baseline orchestration, What-If, handoffs and rehearse all consume
``_load_baseline_inputs`` (or its ``inputs["facts"]``), so derivation
happens once there; ``run_whatif_assessment`` re-derives only the
what-if branch after stripping previously-derived keys (provenance
tells which). IN-GJ behavior is byte-identical.
"""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.handoffs import _run_orchestration
from app.api.orchestration import _load_baseline_inputs, router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.orchestration.facts import apply_derived_facts, resolve_project_facts
from app.orchestration.whatif import run_whatif_assessment
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack

APP_ID = "00000000-0000-0000-0000-000000000099"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
USER_ID = "00000000-0000-0000-0000-000000000001"

_MH_PACK = load_regulatory_pack(IN_MH)


def _mh_app(approval_code, **over):
    app = {
        "id": APP_ID,
        "project_id": PROJECT_ID,
        "applicant_id": USER_ID,
        "status": "draft",
        "approval_id": "00000000-0000-0000-0000-000000000100",
        "approval_code": approval_code,
        "reference_number": "APP-MH-WIRE",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": IN_MH,
        "pack_version": "mh-v5-batch1",
    }
    app.update(over)
    return app


def _facts_record(facts_json):
    return {
        "id": "facts-mh",
        "project_id": PROJECT_ID,
        "entity_type": "pvt-ltd",
        "sector": "chemical",
        "jurisdictions": ["IN-MH"],
        "headcount": 0,
        "annual_turnover_inr": 0,
        "facts_json": dict(facts_json),
        "created_at": "2026-09-15T10:00:00Z",
        "updated_at": "2026-09-15T10:00:00Z",
    }


def _repos(app_dict, facts_record):
    app_repo = MagicMock(spec=ApplicationsRepository)
    app_repo.get_by_id.return_value = app_dict
    app_repo.get_by_project.return_value = [app_dict]
    app_repo.get_approval_stages.return_value = []
    facts_repo = MagicMock(spec=ProjectFactsRepository)
    facts_repo.get_by_project.return_value = facts_record
    docs_repo = MagicMock(spec=DocumentsRepository)
    docs_repo.list_documents_for_application.return_value = []
    docs_repo.get_extraction_result_for_document.return_value = None
    docs_repo.get_validation_result_for_document.return_value = None
    events_repo = MagicMock(spec=WorkflowEventsRepository)
    events_repo.list_for_application.return_value = []
    consistency_repo = MagicMock(spec=ConsistencyRepository)
    consistency_repo.get_latest_result.return_value = None
    return app_repo, facts_repo, docs_repo, events_repo, consistency_repo


def _load(app_dict, facts_record):
    repos = _repos(app_dict, facts_record)
    return _load_baseline_inputs(app_dict, UUID(APP_ID), *repos)


def _mh_orchestrate_kwargs(inputs):
    return {
        "application_id": inputs["application_id"],
        "project_facts": inputs["facts"],
        "approval_rules": inputs["rules"],
        "approval_authorities": inputs["authorities"],
        "dependencies": inputs["dependencies"],
        "all_approval_ids": inputs["all_approval_ids"],
        "document_requirements": inputs["doc_requirements"],
        "uploaded_documents": inputs["uploaded_docs"],
        "extraction_results": inputs["extraction_results"],
        "validation_results": inputs["validation_results"],
        "consistency_result": inputs["consistency_result"],
        "sla_info": inputs["sla_info"],
        "obtained_approvals": inputs["obtained"],
        "evidence_gaps_by_approval": inputs["evidence_gaps_by_approval"],
        "fact_provenance": inputs["fact_provenance"],
    }


class TestApplyDerivedFactsHelper:
    def test_mh_merges_and_reports_provenance(self):
        merged, provenance = apply_derived_facts(
            {"F-INC-02": 2.5, "F-INC-09": 10}, IN_MH
        )
        assert merged["F-INC-01"] == "MICRO"
        entry = provenance["F-INC-01"]
        assert entry["fact_id"] == "F-INC-01"
        assert entry["derived"] is True
        assert entry["derivation"] == "derive_msme_class"
        assert entry["source_facts"] == ["F-INC-02", "F-INC-09"]
        assert entry["value"] == "MICRO"

    def test_gj_passthrough_is_equal(self):
        facts = {"sector": "chemical", "headcount": 60}
        merged, provenance = apply_derived_facts(facts, IN_GJ)
        assert merged == facts
        assert provenance == {}

    def test_unknown_jurisdiction_passthrough(self):
        facts = {"F-INC-02": 2.5}
        merged, provenance = apply_derived_facts(facts, "IN-XX")
        assert merged == facts
        assert provenance == {}

    def test_supplied_value_never_rederived(self):
        merged, provenance = apply_derived_facts(
            {"F-INC-01": "LARGE", "F-INC-02": 2.5, "F-INC-09": 10}, IN_MH
        )
        assert merged["F-INC-01"] == "LARGE"
        assert "F-INC-01" not in provenance


class TestBaselineLoaderDerives:
    def test_loader_derives_msme_for_mh(self):
        inputs = _load(
            _mh_app("APR-043"),
            _facts_record(
                {
                    "F-INC-02": 2.5,
                    "F-INC-09": 10,
                    "F-WAT-05": 5,
                    "F-WAT-06": "DOMESTIC_ONLY",
                }
            ),
        )
        assert inputs["facts"]["F-INC-01"] == "MICRO"
        assert inputs["fact_provenance"]["F-INC-01"]["derivation"] == (
            "derive_msme_class"
        )

    def test_loader_derives_mah_for_mh(self):
        inputs = _load(
            _mh_app("APR-001"),
            _facts_record(
                {
                    "F-PRC-01": 10,
                    "F-PRC-02": 10,
                    "F-HAZ-01": [{"chemical": "Ammonia", "max_qty_t": 40}],
                    "F-HAZ-02": [
                        {
                            "chemical": "Ammonia",
                            "schedule": "Sch3P1",
                            "col3_t": 50,
                        }
                    ],
                }
            ),
        )
        assert inputs["facts"]["F-PRC-03"] is False
        assert inputs["fact_provenance"]["F-PRC-03"]["derivation"] == (
            "derive_mah_status"
        )

    def test_loader_gj_unchanged(self):
        record = _facts_record({"industry_type": "chemical"})
        record["jurisdictions"] = ["IN-GJ"]
        app = _mh_app("A04", jurisdiction=IN_GJ,
                      pack_version="gj-legacy-unversioned")
        inputs = _load(app, record)
        assert inputs["facts"] == resolve_project_facts(record)
        assert inputs["fact_provenance"] == {}
        assert "F-INC-01" not in inputs["facts"]
        assert "F-PRC-03" not in inputs["facts"]


class TestDecisionEffect:
    def test_r002_evaluable_via_derived_mah_false(self):
        from app.orchestration.service import orchestrate_application_full
        from app.rules.applicability import evaluate_approval_applicability

        inputs = _load(
            _mh_app("APR-001"),
            _facts_record(
                {
                    "F-PRC-01": 10,
                    "F-PRC-02": 10,
                    "F-HAZ-01": [{"chemical": "Ammonia", "max_qty_t": 40}],
                    "F-HAZ-02": [
                        {
                            "chemical": "Ammonia",
                            "schedule": "Sch3P1",
                            "col3_t": 50,
                        }
                    ],
                }
            ),
        )
        evals = evaluate_approval_applicability(
            inputs["rules"], inputs["facts"], inputs["authorities"]
        )
        r002 = next(e for e in evals if e.rule_id == "R-002")
        assert r002.result == "applies"
        orch = orchestrate_application_full(**_mh_orchestrate_kwargs(inputs))
        assert orch.approvals["APR-001"].applicability_result == "applies"
        assert orch.fact_provenance["F-PRC-03"].value is False

    def test_r043_evaluable_via_derived_msme(self):
        from app.orchestration.service import orchestrate_application_full
        from app.rules.applicability import evaluate_approval_applicability

        inputs = _load(
            _mh_app("APR-043"),
            _facts_record(
                {
                    "F-INC-02": 2.5,
                    "F-INC-09": 10,
                    "F-WAT-05": 5,
                    "F-WAT-06": "DOMESTIC_ONLY",
                }
            ),
        )
        evals = evaluate_approval_applicability(
            inputs["rules"], inputs["facts"], inputs["authorities"]
        )
        r043 = next(e for e in evals if e.rule_id == "R-043")
        assert r043.result == "applies"
        orch = orchestrate_application_full(**_mh_orchestrate_kwargs(inputs))
        assert orch.approvals["APR-043"].applicability_result == "applies"
        assert orch.fact_provenance["F-INC-01"].value == "MICRO"


class TestProvenanceExposed:
    def test_orchestration_endpoint_returns_provenance(self):
        app = FastAPI()
        app.include_router(router)
        user = UserContext(
            user_id=USER_ID, email="t@t.com", role=SystemRole.APPLICANT,
            raw_claims={},
        )
        app_dict = _mh_app("APR-043")
        record = _facts_record(
            {
                "F-INC-02": 2.5,
                "F-INC-09": 10,
                "F-WAT-05": 5,
                "F-WAT-06": "DOMESTIC_ONLY",
            }
        )
        repos = _repos(app_dict, record)
        app.dependency_overrides[get_current_user] = lambda: user
        from app.api.deps import (
            get_applications_repository,
            get_consistency_repository,
            get_documents_repository,
            get_project_facts_repository,
            get_workflow_events_repository,
        )

        app.dependency_overrides[get_applications_repository] = (
            lambda: repos[0]
        )
        app.dependency_overrides[get_project_facts_repository] = (
            lambda: repos[1]
        )
        app.dependency_overrides[get_documents_repository] = (
            lambda: repos[2]
        )
        app.dependency_overrides[get_workflow_events_repository] = (
            lambda: repos[3]
        )
        app.dependency_overrides[get_consistency_repository] = (
            lambda: repos[4]
        )
        client = TestClient(app)
        response = client.get(f"/applications/{APP_ID}/orchestration")
        assert response.status_code == 200
        provenance = response.json()["fact_provenance"]
        assert provenance["F-INC-01"]["derived"] is True
        assert provenance["F-INC-01"]["derivation"] == "derive_msme_class"
        assert provenance["F-INC-01"]["source_facts"] == [
            "F-INC-02", "F-INC-09",
        ]
        assert provenance["F-INC-01"]["value"] == "MICRO"


def _whatif_kwargs(inputs, overrides, provenance):
    return {
        "application_id": inputs["application_id"],
        "base_facts": inputs["facts"],
        "fact_overrides": overrides,
        "approval_rules": inputs["rules"],
        "approval_authorities": inputs["authorities"],
        "dependencies": inputs["dependencies"],
        "all_approval_ids": inputs["all_approval_ids"],
        "document_requirements": inputs["doc_requirements"],
        "uploaded_documents": inputs["uploaded_docs"],
        "extraction_results": inputs["extraction_results"],
        "validation_results": inputs["validation_results"],
        "consistency_result": inputs["consistency_result"],
        "sla_info": inputs["sla_info"],
        "obtained_approvals": inputs["obtained"],
        "evidence_gaps_by_approval": inputs["evidence_gaps_by_approval"],
        "fact_provenance": provenance,
        "jurisdiction": IN_MH,
    }


class TestWhatIfRederives:
    def _inputs_043(self):
        return _load(
            _mh_app("APR-043"),
            _facts_record(
                {
                    "F-INC-02": 2.5,
                    "F-INC-09": 10,
                    "F-WAT-05": 5,
                    "F-WAT-06": "DOMESTIC_ONLY",
                }
            ),
        )

    def test_override_source_recomputes_msme(self):
        inputs = self._inputs_043()
        resp = run_whatif_assessment(
            **_whatif_kwargs(inputs, {"F-INC-02": 100},
                             inputs["fact_provenance"])
        )
        assert resp.baseline.fact_provenance["F-INC-01"].value == "MICRO"
        assert resp.what_if.fact_provenance["F-INC-01"].value == "MEDIUM"

    def test_override_derived_key_takes_precedence(self):
        # R-044 needs DOMESTIC_ONLY purpose, so use INDUSTRIAL to
        # isolate the R-043 (F-INC-01) decision.
        inputs = _load(
            _mh_app("APR-043"),
            _facts_record(
                {
                    "F-INC-02": 2.5,
                    "F-INC-09": 10,
                    "F-WAT-05": 5,
                    "F-WAT-06": "INDUSTRIAL",
                }
            ),
        )
        assert inputs["facts"]["F-INC-01"] == "MICRO"
        resp = run_whatif_assessment(
            **_whatif_kwargs(inputs, {"F-INC-01": "LARGE"},
                             inputs["fact_provenance"])
        )
        assert "F-INC-01" not in resp.what_if.fact_provenance
        assert resp.what_if.approvals["APR-043"].applicability_result == (
            "does_not_apply"
        )

    def test_override_haz_recomputes_mah(self):
        inputs = _load(
            _mh_app("APR-001"),
            _facts_record(
                {
                    "F-PRC-01": 10,
                    "F-PRC-02": 10,
                    "F-HAZ-01": [{"chemical": "Ammonia", "max_qty_t": 40}],
                    "F-HAZ-02": [
                        {
                            "chemical": "Ammonia",
                            "schedule": "Sch3P1",
                            "col3_t": 50,
                        }
                    ],
                }
            ),
        )
        resp = run_whatif_assessment(
            **_whatif_kwargs(
                inputs,
                {"F-HAZ-01": [{"chemical": "Ammonia", "max_qty_t": 60}]},
                inputs["fact_provenance"],
            )
        )
        assert resp.baseline.fact_provenance["F-PRC-03"].value is False
        assert resp.what_if.fact_provenance["F-PRC-03"].value is True

    def test_missing_source_stays_unknown(self):
        inputs = _load(
            _mh_app("APR-043"),
            _facts_record({"F-INC-02": 2.5, "F-WAT-05": 5}),
        )
        assert "F-INC-01" not in inputs["fact_provenance"]
        resp = run_whatif_assessment(
            **_whatif_kwargs(inputs, {}, inputs["fact_provenance"])
        )
        assert "F-INC-01" not in resp.what_if.fact_provenance

    def test_explicit_unknown_source_stays_unknown(self):
        inputs = _load(
            _mh_app("APR-043"),
            _facts_record(
                {"F-INC-02": 2.5, "F-INC-09": "UNKNOWN", "F-WAT-05": 5}
            ),
        )
        assert "F-INC-01" not in inputs["fact_provenance"]
        resp = run_whatif_assessment(
            **_whatif_kwargs(inputs, {}, inputs["fact_provenance"])
        )
        assert "F-INC-01" not in resp.what_if.fact_provenance

    def test_gj_whatif_unchanged(self):
        record = _facts_record({"industry_type": "chemical"})
        record["jurisdictions"] = ["IN-GJ"]
        app = _mh_app("A04", jurisdiction=IN_GJ,
                      pack_version="gj-legacy-unversioned")
        inputs = _load(app, record)
        kwargs = _whatif_kwargs(inputs, {"headcount": 99}, {})
        kwargs["jurisdiction"] = IN_GJ
        resp = run_whatif_assessment(**kwargs)
        assert resp.baseline.fact_provenance == {}
        assert resp.what_if.fact_provenance == {}


class TestSharedPaths:
    def test_handoff_uses_derived_facts(self):
        inputs = _load(
            _mh_app("APR-043"),
            _facts_record(
                {
                    "F-INC-02": 2.5,
                    "F-INC-09": 10,
                    "F-WAT-05": 5,
                    "F-WAT-06": "DOMESTIC_ONLY",
                }
            ),
        )
        orch = _run_orchestration(inputs)
        assert orch.approvals["APR-043"].applicability_result == "applies"
        assert orch.fact_provenance["F-INC-01"].value == "MICRO"

    def test_rehearse_uses_derived_facts(self):
        from app.regulatory.impact import (
            ChangeDescriptor,
            ChangeKind,
            RehearsalInputs,
            rehearse_impact,
        )

        inputs = _load(
            _mh_app("APR-043"),
            _facts_record(
                {
                    "F-INC-02": 2.5,
                    "F-INC-09": 10,
                    "F-WAT-05": 5,
                    "F-WAT-06": "DOMESTIC_ONLY",
                }
            ),
        )
        pack = inputs["pack"]
        impact = rehearse_impact(
            ChangeDescriptor(
                change_kind=ChangeKind.SOURCE_METADATA_CHANGE,
                source_id="SRC-052",
                old_value={"title": "CGWA guidelines"},
                new_value={"title": "CGWA guidelines (revised locator)"},
            ),
            RehearsalInputs(
                base_facts=inputs["facts"],
                approval_rules=inputs["rules"],
                approval_authorities=inputs["authorities"],
                dependencies=inputs["dependencies"],
                all_approval_ids=inputs["all_approval_ids"],
                document_requirements=inputs["doc_requirements"],
                uploaded_documents=inputs["uploaded_docs"],
                extraction_results=inputs["extraction_results"],
                validation_results=inputs["validation_results"],
                consistency_result=inputs["consistency_result"],
                sla_info=inputs["sla_info"],
                obtained_approvals=inputs["obtained"],
                evidence_gaps_by_approval=inputs[
                    "evidence_gaps_by_approval"
                ],
                known_source_ids={s.id for s in pack.sources},
                evidence_registry=list(pack.evidence_gaps),
                evidence_hints=dict(pack.evidence_hints),
            ),
        )
        assert "APR-043" in impact.affected_approvals
        assert impact.baseline_results["APR-043"]["applicability"] == (
            "applies"
        )
