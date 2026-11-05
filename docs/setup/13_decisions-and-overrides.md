# 13 — Decisions and overrides

> Depends on: 10–12. Every decision with its why and date. The records are in [../decisions/](../decisions/).

## Decisions

| Slug | Decision | Why | Date | Record |
|---|---|---|---|---|
| `layered-architecture-and-ports` | Layered structure, ports and adapters, an `AudioDriver` protocol as the test seam, import rules enforced by a test | The first version was a flat script with about 154 `print` calls and no way to test without a microphone | 2026-09-20 | ADR-001 |
| `contract-event-stream` | `/stream` is NDJSON of `contracts.stream` events, audio as PCM16 mono in `bytes_base64` | One typed wire format for every service | 2026-09-20 | ADR-002 |
| `utterance-cutting-in-the-microphone` | Silence detection and the input treatments live here; one `utterance` event per utterance; the cutting is always on, each treatment is an env var | STT should only transcribe; less traffic; thresholds tuned where the audio is captured | 2026-10-05 | ADR-003 |
| `http-status-mapping-and-device-probe` | 409, 422, 503, 500 mapped in one place; `/available` probes the device without opening it | Brain and the deployment tool must tell "no microphone" from a bug | 2026-09-20 | ADR-004 |
| `no-authentication-for-now` | No authentication, CORS or rate limit; bind `127.0.0.1` by default | Service-to-service authentication is not designed project-wide | 2026-10-01 | ADR-005 |
| `documentation-structure` | The documentation follows the structure of `dynamics_microservice`: setup, tasks, requirements, api, configuration, operations, security, deployment, decisions, proposals; every change updates it | One home per fact, and a rule that keeps it true | 2026-11-05 | ADR-006 |

## Proposed, not decided

| Slug | Proposal | Blocked by | Record |
|---|---|---|---|
| `simulated-capture-backend` | A `sim` backend behind the same ports, code default `real` | Question Q01-1 and Q01-2 (the variable name and where the sim default is set) | PR-001, T-02 |
| `dotenv-and-requirements-split` | Load `.env`, split dev requirements, lower bounds | Q01-4 (the change in `deployment`) | PR-002, T-03 |

## Overrides of the workspace standard

None. The service follows `../CLAUDE.md` (layout, wire format, logging, responses, audio, configuration). Two points where it is behind the standard, not overriding it: `contracts.api` is used for the control answers but the standard's note that `contracts` is "not used as fully as it should be" applies project-wide; and the standard's lower-bound pinning is not applied yet (T-03).
