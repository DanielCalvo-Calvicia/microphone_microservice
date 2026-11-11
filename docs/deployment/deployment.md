# Deployment

How this service is run. The full manual (venvs, every variable, start order, health checks) is `deployment/docs/DEPLOYMENT.md` in the workspace; this file records what is specific to the microphone. Status: **works natively on Windows; Docker and Linux / Raspberry Pi are not verified on real hardware.**

## What the deployment tool knows about it

Entry `[services.microphone]` of `deployment/config/catalogue.toml` (not edited from here):

| Key | Value | Meaning |
|---|---|---|
| `git`, `branch` | this repository, `feature_ai_claude_2` | What `deploy` and `update` clone and pull |
| `port` | `8000` | Matches `SERVICE_PORT` |
| `ready` | `/available` | Readiness is the device probe, not `/health`: a machine with no microphone is reported as failed after a 15 s grace period |
| `audio` | `true` | Needs a sound device; the tool refuses `runtime = "docker"` on a Windows host, **unless** the service runs on its simulated backend (next row) |
| `simulated_when` | `{ MICROPHONE_BACKEND = "sim" }` | With that resolved setting the service uses no sound device: it may run in Docker on Windows and gets no `--device /dev/snd`. Judged on the resolved value (catalogue preset or local file), never on the name |
| `[env]` | `MICROPHONE_BACKEND = "sim"` | A **default deploy runs the simulated microphone** (ADR-007): a machine without a sound card passes the readiness check and `/available` says `simulated microphone` in its `reason` (the tool prints `healthy and available, warning: ...`). **The machine with the microphone must set `MICROPHONE_BACKEND = "real"` in `config/local/microphone.toml`**, or the robot is healthy and deaf |
| `libraries` | `shared-logging` | Installed in editable mode next to the service |
| `requirements` | `requirements.windows.txt` / `requirements.linux.txt` | Per platform; runtime only, exact versions. The tests and lint tools are in `requirements.dev.txt`, which the tool never installs |
| `apt` | `libportaudio2`, `portaudio19-dev` | System packages on Linux |
| `dotenv` | `true` (the default; no key in the catalogue) | The service loads the `.env` in its own folder itself (since 2026-11-10); the tool writes it, and in Docker bind-mounts it read-only at `/app/.env` |

Settings you change live in `deployment/config/local/microphone.toml` (for example `MICROPHONE_TARGET_KEYWORDS` of that machine, and `SERVICE_HOST` when Brain is elsewhere), never in the catalogue.

## Windows (native)

```powershell
cd microphone_microservice
& windows\Scripts\python.exe main.py
```

Allow the microphone for desktop apps (Settings, Privacy & security, Microphone) and open the port in the firewall only if Brain runs on another machine (`SERVICE_HOST=0.0.0.0`). Check: `curl http://<host>:8000/available`.

## Linux / Raspberry Pi

`requirements.linux.txt` and the system packages `libportaudio2 portaudio19-dev`. The user must be in the `audio` group (`sudo usermod -aG audio $USER`, log in again) for a native run. The venv keeps its name, so the interpreter is `windows/bin/python`. **Not run on real Linux hardware yet.**

## Docker

- **Linux host:** the tool adds `--device /dev/snd` because the catalogue has `audio = true`. The image has no ALSA configuration, so "the OS default input" may find no device inside a container: unproven, needs a hardware test.
- **Windows host:** Docker cannot reach the Windows sound card; use `runtime = "native"` (the default) for a real microphone. The tool still refuses `runtime = "docker"` there for `real` (decision Q02-5, 2026-11-09: no per-machine `mode = "local"` override), but accepts it for a microphone on `sim` (Q02-6; built in `deployment`, `simulated_when`). A PulseAudio bridge is an alternative, not planned. Docker with `sim` on this PC was run on 2026-11-10 (below).

There is no `Dockerfile` in this repository; the container is built by the deployment tool.

## Start order and dependencies

The microphone depends on no other service. Start it in any order before Brain, which waits (`STARTUP_PREFLIGHT_TIMEOUT_SECONDS`) for `/available` of the microphone, STT, TTS and speaker before opening the pipeline.

## Checks after a deployment

```bash
curl http://<host>:8000/health      # healthy: true
curl http://<host>:8000/available   # is_available: true, reason: null (on sim: reason says "simulated microphone ...")
```

`/available` false with a `reason` means no usable input device: check the keywords, the OS default input and the permission.

## Things to keep in step

When this repository changes how it starts, its variables or its readiness, update in the same piece of work `deployment/config/catalogue.toml`, `deployment/docs/DEPLOYMENT.md` and the generated `deployment/config/services/microphone.toml` (see `docs/configuration/environment-variables.md`). `deployment/tests/test_env_file_only.py` asserts `dotenv = false` for the microphone and must change together with PR-002.

## Verified in Docker (2026-11-10, tasks T-07.1 to T-07.4; amd64, Docker Desktop 29.5.2, `sim` only, no audio device)

Built and run through `oblivion.py deploy` from a scratch deployment (a copy of the working tree, `runtime = "docker"`, nothing set for the backend so the catalogue preset applied). **Build:** the whole deploy took 41 s (base image cached), the image is 317 MB on Python 3.12.16, `docker build` carried `APT_PACKAGES=libportaudio2 portaudio19-dev` and no `PREPARE`, nothing was compiled (0 `Building wheel`), the pip layer is 93.4 MB (numpy) and the apt layer about 7 MB, so keeping PortAudio in a `sim` image costs little. The `docker run` line has the `.env` as a read-only bind mount at `/app/.env`, `-p 127.0.0.1:8000:8000`, and **no** `--device`. The tool printed `microphone: healthy and available, warning: simulated microphone (MICROPHONE_BACKEND=sim): a generated signal, not a real device`. **Endpoints:** `/health` 200; `/available` true with the note; `/start` 200 (16000 Hz, mono, pcm16, chunk 1024); a second `/start` 409; `/stream?sample_rate=8000` while capturing 16000 Hz 422; `stream_started` at once and one `utterance` of 153,600 samples (9.6 s) after 9.7 s; `/stop` 200 and a second `/stop` 200 (idempotent: it is not a 409); `/available` still true. **Lifecycle:** `docker restart` healthy in 0.9 s; a recreate through the tool (`deploy` again) 31.6 s with a new container, healthy at once; `docker stop` with a capture running and no consumer 0.69 s, exit code 0, log `Shutting down`, `Server stopped; releasing microphone`, `Cleanup finished`; `docker start` healthy in 0.9 s and `/start` 200 (not 409). **Finding (not fixed):** with a `/stream` consumer connected, as Brain is, `docker stop` waits for the whole 10 s grace period and is then killed (exit code 137, 10.46 s): uvicorn's graceful shutdown waits for the open request, so the lifespan cleanup (`Server stopped; releasing microphone`) never runs; without a consumer it stops in 0.69 s with exit code 0. A real device is released by the operating system when the process dies, but the clean path is not taken. **Image:** no pytest, httpx, ruff, black or mypy (`pip list`); `python-dotenv`, numpy and sounddevice are there; no `.env*` file in the image (`ls /app`, and 0 entries in the 9,953 layer entries of `docker save`); 0 matches for key, secret, token or password patterns in `docker history`, `docker inspect` of the image and of the container; the container's environment holds only the Python base image's variables; the process runs as root (the image sets no `USER`); the image also contains `tests/`, `docs/`, `vendor/` and `.engram/` because the Dockerfile copies the whole service tree (1.2 MB). **Not verified:** `/dev/snd` and a real microphone in a container (Linux/Pi, postponed), arm64, and Brain in front of the container.

**Fix of the `docker stop` finding (2026-11-10).** **Fixed 2026-11-10:** `main_flow/http.py` passes `timeout_graceful_shutdown=GRACEFUL_SHUTDOWN_SECONDS` (5 s) to uvicorn, which now cancels the open requests after 5 s and runs the lifespan cleanup. Test first (`tests/main_flow/test_shutdown.py`, failing on the old code), 4 of 4 one-line mutations caught. Re-run in Docker with Docker's default 10 s grace period: with a `/stream` consumer connected `docker stop` took **5.69 s** and ended with exit code **0**; the log shows the stream terminated, `Application shutdown complete`, `Server stopped; releasing microphone` and `Cleanup finished`; the client's stream ended cleanly. uvicorn logs the cancelled request as an ERROR line (`Exception in ASGI application`, `CancelledError: Task cancelled, timeout graceful shutdown exceeded`): expected noise.
