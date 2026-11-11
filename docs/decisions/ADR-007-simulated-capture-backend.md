# ADR-007 — A simulated capture backend, reported in the `reason` of `/available`

**Status:** Accepted (2026-11-09, the maintainer answered [Q02](../questionnaires/Q02_deployment-readiness.md) 1 to 3 "Recommended"; task T-02.1). Not built yet (T-02.2 to T-02.4); see the dated updates when it is.
**Related:** [PR-001](../proposals/PR-001-simulated-capture-backend.md), [tts ADR-008](../../../tts_microservice/docs/decisions/ADR-008-fallback-reported-in-available-reason.md), [deployment audit](../deployment_audit/microphone.md)

## Context

Without a sound card `GET /available` answers `is_available: false`, Brain's start-up preflight requires it, and the deployment tool reports the service as failed after the 15 s grace (`update` can roll back a healthy commit). A machine without a microphone (a server, a CI run, a Docker host on Windows) cannot run the pipeline. A silent fake default would make a robot with a broken microphone look healthy.

## Decision

1. `MICROPHONE_BACKEND=real|sim`. **The code default is `real`.** An unknown value stops the start and names the variable.
2. A machine without a microphone starts on `sim` through a **catalogue preset** (`[services.microphone.env] MICROPHONE_BACKEND = "sim"`, as stepper does with `MOCK_HARDWARE = "1"`); the machine with the sound card sets `real` in `deployment/config/local/microphone.toml`. Accepted consequence: a default deploy is `sim`, so the robot's machine must say `real`; the warning line of the tool (3) is the safety net.
3. The active backend is reported in the `reason` of `/available`: on `sim`, `is_available: true` and a short note that contains `sim`; on `real`, no `reason`. No `contracts` change. The service logs the backend once at start. Brain reads `reason` only when `is_available` is false, so Brain itself will not show it.
4. The simulated signal is **generated** (no file): room noise, a tone, then silence (the pattern of `SineStream` in `contracts/tests/e2e/fake_services.py`, re-written here, never imported), **paced to real time** (one chunk per `chunk_size / sample_rate` seconds), **once per `/start`** and then silence. It goes through the same `UtteranceSegmenter` as a real signal, pre-roll included.
5. The backend is chosen in the composition root **before** the `sounddevice` driver is imported, so a machine without PortAudio can run `sim`.

## Consequences

- Positive: a machine with no microphone passes the readiness check and can run the whole pipeline; the Docker acceptance on a Windows PC can run on `sim`.
- Negative: a default deploy to the robot is silent unless `real` is set; the preset has to be said in the manual.

> **Update 2026-11-10 (built):** `infrastructure/outbound/sim_capture/` (`SimAudioCapture`, `SimAudioStream`), `MicrophoneConfig.backend`, the lazy import in `new_audio_capture`; `/available` answers `is_available: true` and `reason` = `"simulated microphone (MICROPHONE_BACKEND=sim): a generated signal, not a real device"`; one warning at start, `Microphone backend is simulated` (nothing new for `real`). The pattern is 5 chunks of room noise (amplitude 20), 80 chunks of a 300 Hz tone (amplitude 8000), then silence; each chunk is paced to `chunk_size / sample_rate` seconds on a fixed schedule from the open (a slow consumer finds the due chunks and the signal does not drift). The catalogue preset is in `deployment` (`[services.microphone.env]`), with the key `simulated_when` that lets a simulated microphone run in Docker on Windows (the answer to Q02-6). Tests: 14 for the adapter, 2 for the config and 6 for the wiring (22 new, 169 in all); mutations: all of the new code caught except one that changes nothing (the default of `env.get` in front of `or "real"`).

> **Update 2026-11-10 (Docker):** the image builds and runs through `oblivion.py` on a Windows host on `sim` (the tool accepts it through `simulated_when`), the tool prints the note as a warning, every endpoint answers, and restart and recreate work. One finding that is not about `sim`: `docker stop` with a `/stream` consumer connected is killed after the 10 s grace period (uvicorn waits for the open stream); see `docs/deployment/deployment.md`.

> **Update 2026-11-10 (stop fixed):** the `docker stop` finding of the Docker run was fixed with `timeout_graceful_shutdown` (5 s) in `main_flow/http.py`; see `docs/deployment/deployment.md`.
