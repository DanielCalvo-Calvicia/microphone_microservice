# 04 — Glossary and conventions

> Depends on: 01–03

## Glossary

| Term | Meaning |
|---|---|
| Utterance | What is said between two silences: audio that starts when the volume reaches the start threshold and ends after `MICROPHONE_SILENCE_LIMIT_SECONDS` of silence |
| Chunk | The frames read from the device in one call (`chunk_size`, default 1024) |
| PCM16 mono | 16-bit signed samples, one channel; the only audio format between services |
| Volume | RMS of the 16-bit samples of a chunk (0 to about 32000) |
| Silence threshold / start factor | The volume under which it is silent; speech starts at threshold times the factor |
| Noise floor | The quietest non-zero volume heard so far, used to raise the thresholds in a noisy room |
| DC offset | A slowly changing constant added to the signal; removed before measuring when enabled |
| Negotiated rate | The sample rate the device accepted, possibly different from the requested one |
| Event | One NDJSON line of `contracts.stream` (`stream_started`, `utterance`, `completed`, `error`) |
| Envelope | `ApiEnvelope`: `action / status / status_code / message / timestamp / data`, the shape of every non-stream answer |
| Driving / driven port | The ports the outside calls (`MicrophoneInboundPort`, `MicrophoneServicePort`) / the port the application calls (`AudioCapturePort`, `AudioStreamPort`) |
| Brain | The only coordinator of OBLIVION; the only caller of this service |

## Naming and language

| Topic | Answer |
|---|---|
| Layout | `main.py`, `main_flow/`, `composition_root/`, `application/`, `domain/`, `infrastructure/` (`../CLAUDE.md`) |
| Python style | snake_case modules and functions, PascalCase classes; ruff (`E F I B UP`, line length 100), mypy strict, black configured |
| Logging | `shared_logging` only: `get_logger(__name__)`, `init_logging("microphone")`; constant messages with keyword fields; never stdlib `logging`; never `print` (the console meter is the one exception, a manual-test aid) |
| Wire format | Only through `contracts.stream` and its codec; never hand-written JSON |
| Docs language | English |
| Line endings | CRLF in most files; edit with tools that keep them |
| Commit convention | UNKNOWN; the history uses short imperative subjects (`Bundle contracts 0.15.0`) |
| Branching | Work on `feature_ai_claude_2`; commit and push only when the maintainer asks |
