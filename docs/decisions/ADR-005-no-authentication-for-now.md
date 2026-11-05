# ADR-005 — No authentication on the microphone

**Status:** Accepted as a known gap (2026-10-01)

## Context
Only Brain calls the service. Service-to-service authentication is not designed for the project; the one the speaker had was removed.

## Decision
The microphone has no authentication, CORS configuration or rate limit. It binds to `127.0.0.1` by default; `SERVICE_HOST` is configurable for a remote Brain. Access is limited by the network (see `docs/security/security.md`).

## Consequences
- Positive: nothing to configure or rotate.
- Negative: whoever reaches the port can hear the room after a `/start`. A project-wide design supersedes this ADR when it exists.
