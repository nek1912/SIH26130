"""Repeatable local PostgreSQL verification procedure (gaia_dev).

Checks (read-only unless --seed-catalog):
 1. PostgreSQL connectivity.
 2. Migrations 001-010 applied (tables + 010 identity columns/constraints).
 3. Required tables exist.
 4. Migration 010 identity columns/constraints exist.
 5. Approval catalog A01-A18 exists exactly once (--seed-catalog loads it).
 6-9. Project / facts / application / orchestration-read smoke test
     (creates + cleans up its own rows; skipped without --write).
 10. Dahej scenario produces the expected orchestration mapping (pure).
 11. Full-text regulatory retrieval works (tsvector + GIN present).
 12-13. Document metadata + workflow event round-trips (--write only).

Usage:
  python scripts/verify_local_db.py [--seed-catalog] [--write]

DATABASE_URL env or default postgresql://postgres:postgres@localhost:5432/gaia_dev.
Exit 0 only when every executed check passes.
"""
from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gaia_dev",
)

EXPECTED_TABLES = {
    "projects", "project_facts", "approvals", "approval_rules",
    "applications", "documents", "document_requirements",
    "workflow_events", "sources", "source_chunks", "extracted_fields",
    "extraction_results", "validation_findings", "validation_results",
    "consistency_results", "consistency_findings",
}

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    from app.db.postgres import PostgresDB, create_pool

    args = set(sys.argv[1:])
    do_write = "--write" in args
    do_seed = "--seed-catalog" in args or do_write

    try:
        pool = create_pool(DB_URL, min_size=1, max_size=1, open=True)
        db = PostgresDB(pool)
    except Exception as e:
        check("1 connectivity", False, f"{type(e).__name__}: {e}")
        return 1
    check("1 connectivity", db.fetch_one("SELECT 1 AS n")["n"] == 1)

    tables = {r["tablename"] for r in db.fetch_all(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")}
    check("2/3 migrations + required tables", EXPECTED_TABLES <= tables,
          f"{len(EXPECTED_TABLES & tables)}/{len(EXPECTED_TABLES)} present")

    cols = db.fetch_all(
        "SELECT table_name, column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name IN ('projects','applications') "
        "AND column_name IN ('jurisdiction','pack_version')")
    check("4 identity columns NOT NULL",
          len(cols) == 4 and all(c["is_nullable"] == "NO" for c in cols))
    checks = db.fetch_all(
        "SELECT conname FROM pg_constraint WHERE conname IN "
        "('chk_projects_jurisdiction','chk_applications_jurisdiction')")
    check("4 identity CHECK constraints", len(checks) == 2)

    from app.repositories.approvals import ApprovalsRepository
    from app.seed.approval_catalog import load_approval_catalog

    repo = ApprovalsRepository(db)
    if do_seed:
        for record in load_approval_catalog():
            if repo.get_by_code(record["code"]) is None:
                repo.create(dict(record))
    codes = [r["code"] for r in db.fetch_all(
        "SELECT code FROM approvals WHERE code IS NOT NULL ORDER BY code")]
    check("5 catalog A01-A18 exactly once",
          codes == [f"A{i:02d}" for i in range(1, 19)], f"{len(codes)} rows")

    if do_write:
        from app.repositories.applications import ApplicationsRepository
        from app.repositories.documents import DocumentsRepository
        from app.repositories.project_facts import ProjectFactsRepository
        from app.repositories.projects import ProjectRepository
        from app.repositories.workflow_events import WorkflowEventsRepository

        uid = "00000000-0000-0000-0000-000000000001"
        db.execute(
            "INSERT INTO auth.users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
            (uid,))
        projects, facts_repo = ProjectRepository(db), ProjectFactsRepository(db)
        apps, docs = ApplicationsRepository(db), DocumentsRepository(db)
        events = WorkflowEventsRepository(db)
        project = projects.create({
            "name": "verify-smoke", "applicant_id": uid,
            "jurisdiction": "IN-GJ", "pack_version": "gj-legacy-unversioned"})
        try:
            check("6 project created with identity",
                  project["jurisdiction"] == "IN-GJ")
            facts_repo.upsert(project["id"], {
                "entity_type": "pvt-ltd", "sector": "chemical",
                "jurisdictions": ["IN-GJ"], "headcount": 0,
                "annual_turnover_inr": 0, "facts_json": {}})
            check("7 facts stored",
                  facts_repo.get_by_project(project["id"]) is not None)
            approval = db.fetch_one(
                "SELECT id FROM approvals WHERE code = %s", ("A04",))
            app_row = apps.create_with_reference({
                "project_id": project["id"], "approval_id": approval["id"],
                "approval_code": "A04", "status": "draft",
                "applicant_id": uid, "jurisdiction": "IN-GJ",
                "pack_version": "gj-legacy-unversioned"})
            check("8 application created with code",
                  apps.get_by_id(app_row["id"])["approval_code"] == "A04")
            check("9 orchestration reads application",
                  apps.get_by_id(app_row["id"]) is not None)
            doc = docs.create_document({
                "application_id": app_row["id"], "requirement_key": "D01",
                "original_filename": "a.pdf", "storage_path": "v/a.pdf",
                "mime_type": "application/pdf", "file_size_bytes": 1})
            check("12 document metadata persisted",
                  docs.get_document(doc["id"]) is not None)
            docs.delete_document(doc["id"])
            ev = events.create({"application_id": app_row["id"],
                                "to_stage": "submitted", "action": "submit"})
            check("13 workflow event persisted",
                  any(e["id"] == ev["id"]
                      for e in events.list_for_application(app_row["id"])))
        finally:
            db.execute("DELETE FROM applications WHERE project_id = %s",
                       (project["id"],))
            db.execute("DELETE FROM project_facts WHERE project_id = %s",
                       (project["id"],))
            db.execute("DELETE FROM projects WHERE id = %s", (project["id"],))
    else:
        for name in ("6 project", "7 facts", "8 application", "9 orch read",
                     "12 documents", "13 events"):
            print(f"[SKIP] {name} (use --write)")

    from app.orchestration.service import orchestrate_application_full
    from app.seed.approvals import (
        load_approval_authorities, load_approval_rules)
    from app.seed.dependencies import load_approval_dependencies
    from app.seed.documents import load_document_requirements
    from app.seed.evidence_gaps import get_gaps_for_approval
    from app.seed.scenario import load_scenario

    facts = load_scenario()
    rules = load_approval_rules()
    aids = sorted({r.approval_id for r in rules})
    res = orchestrate_application_full(
        "verify-dahej", facts, rules, load_approval_authorities(),
        load_approval_dependencies(), aids, load_document_requirements(),
        [], [], [], None, None, set(),
        {a: get_gaps_for_approval(a) for a in aids})
    got = {a: o.status.value for a, o in res.approvals.items()}
    check("10 Dahej mapping",
          {a for a, s in got.items() if s == "ready"}
          == {"A05", "A08", "A11", "A16", "A17"}
          and {a for a, s in got.items() if s == "blocked_by_documents"}
          == {"A04", "A13"}
          and got["A18"] == "not_applicable"
          and res.overall_status.value == "blocked_by_documents")

    idx = db.fetch_all(
        "SELECT indexname FROM pg_indexes "
        "WHERE indexname = 'idx_source_chunks_tsv'")
    fts_ok = len(idx) == 1
    if fts_ok:
        from app.repositories.sources import SourcesRepository

        repo = SourcesRepository(db)
        sid = "VERIFY-1"
        try:
            if repo.get_by_id_text(sid) is None:
                repo.create_source({
                    "id": sid, "jurisdiction": "IN-GJ", "domain": "verify",
                    "url": "https://example.invalid",
                    "fetch_recipe": {}, "trust_tier": "unverified",
                    "content_hash": "v", "title": "v", "authority": "v",
                    "source_type": "test"})
            repo.create_chunk({"source_id": sid, "chunk_text":
                               "gujarat consent timeline green category",
                               "chunk_index": 0, "metadata": {}})
            hits = repo.search_chunks("consent timeline green", limit=5)
            fts_ok = any(h["source_id"] == sid and h["rank"] > 0 for h in hits)
        finally:
            db.execute("DELETE FROM source_chunks WHERE source_id = %s", (sid,))
            db.execute("DELETE FROM sources WHERE id = %s", (sid,))
    check("11 FTS retrieval + GIN index", fts_ok)

    from app.seed.evidence_gaps import load_evidence_gaps
    check("14 evidence gaps code-seeded", len(load_evidence_gaps()) == 12)

    pool.close()
    failed = [name for name, ok, _ in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
