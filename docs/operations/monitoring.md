# Monitoring and operations

What exists today, checked against the code; anything else is stated as absent.

## Probes

| Probe | Behaviour |
|---|---|
| `GET /health` | `200`, `healthy: true` whenever the process answers; it touches no device |
| `GET /available` | `200` always; `is_available` is true when the selected input device exists and has input channels, with a `reason` when it is not. It looks the device up without opening it. This is the **readiness** check of the deployment tool (`ready = "/available"`) and of Brain's start-up preflight |

A machine without a usable microphone is reported as not ready: the deployment tool waits a grace period (15 s) and then reports the deploy as failed. There is no simulated device yet (`docs/proposals/PR-001-simulated-capture-backend.md`).

## Start and shutdown

Start: config, `init_logging("microphone")`, the container, uvicorn with `log_config=None` (the shared logger owns the output); the line `Starting server` carries `service_name`, `host` and `port`. The device is not opened at start; `POST /start` opens it.

Shutdown: on SIGINT or SIGTERM uvicorn stops accepting requests and returns; `main_flow/http.py` then logs `Server stopped; releasing microphone`, calls `stop_stream()` and logs `Cleanup finished`. A failure to release the device is logged with its traceback, not raised. A Ctrl+C is swallowed by `main.py` after the cleanup.

## Logs

All logs go through `shared_logging` (`get_logger(__name__)`, constant messages with keyword fields). The level is `LOG_LEVEL`. What is logged:

| When | Level | Message and fields |
|---|---|---|
| Start | info | `Starting server` (service name, host, port); `MicrophoneService initialized`; `SoundDeviceAudioCapture initialized` |
| A request | info | one line per request by `shared_logging.http` (method, path, status, duration, trace id) |
| Device choice | info / debug | `Scanning for microphones`, `Found input device`, `Auto-selected keyword match` or `No keyword match; using OS default input`, `Using microphone device` |
| Format | warning / info | `Requested sample rate may not be supported by the device`, `Failed to open device with candidate format`, `Microphone started` (device and format) |
| Capture | info | `Microphone stream started` (device rate, sent rate), `Microphone stream stopped`, `Stream closed` (chunks, bytes, overflows), `Microphone stream completed` (events, seconds) |
| Failure | error / warning | `Operation failed` (action, error), `Microphone stream read failed`, `Microphone capture failed mid-stream`, `Microphone stream terminated unexpectedly; capture is idle again`, `Failed to release the device after the stream terminated` |

**Audio is never logged**: neither samples nor the base64 of an utterance. Overflows (`overflows` in `Stream closed`) mean the machine could not read the device fast enough.

**The console meter** (`MICROPHONE_SHOW_METER=true`, the default) writes a rewritten line to stdout on every chunk (RMS, dB, peak, overflow flag). It is a manual-test aid; turn it off in a service window or a log file.

## Tracing

`TracingMiddleware` continues an incoming `traceparent` or starts a trace and answers with `X-Trace-Id`; every log record of the request carries the trace id and `service = microphone` (tested in `tests/composition_root/test_tracing.py`). Optional export: `TRACE_EXPORT_*` of `shared_logging`.

## Not present

- Metrics and alerting: none.
- Persistence: the service writes no file; the utterances only travel on the stream.
- Rate limiting and authentication: none.
- State survives nothing: a restart returns to idle, and Brain must call `/start` again.
