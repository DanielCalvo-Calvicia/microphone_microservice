# Requirements

Status as of 2026-11-05. **Done** means implemented and covered by the unit tests of the repository; **Done, hardware pending** means the same, but the behaviour on a real microphone was not re-checked since the last changes; **Planned** means decided and not built. Every row names the code that implements it or the record that decided it.

Sources: `../CLAUDE.md` (the rules of the workspace), the contracts in `contracts` (`contracts.stream`, `contracts.api`), the deployment audit of 2026-11-04 (`docs/deployment_audit/microphone.md`), and the decisions in `docs/decisions/`.

## Functional: capture

| ID | Requirement | Status | Where / record |
|---|---|---|---|
| FR-1 | Capture audio from the local input device through `sounddevice` / PortAudio and deliver it as mono 16-bit PCM. | Done, hardware pending | `infrastructure/outbound/sounddevice_capture/`, ADR-001 |
| FR-2 | Choose the device by `MICROPHONE_TARGET_KEYWORDS` (first input device whose name contains a keyword, case-insensitive); with no keyword or no match, the OS default input. | Done | `sounddevice_device_selector.py` |
| FR-3 | Open the device in the requested format, else at the device's native rate, else (mono requests) as stereo at the native rate; a candidate that repeats an earlier one is skipped. | Done | `domain/operations/format_negotiation.py` |
| FR-4 | Downmix what the device delivers to mono (mean of the frame, truncated toward zero). Channels requested above 1 are still delivered as mono. | Done | `domain/operations/pcm.py` |
| FR-5 | A capture can only start when idle; stopping an idle capture is a harmless no-op. | Done | `domain/entities/microphone.py`, ADR-001 |
| FR-6 | A stream that ends on its own (device read failure, or the `/stream` client gone) releases the device and returns the service to idle, so `/start` works again without `/stop`. | Done | `sounddevice_audio_stream.py`, `microphone_service.py` |
| FR-7 | On SIGINT / SIGTERM the device is released before the process exits; a failure to release it is logged, not raised. | Done | `main_flow/http.py` |

## Functional: utterances

| ID | Requirement | Status | Where / record |
|---|---|---|---|
| FR-8 | Cut the capture into utterances: one starts when the volume reaches `silence_threshold x speech_start_factor`, ends after `silence_limit_seconds` below `silence_threshold`, and keeps the silence that ended it. The utterance in progress is sent when the capture is closed and lost if the device fails. The cutting is always on. | Done | `domain/entities/utterance_segmenter.py`, ADR-003 |
| FR-9 | Each treatment has its own variable: DC offset removal, volume smoothing (and its factor), noise-floor tracking (speech over 3 x the floor, silence under 2 x), and the `MICROPHONE_SILENCE_*` and `MICROPHONE_SPEECH_START_FACTOR` thresholds; invalid values stop the start. | Done | `input_treatment.py`, `microphone_config.py`, `docs/configuration/environment-variables.md` |
| FR-10 | Optionally resample what is sent (`MICROPHONE_RESAMPLE_TO_HZ`, linear interpolation, chunk boundaries do not change the output); `/start` and `X-Sample-Rate` report the rate sent. | Done | `domain/operations/resample.py` |

## Functional: the HTTP interface

| ID | Requirement | Status | Where / record |
|---|---|---|---|
| FR-11 | `POST /start` (optional `sample_rate`, `channels`, `chunk_size`), `POST /stop` (idempotent, no body needed), `GET /available` (probe without opening the device), `GET /health`. | Done | `http_handler.py`, `docs/api/api.md` |
| FR-12 | `GET /stream` answers NDJSON `contracts.stream` events: `stream_started`, one `utterance` per utterance (`bytes_base64`, `sample_rate`), then `completed` (`output_bytes_base64` empty) or an `error` event (`capture_failed`, not recoverable). A `sample_rate` query that differs from the capture's is refused. | Done | `ndjson_audio_events.py`, ADR-002 |
| FR-13 | Non-stream answers use the envelope `action / status / status_code / message / timestamp / data` (`ApiEnvelope`); failures map to 409, 422, 503 or 500. | Done | `http_envelope.py`, `http_error_mapper.py`, ADR-004 |
| FR-14 | Only Brain calls the service; the service calls no other service. | Done | `../CLAUDE.md`; the code has no outbound HTTP |

## Functional: planned

| ID | Requirement | Status | Where / record |
|---|---|---|---|
| FR-15 | A simulated capture backend behind the same ports, chosen by an environment variable (code default `real`), reported in `/available` and in the log, so a machine without a microphone can run and be deployed. | Planned | T-02, `docs/proposals/PR-001-simulated-capture-backend.md` |
| FR-16 | Load `.env` at start (`python-dotenv`), then set `dotenv = true` in the deployment catalogue. | Planned | T-03.1, T-03.3, `docs/proposals/PR-002-dotenv-and-requirements-split.md` |

## Non-functional

| ID | Requirement | Status | Where / record |
|---|---|---|---|
| NFR-1 | Layered structure `main.py`, `main_flow`, `composition_root`, `application`, `domain`, `infrastructure`, dependencies pointing inward, enforced by a test. | Done | `tests/architecture/test_dependency_rules.py`, ADR-001 |
| NFR-2 | Configuration only through environment variables, documented in `.env.example`; the bind host is configurable; no hardcoded port. | Done | `infrastructure/config/` |
| NFR-3 | Logging only through `shared_logging`, with constant messages and keyword fields; audio is never logged. | Done | `docs/operations/monitoring.md` |
| NFR-4 | Audio stays PCM16 mono; the only conversions are the downmix of what the device delivers and the optional resample. | Done | FR-4, FR-10 |
| NFR-5 | Blocking device calls run off the event loop. | Done, hardware pending | `asyncio.to_thread` in the adapter |
| NFR-6 | Wire types come from `contracts` (bundled wheel in `vendor/`, refreshed with `contracts/scripts/bundle.py`, currently 0.15.0). | Done | `vendor/`, `requirements.*.txt` |
| NFR-7 | `ruff` and `mypy` (strict) clean; tests need no hardware. | Done | `pyproject.toml`; 127 tests |
| NFR-8 | Runs on Windows and on Linux / Raspberry Pi (`requirements.linux.txt`). | Windows works; Linux not run on real hardware | `docs/deployment/deployment.md` |
| NFR-9 | Authentication between services. | Not designed (project-wide) | ADR-005, `docs/security/security.md` |
