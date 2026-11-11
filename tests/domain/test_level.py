from array import array

import pytest

from domain.operations.level import mean, rms, samples_of


def _pcm(*values: int) -> bytes:
    return array("h", values).tobytes()


def test_samples_are_read_from_pcm_and_a_trailing_odd_byte_is_ignored():
    assert list(samples_of(_pcm(1, -2, 3))) == [1, -2, 3]
    assert list(samples_of(_pcm(1, -2) + b"\x07")) == [1, -2]


def test_rms_is_the_volume_of_the_samples():
    assert rms(samples_of(_pcm(100, -100, 100, -100))) == pytest.approx(100.0)
    assert rms(samples_of(_pcm(0, 0, 0))) == 0.0
    assert rms(array("h")) == 0.0


def test_rms_after_subtracting_an_offset_ignores_a_constant_shift():
    assert rms(samples_of(_pcm(310, 290, 310, 290)), offset=300.0) == pytest.approx(10.0)


def test_mean_of_no_samples_is_zero():
    assert mean(samples_of(_pcm(2, 4))) == 3.0
    assert mean(array("h")) == 0.0
