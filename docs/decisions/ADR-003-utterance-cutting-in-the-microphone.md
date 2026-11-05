# ADR-003 — The microphone cuts the capture into utterances

**Status:** Accepted (2026-10-05, commit `ef25ade`)

## Context
Silence detection lived in STT, which received every chunk. That sent audio nobody needed, put a capture concern in a transcription service and forced STT to know the microphone's volume scale.

## Decision
Silence detection moves here (`UtteranceSegmenter`). The stream carries one `utterance` event per utterance with its whole audio, at `MICROPHONE_RESAMPLE_TO_HZ` when set. The cutting is always on; each treatment (DC offset removal, volume smoothing, noise-floor tracking, resampling) is an environment variable and a field of `InputTreatment`, validated at start. Defaults: threshold 150, limit 2.0 s, start factor 2.0, smoothing on (0.1), noise-floor tracking on, DC offset off, no resample.

## Consequences
- Positive: STT only transcribes; less traffic; the thresholds are tuned where the audio is captured.
- Negative: the utterance in progress is lost if the device fails; the defaults are not tuned on real rooms yet (hardware retest pending); the resample is linear interpolation, not a filtered converter.
