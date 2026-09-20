# CLAUDE.md: microphone_microservice

Port **8000**. Python/FastAPI. Captures audio from the local input device (`sounddevice`/PortAudio, Windows) and streams mono PCM16. Status: working, needs retest after recent changes. See `README.md` and `../CLAUDE.md`.

## Role

Brain calls `POST /start`, reads `GET /stream`, calls `POST /stop`. Nothing else calls it. Stream events are defined in `contracts.stream` (`MICROPHONE_OUTBOUND`) and encoded with the codec. Silent chunks are suppressed, and `completed` is emitted after about 2 s of silence.

## Layout

`main.py` → `main_flow/` (startup/shutdown) → `composition_root/` → `application/` → `domain/` (pure audio ops) → `infrastructure/` (config, HTTP inbound, sounddevice outbound). `tests/architecture/` enforces that dependencies point inward, so keep that intact.

## Rules

- Audio stays PCM16 mono. No format conversion here beyond what the device needs.
- Config through env (`.env.example`): `SERVICE_HOST`, `SERVICE_PORT`, `MICROPHONE_FALLBACK_SAMPLE_RATE`, `MICROPHONE_TARGET_KEYWORDS`. Bind host must be configurable (containers/remote use).
- This is the only service with ruff and mypy configured. Keep both clean.

## Commands

```powershell
& windows\Scripts\python.exe main.py
& windows\Scripts\python.exe -m pytest           # no hardware needed
& windows\Scripts\python.exe tests\simple.py     # end to end, needs a real microphone (ask the user)
& windows\Scripts\python.exe -m ruff check .
& windows\Scripts\python.exe -m mypy .
```
