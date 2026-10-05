# CLAUDE.md: microphone_microservice

Port **8000** (`SERVICE_PORT`). Python/FastAPI. Captures audio from the local input device (`sounddevice`/PortAudio, Windows) and streams mono PCM16 as `contracts.stream` events. Status: working, needs retest on hardware after recent changes. See `README.md` and `../CLAUDE.md`.

Current state (2026-10-01): branch `feature_ai_claude_2` (tracks `origin/feature_ai_claude_2`, in sync), working tree clean, last feature commit `d98c699` "Bundle contracts 0.10.0; refresh README, CLAUDE.md and architecture docs" (pushed). Tests: `88 passed`, ruff clean, mypy clean (48 files). Hardware (`tests/simple.py`, the real sounddevice adapter) not run in the last documentation pass.

## Role

Brain calls `POST /start`, reads `GET /stream` (NDJSON: `stream_started`, one `utterance` per finished utterance, `completed` or `error`), calls `POST /stop`. Also `GET /available` (probes the device, does not open it) and `GET /health`. Nothing else calls it. Events are defined in `contracts.stream` (`MICROPHONE_OUTBOUND`) and encoded with the codec. The microphone cuts the capture into utterances (`domain/entities/utterance_segmenter.py`, silence detection moved here from STT): one `utterance` event per utterance, with its whole audio, at `MICROPHONE_RESAMPLE_TO_HZ` when set. The cutting is always on, each treatment is an env var (`MICROPHONE_SILENCE_*`, `_SPEECH_START_FACTOR`, `_DC_OFFSET_REMOVAL`, `_VOLUME_SMOOTHING[_FACTOR]`, `_NOISE_FLOOR_TRACKING`, `_RESAMPLE_TO_HZ`; `domain/value_objects/input_treatment.py`). Failures map to 409 (capture already active/not active), 422 (invalid format, `sample_rate` mismatch), 503 (no device), else 500.

## Layout

`main.py` -> `main_flow/` (startup/shutdown) -> `composition_root/` -> `application/` -> `domain/` (pure audio ops) -> `infrastructure/` (config, HTTP inbound incl. `ndjson_audio_events.py`, sounddevice outbound). `tests/architecture/` enforces that dependencies point inward, so keep that intact.

## Rules

- Audio stays PCM16 mono. The only conversions here are downmixing what the device delivers and the optional `MICROPHONE_RESAMPLE_TO_HZ`.
- Config through env (`.env.example`): `SERVICE_NAME`, `SERVICE_HOST`, `SERVICE_PORT`, `LOG_LEVEL`, `MICROPHONE_FALLBACK_SAMPLE_RATE`, `MICROPHONE_TARGET_KEYWORDS`, `MICROPHONE_SHOW_METER`, and the input treatments `MICROPHONE_SILENCE_THRESHOLD`, `MICROPHONE_SILENCE_LIMIT_SECONDS`, `MICROPHONE_SPEECH_START_FACTOR`, `MICROPHONE_DC_OFFSET_REMOVAL`, `MICROPHONE_VOLUME_SMOOTHING`, `MICROPHONE_VOLUME_SMOOTHING_FACTOR`, `MICROPHONE_NOISE_FLOOR_TRACKING`, `MICROPHONE_RESAMPLE_TO_HZ`. The bind host must stay configurable (containers/remote use).
- Ruff and mypy are configured in `pyproject.toml`; the microphone venv is the only one with them installed. Keep both clean.
- `contracts` comes from `vendor/contracts_microservice-<version>.whl` (0.12.0); refresh it with `contracts/scripts/bundle.py`, never by hand.
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
