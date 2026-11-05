# ADR-006 — The documentation follows the structure of dynamics_microservice

**Status:** Accepted (2026-11-05, on the maintainer's request)

## Context
The documentation was a README, a `CLAUDE.md` and one architecture document, and parts of it were false (the `contracts` version, the test counts, the stream events). Nothing said who had to update what.

## Decision
The documentation uses the structure of `dynamics_microservice`: `docs/setup/` (the intake sub-forms 01 to 17 and the questionnaires), `docs/tasks/` (the plan, `ORDER.md` and the task files), `docs/requirements/`, `docs/api/`, `docs/configuration/`, `docs/operations/`, `docs/security/`, `docs/deployment/`, `docs/decisions/`, `docs/proposals/`, `docs/architecture/`. `CLAUDE.md` carries a mandatory table: no change is finished until the documents that describe it are true again. Planned is marked as planned; hardware behaviour is never claimed unless it was run on a real microphone. Answers that only the maintainer can give are questions in `docs/setup/questionnaires/`, never invented answers.

Left out on purpose: the Engram intake prompts, `PROMPTS.md` and the Engram Cloud push of that project (this workspace does not use them; the `.engram/` folder here is stale).

## Consequences
- Positive: one home per fact; a stale number is a documentation bug with a named place to fix it.
- Negative: more files to keep in step for a small service; the rule in `CLAUDE.md` is the only thing that enforces it (there is no test, unlike the layout rules).
