import dataclasses

import pytest

from domain.errors import InvalidAudioFormat
from domain.value_objects.audio_format import AudioFormat


def test_valid_format_keeps_values():
    fmt = AudioFormat(sample_rate=16000, channels=1, chunk_size=1024)
    assert (fmt.sample_rate, fmt.channels, fmt.chunk_size) == (16000, 1, 1024)


@pytest.mark.parametrize(
    "rate,channels,chunk",
    [(0, 1, 1024), (-1, 1, 1024), (16000, 0, 1024), (16000, 1, 0), (16000, 1, -5)],
)
def test_non_positive_values_are_rejected(rate, channels, chunk):
    with pytest.raises(InvalidAudioFormat):
        AudioFormat(rate, channels, chunk)


def test_invalid_format_is_also_a_value_error():
    with pytest.raises(ValueError):
        AudioFormat(0, 1, 1)


def test_is_immutable_and_value_equal():
    fmt = AudioFormat(16000, 1, 1024)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fmt.sample_rate = 8000  # type: ignore[misc]
    assert fmt == AudioFormat(16000, 1, 1024)


def test_with_helpers_return_new_instances():
    fmt = AudioFormat(16000, 1, 1024)
    assert fmt.with_sample_rate(48000) == AudioFormat(48000, 1, 1024)
    assert fmt.with_channels(2) == AudioFormat(16000, 2, 1024)
    assert fmt == AudioFormat(16000, 1, 1024)
