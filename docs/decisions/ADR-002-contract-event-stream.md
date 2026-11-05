# ADR-002 — `GET /stream` is an NDJSON stream of `contracts.stream` events

**Status:** Accepted (2026-09-20, commit `b3c0615`)

## Context
The stream used to be raw PCM. Every service of the project must exchange the same typed messages.

## Decision
`/stream` answers `application/x-ndjson`; each line is an event built from `contracts.stream` (`MICROPHONE_OUTBOUND`) and encoded with `contracts.stream.codec`: `stream_started`, the audio events, `completed` or `error`. Audio is PCM16 mono in `bytes_base64`, never converted between services. A new event is defined in `contracts` first, then used here, and the bundled `contracts` wheel is refreshed with `contracts/scripts/bundle.py`.

## Consequences
- Positive: one wire format; consumers decode with the codec.
- Negative: base64 adds about a third to the audio size.

> **Update 2026-10-05:** the audio event is `utterance`, one per finished utterance, no longer one `partial` per chunk (ADR-003).
