# Microphone Microservice

HTTP service that captures audio from the local input device (`sounddevice`/PortAudio) and streams it as mono 16-bit PCM, framed as the project's `MICROPHONE_OUTBOUND` event stream (`contracts.stream`). Only Brain calls it.

## Run

```bash
pip install -r requirements.windows.txt   # Linux / Raspberry Pi: requirements.linux.txt
python main.py
```

(Use the service's own venv, `windows\Scripts\python.exe`.) Configuration is read from the environment; see `.env.example`. The default bind address is `127.0.0.1`; set `SERVICE_HOST` (for example `0.0.0.0`) when Brain runs on another machine.

| Variable | Default | Purpose |
|---|---|---|
| `SERVICE_NAME` | `Microphone Microservice` | API title / log name (the shared logger also reads `SERVICE_NAME`) |
| `SERVICE_HOST` | `127.0.0.1` | Bind address |
| `SERVICE_PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `INFO` | Read by the shared logging module (`TRACE`, `DEBUG`, `INFO`, `WARN`/`WARNING`, `ERROR`, `CRITICAL`) |
| `MICROPHONE_FALLBACK_SAMPLE_RATE` | `16000` | Rate used if the device reports none |
| `MICROPHONE_TARGET_KEYWORDS` | *(empty)* | Comma-separated device-name keywords (first match wins); empty = OS default input |
| `MICROPHONE_SHOW_METER` | `true` | Console volume meter (`1`, `true` or `yes`) |

`LOG_FORMAT`, `LOG_OUTPUT`, `ENVIRONMENT` and `TRACE_EXPORT_*` are also read by the shared logging package, not by this service: see [`shared-logging/docs/logging.md`](../shared-logging/docs/logging.md). `.env.example` lists the seven variables above, the same as `ServerConfig`/`MicrophoneConfig` in `infrastructure/config/`.

## Endpoints

Non-stream answers use the envelope `action / status / status_code / message / timestamp / data` (`contracts.api.common.envelope.ApiEnvelope`).

| Method | Path | Description |
|---|---|---|
| POST | `/start` | Body `{sample_rate, channels, chunk_size}` (all optional; defaults 16000, 1, 1024). Opens the device. `data` is a `MicrophoneConfig` with the negotiated `sample_rate`, `channels` = 1 and the requested `chunk_size` |
| GET | `/stream` | The event stream of the capture started by `/start`: `application/x-ndjson`, rate also in the `X-Sample-Rate` header. Optional query `sample_rate` (must equal the capture's rate, else 422) and `chunk_size` (accepted, ignored) |
| GET | `/available` | Whether an input device is usable, probed without opening it: `data` is `AvailabilityResponse{is_available, reason}` |
| POST | `/stop` | Releases the device. Idempotent; no body needed |
| GET | `/health` | Liveness (`HealthCheckResponse{healthy: true}`) |

Stream events (`contracts.stream`, `MICROPHONE_OUTBOUND`): `stream_started` (`message`, `sample_rate`, `channels`), then one `partial` (`bytes_base64`, raw PCM16 mono) per captured chunk, then `completed` (`reason`, `output_bytes_base64` always empty) when the capture ends, or an `error` event (`code: capture_failed`, `recoverable: false`) if the device fails mid-stream. Every chunk is forwarded; the microphone does no silence detection (that is STT's job).

HTTP status codes of failures (`infrastructure/inbound/http/http_error_mapper.py`): `409` capture already active / not active, `422` invalid audio format or `sample_rate` that differs from the active capture, `503` no usable input device, `500` anything else (device read/close failures).

Notes:

- The negotiated `sample_rate` can differ from the requested one; the device's native rate is tried as a fallback.
- Audio is always delivered as mono, even when `channels > 1` is requested; the response does not say the request was downmixed.
- If the device fails or the `/stream` client disconnects, the stream ends, the device is released and the service returns to idle, so `/start` works again without calling `/stop`.
- There is no authentication.

## Project layout

```text
main.py            entry point (calls main_flow)
main_flow/         config, logging init, uvicorn, graceful shutdown (releases the device)
composition_root/  the only place concrete adapters are wired together
infrastructure/    config, HTTP (inbound: handler, envelope, error mapper, NDJSON events) and sounddevice (outbound) adapters
application/       use-case service, ports, DTOs, application errors
domain/            entities, value objects, pure audio operations
tests/             domain, application, infrastructure, composition_root, architecture; simple.py (needs a real microphone)
```

Dependencies point inward only (`infrastructure -> application -> domain`); `tests/architecture/` enforces this.

## Development

```powershell
windows\Scripts\python.exe -m pytest        # unit + architecture tests, no hardware needed
windows\Scripts\python.exe -m ruff check .
windows\Scripts\python.exe -m mypy .
windows\Scripts\python.exe tests\simple.py  # end to end, needs a real microphone
```

Result on 2026-10-01: `88 passed` in 2.3 s, ruff `All checks passed!`, mypy `no issues found in 48 source files`. `tests/simple.py` and the sounddevice adapter on real hardware were not run (they need a microphone). `black` is configured in `pyproject.toml` and listed in `requirements.windows.txt`; it was not run.

Architecture: [docs/architecture/architecture.md](docs/architecture/architecture.md). The migration plan in `docs/architecture/PYTHON_MIGRATION_PLAN.md` is historical (already executed). `docs/old/` holds the legacy docs of the pre-refactor design.
