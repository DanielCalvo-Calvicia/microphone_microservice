# HTTP API of the service

What `python main.py` answers today, checked against the code (`infrastructure/inbound/http/`, `application/`, `domain/`). Only Brain calls this service. There is **no authentication** (see `docs/security/security.md`). The default port is `8000` (`SERVICE_PORT`). FastAPI also serves `/docs`, `/redoc` and `/openapi.json`.

## Routes

| Method and path | Purpose | State |
|---|---|---|
| `POST /start` | Open the input device and start the capture | Built |
| `GET /stream` | The event stream of the capture started by `/start` (NDJSON) | Built |
| `POST /stop` | Release the device; idempotent; no body needed | Built |
| `GET /available` | Whether an input device is usable, probed without opening it | Built |
| `GET /health` | Liveness: `healthy: true` whenever the process answers; touches no device | Built |

Another method on a known path answers `405` (FastAPI default).

## The answer envelope

Every non-stream answer is `contracts.api.common.envelope.ApiEnvelope`:

```json
{
  "action": "start_stream",
  "status": "success",
  "status_code": 200,
  "message": "Microphone stream started successfully",
  "timestamp": 1790000000.0,
  "data": { "sample_rate": 16000, "channels": 1, "chunk_size": 1024 }
}
```

On a failure `status` is `failure`, `status_code` the HTTP status, `message` is `"<what failed>: <error>"` and `data` is the error text.

## `POST /start`

Body (JSON, all fields optional):

| Field | Default | Meaning |
|---|---|---|
| `sample_rate` | `16000` | Requested rate in Hz |
| `channels` | `1` | Requested channels. Whatever is requested, the audio is delivered as mono |
| `chunk_size` | `1024` | Frames read from the device per chunk |

All three must be above 0 (`422` otherwise). The device is opened as close to the request as it allows: the requested format, then the same layout at the device's native rate, then (for a mono request) stereo at the native rate, which is downmixed afterwards. `data` is `contracts...microphone.start.MicrophoneConfig`: the **negotiated** `sample_rate` of what will be sent (this is `MICROPHONE_RESAMPLE_TO_HZ` when it is set, otherwise the device's rate), `channels` always `1`, and the requested `chunk_size`. A body that is not valid JSON or has a field of the wrong type gets FastAPI's own `422` (not the envelope).

## `GET /stream`

Optional query: `sample_rate` (must equal the capture's rate, else `422`), `chunk_size` (accepted and ignored). Answers `200` `application/x-ndjson` with the headers `X-Sample-Rate`, `X-Action: get_stream`, `X-Status: success`, `X-Message`, `X-Timestamp`. Without a capture started by `/start` it answers `409` with the envelope.

One event per line, built and encoded by `contracts.stream` (`MICROPHONE_OUTBOUND`):

| Event | When | Main fields |
|---|---|---|
| `stream_started` | first | `message`, `sample_rate`, `channels` (always 1) |
| `utterance` | once per finished utterance | `bytes_base64` (raw PCM16 mono, the whole utterance), `sample_rate` |
| `completed` | the capture ended normally | `reason`, `output_bytes_base64` (always empty: the utterances carried all the audio) |
| `error` | the device failed mid-stream (the stream then ends) | `code: capture_failed`, `message`, `recoverable: false` |

An utterance starts when the volume reaches the start threshold and ends after `MICROPHONE_SILENCE_LIMIT_SECONDS` of silence (the silence is kept in the utterance). The utterance in progress is sent when the capture is closed with `/stop`; it is lost if the device fails. How the thresholds are computed: `docs/architecture/architecture.md`, section 8.

If the device fails or the `/stream` client disconnects, the stream ends, the device is released and the service returns to idle: `/start` works again without calling `/stop`.

## `POST /stop`

Releases the device and ends the open `/stream` (with `completed`). Idempotent: `200` when nothing was capturing. `data` is `true`. A failure to release the device is `500` and the capture stays active.

## `GET /available`

`data` is `AvailabilityResponse{is_available, reason}`: the selected device (first keyword match of `MICROPHONE_TARGET_KEYWORDS`, else the OS default input) is looked up and must have input channels; the device is **not opened**. `reason` is `null` when available. The answer is `200` in both cases. The deployment tool uses this route as its readiness check, and Brain's start-up preflight too.

## `GET /health`

`200`, `data` is `HealthCheckResponse{healthy: true}`.

## Status codes of failures

From `infrastructure/inbound/http/http_error_mapper.py`:

| Status | Cause |
|---|---|
| `409` | Capture already active (`/start`), or not active (`/stream`) |
| `422` | Invalid audio format (a value of 0 or less), or a `sample_rate` on `/stream` that differs from the active capture |
| `503` | No usable input device (the device could not be found or opened) |
| `500` | Anything else (device read or close failures) |

## Tracing

`TracingMiddleware` (from `shared_logging`) continues an incoming W3C `traceparent` header or starts a trace, and answers with `X-Trace-Id`. See `docs/operations/monitoring.md`.
