"""Integration tests against local PostgreSQL (gaia_dev).

Real storage, real SQL, real full-text search. Each test cleans up
every row it creates. Skipped only when gaia_dev is unreachable —
never because of Supabase.
"""
from __future__ import annotations

import os

import pytest

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gaia_dev",
)

TEST_USER = "00000000-0000-0000-0000-0000000000db"


def _db():
    from app.db.postgres import PostgresDB, create_pool

    pool = create_pool(DB_URL, min_size=1, max_size=1, open=True)
    return pool, PostgresDB(pool)


def _reachable() -> bool:
    try:
        pool, db = _db()
        db.fetch_one("SELECT 1 AS n")
        pool.close()
        return True
    except Exception:
        return False


needs_pg = pytest.mark.skipif(
    not _reachable(), reason="local PostgreSQL gaia_dev unreachable"
)

EXPECTED_TABLES = {
    "projects",
    "project_facts",
    "approvals",
    "approval_rules",
    "applications",
    "documents",
    "document_requirements",
    "workflow_events",
    "sources",
    "source_chunks",
    "extracted_fields",
    "extraction_results",
    "validation_findings",
    "validation_results",
    "consistency_results",
    "consistency_findings",
    "instruments",
    "obligations",
    "entity_profiles",
    "audit_log",
}


@pytest.fixture(autouse=True)
def _test_user():
    try:
        pool, db = _db()
    except Exception:
        return  # needs_pg skips DB tests; pure tests don't need the user
    try:
        db.execute(
            "INSERT INTO auth.users (id) VALUES (%s) "
            "ON CONFLICT (id) DO NOTHING",
            (TEST_USER,),
        )
    finally:
        pool.close()


@pytest.fixture
def db():
    pool, handle = _db()
    yield handle
    pool.close()


@needs_pg
def test_01_connectivity(db):
    assert db.fetch_one("SELECT 1 AS n")["n"] == 1


@needs_pg
def test_02_03_required_tables_exist(db):
    rows = db.fetch_all(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )
    names = {r["tablename"] for r in rows}
    assert EXPECTED_TABLES <= names


@needs_pg
def test_04_identity_columns_constraints(db):
    cols = db.fetch_all(
        "SELECT table_name, column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name IN ('projects','applications') "
        "AND column_name IN ('jurisdiction','pack_version')"
    )
    assert len(cols) == 4
    assert all(c["is_nullable"] == "NO" for c in cols)
    checks = db.fetch_all(
        "SELECT conname FROM pg_constraint "
        "WHERE conname IN "
        "('chk_projects_jurisdiction','chk_applications_jurisdiction')"
    )
    assert len(checks) == 2
    idx = db.fetch_all(
        "SELECT indexname FROM pg_indexes WHERE indexname IN "
        "('idx_projects_jurisdiction','idx_applications_jurisdiction')"
    )
    assert len(idx) == 2


@needs_pg
def test_05_catalog_a01_a18_exactly_once(db):
    from app.repositories.approvals import ApprovalsRepository
    from app.seed.approval_catalog import load_approval_catalog

    repo = ApprovalsRepository(db)
    for record in load_approval_catalog():
        if repo.get_by_code(record["code"]) is None:
            repo.create(dict(record))
    rows = db.fetch_all("SELECT code, name FROM approvals ORDER BY code")
    codes = [r["code"] for r in rows if r["code"] is not None]
    assert codes == [f"A{i:02d}" for i in range(1, 19)]
    with pytest.raises(Exception):
        repo.create({"code": "A04", "name": "dup", "authority": "x"})


@needs_pg
def test_06_project_create(db):
    from app.repositories.projects import ProjectRepository

    repo = ProjectRepository(db)
    row = repo.create({
        "name": "itest-proj",
        "applicant_id": TEST_USER,
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    })
    try:
        assert row["jurisdiction"] == "IN-GJ"
        assert row["pack_version"] == "gj-legacy-unversioned"
    finally:
        db.execute("DELETE FROM projects WHERE id = %s", (row["id"],))


@needs_pg
def test_07_project_facts_roundtrip(db):
    from app.repositories.project_facts import ProjectFactsRepository
    from app.repositories.projects import ProjectRepository

    projects = ProjectRepository(db)
    facts_repo = ProjectFactsRepository(db)
    project = projects.create({
        "name": "itest-facts",
        "applicant_id": TEST_USER,
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    })
    try:
        saved = facts_repo.upsert(project["id"], {
            "entity_type": "pvt-ltd",
            "sector": "chemical",
            "jurisdictions": ["IN-GJ"],
            "headcount": 60,
            "annual_turnover_inr": 0,
            "facts_json": {"production_capacity": 20000},
        })
        assert saved["headcount"] == 60
        assert saved["facts_json"]["production_capacity"] == 20000
        again = facts_repo.upsert(project["id"], {
            "entity_type": "pvt-ltd",
            "sector": "chemical",
            "jurisdictions": ["IN-GJ"],
            "headcount": 61,
            "annual_turnover_inr": 0,
            "facts_json": {},
        })
        assert again["headcount"] == 61
        assert again["id"] == saved["id"]
    finally:
        db.execute(
            "DELETE FROM project_facts WHERE project_id = %s", (project["id"],)
        )
        db.execute("DELETE FROM projects WHERE id = %s", (project["id"],))


@needs_pg
def test_08_application_create_with_code(db):
    from app.repositories.applications import ApplicationsRepository
    from app.repositories.projects import ProjectRepository

    projects = ProjectRepository(db)
    apps = ApplicationsRepository(db)
    project = projects.create({
        "name": "itest-app",
        "applicant_id": TEST_USER,
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    })
    try:
        approval = db.fetch_one(
            "SELECT id FROM approvals WHERE code = %s", ("A04",)
        )
        assert approval is not None
        row = apps.create_with_reference({
            "project_id": project["id"],
            "approval_id": approval["id"],
            "approval_code": "A04",
            "status": "draft",
            "applicant_id": project["applicant_id"],
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        })
        assert row["approval_code"] == "A04"
        assert row["reference_number"].startswith("APP-")
        assert row["jurisdiction"] == "IN-GJ"
    finally:
        db.execute(
            "DELETE FROM applications WHERE project_id = %s", (project["id"],)
        )
        db.execute("DELETE FROM projects WHERE id = %s", (project["id"],))


@needs_pg
def test_09_orchestration_reads_application(db):
    from app.orchestration.facts import resolve_project_facts
    from app.repositories.applications import ApplicationsRepository
    from app.repositories.project_facts import ProjectFactsRepository
    from app.repositories.projects import ProjectRepository
    from app.rules.applicability import evaluate_approval_applicability
    from app.seed.approvals import (
        load_approval_authorities,
        load_approval_rules,
    )

    projects = ProjectRepository(db)
    facts_repo = ProjectFactsRepository(db)
    apps = ApplicationsRepository(db)
    project = projects.create({
        "name": "itest-orch",
        "applicant_id": TEST_USER,
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    })
    try:
        facts_repo.upsert(project["id"], {
            "entity_type": "pvt-ltd",
            "sector": "chemical",
            "jurisdictions": ["IN-GJ"],
            "headcount": 0,
            "annual_turnover_inr": 0,
            "facts_json": {
                "industry_type": (
                    "synthetic organic / specialty chemical manufacturing"
                )
            },
        })
        approval = db.fetch_one(
            "SELECT id FROM approvals WHERE code = %s", ("A04",)
        )
        app_row = apps.create_with_reference({
            "project_id": project["id"],
            "approval_id": approval["id"],
            "approval_code": "A04",
            "status": "draft",
            "applicant_id": project["applicant_id"],
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        })
        stored = apps.get_by_id(app_row["id"])
        assert stored is not None and stored["approval_code"] == "A04"
        facts = resolve_project_facts(
            facts_repo.get_by_project(project["id"])
        )
        evals = evaluate_approval_applicability(
            load_approval_rules(), facts, load_approval_authorities(), ["A04"]
        )
        assert evals[0].result == "applies"
    finally:
        db.execute(
            "DELETE FROM applications WHERE project_id = %s", (project["id"],)
        )
        db.execute(
            "DELETE FROM project_facts WHERE project_id = %s", (project["id"],)
        )
        db.execute("DELETE FROM projects WHERE id = %s", (project["id"],))


@needs_pg
def test_10_dahej_expected_mapping():
    from app.orchestration.service import orchestrate_application_full
    from app.seed.approvals import (
        load_approval_authorities,
        load_approval_rules,
    )
    from app.seed.dependencies import load_approval_dependencies
    from app.seed.documents import load_document_requirements
    from app.seed.evidence_gaps import get_gaps_for_approval
    from app.seed.scenario import load_scenario

    facts = load_scenario()
    rules = load_approval_rules()
    aids = sorted({r.approval_id for r in rules})
    result = orchestrate_application_full(
        application_id="dahej-itest",
        project_facts=facts,
        approval_rules=rules,
        approval_authorities=load_approval_authorities(),
        dependencies=load_approval_dependencies(),
        all_approval_ids=aids,
        document_requirements=load_document_requirements(),
        uploaded_documents=[],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=set(),
        evidence_gaps_by_approval={
            aid: get_gaps_for_approval(aid) for aid in aids
        },
    )
    got = {aid: o.status.value for aid, o in result.approvals.items()}
    assert {a for a, s in got.items() if s == "ready"} == {
        "A05", "A08", "A11", "A16", "A17",
    }
    assert {a for a, s in got.items() if s == "blocked_by_documents"} == {
        "A04", "A13",
    }
    assert {a for a, s in got.items() if s == "insufficient_data"} == {
        "A01", "A02", "A03", "A06", "A07", "A09", "A10",
        "A12", "A14", "A15",
    }
    assert got["A18"] == "not_applicable"
    assert result.overall_status.value == "blocked_by_documents"


@needs_pg
def test_11_fts_retrieval_and_gin_index(db):
    from app.repositories.sources import SourcesRepository

    idx = db.fetch_all(
        "SELECT indexname FROM pg_indexes "
        "WHERE indexname = 'idx_source_chunks_tsv'"
    )
    assert len(idx) == 1
    repo = SourcesRepository(db)
    assert repo.count_sources() >= 0
    assert repo.search_chunks("   ") == []
    sid = "ITEST-1"
    try:
        assert repo.get_by_id_text(sid) is None
        repo.create_source({
            "id": sid,
            "jurisdiction": "IN-GJ",
            "domain": "itest",
            "url": "https://example.invalid",
            "fetch_recipe": {},
            "trust_tier": "unverified",
            "content_hash": "itest",
            "title": "itest",
            "authority": "itest",
            "source_type": "test",
        })
        repo.create_chunk({
            "source_id": sid,
            "chunk_text": "gujarat fire safety certificate renewal period",
            "chunk_index": 0,
            "metadata": {},
        })
        hits = repo.search_chunks("fire safety certificate", limit=5)
        assert any(h["source_id"] == sid for h in hits)
        assert all("rank" in h for h in hits)
        ranks = [h["rank"] for h in hits if h["source_id"] == sid]
        assert all(r > 0 for r in ranks)
    finally:
        db.execute("DELETE FROM source_chunks WHERE source_id = %s", (sid,))
        db.execute("DELETE FROM sources WHERE id = %s", (sid,))


@needs_pg
def test_12_document_metadata_roundtrip(db):
    from app.repositories.applications import ApplicationsRepository
    from app.repositories.documents import DocumentsRepository
    from app.repositories.projects import ProjectRepository

    projects = ProjectRepository(db)
    apps = ApplicationsRepository(db)
    docs = DocumentsRepository(db)
    project = projects.create({
        "name": "itest-docs",
        "applicant_id": TEST_USER,
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    })
    doc_id = None
    try:
        approval = db.fetch_one(
            "SELECT id FROM approvals WHERE code = %s", ("A04",)
        )
        app_row = apps.create_with_reference({
            "project_id": project["id"],
            "approval_id": approval["id"],
            "approval_code": "A04",
            "status": "draft",
            "applicant_id": project["applicant_id"],
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        })
        row = docs.create_document({
            "application_id": app_row["id"],
            "requirement_key": "D01",
            "original_filename": "a.pdf",
            "storage_path": "itest/a.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 10,
        })
        doc_id = row["id"]
        assert docs.get_document(doc_id)["requirement_key"] == "D01"
    finally:
        if doc_id:
            docs.delete_document(doc_id)
        db.execute(
            "DELETE FROM applications WHERE project_id = %s", (project["id"],)
        )
        db.execute("DELETE FROM projects WHERE id = %s", (project["id"],))


@needs_pg
def test_13_workflow_events_roundtrip(db):
    from app.repositories.applications import ApplicationsRepository
    from app.repositories.projects import ProjectRepository
    from app.repositories.workflow_events import WorkflowEventsRepository

    projects = ProjectRepository(db)
    apps = ApplicationsRepository(db)
    events = WorkflowEventsRepository(db)
    project = projects.create({
        "name": "itest-events",
        "applicant_id": TEST_USER,
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    })
    try:
        approval = db.fetch_one(
            "SELECT id FROM approvals WHERE code = %s", ("A04",)
        )
        app_row = apps.create_with_reference({
            "project_id": project["id"],
            "approval_id": approval["id"],
            "approval_code": "A04",
            "status": "draft",
            "applicant_id": project["applicant_id"],
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        })
        created = events.create({
            "application_id": app_row["id"],
            "to_stage": "submitted",
            "action": "submit",
        })
        listed = events.list_for_application(app_row["id"])
        assert any(e["id"] == created["id"] for e in listed)
    finally:
        db.execute(
            "DELETE FROM applications WHERE project_id = %s", (project["id"],)
        )
        db.execute("DELETE FROM projects WHERE id = %s", (project["id"],))


@needs_pg
def test_14_evidence_gaps_are_code_seeded():
    from app.seed.evidence_gaps import load_evidence_gaps

    gaps = load_evidence_gaps()
    assert len(gaps) == 12
    assert {g.evidence_id for g in gaps} == {
        f"G0R5-{suffix}" for suffix in (
            "OSH-01", "FIRE-R25", "FIRE-RENEWAL", "EODB-2026",
            "ELEC-VOLTAGE", "CGDCR-CONSOL", "GIDC-GDCR",
            "GW-JURISDICTION", "GW-NO-EXTRACTION", "LIFT-RULES",
            "MSIHC-AUTHORITY", "VGIP-2026",
        )
    }


@needs_pg
def test_15_document_upload_writes_file_and_metadata(tmp_path):
    """End-to-end upload: bytes land on disk, metadata in PostgreSQL."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.deps import (
        get_documents_repository,
    )
    from app.api.documents import router
    from app.auth.dependencies import get_current_user
    from app.auth.models import SystemRole, UserContext
    from app.repositories.applications import ApplicationsRepository
    from app.repositories.documents import DocumentsRepository
    from app.repositories.projects import ProjectRepository
    from app.storage.local import LocalFileStorage

    pool, db = _db()
    try:
        projects, apps, docs = (
            ProjectRepository(db),
            ApplicationsRepository(db),
            DocumentsRepository(db),
        )
        project = projects.create({
            "name": "itest-upload", "applicant_id": TEST_USER,
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        })
        approval = db.fetch_one(
            "SELECT id FROM approvals WHERE code = %s", ("A04",))
        app_row = apps.create_with_reference({
            "project_id": project["id"], "approval_id": approval["id"],
            "approval_code": "A04", "status": "draft",
            "applicant_id": TEST_USER, "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned"})
        docs.create_requirement({
            "application_id": app_row["id"], "requirement_key": "D01",
            "document_name": "Test doc", "approval_id": "A04",
            "domain": "LAND", "requirement_level": "required",
        })
        storage = LocalFileStorage(tmp_path / "uploads")

        fapp = FastAPI()
        fapp.include_router(router)
        fapp.dependency_overrides[get_current_user] = lambda: UserContext(
            user_id=TEST_USER, email="t@t.com",
            role=SystemRole.APPLICANT, raw_claims={})
        fapp.dependency_overrides[get_documents_repository] = lambda: docs

        import app.storage as storage_module

        real_storage = storage_module.get_storage
        storage_module.get_storage = lambda: storage
        try:
            client = TestClient(fapp)
            resp = client.post(
                f"/applications/{app_row['id']}/documents/D01/upload",
                files={"file": ("a.pdf", b"%PDF-1.4 test",
                                 "application/pdf")},
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert (tmp_path / "uploads" / body["document"][
                "storage_path"]).exists()
            assert docs.get_document(
                body["document"]["id"])["original_filename"] == "a.pdf"
        finally:
            storage_module.get_storage = real_storage
            db.execute("DELETE FROM applications WHERE project_id = %s",
                       (project["id"],))
            db.execute("DELETE FROM projects WHERE id = %s",
                       (project["id"],))
    finally:
        pool.close()
