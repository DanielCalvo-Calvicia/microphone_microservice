# Architecture Design Document

Describes the structure of `microphone_microservice` as it is in the code (reviewed 2026-11-05, branch `feature_ai_claude_2`). It supersedes the legacy notes in `docs/old/`. `docs/architecture/PYTHON_MIGRATION_PLAN.md` is the historical plan of the refactor that created this layout (executed, kept as history).

## Table of Contents

1. Purpose and scope
2. High-level architecture
3. Module responsibilities
4. Package map
5. Control flow
6. Public APIs (ports)
7. Data structures
8. Utterance cutting
9. Design patterns
10. Dependency rules
11. Execution sequence
12. Known issues and debt
13. Recommendations

## 1. Purpose and scope

The service captures audio from the local input device (`sounddevice` / PortAudio), cuts it into **utterances** (what is said between two silences) and streams them as `contracts.stream` events (`MICROPHONE_OUTBOUND`). It is one of the small HTTP microservices of OBLIVION; **only Brain calls it** (Brain is the only coordinator, see `../CLAUDE.md`). It does not transcribe, decide or play anything.

In scope: opening and releasing the device, negotiating a format the hardware accepts, downmixing to mono PCM16, silence detection and cutting, the optional resampling of what is sent on, the HTTP control routes and the event stream.

Out of scope: speech to text (STT), any call to another service, authentication (not designed for the project yet, see `docs/security/security.md`), recording audio to disk.

## 2. High-level architecture

```
composition_root  ──▶  infrastructure  ──▶  application  ──▶  domain
 (chooses concretes)    inbound/outbound     ports + service    entities, value objects, operations
```

Source dependencies point inward only. At run time the calls go outward (HTTP, then the service, then the hardware) through ports owned by `application`:

```
HTTP handler ──▶ MicrophoneStreamingPort ◀── MicrophoneService ──▶ AudioCapturePort ◀── SoundDeviceAudioCapture ──▶ sounddevice
(inbound)        (driving port)               (application)         (driven port)         (outbound)
                                                   │
                                                   ▼
                       domain: Microphone, AudioFormat, InputTreatment, UtteranceSegmenter, pcm / level / resample / format_negotiation
```

Wire format: the stream is NDJSON, one `contracts.stream` event per line, encoded with `contracts.stream.codec`; the non-stream answers use `contracts.api.common.envelope.ApiEnvelope`. Nothing here hand-writes event JSON.

## 3. Module responsibilities

| Layer | Responsibility |
|---|---|
| `main.py`, `main_flow/` | Read the config, init logging (`init_logging("microphone")`), run uvicorn, and on shutdown release the device. No wiring and no rules. |
| `composition_root/` | The only place concrete adapters are chosen and connected (`new_audio_capture`, `new_microphone_service`, `new_http_app`, `HttpContainer`). |
| `infrastructure/config` | `ServerConfig` and `MicrophoneConfig`: environment variables into frozen dataclasses. |
| `infrastructure/inbound/http` | FastAPI handler, envelope answers, error to status mapping, the NDJSON event framing. Decode, call the port, encode. |
| `infrastructure/outbound/sounddevice_capture` | The hardware adapter behind `AudioCapturePort` / `AudioStreamPort`: driver, device selector, stream, error mapper. The only module that imports `sounddevice` is `sounddevice_driver.py`. |
| `application` | `MicrophoneService` (orchestration under a lock, no rules of its own), `utterances_of` (feeds the segmenter), ports, DTOs, application errors. |
| `domain` | The rules: `Microphone` state machine, `AudioFormat`, `InputTreatment`, `UtteranceSegmenter`, pure audio operations. Imports nothing outside the standard library. |

## 4. Package map

```
main.py                              entry point: asyncio.run(run_http())
main_flow/
  http.py                            config -> logging -> container -> uvicorn -> cleanup (stop_stream) in finally
composition_root/
  dependencies/microphone_dependencies.py   new_audio_capture, new_microphone_service, new_http_app (adds TracingMiddleware)
  containers/http_container.py              HttpContainer(app, microphone), new_http_container
application/
  errors.py                          ApplicationError, MicrophoneUnavailable, StreamCloseFailed, StreamReadFailed, FormatMismatch
  dtos/start_stream_inbound.py       StartStreamInboundDTO(sample_rate=16000, channels=1, chunk_size=1024)
  dtos/stream_outbound.py            StreamOutboundDTO(sample_rate, stream)
  ports/inbound/microphone_streaming_port.py   MicrophoneStreamingPort (driving)
  ports/outbound/audio_capture_port.py         AudioCapturePort (driven)
  ports/outbound/audio_stream_port.py          AudioStreamPort (driven)
  services/microphone_service.py     MicrophoneService
  services/utterance_stream.py       utterances_of(chunks, segmenter)
domain/
  errors.py                          DomainError, InvalidAudioFormat, CaptureAlreadyActive, CaptureNotActive, InvalidInputTreatment
  value_objects/audio_format.py      AudioFormat(sample_rate, channels, chunk_size), all > 0
  value_objects/input_treatment.py   InputTreatment: the cutting and the four treatments, validated
  entities/microphone.py             Microphone: idle / capturing state machine
  entities/utterance_segmenter.py    UtteranceSegmenter: chunks in, utterances out
  operations/pcm.py                  downmix_to_mono
  operations/level.py                samples_of, mean, rms
  operations/resample.py             LinearResampler (chunk by chunk, exact fractions)
  operations/format_negotiation.py   fallback_formats
infrastructure/
  config/                            server_config.py, microphone_config.py
  inbound/http/                      http_handler.py, http_envelope.py, http_error_mapper.py, ndjson_audio_events.py
  outbound/sounddevice_capture/      audio_driver.py (protocol), sounddevice_driver.py, sounddevice_device_selector.py,
                                     sounddevice_audio_capture.py, sounddevice_audio_stream.py, sounddevice_error_mapper.py
tests/                               domain, application, infrastructure, composition_root, architecture; simple.py (needs a real microphone)
```

## 5. Control flow

**Start (`POST /start`).** The handler builds a `StartStreamInboundDTO` and calls `MicrophoneService.start_stream` under the service lock: `Microphone.ensure_idle()` (409 if already capturing), `AudioCapturePort.open_stream(requested)` (tries `fallback_formats`, 503 if nothing opens), `Microphone.start(negotiated format)`, then an `UtteranceSegmenter` is built for the device rate and the stream is wrapped by `utterances_of`. The answer carries the rate of what will be **sent**, which is `MICROPHONE_RESAMPLE_TO_HZ` when it is set. The service registers `on_terminated` on the raw stream.

**Stream (`GET /stream`).** `current_stream()` (409 if not capturing); a `sample_rate` query that differs from the capture's is a `FormatMismatch` (422). The handler returns a `StreamingResponse` over `ndjson_audio_events`: `stream_started`, one `utterance` per finished utterance, then `completed` (`output_bytes_base64` always empty), or an `error` event (`capture_failed`, not recoverable) if reading fails.

**Stop (`POST /stop`).** Under the lock, close the stream and set the microphone idle. Idempotent when idle. A `StreamCloseFailed` propagates (500) and the capture stays active.

**Stream dies on its own.** A read failure or the consumer disconnecting makes `SoundDeviceAudioStream` release the device and fire `on_terminated`; the service then clears its state and goes idle, so `/start` works again without `/stop`.

**Shutdown.** uvicorn returns on SIGINT / SIGTERM; `main_flow/http.py` calls `stop_stream()` in `finally`, logging (not raising) a failure.

## 6. Public APIs (ports)

| Port | Direction | Methods |
|---|---|---|
| `MicrophoneStreamingPort` | driving (HTTP uses it) | `start_stream(StartStreamInboundDTO) -> StreamOutboundDTO`, `stop_stream()`, `is_available()`, `current_stream()`, `check_device() -> (ok, reason)` |
| `AudioCapturePort` | driven | `open_stream(AudioFormat) -> AudioStreamPort`, `check_device() -> (ok, reason)` |
| `AudioStreamPort` | driven | `sample_rate`, `__aiter__` (mono PCM16 chunks), `on_terminated(callback)`, `close()` (idempotent) |
| `AudioDriver` (adapter-internal protocol) | seam faked in tests | `input_devices`, `default_input_index`, `device_info`, `open_input` |

The HTTP routes are documented in `docs/api/api.md`.

## 7. Data structures

- `AudioFormat` (frozen): `sample_rate`, `channels`, `chunk_size`, all above 0 or `InvalidAudioFormat`.
- `InputTreatment` (frozen): `silence_threshold` 150, `silence_limit_seconds` 2.0, `speech_start_factor` 2.0, `dc_offset_removal` false, `volume_smoothing` true, `volume_smoothing_factor` 0.1, `noise_floor_tracking` true, `resample_to_hz` 0, `preroll_seconds` 0.2; out of range values raise `InvalidInputTreatment`.
- `StreamOutboundDTO(sample_rate, stream)`: the live utterance stream and the rate of its audio.
- Events (`contracts.stream.microservices.microphone.outbound`): `MicrophoneStreamStartedEvent`, `MicrophoneUtteranceEvent`, `MicrophoneCompletedOutboundEvent`, plus the common `ErrorEvent`. Control payloads: `contracts.api.microservices.microphone` (`start`, `stop`) and `common` (`availability`, `health_check`).

## 8. Utterance cutting

`UtteranceSegmenter.feed(chunk)` measures the volume of each chunk and keeps a small state machine (not speaking, speaking):

1. **Volume**: RMS of the 16-bit samples. With `dc_offset_removal` the slowly moving offset (95 % old value, 5 % of each chunk mean) is subtracted first. With `volume_smoothing` the volume is an exponential average (`volume_smoothing_factor` is the weight of the newest chunk), so one click is not speech. With `noise_floor_tracking` the quietest non-zero raw volume heard is remembered.
2. **Thresholds**: speech starts at `silence_threshold x speech_start_factor`, silence is under `silence_threshold`. With the noise floor, they are raised to at least 3 x the floor (start) and 2 x the floor (end).
3. **Speaking**: starts when the volume reaches the start threshold, and the **pre-roll** is put in front first (the latest quiet chunks, kept in a small rolling buffer while idle: whole chunks, at least `preroll_seconds`; nothing is buffered while an utterance is in progress, so the buffer never leaks into the next utterance); every chunk of the utterance is kept (resampled when `resample_to_hz` differs from the device rate); consecutive samples under the end threshold are counted and when they reach `silence_limit_seconds` the utterance is handed back (it keeps the silence that ended it).
4. **End of stream**: `flush()` hands back the utterance in progress. If the device fails instead, the half utterance is lost.

## 9. Design patterns

- **Ports and adapters** (hexagonal): `MicrophoneStreamingPort` driving, `AudioCapturePort` / `AudioStreamPort` driven, a driver protocol as the test seam.
- **State machine** in the `Microphone` entity (idle or capturing; start only when idle; stop is idempotent).
- **Strategy by configuration**: the treatments are flags of an immutable `InputTreatment`, not subclasses.
- **Composition root**: one function per concrete choice; tests build the container with fake drivers.
- **Error translation at the edge**: domain and application errors are mapped to HTTP statuses only in `http_error_mapper.py`; the sounddevice errors are wrapped by `sounddevice_error_mapper.py`.
- **Blocking calls off the loop**: device discovery, open, read and close run through `asyncio.to_thread`.

## 10. Dependency rules

`tests/architecture/test_dependency_rules.py` parses the imports and enforces:

| Layer | May import | Must not import |
|---|---|---|
| `domain` | stdlib, `domain` | everything else |
| `application` | stdlib, `domain`, `application` | `infrastructure`, `composition_root`, fastapi / starlette / pydantic / uvicorn / sounddevice / numpy / httpx |
| `infrastructure/inbound` | application, domain, frameworks | `infrastructure.outbound`, `composition_root` |
| `infrastructure/outbound` | application, domain, frameworks | `infrastructure.inbound`, `composition_root` |
| `composition_root` | everything | none |
| `main_flow` | `composition_root`, `infrastructure.config` | `infrastructure.inbound`, `infrastructure.outbound` |

## 11. Execution sequence

```
Brain          handler            MicrophoneService      SoundDeviceAudioCapture        device
  │ POST /start    │                      │                        │                       │
  │───────────────▶│ start_stream(dto) ──▶│ lock, ensure_idle      │                       │
  │                │                      │ open_stream(format) ──▶│ fallback_formats ─────▶ open_input
  │                │                      │◀── AudioStreamPort ────│                       │
  │◀── envelope (sample_rate sent) ───────│ Microphone.start, build UtteranceSegmenter     │
  │ GET /stream    │                      │                        │                       │
  │───────────────▶│ current_stream() ───▶│                        │                       │
  │◀── stream_started                     │                        │                       │
  │◀── utterance ... (one per utterance: read chunk -> feed segmenter -> yield) ◀── read ──│
  │ POST /stop     │                      │                        │                       │
  │───────────────▶│ stop_stream() ──────▶│ close() ──────────────▶│ stop + close ─────────▶│
  │◀── envelope    │    (the open /stream ends with `completed`)    │                       │
```

## 12. Known issues and debt

1. **No simulation backend.** Without a device `/available` answers `is_available: false` and Brain's start-up preflight requires it, so a machine with no microphone cannot run the pipeline. The deployment readiness check (`ready = "/available"`) also fails there. Proposal: `docs/proposals/PR-001-simulated-capture-backend.md` (epic T-02 in `docs/tasks/ORDER.md`).
2. **`channels > 1` is mixed to mono silently**; the `/start` answer always says `channels = 1` and does not say the request was downmixed.
3. **No authentication.** Service-to-service authentication is not designed for the project.
4. **The sounddevice adapter is unvalidated on real hardware** since the last changes (it is tested against a fake `AudioDriver`; `tests/simple.py` needs a real microphone). The silence thresholds are not tuned on real rooms either.
5. **No `.env` loading.** `main_flow/http.py` does not load `.env` (no `python-dotenv`); the deployment tool reads the file and starts the process (catalogue key `dotenv = false`), and a hand start must export the variables.
6. **Dev tools in the runtime requirements** (`ruff`, `black`, `mypy`, `pytest`, `httpx`), and nothing is version-pinned.
7. **A mid-stream device failure loses the utterance in progress.**
8. **`MICROPHONE_SHOW_METER` defaults to `true`**: the console meter writes to stdout on every chunk, which is noise in a service log; set it to `false` outside a manual test.
9. **`chunk_size` on `/stream`** is accepted and ignored (the capture's value is fixed by `/start`).

## 13. Recommendations

**Planned (from the deployment audit of 2026-11-04, not built; the order is in `docs/tasks/ORDER.md`: T-02 sim backend, T-03 start-up configuration, T-04 hardware verification):**

- A `sim` backend behind `AudioCapturePort` (`PR-001`), code default `real`.
- `python-dotenv` loading in `main_flow/http.py`, then `dotenv = true` in the deployment catalogue (and the matching test of `deployment`).
- Split the requirements: runtime and development files, with lower bounds (`>=`).

**Cleanup:** the stale `.engram/` folder and `docs/old/` can be removed once nothing is wanted from them.
