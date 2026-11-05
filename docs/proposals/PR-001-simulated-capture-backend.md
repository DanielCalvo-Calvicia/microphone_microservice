# PR-001 — A simulated capture backend

**Status:** Proposed, not built (source: the deployment audit of 2026-11-04, `docs/deployment_audit/microphone.md`; requirement FR-15). Planned as epic [T-02](../tasks/T-02_simulated-backend/T-02_simulated-backend.md); the decisions (default, variable, signal) wait for the maintainer in [Q01](../setup/questionnaires/Q01_open-questions.md) 1 to 3.

## Problem
There is no simulation backend in production code. Without a device `/available` is `is_available: false`, Brain's start-up preflight requires it, and the deployment readiness check (`ready = "/available"`, 15 s grace) reports the service as failed. A machine without a microphone cannot run the pipeline, and `update` can roll back a healthy commit.

## Proposal
1. A `sim` implementation of `AudioCapturePort` / `AudioStreamPort`, chosen by an environment variable (for example `MICROPHONE_BACKEND=real|sim`) in `composition_root/dependencies/microphone_dependencies.py:new_audio_capture`. Seed: `SineStream` in `contracts/tests/e2e/fake_services.py` (room noise, a tone, silence); a looped WAV is the alternative.
2. The **code default stays `real`**: a silent fake default would make a robot with a broken microphone look healthy. A deployed machine that should start on `sim` uses a preset in the catalogue (`[services.microphone.env]`, as stepper does with `MOCK_HARDWARE`), and the machine with the sound card sets `real` in `config/local/microphone.toml`.
3. `/available` reports `sim` in its `reason` and the service logs it at start.

## Tests
Sim-backend unit tests; the same API tests against `sim` and `real` (fake driver); an end-to-end run of the pipeline with `sim`; in `deployment`, a layout with `MICROPHONE_BACKEND=sim` passing the readiness check without a device.

## Notes
Update `.env.example`, the README, `docs/configuration/environment-variables.md`, `docs/api/api.md` (`/available`), `docs/requirements/requirements.md` (FR-15) and an ADR when it is built.
