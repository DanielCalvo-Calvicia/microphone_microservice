# Environment variables

All variables are read once at start-up by `ServerConfig.from_env()` and `MicrophoneConfig.from_env()` (`infrastructure/config/`), in `main_flow/http.py`. The template with comments is [`.env.example`](../../.env.example); the README repeats the tables. **No variable of this service holds a secret.** Never write a real secret in `.env.example`, in the code or in a document.

The service does **not** load a `.env` file itself (no `python-dotenv`): the variables must be in the process environment. The deployment tool (`../deployment`) reads `config/local/microphone.toml` and the catalogue and starts the process with them (catalogue key `dotenv = false`); for a hand start, export them first. The git-ignored files `.env`, `.env.staging` and `.env.production` exist next to `.env.example`: do not open or copy them.

A value that cannot be parsed (`int("abc")`, `float("x")`) stops the start with the Python exception. A value out of range stops it with `InvalidInputTreatment` naming the setting (see the *Rule* column).

## Server

| Variable | Default | Description | Sensitive |
|---|---|---|---|
| `SERVICE_NAME` | `Microphone Microservice` | API title and the name in the start-up log (the shared logger also reads `SERVICE_NAME`) | no |
| `SERVICE_HOST` | `127.0.0.1` | Bind address. Set it (for example `0.0.0.0`) when Brain runs on another machine; never assume `localhost` in a deployment | no |
| `SERVICE_PORT` | `8000` | Bind port | no |
| `LOG_LEVEL` | `INFO` | Read by `shared_logging` (`TRACE`, `DEBUG`, `INFO`, `WARN` / `WARNING`, `ERROR`, `CRITICAL`) | no |

## Device

| Variable | Default | Description | Sensitive |
|---|---|---|---|
| `MICROPHONE_FALLBACK_SAMPLE_RATE` | `16000` | Rate used when the device reports none | no |
| `MICROPHONE_TARGET_KEYWORDS` | empty | Comma-separated words of the device name; the first input device whose name contains one of them (case-insensitive) is used; empty or no match means the OS default input. Machine-specific: set it in that machine's local deployment settings | no |
| `MICROPHONE_SHOW_METER` | `true` | Console volume meter, rewritten on every chunk. Accepts `1`, `true`, `yes` (anything else is off). Set `false` outside a manual test | no |

## Input treatments (the cutting into utterances)

The cutting is **always on**; each treatment can be switched on or off. Volume is the RMS of the 16-bit samples of a chunk (0 to about 32000). Defaults live in `domain/value_objects/input_treatment.py`; flags accept `1`, `true`, `yes`, `on` for true, anything else is false, an empty value keeps the default.

| Variable | Default | Rule | Description |
|---|---|---|---|
| `MICROPHONE_SILENCE_THRESHOLD` | `150` | 0 or more (integer) | Volume under which it is silent |
| `MICROPHONE_SILENCE_LIMIT_SECONDS` | `2.0` | above 0 | Seconds of silence that end an utterance; lower answers faster, higher waits through pauses |
| `MICROPHONE_SPEECH_START_FACTOR` | `2.0` | at least 1 | Speech starts at the threshold times this factor (1 = the same volume that counts as silence) |
| `MICROPHONE_DC_OFFSET_REMOVAL` | `false` | flag | Subtract the slowly changing constant offset of the signal before measuring volume |
| `MICROPHONE_VOLUME_SMOOTHING` | `true` | flag | Measure a smoothed volume so one click is not speech |
| `MICROPHONE_VOLUME_SMOOTHING_FACTOR` | `0.1` | above 0, up to 1 | Weight of the newest chunk in the smoothed volume |
| `MICROPHONE_NOISE_FLOOR_TRACKING` | `true` | flag | Raise the thresholds above the quietest volume heard (speech over 3 x it, silence under 2 x it). Turn it off in a very quiet room whose floor stays too high |
| `MICROPHONE_RESAMPLE_TO_HZ` | `0` | 0 or more (integer) | Rate of the audio sent on (linear interpolation, in the microphone's CPU); `0` = the device's rate; `16000` is what Whisper uses and sends less data. `/start` and `X-Sample-Rate` report this rate |

## Read by other packages, not by this service

`LOG_FORMAT`, `LOG_OUTPUT`, `ENVIRONMENT` and `TRACE_EXPORT_*` are read by `shared_logging`: see [`shared-logging/docs/logging.md`](../../../shared-logging/docs/logging.md).

## Where else the variables are documented

When a variable is added, changed or removed, update in the same change: `.env.example`, the table in [README.md](../../README.md), this file, and (outside this repository) `deployment/docs/DEPLOYMENT.md` and `deployment/config/services/microphone.toml` (regenerate it with `brain_microservice\windows\Scripts\python.exe deployment\scripts\env_inventory.py --write`).
