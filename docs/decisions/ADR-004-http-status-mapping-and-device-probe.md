# ADR-004 — Natural HTTP statuses and a device probe on `/available`

**Status:** Accepted (2026-09-20, commit `b3c0615`)

## Context
Every failure used to answer 500, and `/available` meant "a stream is active", which told Brain nothing about the hardware.

## Decision
Failures are mapped in one place (`http_error_mapper.py`): 409 capture already active or not active, 422 invalid format or a `sample_rate` that contradicts the capture, 503 no usable device, 500 anything else. `GET /available` probes the selected device without opening it and answers `AvailabilityResponse{is_available, reason}`. Non-stream answers keep the `ApiEnvelope`.

## Consequences
- Positive: Brain and the deployment tool can tell "no microphone" from a bug; the probe is cheap and does not disturb a running capture.
- Negative: a machine without a microphone is reported as not ready (see PR-001).
