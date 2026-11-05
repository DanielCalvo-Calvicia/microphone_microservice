# ADR-001 — Layered structure with ports and adapters

**Status:** Accepted (2026-09-20, the refactor of commits `15c9ee4` to `4f72d56`)

## Context
The first version was a flat script with about 154 `print` calls, hardware access mixed with HTTP code, and no way to test without a microphone.

## Decision
The service follows the layout shared by all OBLIVION services: `main.py`, `main_flow/`, `composition_root/`, `application/`, `domain/`, `infrastructure/`. Dependencies point inward only. The application owns the ports (`MicrophoneStreamingPort` driving, `AudioCapturePort` and `AudioStreamPort` driven); the sounddevice adapter sits behind an `AudioDriver` protocol that tests fake. `tests/architecture/test_dependency_rules.py` enforces the import rules.

## Consequences
- Positive: everything but the real driver is tested without hardware; the hardware library is imported in one module.
- Negative: more files for a small service; the real driver still needs a manual hardware run (`tests/simple.py`).
