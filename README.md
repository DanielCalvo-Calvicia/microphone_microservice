# Microphone Microservice

HTTP service that captures audio from the local microphone (Windows, via `sounddevice`) and
streams it as mono 16-bit PCM.

## Run

```bash
pip install -r requirements.windows.txt
python main.py
```

Configuration is read from the environment; see `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `SERVICE_NAME` | `Microphone Microservice` | API title / log name |
| `SERVICE_HOST` | `127.0.0.1` | Bind address |
| `SERVICE_PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `INFO` | `TRACE`→DEBUG, `WARN`→WARNING also accepted |
| `MICROPHONE_FALLBACK_SAMPLE_RATE` | `16000` | Rate used if the device reports none |
| `MICROPHONE_TARGET_KEYWORDS` | *(empty)* | Comma-separated device-name keywords; empty = OS default input |
| `MICROPHONE_SHOW_METER` | `true` | Console volume meter |

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/start` | Body `{sample_rate, channels, chunk_size}` (all optional). Opens the device; returns the negotiated rate |
| GET | `/stream` | Raw PCM bytes of the active stream; rate in the `X-Sample-Rate` header |
| GET | `/available` | `true` while a stream is active |
| POST | `/stop` | Releases the device (idempotent) |
| GET | `/health` | Liveness |

Responses use the envelope `action / status / status_code / message / timestamp / data`.
Every failure currently returns HTTP 500.

## Tests

```bash
pytest                    # unit + architecture tests (no hardware needed)
python tests/simple.py    # end-to-end, needs a real microphone
```

Architecture: [docs/architecture/architecture.md](docs/architecture/architecture.md).
Migration plan: [docs/architecture/PYTHON_MIGRATION_PLAN.md](docs/architecture/PYTHON_MIGRATION_PLAN.md).
