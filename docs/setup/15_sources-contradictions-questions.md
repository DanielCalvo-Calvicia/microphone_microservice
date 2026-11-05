# 15 — Sources, contradictions, open questions

> Depends on: all previous

## Authoritative sources

| Source | Location | Authoritative for |
|---|---|---|
| The code | this repository | What the service does |
| Workspace rules | `../CLAUDE.md`, `../README.md` | Layout, wire format, logging, hard rules |
| Wire format | `../contracts` (`contracts.stream`, `contracts.api`), bundled wheel `vendor/contracts_microservice-0.15.0` | Events and answers |
| Logging | `../shared-logging/docs/logging.md` | Log fields, trace propagation |
| Deployment | `../deployment/docs/DEPLOYMENT.md`, `../deployment/config/catalogue.toml` | How it is built, started, checked |
| Deployment audit | `docs/deployment_audit/microphone.md` (2026-11-04, verified against the code) | The gaps seen from the deployment side; the source of PR-001 and PR-002 |
| Decisions and questionnaires | `docs/decisions`, `docs/proposals`, `docs/setup/questionnaires` | What was decided (the newest answer wins) |
| Git history | `git log` | When things changed |

Stale, do not trust: `.engram/` (5 short notes from the first refactor), `docs/old/` (legacy design), the "Known remaining debt" lines of the pre-2026-11-05 architecture document.

## Contradictions found and resolved on 2026-11-05

| Subject | Conflict | Resolution |
|---|---|---|
| `contracts` version | `CLAUDE.md` said 0.12.0; `vendor/` and the requirements hold 0.15.0 | Resolved: 0.15.0 everywhere |
| Test and mypy counts | `CLAUDE.md` and the README said 88 tests and 48 files; the suite has 127 tests and 53 files (the deployment audit says the same) | Resolved: re-run on 2026-11-05 |
| `.env.example` size | The README said it lists seven variables; it lists 15 | Resolved |
| What `/stream` sends | The architecture document said one `partial` per chunk and "the microphone does no silence detection" | Resolved: one `utterance` per utterance (ADR-003) |
| `MICROPHONE_API_KEY`, `APP_ENV` | `.engram/decisions.md` (D6) says they are in the `.env*` files and read nowhere | Resolved by search: no code reads them; whether the git-ignored files still list them is UNKNOWN (not opened) |
| Docker audio on Windows | The first draft of the audit said a `mode = "local"` setting existed | Resolved in the audit: the setting is `runtime = "native"`, and the tool rejects `docker` on a Windows host |

## Open questions

**Blocking:** none for the documentation. T-02.1 (the sim backend decision) is `awaiting-user`: Q01-1 and Q01-2.

**Important (non-blocking):** all of [questionnaires/Q01_open-questions.md](questionnaires/Q01_open-questions.md): the sim default, the variable name, the `dotenv` change in `deployment`, the meter default, the stale folders, the staging and production env files, and when a hardware session is possible.

**Later ideas:** a filtered resampler; a PulseAudio bridge for Docker on Windows; a project-wide authentication design.
