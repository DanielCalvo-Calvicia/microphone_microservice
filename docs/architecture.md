# Architecture

This document describes the architecture **after** the Clean Architecture refactor and records what was wrong before. It supersedes the structure described in `README.md` and the mapper/DTO conventions in `docs/general.md` where they disagree.

## Layers and dependency rule

```
composition_root  ──▶  infrastructure  ──▶  application  ──▶  domain
 (chooses concretes)    inbound/outbound     ports+services    entities, value objects, operations
```

Source-code dependencies point inward only. Runtime calls go outward (HTTP → service → hardware) through ports owned by `application`.

```
HTTP route ──▶ ServicePort ◀── MicrophoneService ──▶ MicrophonePort ◀── SoundDeviceMicrophone ──▶ sounddevice
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

## Layout

```
domain/
  errors.py                       DomainError, InvalidAudioFormat, CaptureAlreadyActive, CaptureNotActive
  value_objects/audio_format.py   AudioFormat(sample_rate, channels, chunk_size) — all fields > 0
  entities/microphone.py          Microphone — idle/capturing state machine
  operations/pcm.py               downmix_to_mono(pcm, channels)
  operations/format_negotiation.py fallback_formats(requested, device_default_rate)
application/
  dtos/stream_dtos.py             StartStreamCommand
  ports/service_port.py           ServicePort      (driving port used by inbound adapters)
  ports/microphone_port.py        MicrophonePort, AudioStream   (driven port)
  services/microphone_service.py  MicrophoneService — orchestration + lock, no rules of its own
infrastructure/
  inbound/http/routes/microphone_routes.py   build_microphone_router(service) + StartStreamBody
  outbound/sounddevice_microphone.py         SoundDeviceMicrophone, SoundDeviceAudioStream
composition_root/
  dependencies/microphone_dependency.py      picks the adapter, builds service, FastAPI app, router
  containers/container.py                    Container / BuildContainer
  setup/setup.py                             logging config (LOG_LEVEL), uvicorn lifecycle, cleanup
tests/  domain/ application/ infrastructure/ architecture/   (pytest)   +   simple.py (e2e, needs a real mic)
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
* A client disconnecting from `/stream` still ends the shared stream until stop + start.

## Deliberate changes

* `print` tracing (~154 calls, two per audio chunk) → `logging`; `LOG_LEVEL` is now honoured (default INFO).
* `POST /stop` no longer needs an empty JSON body.
* A retry with a format identical to the one that just failed is skipped.
* A raw stream that fails in `start()` is now closed (previously leaked). Shutdown cleanup runs in `finally`.
* A failed start no longer leaves stale rate/channel/chunk state.

## Known remaining debt

1. Domain errors are not mapped to 4xx (`InvalidAudioFormat` → 422, `CaptureAlreadyActive` → 409 would be natural).
2. Disconnected `/stream` consumer leaves the domain "capturing" while the shared stream is dead.
3. Requested `channels > 1` is silently mixed to mono and the response does not say so.
4. `MICROPHONE_API_KEY` and `APP_ENV` are defined in `.env*` but never read; there is no authentication.
5. `README.md` and `docs/general.md` still describe the old structure (`windows_sounddevice`, mappers, `FastApiAdapter`, `get_app`).
6. `soundfile` in `requirements.windows.txt` is unused.
7. `sounddevice` open/start/stop calls block the event loop (as before); `asyncio.to_thread` would fix it but needs hardware to validate.
8. The sounddevice adapter is tested against a fake module; run `python tests/simple.py` on the Windows machine with a real microphone to confirm.
9. Host/port/fallback rate/meter are constants in the composition root, not configuration.
