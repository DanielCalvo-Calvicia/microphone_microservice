# Tasks

Hierarchical task plan of `microphone_microservice`, in the format of `dynamics_microservice` (`docs/tasks/`): **T-01 capture and utterances (done, history), T-02 the simulated capture backend, T-03 start-up configuration, T-04 hardware verification, T-05 documentation sync**. Every leaf task states what to create or change, what it must not do, and how to prove it is done, so it can be executed step by step without conflicts between tasks.

**The order in which the tasks must be done, with the state and the date of each, is in [ORDER.md](ORDER.md)** (kept in step with the board of section 5 and with every task file).

**Plan revision 1 (2026-11-05):** the plan was written after the deployment audit of 2026-11-04 (`docs/deployment_audit/microphone.md`), together with the documentation pass of the same day. T-01 records what was already built (the refactor of 2026-09-20, the contract stream, the utterance cutting of 2026-10-05); T-02 and T-03 come from PR-001 and PR-002; T-04 collects what only a real microphone can answer. Nothing of T-02 to T-04 is built.

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
└── T-05_documentation-sync.md         recurring
```

## 2. Execution protocol

1. Pick the first task whose status is `todo` and whose `Depends on` tasks are all `done`. A decision task that is `awaiting-user` **stops the chain**: ask the maintainer (the questions are in [../setup/questionnaires/Q01_open-questions.md](../setup/questionnaires/Q01_open-questions.md)), record the answer in the task's *Resolution* and in the questionnaire, then continue.
2. Read `../CLAUDE.md` (workspace) and the service `CLAUDE.md` first. Follow them literally: layout, wire format, logging, audio rules.
3. Create or modify only the files listed under *Files* (tests included). Another file, folder or dependency means updating the task first.
4. Implement, then run the task's *Verification* and the baseline of section 3. A task is `done` only when every acceptance criterion passes.
5. Set the task's `Status` to `done`, its row in section 5 and in `ORDER.md`, update the parent if its exit criteria are met, and record any new fact or deviation in the task's *Notes*. Update the documents the change touches (the table in `CLAUDE.md`).
6. A task that needs hardware (T-04, and the hardware part of any other) is **not** done by running unit tests: say so and ask the maintainer.
7. Do not commit, push or publish unless the maintainer asks. Do not touch `.env*` files, `old/`, the venvs or the generated `contracts` folders.

Status values: `todo`, `awaiting-user` (a decision needs an answer), `blocked` (depends on unfinished or undecided work), `in-progress`, `done`.

## 3. Baseline definition of done (every code task)

From the service folder, with its own venv:

```powershell
& windows\Scripts\python.exe -m pytest        # all green, no hardware needed
& windows\Scripts\python.exe -m ruff check .  # All checks passed!
& windows\Scripts\python.exe -m mypy .        # no issues found
```

- `tests/architecture/test_dependency_rules.py` stays green: dependencies point inward only; `application` imports no framework or `sounddevice`; only `sounddevice_driver.py` imports `sounddevice`.
- Logging only through `shared_logging`; never log audio; never import stdlib `logging`.
- Audio stays PCM16 mono; the only conversions are the downmix and the optional resample.
- Config only through environment variables, documented in `.env.example`, the README table and `docs/configuration/environment-variables.md`; the bind host stays configurable; no hardcoded port.
- Wire types come from `contracts`; a new event goes to `contracts` first, then here, and the wheel is re-bundled with `contracts/scripts/bundle.py`.
- No secrets, tokens or real recordings in code, tests, fixtures or documents.
- The documents named in the table of `CLAUDE.md` are updated in the same change, and the counts (tests, mypy files) are refreshed only after running them.
- The workspace pipeline check still passes when the change can affect it: `brain_microservice\windows\Scripts\python.exe -m pytest contracts\tests -q` from the workspace root (it starts real service processes with fake hardware).

### 3.1 Layout of the code (what every task must follow)

```
main.py, main_flow/            entry point and start-up/shutdown (no wiring, no rules)
composition_root/              the only place concrete adapters are chosen (dependencies/, containers/)
application/                   ports/inbound, ports/outbound, services, dtos, errors
domain/                        entities, value objects, operations (pure, standard library only)
infrastructure/                config/, inbound/http/, outbound/<adapter>/
tests/                         domain, application, infrastructure, composition_root, architecture (mirror of the code); simple.py (real microphone)
```

A new outbound adapter lives in `infrastructure/outbound/<name>/` and implements `AudioCapturePort` and `AudioStreamPort`; the choice between adapters is made only in `composition_root/dependencies/microphone_dependencies.py`.

## 4. Facts the tasks rely on

| Fact | Value | Source |
|---|---|---|
| Port | 8000 (`SERVICE_PORT`) | `infrastructure/config/server_config.py` |
| Readiness of the deployment tool | `GET /available`, 15 s grace (`UNAVAILABLE_GRACE_SECONDS`) | deployment audit, `deployment/config/catalogue.toml` |
| Default format | 16000 Hz, 1 channel, chunk 1024 | `application/dtos/start_stream_inbound.py` |
| Treatment defaults | threshold 150, limit 2.0 s, start factor 2.0, smoothing on (0.1), noise floor on, DC offset off, resample 0 | `domain/value_objects/input_treatment.py` |
| Fake stream seed | `SineStream` in `contracts/tests/e2e/fake_services.py`: 5 chunks of amplitude 20, 80 chunks of a 300 Hz tone at 8000, then silence | the file |
| Tests | 127 passed, ruff clean, mypy 53 files (2026-11-05) | run on that day |
| `dotenv` flag | `dotenv = false` in the catalogue, asserted by `deployment/tests/test_env_file_only.py` | deployment audit |

## 5. Board

| Task | Name | Kind | Status |
|---|---|---|---|
| [T-01](T-01_capture-and-utterances/T-01_capture-and-utterances.md) | Capture and utterances (history) | epic | done (hardware pending, T-04) |
| [T-02](T-02_simulated-backend/T-02_simulated-backend.md) | Simulated capture backend | epic | todo |
| [T-02.1](T-02_simulated-backend/T-02.1_decisions.md) | Decisions: default, variable, signal | decision | awaiting-user |
| [T-02.2](T-02_simulated-backend/T-02.2_sim-capture-adapter.md) | The simulated capture adapter | code | blocked (T-02.1) |
| [T-02.3](T-02_simulated-backend/T-02.3_wiring-and-config.md) | Wiring and configuration | code | blocked (T-02.2) |
| [T-02.4](T-02_simulated-backend/T-02.4_tests.md) | Tests of the backend | code | blocked (T-02.3) |
| [T-02.5](T-02_simulated-backend/T-02.5_deployment-and-pipeline.md) | Deployment preset and pipeline check | code (other repository) | blocked (T-02.4) |
| [T-03](T-03_startup-configuration/T-03_startup-configuration.md) | Start-up configuration | epic | todo |
| [T-03.1](T-03_startup-configuration/T-03.1_load-dotenv.md) | Load `.env` at start | code | blocked (T-03.3) |
| [T-03.2](T-03_startup-configuration/T-03.2_requirements-split.md) | Split the requirements, lower bounds | code | todo |
| [T-03.3](T-03_startup-configuration/T-03.3_deployment-side.md) | The matching change in `deployment` | decision | awaiting-user |
| [T-04](T-04_hardware-verification/T-04_hardware-verification.md) | Hardware verification | epic | todo (needs the maintainer) |
| [T-04.1](T-04_hardware-verification/T-04.1_end-to-end-run.md) | Run `tests/simple.py` on a real microphone | manual | todo |
| [T-04.2](T-04_hardware-verification/T-04.2_tune-the-defaults.md) | Tune the treatment defaults | decision + code | blocked (T-04.1) |
| [T-04.3](T-04_hardware-verification/T-04.3_linux-and-raspberry-pi.md) | Linux and Raspberry Pi | manual | todo |
| [T-04.4](T-04_hardware-verification/T-04.4_docker-dev-snd.md) | Docker with `/dev/snd` | manual | blocked (T-04.3) |
| [T-05](T-05_documentation-sync.md) | Documentation sync | docs | recurring (first pass 2026-11-05) |
