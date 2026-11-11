# 09 — Technology requirements

> Depends on: 05–07

| Category | Answer |
|---|---|
| Required | Python (venv `windows\Scripts\python.exe`, 3.14.2); FastAPI and uvicorn for HTTP; `sounddevice` (PortAudio) and `numpy` for the device and the meter; the workspace libraries `shared-logging` (editable install of `../shared-logging`) and `contracts` (wheel in `vendor/`) |
| Allowed | Standard library for the domain (`array`, `math`) |
| Forbidden | stdlib `logging` in service code; hand-written event JSON; `print` outside manual scripts and the console meter; calls to other services (`../CLAUDE.md`) |
| Installed versions (service venv, 2026-11-05) | fastapi 0.136.1, starlette 1.0.0, uvicorn 0.47.0, pydantic 2.13.4, sounddevice 0.5.5, numpy 2.4.5, httpx 0.28.1, pytest 9.0.3, pytest-asyncio 1.4.0, ruff 0.16.8, mypy 2.3.1, black 26.5.1, contracts-microservice 0.15.0, shared-logging 0.1.0 |
| Pinned versions | Exact `==` in `requirements.*.txt` for fastapi, uvicorn, sounddevice and numpy (the versions of the venv where the service ran, 2026-11-09); transitive packages are not locked; `contracts` by its wheel file name (0.16.0) |
| Dev tools in runtime requirements | No (T-03.2, 2026-11-09): they are in `requirements.dev.txt` |
| System packages | Linux: `libportaudio2`, `portaudio19-dev` (catalogue `apt`) |
| Dependency policy | Exact pins of what ran for the runtime file (as stt, decision Q02-7 of 2026-11-09); lower bounds for the dev tools. The pins resolve binary wheels for CPython 3.11 and 3.12 on `manylinux_2_28_aarch64` (`pip --dry-run`, nothing installed on aarch64) |
| Licensing restrictions | UNKNOWN |
| Legacy dependencies | None; the pre-refactor design is in `docs/old/` |
