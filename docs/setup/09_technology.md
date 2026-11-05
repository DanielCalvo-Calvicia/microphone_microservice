# 09 — Technology requirements

> Depends on: 05–07

| Category | Answer |
|---|---|
| Required | Python (venv `windows\Scripts\python.exe`, 3.14.2); FastAPI and uvicorn for HTTP; `sounddevice` (PortAudio) and `numpy` for the device and the meter; the workspace libraries `shared-logging` (editable install of `../shared-logging`) and `contracts` (wheel in `vendor/`) |
| Allowed | Standard library for the domain (`array`, `math`) |
| Forbidden | stdlib `logging` in service code; hand-written event JSON; `print` outside manual scripts and the console meter; calls to other services (`../CLAUDE.md`) |
| Installed versions (service venv, 2026-11-05) | fastapi 0.136.1, starlette 1.0.0, uvicorn 0.47.0, pydantic 2.13.4, sounddevice 0.5.5, numpy 2.4.5, httpx 0.28.1, pytest 9.0.3, pytest-asyncio 1.4.0, ruff 0.16.8, mypy 2.3.1, black 26.5.1, contracts-microservice 0.15.0, shared-logging 0.1.0 |
| Pinned versions | None in `requirements.*.txt` (bare names); `contracts` by its wheel file name |
| Dev tools in runtime requirements | Yes: `pytest`, `httpx`, `ruff`, `black`, `mypy` (to be split, PR-002) |
| System packages | Linux: `libportaudio2`, `portaudio19-dev` (catalogue `apt`) |
| Dependency policy | Lower bounds (`>=`) are the workspace convention (`deployment/docs/DEPLOYMENT.md`); not applied here yet |
| Licensing restrictions | UNKNOWN |
| Legacy dependencies | None; the pre-refactor design is in `docs/old/` |
