# 03 — Business context and scope

> Depends on: 01, 02

| Field | Answer |
|---|---|
| Context | A hobby project: a static robot you talk to. Services run on one or several machines (Windows PC, Linux server, Raspberry Pi); the microphone runs on the machine that has the sound card. |
| In scope now | Capture, format negotiation, mono PCM16, utterance cutting and its treatments, optional resample, the five HTTP routes, the NDJSON event stream, release of the device on every way out. |
| Built, run on a real microphone 2026-11-10 (tuning pending) | All of the above works against a fake driver; the behaviour on a real microphone was not re-checked since the cutting moved here (2026-10-05). |
| Built (2026-11-10) | A simulated capture backend so a machine without a microphone can run the pipeline (PR-001, ADR-007, T-02.1 to T-02.4); `.env` loading and a split of the requirements (PR-002, T-03). |
| Planned | The hardware verification (T-04). The pipeline check and Docker on `sim` were run on 2026-11-10 (T-02.5, T-07). |
| Later ideas | A PulseAudio bridge for Docker on a Windows host (not planned); a filtered resampler instead of linear interpolation (not requested). |
| Non-goals | Transcription, wake-word detection, noise cancellation beyond the treatments listed, audio recording, multiple simultaneous captures, authentication of its own. |
| Users | The maintainer; Brain as the single caller. |
| Success | Brain gets one `utterance` per phrase said, quickly after the silence that ends it, with no clipped starts and no endless utterances in a noisy room; the device is always released. |
