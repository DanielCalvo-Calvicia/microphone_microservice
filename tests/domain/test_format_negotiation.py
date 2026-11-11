from domain.operations.format_negotiation import fallback_formats
from domain.value_objects.audio_format import AudioFormat


def test_mono_request_falls_back_to_native_rate_then_stereo():
    requested = AudioFormat(16000, 1, 1024)
    assert fallback_formats(requested, 48000) == (
        AudioFormat(16000, 1, 1024),
        AudioFormat(48000, 1, 1024),
        AudioFormat(48000, 2, 1024),
    )


def test_identical_retry_is_skipped_when_rate_already_native():
    requested = AudioFormat(48000, 1, 512)
    assert fallback_formats(requested, 48000) == (
        AudioFormat(48000, 1, 512),
        AudioFormat(48000, 2, 512),
    )


def test_multichannel_request_has_no_stereo_fallback():
    requested = AudioFormat(16000, 2, 1024)
    assert fallback_formats(requested, 44100) == (
        AudioFormat(16000, 2, 1024),
        AudioFormat(44100, 2, 1024),
    )
