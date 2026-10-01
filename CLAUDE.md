# CLAUDE.md: microphone_microservice

Port **8000** (`SERVICE_PORT`). Python/FastAPI. Captures audio from the local input device (`sounddevice`/PortAudio, Windows) and streams mono PCM16 as `contracts.stream` events. Status: working, needs retest on hardware after recent changes. See `README.md` and `../CLAUDE.md`.

Current state (2026-10-01): branch `feature_ai_claude_2` (tracks `origin/feature_ai_claude_2`, in sync), working tree clean, last commit `55def40` "Bundle contracts 0.9.0". Tests: `88 passed`, ruff clean, mypy clean (48 files). Hardware (`tests/simple.py`, the real sounddevice adapter) not run in the last documentation pass.

## Role

Brain calls `POST /start`, reads `GET /stream` (NDJSON: `stream_started`, one `partial` per chunk, `completed` or `error`), calls `POST /stop`. Also `GET /available` (probes the device, does not open it) and `GET /health`. Nothing else calls it. Events are defined in `contracts.stream` (`MICROPHONE_OUTBOUND`) and encoded with the codec. Every chunk is forwarded: there is **no** silence suppression and no silence-based `completed` here (STT does the silence detection). Failures map to 409 (capture already active/not active), 422 (invalid format, `sample_rate` mismatch), 503 (no device), else 500.

## Layout

`main.py` -> `main_flow/` (startup/shutdown) -> `composition_root/` -> `application/` -> `domain/` (pure audio ops) -> `infrastructure/` (config, HTTP inbound incl. `ndjson_audio_events.py`, sounddevice outbound). `tests/architecture/` enforces that dependencies point inward, so keep that intact.

## Rules

- Audio stays PCM16 mono. No format conversion here beyond downmixing what the device delivers.
- Config through env (`.env.example`): `SERVICE_NAME`, `SERVICE_HOST`, `SERVICE_PORT`, `LOG_LEVEL`, `MICROPHONE_FALLBACK_SAMPLE_RATE`, `MICROPHONE_TARGET_KEYWORDS`, `MICROPHONE_SHOW_METER`. The bind host must stay configurable (containers/remote use).
- Ruff and mypy are configured in `pyproject.toml`; the microphone venv is the only one with them installed. Keep both clean.
- `contracts` comes from `vendor/contracts_microservice-<version>.whl` (0.10.0); refresh it with `contracts/scripts/bundle.py`, never by hand.
- Gotcha: `.env.staging` and `.env.production` exist next to `.env`. Do not open or copy them.
- `.engram/` and `docs/old/` are stale. `docs/architecture/PYTHON_MIGRATION_PLAN.md` is a historical plan that was executed.

## Commands

```powershell
& windows\Scripts\python.exe main.py
& windows\Scripts\python.exe -m pytest           # no hardware needed, ~2 s
& windows\Scripts\python.exe tests\simple.py     # end to end, needs a real microphone (ask the user)
& windows\Scripts\python.exe -m ruff check .
& windows\Scripts\python.exe -m mypy .
```
