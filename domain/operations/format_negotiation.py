from domain.value_objects.audio_format import AudioFormat


def fallback_formats(requested: AudioFormat, device_default_rate: int) -> tuple[AudioFormat, ...]:
    """Ordered list of formats to try when opening the device.

    1. exactly what was requested;
    2. the same layout at the device's native sample rate;
    3. for a mono request, stereo at the native rate (mono-only capture is
       rejected by many drivers; the stereo signal is downmixed afterwards).

    Candidates that would repeat an earlier one are skipped.
    """
    candidates = [requested]

    at_native_rate = requested.with_sample_rate(device_default_rate)
    if at_native_rate != requested:
        candidates.append(at_native_rate)

    if requested.channels == 1:
        candidates.append(at_native_rate.with_channels(2))

    return tuple(candidates)
