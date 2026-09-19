from array import array

import pytest

from domain.operations.pcm import downmix_to_mono


def pcm(*samples: int) -> bytes:
    return array("h", samples).tobytes()


def unpcm(data: bytes) -> list[int]:
    out = array("h")
    out.frombytes(data)
    return list(out)


def test_mono_is_returned_untouched():
    data = pcm(1, 2, 3)
    assert downmix_to_mono(data, 1) is data


def test_stereo_frames_are_averaged():
    assert unpcm(downmix_to_mono(pcm(100, 200, 10, 30), 2)) == [150, 20]


def test_average_truncates_toward_zero():
    assert unpcm(downmix_to_mono(pcm(-3, -4, 3, 4), 2)) == [-3, 3]


def test_more_than_two_channels():
    assert unpcm(downmix_to_mono(pcm(3, 6, 9, 0, 0, 3), 3)) == [6, 1]


def test_extreme_values_do_not_overflow():
    assert unpcm(downmix_to_mono(pcm(32767, 32767, -32768, -32768), 2)) == [32767, -32768]


def test_partial_frame_is_rejected():
    with pytest.raises(ValueError):
        downmix_to_mono(pcm(1, 2, 3), 2)


def test_zero_channels_rejected():
    with pytest.raises(ValueError):
        downmix_to_mono(b"", 0)
