# Architecture

This document describes the architecture **after** the Clean Architecture refactor and records what was wrong before. It supersedes the legacy docs in `docs/old/`.

## Layers and dependency rule

```
composition_root  ──▶  infrastructure  ──▶  application  ──▶  domain
 (chooses concretes)    inbound/outbound     ports+services    entities, value objects, operations
```

Source-code dependencies point inward only. Runtime calls go outward (HTTP → service → hardware) through ports owned by `application`.

```
HTTP handler ──▶ MicrophoneStreamingPort ◀── MicrophoneService ──▶ AudioCapturePort ◀── SoundDeviceAudioCapture ──▶ sounddevice
(inbound)      (driving port)   (application)         (driven port)       (outbound)
                                     │
                                     ▼
                              domain: Microphone, AudioFormat, pcm / format_negotiation
```

`tests/architecture/test_dependency_rules.py` enforces this by parsing imports:

| Layer | May import | Must not import |
|---|---|---|
| `domain` | stdlib, `domain` | everything else |
| `application` | stdlib, `domain`, `application` | `infrastructure`, `composition_root`, fastapi/starlette/pydantic/uvicorn/sounddevice/numpy/httpx |
| `infrastructure/inbound` | application, domain, frameworks | `infrastructure.outbound`, `composition_root` |
| `infrastructure/outbound` | application, domain, frameworks | `infrastructure.inbound`, `composition_root` |
| `composition_root` | everything | — |
| `main_flow` | `composition_root`, `infrastructure.config` | `infrastructure.inbound`, `infrastructure.outbound` |

## Layout

```
main.py                           calls main_flow.http.run_http()
main_flow/
  http.py                         config -> container -> uvicorn -> shutdown cleanup
  logging_setup.py                configure_logging (TRACE/WARN aliases)
domain/
  errors.py                       DomainError, InvalidAudioFormat, CaptureAlreadyActive, CaptureNotActive
  value_objects/audio_format.py   AudioFormat(sample_rate, channels, chunk_size) — all fields > 0
  entities/microphone.py          Microphone — idle/capturing state machine
  operations/pcm.py               downmix_to_mono(pcm, channels)
  operations/format_negotiation.py fallback_formats(requested, device_default_rate)
application/
  errors.py                       ApplicationError, MicrophoneUnavailable, StreamCloseFailed
  dtos/start_stream_inbound.py    StartStreamInboundDTO
  dtos/stream_outbound.py         StreamOutboundDTO
  ports/inbound/microphone_streaming_port.py   MicrophoneStreamingPort (driving)
  ports/outbound/audio_capture_port.py         AudioCapturePort (driven)
  ports/outbound/audio_stream_port.py          AudioStreamPort (driven)
  services/microphone_service.py  MicrophoneService — orchestration + lock, no rules of its own
infrastructure/
  config/                         ServerConfig, MicrophoneConfig (env -> frozen dataclasses)
  inbound/http/                   http_handler.py (MicrophoneHandler), http_envelope.py, http_error_mapper.py
  outbound/sounddevice_capture/   audio_driver.py (protocol), sounddevice_driver.py, sounddevice_device_selector.py,
                                  sounddevice_audio_capture.py, sounddevice_audio_stream.py, sounddevice_error_mapper.py
composition_root/
  dependencies/microphone_dependencies.py    new_audio_capture / new_microphone_service / new_http_app
  containers/http_container.py               HttpContainer, new_http_container
tests/  domain/ application/ infrastructure/ composition_root/ architecture/   (pytest)   +   simple.py (e2e, needs a real mic)
```

## Domain model (all of it is evidenced by pre-refactor code)

* **AudioFormat** (value object): immutable; rejects non-positive values.
* **Microphone** (entity): may only start when idle; stop is idempotent; remembers the format actually negotiated.
* **downmix_to_mono**: mean of each frame's channels, truncated toward zero (same result as the old numpy code).
* **fallback_formats**: requested → same layout at the device's native rate → (mono requests only) stereo at native rate. Identical repeats are skipped.
* Not introduced (no evidence): aggregates beyond `Microphone`, domain events, domain services.

## Behaviour that was deliberately preserved

* Every failure returns HTTP 500 with the same JSON envelope (`action/status/status_code/message/timestamp/data`).
* `channels > 1` requests are still delivered as mono.
* `/available` still means "a stream is active"; `/start` still returns JSON, audio is read from `/stream`.
* A client disconnecting from `/stream` still ends the shared stream (see "Deliberate changes": the service now goes idle by itself).

## Deliberate changes

* `print` tracing (~154 calls, two per audio chunk) → `logging`; `LOG_LEVEL` is now honoured (default INFO).
* `POST /stop` no longer needs an empty JSON body.
* A retry with a format identical to the one that just failed is skipped.
* A raw stream that fails in `start()` is now closed (previously leaked). Shutdown cleanup runs in `finally`.
* A failed start no longer leaves stale rate/channel/chunk state.
* A stream that dies on its own (device read failure, or the `/stream` consumer disconnecting) releases the device and returns the service to idle, so `/start` works again without `/stop`. A read failure surfaces as `StreamReadFailed` instead of a silent end of stream.
* The sounddevice adapter is split behind an `AudioDriver` protocol (`sounddevice_driver.py` is the only module importing `sounddevice`) and a `DeviceSelector`; open/read/close run in threads.

## Known remaining debt

1. Domain errors are not mapped to 4xx (`InvalidAudioFormat` → 422, `CaptureAlreadyActive` → 409); see `http_error_mapper.py`, decision D4.
2. Requested `channels > 1` is silently mixed to mono and the response does not say so.
3. `MICROPHONE_API_KEY` and `APP_ENV` are defined in `.env*` but never read; there is no authentication (decision D6).
4. Blocking `sounddevice` calls now run via `asyncio.to_thread`, but this is unvalidated on real hardware.
5. The sounddevice adapter is tested against a fake `AudioDriver`; run `python tests/simple.py` on the Windows machine with a real microphone to confirm.
