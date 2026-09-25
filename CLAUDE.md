# CLAUDE.md: microphone_microservice

Port **8000**. Python/FastAPI. Captures audio from the local input device (`sounddevice`/PortAudio, Windows) and streams mono PCM16. Status: working, needs retest after recent changes. See `README.md` and `../CLAUDE.md`.

Current state (2026-09-22): branch `feature_ai_claude`, clean, last commit "Microphone: emit contract event streams, natural HTTP statuses, device probe".

## Role

Brain calls `POST /start`, reads `GET /stream`, calls `POST /stop`. Also `GET /available` and `GET /health`. Nothing else calls it. Stream events are defined in `contracts.stream` (`MICROPHONE_OUTBOUND`) and encoded with the codec. Silent chunks are suppressed, and `completed` is emitted after about 2 s of silence.

## Layout

`main.py` → `main_flow/` (startup/shutdown) → `composition_root/` → `application/` → `domain/` (pure audio ops) → `infrastructure/` (config, HTTP inbound, sounddevice outbound). `tests/architecture/` enforces that dependencies point inward, so keep that intact.

## Rules

- Audio stays PCM16 mono. No format conversion here beyond what the device needs.
- Config through env (`.env.example`): `SERVICE_NAME`, `SERVICE_HOST`, `SERVICE_PORT`, `LOG_LEVEL`, `MICROPHONE_FALLBACK_SAMPLE_RATE`, `MICROPHONE_TARGET_KEYWORDS`, `MICROPHONE_SHOW_METER`. Bind host must be configurable (containers/remote use).
- Ruff and mypy are configured in `pyproject.toml` and installed in this venv (the only one). Keep both clean.
- Gotcha: `.env.staging` and `.env.production` exist next to `.env`. Do not open or copy them.

## Commands

```powershell
& windows\Scripts\python.exe main.py
& windows\Scripts\python.exe -m pytest           # no hardware needed
& windows\Scripts\python.exe tests\simple.py     # end to end, needs a real microphone (ask the user)
& windows\Scripts\python.exe -m ruff check .
& windows\Scripts\python.exe -m mypy .
```
