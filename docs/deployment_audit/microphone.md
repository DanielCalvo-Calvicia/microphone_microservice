# microphone_microservice (port 8000)

> Verified against the code and the `deployment` tool on 2026-11-04. Items marked **[corrected]** were wrong in the first draft.

## Role
Captures audio (`sounddevice`/PortAudio), cuts utterances by silence, streams NDJSON `utterance` events. Only Brain calls it. Endpoints: `/start`, `/stream`, `/stop`, `/available`, `/health`. [C: `CLAUDE.md`]

## Dependencies
fastapi, uvicorn, sounddevice, numpy; **ruff, black, mypy, pytest in runtime requirements** (stt, tts and speaker do the same); unpinned (no bounds at all). **No python-dotenv**: `main_flow/http.py` never loads `.env`. The catalogue marks `dotenv = false`, so the deploy tool starts it through `service_runner.py` (native) and passes `--env-file` (Docker, `docker_runtime.py:47-51`). System: PortAudio (`libportaudio2`, `portaudio19-dev`). [C]

## Hardware
Audio input device.

## Portability
Windows and Linux. `.env.production` and `.env.staging` exist beside `.env` (not tracked; not opened).

## Local
Works on Windows; needs a hardware retest [D]. Linux/Pi unverified [U].

## Docker
- **Linux host**: `--device /dev/snd`, added by the tool because the catalogue has `audio = true` and the host is Linux (`docker_runtime.py:52-53`). **[corrected]** It does not come from a hardware config (none exists), and no `audio` group is needed in the container: the image has no `USER`, so it runs as root. The `audio` group matters only for native runs (`DEPLOYMENT.md`, `usermod -aG audio`). The image has no ALSA configuration, and the "OS default input" choice may find no device inside a container. Unproven [U]; needs a hardware test.
- **Windows host**: Docker cannot reach the Windows sound card. **[corrected]** There is no `mode = "local"` / `reason` setting. The real setting is `runtime = "native"` (the default) in `config/local/microphone.toml`, and `host_validation.py:18` already rejects `runtime = "docker"` for an audio service on a Windows host. A PulseAudio bridge is the alternative, not planned.

## Configuration
`SERVICE_HOST/PORT`, `MICROPHONE_TARGET_KEYWORDS`, `MICROPHONE_SILENCE_*`, `MICROPHONE_RESAMPLE_TO_HZ`, etc. **[corrected]** Device choice is machine-specific, and it is already per machine: each service runs on exactly one machine, so `MICROPHONE_TARGET_KEYWORDS` goes in that machine's `config/local/microphone.toml`. There is no separate "hardware config" (`config/machines/<m>.toml` holds only Python, workdir, OS and bind).

## Problems
1. **No simulation backend** in production code (the only match for mock/fake/simulat in `infrastructure/ application/ domain/` is a docstring in `audio_driver.py`). `/available` is `is_available: false` without a device and Brain's startup preflight requires it, so a machine without a microphone cannot run the pipeline. [C]
2. **The deploy readiness check fails without a device (missed in the first draft).** The catalogue entry has `ready = "/available"`; `http_health.py` gives a service that answers but reports itself unavailable only 15 s (`UNAVAILABLE_GRACE_SECONDS`). On a machine with no microphone, `deploy`/`update` report it as failed ("available: ..."). `update` then rolls back to the previous commit when it had pulled a new one (`deployment_service.py:246-251`), or just restarts the old process when the code did not change, although the code is fine either way. A sim backend fixes this too.
3. Dev tools at runtime; unpinned versions.
4. `dotenv = false` quirk complicates the Docker env path (works today, low priority).

## Recommended changes
1. Add a `sim` input backend behind the existing port (`AudioCapturePort` / `AudioStreamPort`), chosen by an env var (for example `MICROPHONE_BACKEND=real|sim`), switched in `composition_root/dependencies/microphone_dependencies.py:new_audio_capture`.
   - **[corrected]** The **code default stays `real`**. A silent fake default would make a robot with a broken microphone look healthy. Where a deployed machine should start on `sim`, use a preset in the catalogue's `[services.microphone.env]`, as stepper does with `MOCK_HARDWARE = "1"`, and set `real` in `config/local/microphone.toml` on the machine with the sound card.
   - `/available` must report `sim` in its `reason` and the service must log it at start.
   - Seed: `SineStream` in `contracts/tests/e2e/fake_services.py` already fakes a capture behind the same ports (room noise, a tone, silence). A looped WAV is the alternative.
2. Add `python-dotenv>=1.0.1` and load `.env` like stt and stepper (`_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"` and `load_dotenv(dotenv_path=_ENV_FILE)` in `main_flow/http.py`; in the container that resolves to `/app/.env`, where the tool bind-mounts the file), then set `dotenv = true` in the catalogue. **[corrected]** `deployment/tests/test_env_file_only.py:130` asserts `dotenv is False` for the microphone, so that test and `DEPLOYMENT.md` (lines 292 and 315) change in the same step.
3. Split dev requirements (add `requirements-dev.*`, keep the catalogue's `requirements` pointing at the runtime file; update the venv instructions in `CLAUDE.md`). **[corrected]** Pin with lower bounds (`>=`), the repo convention (`DEPLOYMENT.md` §3), not ranges.
4. ~~Move device keywords into the machine's hardware config.~~ **[corrected]** Nothing to do: `config/local/microphone.toml` is already per machine.

## Tests
- Existing tests: **127 passed** (2026-11-04), ruff clean, mypy clean (53 files). **[corrected]** The first draft said 88.
- Add sim-backend tests and an e2e where the pipeline runs with it.
- Hardware: real microphone on Windows (native) and on Linux/Pi (Docker with `/dev/snd`), measuring utterance cutting.
- Same API/contract tests against `sim` and `real`.
- `deployment`: a test that a layout with `MICROPHONE_BACKEND=sim` passes the readiness check without a device.
