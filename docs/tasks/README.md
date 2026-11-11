# Tasks

Hierarchical task plan of `microphone_microservice`, in the format of `dynamics_microservice` and of the stt and tts deployment plans: **T-01 capture and utterances (done, history), T-02 the simulated capture backend, T-03 start-up configuration, T-04 hardware verification, T-05 documentation sync, T-06 deployment tool changes (the `deployment` repository), T-07 Docker and arm64 acceptance**. Every leaf task states what to create or change, what it must not do, and how to prove it is done, so it can be executed step by step without conflicts between tasks.

**The order in which the tasks must be done, with the state and the date of each, is in [ORDER.md](ORDER.md)** (kept in step with the board of section 5 and with every task file).

**Plan revision 1 (2026-11-05):** the plan was written after the deployment audit of 2026-11-04 (`docs/deployment_audit/microphone.md`), together with the documentation pass of the same day. T-01 records what was already built (the refactor of 2026-09-20, the contract stream, the utterance cutting of 2026-10-05); T-02 and T-03 come from PR-001 and PR-002; T-04 collects what only a real microphone can answer. Nothing of T-02 to T-04 is built.

**Plan revision 2 (2026-11-09):** reconciled with the stt and tts deployment plans. The audit was checked against the code and the tests were run (section 4). Changes: the pre-roll (`MICROPHONE_PREROLL_SECONDS`, built 2026-11-09, commit `fde20ad`) is recorded as history in T-01; the facts and test counts are refreshed (142 tests, `contracts` 0.16.0 bundled); **new epics T-06** (the `deployment` repository: catalogue entry, dotenv, the sim preset, the readiness check on a machine without a device, the manual) and **T-07** (Docker and arm64 acceptance, on `sim` only on this PC); the **Linux and Raspberry Pi tasks T-04.3 and T-04.4 are `postponed`** (decision of the maintainer of 2026-11-09: the Pi waits until the services work at 100 % on Windows); T-04.2 now names the finding of 2026-11-09 (phrases about 5 s apart merge with the default smoothing); the sim task T-02.3 now also names the lazy import of `sounddevice` (F5). One new questionnaire, [Q02](../questionnaires/Q02_deployment-readiness.md), re-asks Q01-1 to Q01-4 with what was found and adds the decisions of the deployment work. **No code task is done by this revision; the decisions T-02.1 and T-03.3 are still `awaiting-user`.**

## 1. Structure and naming

- Every task is a Markdown file. A task with subtasks lives in a folder of the same name, and its own file has the same name inside that folder. Leaves are single files.
- IDs are hierarchical and stable: `T-02` -> `T-02.3`. Never reuse or renumber an ID.
- A parent task describes goal, order and exit criteria; **leaves carry the implementation detail**.

```
docs/tasks/
├── README.md                          (this file)
├── ORDER.md                           the order, the state, the dates
├── T-01_capture-and-utterances/       done, history
├── T-02_simulated-backend/            PR-001
├── T-03_startup-configuration/        PR-002
├── T-04_hardware-verification/        needs the maintainer and a microphone
├── T-05_documentation-sync.md         recurring
├── T-06_deployment-tool-changes/      the `deployment` repository
└── T-07_docker-and-arm64-acceptance/  Docker on amd64 with `sim`; arm64 postponed
```

Kinds: `code`, `test`, `decision`, `docs`, `manual` (needs a real microphone, a Docker build, a download or a person: the assistant prepares the commands and says what to look at, and runs it after the maintainer says "go" for that task).

## 2. Execution protocol

1. Pick the first task whose status is `todo` and whose `Depends on` tasks are all `done`. A decision task that is `awaiting-user` **stops the chain**: ask the maintainer (the questions are in [../questionnaires/Q02_deployment-readiness.md](../questionnaires/Q02_deployment-readiness.md) and, for Q01-5 to Q01-10, [../questionnaires/Q01_open-questions.md](../questionnaires/Q01_open-questions.md)), record the answer in the task's *Resolution* and in the questionnaire, then continue.
2. Read `../CLAUDE.md` (workspace) and the service `CLAUDE.md` first; for T-06 also `deployment/CLAUDE.md`. Follow them literally: layout, wire format, logging, audio rules.
3. Create or modify only the files listed under *Files* (tests included). Another file, folder or dependency means updating the task first.
4. Implement, then run the task's *Verification* and the baseline of section 3. A task is `done` only when every acceptance criterion passes. **Code tasks:** when a defect is fixed, write the test first and show it fails on the old code; after the change, run one-line mutations of the new code with a script that restores the file in a `finally` (aim for all caught; a missed mutation means a missing test or dead code).
5. Set the task's `Status` to `done`, its row in section 5 and in `ORDER.md`, update the parent if its exit criteria are met, and record any new fact or deviation in the task's *Notes* and a *Result* with what was really run and numbers. Update the documents the change touches (the table in `CLAUDE.md`).
6. A task that needs hardware (T-04, and the hardware part of any other) is **not** done by running unit tests: say so and ask the maintainer. **Standing permission (proposed in Q02-9, not yet answered):** the maintainer says "go" for each manual task; the assistant says first what it will do and cost, warns before the microphone opens, and the maintainer is at the PC for the audio ones.
7. Do not commit, push or publish unless the maintainer asks. Do not touch `.env*` files (the folder has `.env.staging` and `.env.production`: never open them), `old/`, the venvs or the generated `contracts` folders. Never `git stash`, `reset` or `checkout` to compare with a baseline: use `git diff`, `git show HEAD:<file>` or a scratch copy.

Status values: `todo`, `awaiting-user` (a decision needs an answer), `blocked` (depends on unfinished or undecided work), `in-progress`, `done`, `postponed` (decided not to run yet; it does not block the Windows work).

## 3. Baseline definition of done (every code task)

From the service folder, with its own venv:

```powershell
& windows\Scripts\python.exe -m pytest        # all green, no hardware needed
& windows\Scripts\ruff.exe check .            # All checks passed!
& windows\Scripts\python.exe -m mypy .        # no issues found
```

- `tests/architecture/test_dependency_rules.py` stays green: dependencies point inward only; `application` imports no framework or `sounddevice`; only `sounddevice_driver.py` imports `sounddevice`.
- Logging only through `shared_logging`; never log audio; never import stdlib `logging`.
- Audio stays PCM16 mono; the only conversions are the downmix and the optional resample.
- Config only through environment variables, documented in `.env.example`, the README table and `docs/configuration/environment-variables.md`; the bind host stays configurable; no hardcoded port. After any `.env.example` change run `brain_microservice\windows\Scripts\python.exe deployment\scripts\env_inventory.py --write` from the workspace root and `--check` from `deployment/` (read the `git status` of `deployment` first).
- Wire types come from `contracts`; a new event goes to `contracts` first, then here, and the wheel is re-bundled with `contracts/scripts/bundle.py`. **No `contracts` change is planned** (Q02-2 recommends the `reason` of `/available`).
- No secrets, tokens or real recordings in code, tests, fixtures or documents.
- The documents named in the table of `CLAUDE.md` are updated in the same change, and the counts (tests, mypy files) are refreshed only after running them.
- The workspace pipeline check still passes when the change can affect it: `brain_microservice\windows\Scripts\python.exe -m pytest contracts\tests -q` from the workspace root (it starts real service processes with fake hardware).
- Search only inside the service and exclude `windows/` and the cache folders. Never grep the whole workspace.

### 3.1 Layout of the code (what every task must follow)

```
main.py, main_flow/            entry point and start-up/shutdown (no wiring, no rules)
composition_root/              the only place concrete adapters are chosen (dependencies/, containers/)
application/                   ports/{inbound,service,outbound}, services, dtos/{inbound,outbound}, errors
domain/                        entities, value objects, operations (pure, standard library only)
infrastructure/                config/, inbound/http/{routes,response,errors}, outbound/<adapter>/
tests/                         domain, application, infrastructure, composition_root, architecture (mirror of the code); simple.py (real microphone)
```

A new outbound adapter lives in `infrastructure/outbound/<name>/` and implements `AudioCapturePort` and `AudioStreamPort`; the choice between adapters is made only in `composition_root/dependencies/audio_capture_dependency.py` (it was `microphone_dependencies.py` until 2026-11-11).

## 4. Facts the tasks rely on

Verified on 2026-11-09 by reading the code (`[C]`) or by running something (`[D]`); `[U]` is not verified. Nothing was deployed, built or downloaded; no sound was recorded.

| # | Fact |
|---|---|
| F1 | The repository is on `feature_ai_claude_2`, HEAD `fde20ad` "Microphone: put a pre-roll in front of each utterance (MICROPHONE_PREROLL_SECONDS)"; the working tree was clean when the plan was written. `pytest`: **142 passed** in 2.2 s, `ruff check .`: All checks passed, `mypy .`: no issues in 53 source files (`[D]`). The earlier figures of this plan (127 tests) are from 2026-11-05. After the work of 2026-11-10: **171 passed**, ruff clean, mypy clean on 56 files. |
| F2 | `vendor/` holds `contracts_microservice-0.16.0-py3-none-any.whl` and both requirements files name it, but `CLAUDE.md`, the README and several documents still say 0.15.0 and the **service venv has `contracts-microservice 0.15.0` installed** (`pip list`): the venv was not refreshed. `[C]`, `[D]` |
| F3 | `requirements.windows.txt` and `requirements.linux.txt` are identical and unpinned: fastapi, uvicorn, sounddevice, numpy, **pytest, httpx, ruff, black, mypy** (dev tools in the runtime file), `-e ../shared-logging` and the vendored wheel. **No `python-dotenv`**: `main_flow/http.py` loads no `.env` (and `python-dotenv` is not installed in the venv). `[C]`, `[D]` |
| F4 | `[services.microphone]` in `deployment/config/catalogue.toml`: port 8000, `ready = "/available"`, `audio = true`, `libraries = ["shared-logging"]`, requirements windows/linux, `apt = ["libportaudio2", "portaudio19-dev"]`, **`dotenv = false`**, no `[env]` preset, no `prepare`. `[C]` |
| F5 | `sounddevice` is imported at module level in `infrastructure/outbound/sounddevice_capture/sounddevice_driver.py` (the only importer), and `composition_root/dependencies/microphone_dependencies.py` imports that module at the top, so importing the composition root needs PortAudio. On Windows the `sounddevice` wheel carries PortAudio; on Linux without `libportaudio2` the import fails. A `sim` backend that is chosen after that import would still crash on such a machine (the same defect as speaker R-2). `[C]` |
| F6 | `GET /available` calls `check_device()`: with no device (or no input channels) it answers `is_available: false` and a `reason`; with a device `is_available: true` and no reason. The deployment tool waits for `/available` and gives a service that answers but is unavailable only `UNAVAILABLE_GRACE_SECONDS` = 15 s, so a machine without a microphone reports `deploy` as failed and `update` rolls back although the code is fine. `[C]` (audit, `http_health.py`) |
| F7 | `deployment/domain/rules/host_validation.py:18` rejects `runtime = "docker"` for an `audio` service on a Windows host; `docker_runtime.py:69` adds `--device /dev/snd` for an `audio` service on a Linux host. Both look at the catalogue flag, not at the backend. `[C]` |
| F8 | Three tests of `deployment/tests/test_env_file_only.py` depend on `dotenv = false` for the microphone: the native-runner test (line about 126, asserts `dotenv is False`), the Docker test that names the microphone as the service that "cannot read a file" (it expects `--env-file`, not a bind mount) and `test_the_dotenv_flag_of_every_service_matches_what_its_source_does`, which fails as soon as any file of the service calls `load_dotenv` while the flag is false. So the service change and the catalogue change must land together. `[C]` |
| F9 | Pre-roll (built 2026-11-09, ADR-003 updates): `MICROPHONE_PREROLL_SECONDS`, default 0.2 s, `domain/entities/utterance_segmenter.py`; 12 tests, 10 of 10 mutations caught; live round trip through Brain 2026-11-09: 4 of 4 phrases that reached the wake gate were accepted. Not in the plan of 2026-11-05. `[C]`, from ADR-003 |
| F10 | Finding of 2026-11-09 (ADR-003, second update): with the default smoothed volume, phrases about 5 s apart merge into one utterance (the smoothed volume needs about 1.8 s to fall under the end threshold, plus the 2 s silence limit; one cut was 46 s long); with smoothing off each phrase was its own utterance. stt's wake-phrase gate only works when the utterance starts early enough (stt ADR-005). Belongs to T-04.2. |
| F11 | Seed for the simulated signal: `SineStream` in `contracts/tests/e2e/fake_services.py` (5 chunks of amplitude 20, 80 chunks of a 300 Hz tone at 8000, then 0), a test double that sleeps 10 ms per chunk. It must be re-written here, not imported (services never import each other's tests). `[C]` |
| F12 | Docker Desktop 29.5.2 is running on this PC (`desktop-linux`, linux/amd64); the saved context is not the PC's, so every command needs `--context desktop-linux`. Docker on a Windows host cannot reach the sound card, so on this PC a container of the microphone can only run on `sim`. `[D]` |
| F13 | Brain's echo guard (`brain_microservice/domain/entities/echo_guard.py`) works on the audio Brain sends to the speaker and the times the microphone utterances were captured; it does not need the microphone to be real, only realistic in time. `[C]` |
| F14 | The speaker plan (`speaker_microservice/docs/tasks/`) edits the same two files of `deployment` (`config/catalogue.toml`, `docs/DEPLOYMENT.md`): do the microphone first, then the speaker, in one session, and read `git status` and `git diff` of each file before editing. `[C]` |

## 5. Board

| Task | Name | Kind | Status |
|---|---|---|---|
| [T-01](T-01_capture-and-utterances/T-01_capture-and-utterances.md) | Capture and utterances (history) | epic | done (hardware pending, T-04) |
| [T-02](T-02_simulated-backend/T-02_simulated-backend.md) | Simulated capture backend | epic | done |
| [T-02.1](T-02_simulated-backend/T-02.1_decisions.md) | Decisions: default, variable, signal (Q02-1 to Q02-3) | decision | done |
| [T-02.2](T-02_simulated-backend/T-02.2_sim-capture-adapter.md) | The simulated capture adapter | code | done |
| [T-02.3](T-02_simulated-backend/T-02.3_wiring-and-config.md) | Wiring and configuration (lazy import of `sounddevice`) | code | done |
| [T-02.4](T-02_simulated-backend/T-02.4_tests.md) | Tests of the backend | code | done |
| [T-02.5](T-02_simulated-backend/T-02.5_deployment-and-pipeline.md) | Pipeline check with the real service on `sim` (the `deployment` part moved to T-06.2) | code | done |
| [T-03](T-03_startup-configuration/T-03_startup-configuration.md) | Start-up configuration | epic | done |
| [T-03.1](T-03_startup-configuration/T-03.1_load-dotenv.md) | Load `.env` at start (the `deployment` part moved to T-06.1) | code | done |
| [T-03.2](T-03_startup-configuration/T-03.2_requirements-split.md) | Split the requirements, pin what ran | code | done |
| [T-03.3](T-03_startup-configuration/T-03.3_deployment-side.md) | The matching change in `deployment` (Q02-4) | decision | done |
| [T-04](T-04_hardware-verification/T-04_hardware-verification.md) | Hardware verification | epic | done |
| [T-04.1](T-04_hardware-verification/T-04.1_end-to-end-run.md) | Run `tests/simple.py` on a real microphone | manual | done |
| [T-04.2](T-04_hardware-verification/T-04.2_tune-the-defaults.md) | Tune the treatment defaults (smoothing merge, silence limit) | decision + code | done |
| [T-04.3](T-04_hardware-verification/T-04.3_linux-and-raspberry-pi.md) | Linux and Raspberry Pi | manual | postponed |
| [T-04.4](T-04_hardware-verification/T-04.4_docker-dev-snd.md) | Docker with `/dev/snd` | manual | postponed |
| [T-05](T-05_documentation-sync.md) | Documentation sync | docs | recurring (first pass 2026-11-05) |
| [T-06](T-06_deployment-tool-changes/T-06_deployment-tool-changes.md) | **Deployment tool changes** (the `deployment` repository) | epic | done |
| [T-06.1](T-06_deployment-tool-changes/T-06.1_dotenv-in-the-catalogue.md) | `dotenv = true` and the tests that name the microphone | code | done |
| [T-06.2](T-06_deployment-tool-changes/T-06.2_sim-preset.md) | The `sim` preset in the catalogue | code | done |
| [T-06.3](T-06_deployment-tool-changes/T-06.3_readiness-without-a-device.md) | Readiness on a machine without a device | code | done |
| [T-06.4](T-06_deployment-tool-changes/T-06.4_docker-on-windows-with-sim.md) | Docker on Windows for a microphone on `sim` (Q02-6) | code | done |
| [T-06.5](T-06_deployment-tool-changes/T-06.5_inventory-and-manual.md) | Inventory and manual | docs | done |
| [T-07](T-07_docker-and-arm64-acceptance/T-07_docker-and-arm64-acceptance.md) | **Docker and arm64 acceptance** | epic | done |
| [T-07.1](T-07_docker-and-arm64-acceptance/T-07.1_amd64-build.md) | Build the image on amd64 | manual | done |
| [T-07.2](T-07_docker-and-arm64-acceptance/T-07.2_run-and-call.md) | Run the container on `sim` and call every endpoint | manual | done |
| [T-07.3](T-07_docker-and-arm64-acceptance/T-07.3_restart-recreate-stop.md) | Restart, recreate and `docker stop` | manual | done |
| [T-07.4](T-07_docker-and-arm64-acceptance/T-07.4_image-contents-and-secrets.md) | Image contents and secrets | manual | done |
| [T-07.5](T-07_docker-and-arm64-acceptance/T-07.5_docker-on-arm64.md) | Docker on arm64 | manual | postponed |
| [T-07.6](T-07_docker-and-arm64-acceptance/T-07.6_record-the-results.md) | Record what was verified | docs | done |
