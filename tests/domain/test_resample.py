from array import array

import pytest

from domain.operations.level import samples_of
from domain.operations.resample import LinearResampler


def _pcm(values) -> bytes:
    return array("h", values).tobytes()


def _convert(resampler: LinearResampler, pcm: bytes, chunk_samples: int) -> list[int]:
    out: list[int] = []
    for start in range(0, len(pcm), chunk_samples * 2):
        out += list(samples_of(resampler.process(pcm[start : start + chunk_samples * 2])))
    return out


def test_downsampling_by_two_keeps_every_other_sample():
    out = LinearResampler(1000, 500).process(_pcm([0, 10, 20, 30, 40, 50]))

    assert list(samples_of(out)) == [0, 20, 40]


def test_upsampling_by_two_interpolates_the_middle():
    out = LinearResampler(500, 1000).process(_pcm([0, 100, 200]))

    assert list(samples_of(out)) == [0, 50, 100, 150]


@pytest.mark.parametrize("chunk_samples", [1, 3, 7, 64])
def test_the_chunks_it_is_fed_in_do_not_change_the_result(chunk_samples):
    pcm = _pcm([(i * 37) % 2000 - 1000 for i in range(500)])

    whole = _convert(LinearResampler(44100, 16000), pcm, 500)
    chunked = _convert(LinearResampler(44100, 16000), pcm, chunk_samples)

    assert chunked == whole
    assert len(whole) == pytest.approx(500 * 16000 / 44100, abs=2)


def test_reset_starts_an_independent_stream():
    resampler = LinearResampler(1000, 500)
    resampler.process(_pcm([0, 10, 20]))
    resampler.reset()

    assert list(samples_of(resampler.process(_pcm([5, 15, 25, 35])))) == [5, 25]


def test_a_rate_of_zero_is_refused():
    with pytest.raises(ValueError):
        LinearResampler(0, 16000)
