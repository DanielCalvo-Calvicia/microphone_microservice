# 06 — Inputs and outputs

> Depends on: 05

## Inputs

| Input | Form | Details |
|---|---|---|
| Control requests | HTTP from Brain | `POST /start` (JSON body, all optional: `sample_rate` 16000, `channels` 1, `chunk_size` 1024), `POST /stop`, `GET /stream` (optional `sample_rate`, `chunk_size`), `GET /available`, `GET /health` |
| Audio | The input device | Whatever the device delivers; opened at the requested format, else at its native rate, else (mono request) as stereo at the native rate; downmixed to mono |
| Configuration | Process environment | 15 variables (`docs/configuration/environment-variables.md`); the `.env` next to `main.py` is loaded at start |
| Trace context | HTTP header | W3C `traceparent`, continued by `TracingMiddleware` |

## Outputs

| Output | Form | Details |
|---|---|---|
| Event stream | `application/x-ndjson` on `GET /stream` | `stream_started` (message, sample_rate, channels=1), one `utterance` per finished utterance (`bytes_base64` PCM16 mono, `sample_rate`), then `completed` (`output_bytes_base64` empty) or `error` (`capture_failed`, not recoverable); headers `X-Sample-Rate`, `X-Action`, `X-Status`, `X-Message`, `X-Timestamp` |
| Control answers | JSON `ApiEnvelope` | `data` is `MicrophoneConfig` (start), `true` (stop), `AvailabilityResponse` (available), `HealthCheckResponse` (health) |
| Failures | HTTP status in the envelope | 409, 422, 503, 500 (`docs/api/api.md`) |
| Logs | stdout through `shared_logging` | Constant messages with fields; never audio |
| Console meter | stdout | A rewritten line per chunk while `MICROPHONE_SHOW_METER` is true (default) |
| Trace id | HTTP header `X-Trace-Id` | On every answer |

## Not produced

Files, metrics, database rows, calls to other services.
