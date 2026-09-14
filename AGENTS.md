# SIH 26130 — Agent Instructions

## Mission
Build a narrow Gujarat-focused industrial approvals assistant for SIH PS 26130. Reuse existing open-source code; do not rebuild generic permit/workflow infrastructure without a demonstrated gap.

## Locked stack
- Frontend: React + TypeScript + Vite + Tailwind CSS.
- Backend: FastAPI + Python.
- Database/Auth/Storage: Supabase (PostgreSQL, Auth, Storage where appropriate).
- API style: REST; OpenAPI generated from FastAPI.
- Regulatory search: PostgreSQL/pgvector or another justified vector layer; prefer the simplest Supabase-compatible option.
- Background jobs: only when required for ingestion/extraction/notifications.

Use current stable releases and official documentation at implementation time. Do not introduce deprecated APIs, packages, setup patterns, or framework syntax. Verify before coding when a library/API may have changed.

## Existing codebases
- All necessary logic from `Digital-Permit-Platform/` and `compliance-grid/` has been extracted and ported to Python.
- Those repositories have been deleted. Do not reference them as runtime dependencies.
- Adapt existing code instead of rebuilding.

## Before every task/session
1. Read `AGENTS.md`.
2. Read `ARCHITECTURE.md`, `RULES.md`, and `PRD.md`.
3. Inspect the current git state and relevant existing code before editing.
4. Identify which existing repository/component can be reused before creating a new implementation.
5. If requirements conflict or important facts are missing, stop and ask rather than guessing.

## During work
- Keep changes task-scoped.
- Prefer configuration/adapters/extensions over forks of large subsystems.
- Do not invent regulatory facts. Regulatory truth will come from the separately collected Gujarat dataset and official sources.
- Keep legal/regulatory decisions deterministic and traceable. LLMs explain/retrieve; they do not make unsupported statutory determinations.
- Never claim a real government integration unless an actual authorized integration exists.
- Never put secrets in source control.
- Preserve existing working functionality unless the task explicitly changes it.
- Add tests for business-critical logic, especially applicability, dependencies, permissions, SLA calculation, and document validation.

## Anti-overengineering gate
Before adding a service, dependency, abstraction, queue, microservice, ML model, or external platform, answer:
1. What concrete MVP requirement requires it?
2. Why can the existing stack not satisfy it?
3. What maintenance/integration cost does it add?
If the answer is weak, do not add it.

## End of every task
- Run the narrowest relevant checks, then broader checks when practical.
- Inspect the diff and remove unrelated changes.
- Update documentation/context so a fresh session can continue without relying on chat history.
- At minimum, review all four context files. Update only the files whose facts/status changed; do not add filler.
- Record important decisions, changed architecture, completed work, known limitations, and next task in concise form.
- Never rewrite these files just for the sake of changing them.

## Evidence hierarchy
For regulatory facts: official laws/rules/notifications and official Gujarat/government portals first. Community sources may help discover material but are not authoritative.
For technical decisions: official framework/library documentation first, then the repository's own current documentation/issues.

## Definition of done
A task is not complete merely because code was written. It requires:
- implementation,
- relevant tests/checks,
- no known lint/type/test errors for the changed scope,
- documentation/context updates,
- clear statement of any remaining uncertainty.
