# T-02 — Simulated capture backend

| | |
|---|---|
| Status | done |
| Kind | epic |
| Depends on | T-02.1 |
| Blocks | — |
| Record | [PR-001](../../proposals/PR-001-simulated-capture-backend.md), requirement FR-15, risk 2 of `docs/setup/14_risks-and-debt.md` |

## Goal

A `sim` implementation of the capture, behind the existing ports, so a machine without a microphone can run the whole pipeline and pass the deployment readiness check, **without** making a broken microphone look healthy.

## Why

Without a device `/available` answers `is_available: false`; Brain's start-up preflight requires it, and the deployment tool (`ready = "/available"`, 15 s grace) reports the deploy as failed. `update` then rolls back a healthy commit, or restarts the old process.

## Order

T-02.1 (decisions) -> T-02.2 (the adapter) -> T-02.3 (wiring and configuration) -> T-02.4 (tests) -> T-02.5 (deployment preset and pipeline check, in the `deployment` repository).

## Rules for the whole epic

- The **code default stays `real`** unless T-02.1 records another answer from the maintainer.
- The simulated adapter lives in `infrastructure/outbound/` and implements `AudioCapturePort` and `AudioStreamPort`; nothing in `application` or `domain` knows it exists, except that the choice is made in `composition_root/dependencies/microphone_dependencies.py:new_audio_capture`.
- `/available` must say it is simulated in its `reason`, and the service logs it at start, so a simulated microphone is never mistaken for a real one.
- The simulated signal goes through the same `UtteranceSegmenter` as a real one: it is a fake device, not a fake service.
- No real recordings in the repository.

## Exit criteria

- With the variable set to `sim` the service starts without a sound card, `/available` is `is_available: true` with a reason that says `sim`, `/start` + `/stream` produce `stream_started`, at least one `utterance`, and `completed` on `/stop`.
- With the variable unset the service behaves exactly as before (unit tests unchanged and green).
- The documents of the table in `CLAUDE.md` are updated; FR-15 is `Done`; PR-001 has a dated note; an ADR records the decision.
- The pipeline check (`contracts\tests`) and the `deployment` test of T-02.5 pass.

## Notes

The seed signal is `SineStream` in `contracts/tests/e2e/fake_services.py`; it is a test double of another repository and must not be imported from here (services never import each other's tests): copy the idea, not the module.
