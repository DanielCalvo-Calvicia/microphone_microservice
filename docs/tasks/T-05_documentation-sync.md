# T-05 — Documentation sync

| | |
|---|---|
| Status | recurring: the first pass is done (2026-11-05); run again after every change that touches the documents |
| Kind | docs |
| Depends on | the task being documented |

## Goal

Keep the documentation true to the repository: document only what exists, mark plans as plans, write `UNKNOWN` for unknowns, no secrets, one home per fact, no empty documents. The day-to-day rule is the table in `CLAUDE.md`; this task is the checklist for a whole pass.

## Checklist after each task

| Trigger | Update |
|---|---|
| Any task done | its status in this folder's README board and in [ORDER.md](ORDER.md); the status table of `README.md`; `docs/requirements/requirements.md` (status and where of each requirement it touches); the work item of `docs/setup/16_work-items.md` |
| A decision is taken | an ADR for each non-obvious one (`docs/decisions/`); the task's *Resolution*; `docs/setup/13_decisions-and-overrides.md`; the question in `docs/questionnaires/` (the answer after `A:`, and its row in `00_README.md`) |
| The layout or a convention changes | the ADR it changes (a dated note), `docs/tasks/README.md` sections 3 and 3.1, `docs/architecture/architecture.md`, `docs/setup/10_architecture.md` |
| A variable is added, changed or removed | `.env.example`, `README.md`, `docs/configuration/environment-variables.md`, `docs/setup/06_inputs-and-outputs.md`, `CLAUDE.md` (Rules), and in `deployment` the manual and the generated toml |
| A route, a field, an event or a status changes | `docs/api/api.md`, `README.md`, `docs/requirements/requirements.md`, `docs/setup/06_inputs-and-outputs.md`, and `contracts` first |
| Logging, probes, shutdown or tracing changes | `docs/operations/monitoring.md` |
| Access, secrets, dependencies, what is captured changes | `docs/security/security.md`, `docs/setup/07_data-and-persistence.md` |
| How it starts or is deployed changes | `docs/deployment/deployment.md`, `docs/setup/11_runtime-and-deployment.md` and the deployment tool's catalogue and manual |
| A risk is found or closed | `docs/setup/14_risks-and-debt.md`, the debt list of `docs/architecture/architecture.md` section 12, the *Known limitations* of `README.md` |
| Test, ruff or mypy counts change | `CLAUDE.md` (Current state), `README.md` (Test), `docs/tasks/README.md` section 4, `docs/setup/12_quality-and-operations.md` (only after running them) |
| The `contracts` version changes | `requirements.*.txt`, `vendor/`, `CLAUDE.md`, `README.md`, NFR-6, `docs/setup/05_external-services.md`, `docs/setup/09_technology.md`, `docs/setup/15_sources-contradictions-questions.md` |

## Checks at the end of a pass

1. Every Markdown link of `README.md`, `CLAUDE.md` and `docs/` resolves (except `docs/old/` and the historical migration plan); every path a document names exists.
2. The board of the tasks README, `ORDER.md` and each task file give the same status for every task.
3. Every environment variable of `.env.example` is in the README table and in `docs/configuration/environment-variables.md`, and the other way round.
4. The numbers (tests, mypy files, `contracts` version) are the ones of a run made that day.
5. No `.env*` file was opened; no secret appears.
6. Report what was updated, and what was not verified (hardware).

## Pass of 2026-11-05 (done)

Rewrote the README, `CLAUDE.md` (with the mandatory table) and the architecture document; created `docs/api`, `configuration`, `operations`, `requirements`, `security`, `deployment`, `decisions` (ADR-001 to ADR-006), `proposals` (PR-001, PR-002), `setup` (00 to 17 and the questionnaires Q01) and this task plan, in the structure of `dynamics_microservice`. Contradictions fixed are listed in `docs/setup/15_sources-contradictions-questions.md`. Not verified: any behaviour on real hardware.
