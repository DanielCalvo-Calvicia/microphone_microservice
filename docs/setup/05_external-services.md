# 05 — External services

> Depends on: 02, 03

Never write credentials here. This service has none.

| System | Direction | Protocol | Auth method | Purpose | Status |
|---|---|---|---|---|---|
| Brain (`brain_microservice`) | In (HTTP calls to this service) | HTTP: JSON control routes, NDJSON stream | none (ADR-005) | Starts and stops the capture, reads the utterance events, probes `/available` at its start-up preflight | Working (end-to-end suite of `contracts` with fake hardware; real hardware pending) |
| Audio input device | Out (local hardware) | PortAudio through `sounddevice` | OS permission to use the microphone | The source of the audio | Windows works; Linux / Raspberry Pi not run |
| `deployment` tool | In (HTTP `GET /available`) | HTTP | none | Readiness check after a deploy or update (`ready = "/available"`, 15 s grace) | Working |
| `shared-logging` | Library (in process) | Python import, editable install | — | Logging, tracing middleware (`TracingMiddleware`, `X-Trace-Id`), optional trace export | Working |
| `contracts` | Library (in process) | Python wheel bundled in `vendor/` (0.16.0) | — | Event schemas, codec, envelope, API dataclasses | Working |
| STT, TTS, speaker, stepper, ai-agent | None | — | — | They never talk to this service, and it never talks to them (Brain is the only coordinator) | NOT APPLICABLE |
| AWS, databases, cloud APIs | None | — | — | — | NOT APPLICABLE |
| Source control / CI | GitHub remote; no workflows in this repository | — | — | — | Repository active; CI UNKNOWN |

## Details

- Brain's address comes from the deployment tool (`MICROPHONE_BASE_URL`, computed from the layout), never `localhost` by assumption; the microphone's own bind host is `SERVICE_HOST`.
- Failure behaviour: no device is `503` on `/start` and `is_available: false` on `/available`; a device that fails while streaming ends the stream with an `error` event and the service returns to idle.
