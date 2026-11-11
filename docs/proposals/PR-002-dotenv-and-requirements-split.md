# PR-002 — Load `.env` and split the requirements

**Status:** Proposed, not built (source: the deployment audit of 2026-11-04; requirement FR-16). Planned as epic [T-03](../tasks/T-03_startup-configuration/T-03_startup-configuration.md): the requirements split (T-03.2) needs no decision; loading `.env` (T-03.1) waits for the maintainer's answer about `deployment` ([Q01](../questionnaires/Q01_open-questions.md) 4).

## Problem
`main_flow/http.py` never loads `.env` (no `python-dotenv`), so the catalogue has `dotenv = false` and the deployment tool has a special path for it. The requirements files list `ruff`, `black`, `mypy`, `pytest` and `httpx` next to the runtime packages, and nothing is pinned.

## Proposal
1. Add `python-dotenv>=1.0.1` and load `.env` as stt and stepper do (`_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"`, `load_dotenv(dotenv_path=_ENV_FILE)` in `main_flow/http.py`; in a container that resolves to `/app/.env`), then set `dotenv = true` in the catalogue. `deployment/tests/test_env_file_only.py` (asserts `dotenv is False` for the microphone) and `deployment/docs/DEPLOYMENT.md` change in the same step.
2. Split the development tools into `requirements-dev.*` and keep the catalogue's `requirements` pointing at the runtime file; update the venv instructions in `CLAUDE.md`.
3. Pin with lower bounds (`>=`), the repository convention.

## Notes
Update `docs/configuration/environment-variables.md` (the note on `.env`), `docs/deployment/deployment.md`, `docs/security/security.md` (supply chain) and FR-16 when built.

> **Update 2026-11-09:** the maintainer answered Q02-4 and Q02-7 "Recommended": load the `.env` (`python-dotenv`) with `dotenv = true` in `deployment` in the same piece of work (T-03.1 and T-06.1), exact `==` pins of the versions that ran (as stt), and one `requirements-dev.txt` (as tts). Not built yet.

> **Update 2026-11-09 (items 2 and 3 built, T-03.2):** `requirements.windows.txt` and `requirements.linux.txt` hold only `fastapi==0.136.1`, `uvicorn==0.47.0`, `sounddevice==0.5.5`, `numpy==2.4.5`, `shared-logging` and the `contracts` 0.16.0 wheel; the tools are in `requirements-dev.txt`. Item 1 (the `.env` loading) is not built (T-03.1).

> **Update 2026-11-10 (item 1 built, T-03.1 and T-06.1):** `main_flow/http.py` has `load_environment(path)` (`python-dotenv==1.2.4`, `override=False`, a missing file is fine) and `run_http` calls it before reading any setting; 5 tests in `tests/main_flow/test_environment.py`, 5 of 5 one-line mutations caught. In `deployment` the catalogue entry lost `dotenv = false` (the default is true), `tests/test_env_file_only.py` was reworked (the runner and the `--env-file` tests use a stand-in service with the flag off, since no shipped service lacks dotenv now; a new test pins that the microphone is mounted at `/app/.env` and not run through the runner) and the manual says so. **Status: Built.**

> **Update 2026-11-11:** the dev file is now `requirements.dev.txt` (as stt), renamed from `requirements-dev.txt`.
