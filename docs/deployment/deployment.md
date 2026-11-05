# Deployment

How this service is run. The full manual (venvs, every variable, start order, health checks) is `deployment/docs/DEPLOYMENT.md` in the workspace; this file records what is specific to the microphone. Status: **works natively on Windows; Docker and Linux / Raspberry Pi are not verified on real hardware.**

## What the deployment tool knows about it

Entry `[services.microphone]` of `deployment/config/catalogue.toml` (not edited from here):

| Key | Value | Meaning |
|---|---|---|
| `git`, `branch` | this repository, `feature_ai_claude_2` | What `deploy` and `update` clone and pull |
| `port` | `8000` | Matches `SERVICE_PORT` |
| `ready` | `/available` | Readiness is the device probe, not `/health`: a machine with no microphone is reported as failed after a 15 s grace period |
| `audio` | `true` | Needs a sound device; the tool refuses `runtime = "docker"` on a Windows host |
| `libraries` | `shared-logging` | Installed in editable mode next to the service |
| `requirements` | `requirements.windows.txt` / `requirements.linux.txt` | Per platform |
| `apt` | `libportaudio2`, `portaudio19-dev` | System packages on Linux |
| `dotenv` | `false` | The service does not load `.env`; the tool reads the file and starts the process with it (native) or passes `--env-file` (Docker) |

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
- **Windows host:** Docker cannot reach the Windows sound card; use `runtime = "native"` (the default). A PulseAudio bridge is an alternative, not planned.

There is no `Dockerfile` in this repository; the container is built by the deployment tool.

## Start order and dependencies

The microphone depends on no other service. Start it in any order before Brain, which waits (`STARTUP_PREFLIGHT_TIMEOUT_SECONDS`) for `/available` of the microphone, STT, TTS and speaker before opening the pipeline.

## Checks after a deployment

```bash
curl http://<host>:8000/health      # healthy: true
curl http://<host>:8000/available   # is_available: true, reason: null
```

`/available` false with a `reason` means no usable input device: check the keywords, the OS default input and the permission.

## Things to keep in step

When this repository changes how it starts, its variables or its readiness, update in the same piece of work `deployment/config/catalogue.toml`, `deployment/docs/DEPLOYMENT.md` and the generated `deployment/config/services/microphone.toml` (see `docs/configuration/environment-variables.md`). `deployment/tests/test_env_file_only.py` asserts `dotenv = false` for the microphone and must change together with PR-002.
