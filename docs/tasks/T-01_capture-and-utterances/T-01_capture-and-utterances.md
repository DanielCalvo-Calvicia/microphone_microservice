# T-01 — Capture and utterances

| | |
|---|---|
| Status | done (history); the behaviour on a real microphone was not re-checked since 2026-10-05, see T-04 |
| Kind | epic |
| Depends on | — |
| Blocks | T-04 |

> Written on 2026-11-05 from the git history. This epic records what was built; it is not a plan to execute. Nothing here is to be redone.

## Goal

A service that captures the local microphone, cuts the capture into utterances and streams them as `contracts.stream` events to Brain.

## What was built, in order

| Date | Commit | What |
|---|---|---|
| 2026-05-23 | `e7e34db` | First version: a flat script with about 154 `print` calls |
| 2026-09-20 | `15c9ee4` to `57e49a0` | The layered refactor: ports and adapters, error translation, `MicrophoneHandler`, composition root, architecture tests, ruff / black / mypy clean-up (ADR-001) |
| 2026-09-20 | `4f72d56` | The `AudioDriver` seam, `DeviceSelector`, stream termination, device I/O off the event loop |
| 2026-09-20 | `b3c0615` | Contract event streams, natural HTTP statuses, the device probe on `/available` (ADR-002, ADR-004) |
| 2026-09-25 to 2026-10-01 | `9229fe4`, `55def40`, `d98c699` | `contracts` 0.8.0, 0.9.0, 0.10.0 bundled; README, CLAUDE.md and architecture refreshed |
| 2026-10-01 | `cd84291` | `requirements.linux.txt` |
| 2026-10-05 | `ef25ade` | Silence detection and the input treatments move here from STT: one `utterance` event per utterance, each treatment an env var (ADR-003) |
| 2026-10-05 to 2026-10-08 | `6671f52`, `d06a338`, `b017314` | `contracts` 0.11.0, 0.14.0, 0.15.0 bundled |

## Exit criteria (met)

- `POST /start`, `GET /stream`, `POST /stop`, `GET /available`, `GET /health` answer as in `docs/api/api.md` (unit tests: `tests/infrastructure/test_http_handler.py`, `test_streaming_over_http.py`).
- The cutting and its treatments behave as in `docs/architecture/architecture.md` section 8 (`tests/domain/test_utterance_segmenter.py`, `test_input_treatment.py`, `test_level.py`, `test_resample.py`).
- The device is released on `/stop`, on a stream that dies, and on shutdown (`tests/application/test_microphone_service.py`, `tests/infrastructure/test_sounddevice_audio_capture.py`).
- The layout rules hold (`tests/architecture/test_dependency_rules.py`).
- 127 tests pass without hardware; ruff and mypy are clean (2026-11-05).

## Not verified

The sounddevice adapter and the thresholds on a real microphone (`tests/simple.py`), Linux / Raspberry Pi, Docker. These are T-04.

## Notes

- The requirement rows are FR-1 to FR-14 and NFR-1 to NFR-7 of `docs/requirements/requirements.md`.
- The decisions are ADR-001 to ADR-005.
