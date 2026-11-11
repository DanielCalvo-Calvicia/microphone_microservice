# CLAUDE.md: microphone_microservice

Port **8000** (`SERVICE_PORT`). Python/FastAPI. Captures audio from the local input device (`sounddevice`/PortAudio, Windows) and streams mono PCM16 as `contracts.stream` events. Status: working, needs retest on hardware after recent changes. Read [README.md](README.md) for the state, [docs/architecture/architecture.md](docs/architecture/architecture.md) for the structure, [docs/tasks/ORDER.md](docs/tasks/ORDER.md) for what is done and what comes next, [docs/README.md](docs/README.md) for the index of the documentation and `../CLAUDE.md` for the rules of the workspace.

Current state (2026-11-10): branch `feature_ai_claude_2` (tracks `origin/feature_ai_claude_2`), last commit `dd50502` (the work of the deployment plan, `docs/tasks/`); the restructure that mirrors stt (2026-11-11) is uncommitted. Tests: `184 passed` (2026-11-11: the layout was restructured to mirror stt, +13 architecture tests; 171 on 2026-11-10: the simulated backend `MICROPHONE_BACKEND=sim`, the `.env` loading and the requirements split; 142 before), ruff clean, mypy clean (71 files). The simulated backend was run as the real service in a scratch folder (every endpoint, no sound device) and through the workspace pipeline check (`contracts/tests`: 84 passed, 18 skipped); Docker on `sim` on amd64 was run on 2026-11-10 (T-07: build, every endpoint, restart, recreate, image contents; `docker stop` with a `/stream` consumer was killed after 10 s until the graceful-shutdown timeout of the same day; now 5.7 s, exit code 0). Hardware: the real sounddevice adapter and the cutting ran on a real headset microphone on 2026-11-10 (T-04.1: three sentences, three utterances, 0 overflows; `tests/simple.py` was stale and is fixed, 7 of 7 on `sim`, not re-run on the real device); the defaults are not tuned (T-04.2). `git status` is the truth for what is uncommitted.

## MANDATORY: every change updates the documentation

**No change is finished until the documents that describe it are true again.** This applies to every change: code, configuration, tests, a decision, a requirement. Do it in the same piece of work, not later. A change that leaves a document saying something false is not done.

| If you change... | Update, in the same change |
|---|---|
| The state of a task (started, done, blocked, split, a new task, a new dependency, the order) | the task file (`Status`, `Depends on`, *Results* or *Resolution*), the board in [docs/tasks/README.md](docs/tasks/README.md) section 5, **[docs/tasks/ORDER.md](docs/tasks/ORDER.md)** (state, detail, last updated; keep the order), the epic file and the work item of [docs/setup/16_work-items.md](docs/setup/16_work-items.md) |
| Code, a package, a folder or a file name | [docs/architecture/architecture.md](docs/architecture/architecture.md) (sections 3, 4 and 6), the paths named in the task files, the layout of [README.md](README.md), [docs/tasks/README.md](docs/tasks/README.md) section 3.1 and the **Layout** below |
| An environment variable, a default or a rule | `.env.example`, the table of [README.md](README.md), [docs/configuration/environment-variables.md](docs/configuration/environment-variables.md), the **Rules** below, and (outside this repository) `deployment/docs/DEPLOYMENT.md` and `deployment/config/services/microphone.toml` (regenerate with `brain_microservice\windows\Scripts\python.exe deployment\scripts\env_inventory.py --write`) |
| A route, a request or response field, an event, a status code or an error | [docs/api/api.md](docs/api/api.md), the endpoints of [README.md](README.md), [docs/requirements/requirements.md](docs/requirements/requirements.md), and `contracts` first (`stream/schemas.py`, then bump and re-bundle the wheel) |
| Logging, probes, shutdown, tracing, files on disk | [docs/operations/monitoring.md](docs/operations/monitoring.md) |
| A requirement (new, changed, done) | [docs/requirements/requirements.md](docs/requirements/requirements.md) (status and where) and the status table of [README.md](README.md) |
| A decision, an override, an answer of the maintainer | an ADR in `docs/decisions/` (new, or a dated update of the one it changes), [docs/setup/13_decisions-and-overrides.md](docs/setup/13_decisions-and-overrides.md), the *Resolution* of the task, the question in `docs/questionnaires/` (the answer after `A:`, and its row in `00_README.md`) and the requirement it touches |
| A proposal that was accepted, built or dropped | its status line in `docs/proposals/` (keep the body as history, add a dated note) and the requirement it names |
| A risk, a limit, a known debt | [docs/setup/14_risks-and-debt.md](docs/setup/14_risks-and-debt.md), the *Known issues and debt* of the architecture document and the *Known limitations* of [README.md](README.md) |
| What the project is, its counts or its context (purpose, scope, external services, technology, versions) | the matching file of [docs/setup/](docs/setup/00_README.md) (01 to 12) and [README.md](README.md) |
| Access, secrets, dependencies, what is captured or exposed | [docs/security/security.md](docs/security/security.md) |
| How it starts, its readiness, its requirements files or the supported platforms | [docs/deployment/deployment.md](docs/deployment/deployment.md) and the deployment tool's catalogue and manual (outside this repository) |
| The bundled `contracts` version | `requirements.*.txt`, `vendor/`, the **Rules** below, [README.md](README.md) status table and [docs/requirements/requirements.md](docs/requirements/requirements.md) NFR-6 |
| Test, ruff or mypy counts | the **Current state** above and the *Test* section of [README.md](README.md) (only after running them) |

How to do it:

1. Change the documents **with** the change, and say what you updated when you report the work.
2. Use dated notes (`> **Update 2026-11-05:** ...`) in documents that are history (ADRs, proposals); correct the text in documents that describe the present (README, architecture, API, configuration, monitoring, requirements, security, deployment).
3. Mark what is planned as planned and what is built as built; never describe as working something that is not, and never claim hardware behaviour that was not run on a real microphone.
4. After editing, check that the links resolve and that every path named in a document still exists.
5. When the documents and the code disagree and you cannot tell which is right, do not guess: ask the maintainer.

## Role

Brain calls `POST /start`, reads `GET /stream` (NDJSON: `stream_started`, one `utterance` per finished utterance, `completed` or `error`), calls `POST /stop`. Also `GET /available` (probes the device, does not open it) and `GET /health`. Nothing else calls it, and it calls nothing. Events are defined in `contracts.stream` (`MICROPHONE_OUTBOUND`) and encoded with the codec. The microphone cuts the capture into utterances (`domain/entities/utterance_segmenter.py`, silence detection moved here from STT): one `utterance` event per utterance, with its whole audio, at `MICROPHONE_RESAMPLE_TO_HZ` when set. The cutting is always on, each treatment is an env var (`MICROPHONE_SILENCE_*`, `_SPEECH_START_FACTOR`, `_DC_OFFSET_REMOVAL`, `_VOLUME_SMOOTHING[_FACTOR]`, `_NOISE_FLOOR_TRACKING`, `_RESAMPLE_TO_HZ`, `_PREROLL_SECONDS`; `domain/value_objects/input_treatment.py`). Failures map to 409 (capture already active/not active), 422 (invalid format, `sample_rate` mismatch), 503 (no device), else 500.

## Layout

`main.py` -> `main_flow/` (startup/shutdown) -> `composition_root/` -> `application/` -> `domain/` (pure audio ops) -> `infrastructure/` (config, HTTP inbound split into `routes/`, `response/` (incl. `stream_events.py`, the NDJSON framing) and `errors/`, capture outbound: sounddevice and sim). The layout mirrors `stt_microservice` (DTOs in `application/dtos/{inbound,outbound}`, ports in `application/ports/{inbound,service,outbound}`, one file per object in `composition_root/dependencies/`). `tests/architecture/` enforces that dependencies point inward and the DTO and port rules, so keep that intact. Documentation lives in `docs/` (architecture, api, configuration, operations, requirements, security, deployment, decisions, proposals).

## Rules

- Audio stays PCM16 mono. The only conversions here are downmixing what the device delivers and the optional `MICROPHONE_RESAMPLE_TO_HZ`.
- Config through env (`.env.example`): `SERVICE_NAME`, `SERVICE_HOST`, `SERVICE_PORT`, `LOG_LEVEL`, `MICROPHONE_FALLBACK_SAMPLE_RATE`, `MICROPHONE_TARGET_KEYWORDS`, `MICROPHONE_SHOW_METER`, and the input treatments `MICROPHONE_SILENCE_THRESHOLD`, `MICROPHONE_SILENCE_LIMIT_SECONDS`, `MICROPHONE_SPEECH_START_FACTOR`, `MICROPHONE_DC_OFFSET_REMOVAL`, `MICROPHONE_VOLUME_SMOOTHING`, `MICROPHONE_VOLUME_SMOOTHING_FACTOR`, `MICROPHONE_NOISE_FLOOR_TRACKING`, `MICROPHONE_RESAMPLE_TO_HZ`, `MICROPHONE_PREROLL_SECONDS`. The bind host must stay configurable (containers/remote use). The service loads the `.env` next to `main.py` at start (`main_flow/http.py` `load_environment`, `python-dotenv`; a missing file is fine and a variable already set in the process wins).
- Ruff and mypy are configured in `pyproject.toml`; the microphone venv is the only one with them installed. Keep both clean.
- `contracts` comes from `vendor/contracts_microservice-<version>.whl` (0.16.0; the service venv still has 0.15.0 installed, reinstall the wheel to refresh it); refresh the wheel with `contracts/scripts/bundle.py`, never by hand.
- Logging only through `shared_logging`; never log audio.
- Gotcha: `.env.staging` and `.env.production` exist next to `.env`. Do not open or copy them.
- `.engram/` and `docs/old/` are stale. `docs/architecture/PYTHON_MIGRATION_PLAN.md` is a historical plan that was executed. `docs/deployment_audit/microphone.md` is an audit made from the deployment side (2026-11-04) and the source of PR-001 and PR-002.
- **Tasks:** follow [docs/tasks/ORDER.md](docs/tasks/ORDER.md) and the protocol of [docs/tasks/README.md](docs/tasks/README.md) section 2: the first `todo` task whose dependencies are done; create or change only the files the task lists (update the task first if you need another); a decision that is `awaiting-user` stops the chain (the questions are in `docs/questionnaires/Q01_open-questions.md`); a task that needs hardware is not done by unit tests (T-04: ask the maintainer).
- Never invent an answer that only the maintainer can give: write `UNKNOWN`, or add a question to `docs/questionnaires/`.
- Code, comments and documents are in English.
- Do not commit or push unless asked.

## Commands

```powershell
& windows\Scripts\python.exe -m pip install -r requirements.dev.txt   # once: pytest, httpx and the lint tools (the deploy tool never installs them)
& windows\Scripts\python.exe main.py
& windows\Scripts\python.exe -m pytest           # no hardware needed, ~2 s
& windows\Scripts\python.exe tests\simple.py     # end to end, needs a real microphone (ask the user)
& windows\Scripts\python.exe -m ruff check .
& windows\Scripts\python.exe -m mypy .
```
