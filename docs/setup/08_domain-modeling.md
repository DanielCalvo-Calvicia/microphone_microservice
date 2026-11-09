# 08 — Domain modeling

> Depends on: 02–07. Everything here is in `domain/` and is evidenced by the code.

## Entities

| Entity | Rules |
|---|---|
| `Microphone` | Idle or capturing in an `AudioFormat`; it can only start when idle (`CaptureAlreadyActive` otherwise); stopping an idle microphone is a no-op; `active_format` on an idle one raises `CaptureNotActive` |
| `UtteranceSegmenter` | Fed chunks, hands back utterances. Starts speaking when the volume reaches the start threshold; ends when the silent samples reach `silence_limit_seconds`; keeps the silence that ended the utterance; `flush()` returns the utterance in progress; resamples the audio it keeps when `resample_to_hz` differs from the device rate |

## Value objects

| Value object | Rules |
|---|---|
| `AudioFormat(sample_rate, channels, chunk_size)` | Frozen; every field above 0 (`InvalidAudioFormat`); `with_sample_rate`, `with_channels` |
| `InputTreatment` | Frozen; `silence_threshold` >= 0 (150), `silence_limit_seconds` > 0 (2.0), `speech_start_factor` >= 1 (2.0), `dc_offset_removal` (false), `volume_smoothing` (true), `volume_smoothing_factor` in (0, 1] (0.1), `noise_floor_tracking` (true), `resample_to_hz` >= 0 (0), `preroll_seconds` >= 0 (0.2) (`InvalidInputTreatment`) |

## Operations (pure functions)

| Operation | Behaviour |
|---|---|
| `downmix_to_mono(pcm, channels)` | Mean of each frame, truncated toward zero; the buffer must be whole frames |
| `samples_of`, `mean`, `rms` | The 16-bit samples of a buffer, their mean, the volume (optionally after subtracting an offset) |
| `LinearResampler(from_hz, to_hz)` | Linear interpolation chunk by chunk with exact fractions (chunking does not change the output); `reset()` for a new stream |
| `fallback_formats(requested, device_default_rate)` | Requested, then the same layout at the device rate, then (mono) stereo at the device rate; repeats skipped |

## Errors

Domain: `DomainError`, `InvalidAudioFormat`, `CaptureAlreadyActive`, `CaptureNotActive`, `InvalidInputTreatment` (the first three also inherit `ValueError` / `RuntimeError`). Application: `ApplicationError`, `MicrophoneUnavailable`, `StreamCloseFailed`, `StreamReadFailed`, `FormatMismatch`.

## Not introduced

Aggregates beyond `Microphone`, domain events, domain services: there is no evidence that they are needed.
