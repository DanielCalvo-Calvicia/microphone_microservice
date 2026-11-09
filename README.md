# Microphone Microservice

HTTP service that captures audio from the local input device (`sounddevice` / PortAudio), cuts it into utterances and streams them as the project's `MICROPHONE_OUTBOUND` event stream (`contracts.stream`). Only Brain calls it.

Part of OBLIVION (`../README.md`). Owner: Daniel Calvo. Repository: `microphone_microservice`, branch `feature_ai_claude_2`.

```
input device  ──►  capture (mono PCM16)  ──►  utterance cutting  ──►  NDJSON events on GET /stream  ──►  Brain
(sounddevice)      downmix, negotiate         silence detection        stream_started, utterance, completed
```

## Status

Working on Windows, **needs a retest on real hardware** after the last changes (the utterance cutting moved here from STT on 2026-10-05). Linux / Raspberry Pi and Docker are not run on real hardware yet.

| Area | State |
|---|---|
| Capture from the input device, format negotiation, downmix to mono | Implemented; tested against a fake driver, hardware pending |
| Device choice by name keywords, else the OS default input | Implemented |
| Utterance cutting and its treatments (DC offset, smoothing, noise floor, resample, pre-roll) | Implemented (ADR-003); defaults not tuned on real rooms; the pre-roll (2026-11-09) is tested with fake audio and one offline recording of the stt diagnosis, not on this service with a real microphone |
| Routes `/start`, `/stream`, `/stop`, `/available`, `/health` | Implemented |
| Wire format: `contracts.stream` NDJSON events and the `ApiEnvelope` | Implemented; `contracts` 0.15.0 bundled in `vendor/` |
| Simulated capture backend (a machine without a microphone) | Planned ([PR-001](docs/proposals/PR-001-simulated-capture-backend.md), epic T-02; its first task waits for the maintainer's decisions, Q01-1 to Q01-3) |
| `.env` loading, runtime and dev requirements split | Planned ([PR-002](docs/proposals/PR-002-dotenv-and-requirements-split.md), epic T-03; T-03.2, the requirements split, is the next task) |
| Hardware verification: a real microphone, Linux / Raspberry Pi, Docker | Not done; needs the maintainer (epic T-04) |
| Authentication | Not designed (project-wide, ADR-005) |

## Requirements

- Python 3.14 in the service venv (`windows\Scripts\python.exe`); 3.11 or newer works for the code (`pyproject.toml`).
- An input device and PortAudio (Linux: `libportaudio2`, `portaudio19-dev`).
- `shared-logging` next to this folder (installed editable by the requirements file) and the bundled `contracts` wheel.

## Run

```bash
pip install -r requirements.windows.txt   # Linux / Raspberry Pi: requirements.linux.txt
python main.py
```

Use the service's own venv, `windows\Scripts\python.exe`. Configuration is read from the process environment (the service does not load `.env`; the deployment tool does it for you); see `.env.example`. The default bind address is `127.0.0.1`; set `SERVICE_HOST` (for example `0.0.0.0`) when Brain runs on another machine.

## Configuration

Full table with the rules of each value: [docs/configuration/environment-variables.md](docs/configuration/environment-variables.md).

| Variable | Default | Purpose |
|---|---|---|
| `SERVICE_NAME` | `Microphone Microservice` | API title / log name (the shared logger also reads `SERVICE_NAME`) |
| `SERVICE_HOST` | `127.0.0.1` | Bind address |
| `SERVICE_PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `INFO` | Read by the shared logging module (`TRACE`, `DEBUG`, `INFO`, `WARN`/`WARNING`, `ERROR`, `CRITICAL`) |
| `MICROPHONE_FALLBACK_SAMPLE_RATE` | `16000` | Rate used if the device reports none |
| `MICROPHONE_TARGET_KEYWORDS` | *(empty)* | Comma-separated device-name keywords (first match wins); empty = OS default input |
| `MICROPHONE_SHOW_METER` | `true` | Console volume meter (`1`, `true` or `yes`); turn it off outside a manual test |
| `MICROPHONE_SILENCE_THRESHOLD` | `150` | Volume (RMS of 16-bit samples) under which it is silent |
| `MICROPHONE_SILENCE_LIMIT_SECONDS` | `2.0` | Seconds of silence that end an utterance (must be above 0) |
| `MICROPHONE_SPEECH_START_FACTOR` | `2.0` | Speech starts at threshold x this factor (at least 1) |
| `MICROPHONE_DC_OFFSET_REMOVAL` | `false` | Subtract the slowly changing constant offset of the signal before measuring volume |
| `MICROPHONE_VOLUME_SMOOTHING` / `MICROPHONE_VOLUME_SMOOTHING_FACTOR` | `true` / `0.1` | Measure a smoothed volume (weight of the newest chunk, above 0 up to 1) so one click is not speech |
| `MICROPHONE_NOISE_FLOOR_TRACKING` | `true` | Raise the thresholds above the quietest volume heard (speech over 3 x it, silence under 2 x it) |
| `MICROPHONE_RESAMPLE_TO_HZ` | `0` | Rate of the audio sent on (linear interpolation); `0` = the device's rate, `16000` = what Whisper uses |
| `MICROPHONE_PREROLL_SECONDS` | `0.2` | Audio heard just before the volume reached the start volume, put in front of each utterance (whole chunks, at least this long) so the first sounds of the first word are not lost; `0` = off |

`LOG_FORMAT`, `LOG_OUTPUT`, `ENVIRONMENT` and `TRACE_EXPORT_*` are also read by the shared logging package, not by this service: see [`shared-logging/docs/logging.md`](../shared-logging/docs/logging.md). `.env.example` lists the 15 variables above, the same as `ServerConfig` / `MicrophoneConfig` in `infrastructure/config/`.

## Endpoints

Non-stream answers use the envelope `action / status / status_code / message / timestamp / data` (`contracts.api.common.envelope.ApiEnvelope`). Details: [docs/api/api.md](docs/api/api.md).

| Method | Path | Description |
|---|---|---|
| POST | `/start` | Body `{sample_rate, channels, chunk_size}` (all optional; defaults 16000, 1, 1024). Opens the device. `data` is a `MicrophoneConfig` with the negotiated `sample_rate` (of what is sent), `channels` = 1 and the requested `chunk_size` |
| GET | `/stream` | The event stream of the capture started by `/start`: `application/x-ndjson`, rate also in the `X-Sample-Rate` header. Optional query `sample_rate` (must equal the capture's rate, else 422) and `chunk_size` (accepted, ignored) |
| GET | `/available` | Whether an input device is usable, probed without opening it: `data` is `AvailabilityResponse{is_available, reason}` |
| POST | `/stop` | Releases the device. Idempotent; no body needed |
| GET | `/health` | Liveness (`HealthCheckResponse{healthy: true}`) |

Stream events (`contracts.stream`, `MICROPHONE_OUTBOUND`): `stream_started` (`message`, `sample_rate`, `channels`), then one `utterance` (`bytes_base64`, raw PCM16 mono, and its `sample_rate`) per finished utterance, then `completed` (`reason`, `output_bytes_base64` always empty) when the capture ends, or an `error` event (`code: capture_failed`, `recoverable: false`) if the device fails mid-stream. The microphone cuts what it hears into utterances (silence detection lives here, not in STT): an utterance starts when the volume reaches the start threshold and ends after `MICROPHONE_SILENCE_LIMIT_SECONDS` of silence, and the utterance in progress is sent when the capture is closed (it is lost if the device fails). The cutting is always on; each treatment has its own `MICROPHONE_*` variable.

HTTP status codes of failures (`infrastructure/inbound/http/http_error_mapper.py`): `409` capture already active / not active, `422` invalid audio format or `sample_rate` that differs from the active capture, `503` no usable input device, `500` anything else (device read/close failures).

Notes:

- The negotiated `sample_rate` can differ from the requested one; the device's native rate is tried as a fallback.
- Audio is always delivered as mono, even when `channels > 1` is requested; the response does not say the request was downmixed.
- If the device fails or the `/stream` client disconnects, the stream ends, the device is released and the service returns to idle, so `/start` works again without calling `/stop`.
- There is no authentication.

## Test

```powershell
windows\Scripts\python.exe -m pytest        # unit + architecture tests, no hardware needed
windows\Scripts\python.exe -m ruff check .
windows\Scripts\python.exe -m mypy .
windows\Scripts\python.exe tests\simple.py  # end to end, needs a real microphone
```

Result on 2026-11-09: `142 passed` in 2.1 s, ruff `All checks passed!`, mypy `no issues found in 53 source files` (127 passed on 2026-11-05, before the pre-roll). `tests/simple.py` and the sounddevice adapter on real hardware were not run (they need a microphone). `black` is configured in `pyproject.toml` and listed in the requirements; it was not run.

## Project layout

```text
main.py            entry point (calls main_flow)
main_flow/         config, logging init, uvicorn, graceful shutdown (releases the device)
composition_root/  the only place concrete adapters are wired together
infrastructure/    config, HTTP (inbound: handler, envelope, error mapper, NDJSON events) and sounddevice (outbound) adapters
application/       use-case service, utterance stream, ports, DTOs, application errors
domain/            entities (Microphone, UtteranceSegmenter), value objects, pure audio operations
tests/             domain, application, infrastructure, composition_root, architecture; simple.py (needs a real microphone)
vendor/            the bundled contracts wheel (0.15.0)
docs/              architecture, api, configuration, operations, requirements, security, deployment, decisions, proposals
```

Dependencies point inward only (`infrastructure -> application -> domain`); `tests/architecture/` enforces this.

## Scope

- **In scope:** capture, format negotiation, mono PCM16, utterance cutting, the optional resample, the HTTP control routes and the event stream.
- **Planned:** a simulated capture backend and `.env` loading (PR-001, PR-002).
- **Non-goals:** speech to text (STT), calling any other service (Brain is the only coordinator), authentication (not designed project-wide), recording audio to disk.

## Known limitations

- The sounddevice adapter and the thresholds are not validated on real hardware since the utterance cutting moved here.
- A machine without a microphone cannot run the pipeline (no simulated backend), and the deployment readiness check (`/available`) reports it as failed.
- `channels > 1` is mixed to mono silently.
- The utterance in progress is lost if the device fails mid-stream.
- The service does not load `.env`; the dev tools are in the runtime requirements and nothing is pinned.
- No authentication: restrict the port with the host firewall when `SERVICE_HOST` is not `127.0.0.1`.

## Documentation

| Document | Content |
|---|---|
| [docs/architecture/architecture.md](docs/architecture/architecture.md) | Architecture, control flow, the utterance cutting, debt |
| [docs/api/api.md](docs/api/api.md) | Routes, envelope, events, status codes |
| [docs/configuration/environment-variables.md](docs/configuration/environment-variables.md) | Every environment variable |
| [docs/operations/monitoring.md](docs/operations/monitoring.md) | Probes, shutdown, logs, tracing |
| [docs/requirements/requirements.md](docs/requirements/requirements.md) | Requirements and their status |
| [docs/security/security.md](docs/security/security.md) | Access, privacy, secrets, supply chain |
| [docs/deployment/deployment.md](docs/deployment/deployment.md) | How the deployment tool runs it; Windows, Linux, Docker |
| [docs/tasks/README.md](docs/tasks/README.md) | Task plan; [docs/tasks/ORDER.md](docs/tasks/ORDER.md) is the order to follow, with the state and the last update of every task |
| [docs/setup/00_README.md](docs/setup/00_README.md) | The project context in 17 sub-forms, and the [questions for the maintainer](docs/setup/questionnaires/Q01_open-questions.md) |
| [docs/decisions/](docs/decisions/) | Architecture decision records (ADR-001 to ADR-006) |
| [docs/proposals/](docs/proposals/) | Changes proposed and not built (PR-001, PR-002) |
| [docs/README.md](docs/README.md) | Index of the documentation, including the history (`architecture/PYTHON_MIGRATION_PLAN.md`, `old/`) |
| [CLAUDE.md](CLAUDE.md) | Rules for working in the repository, including the mandatory update of the documentation with every change |
