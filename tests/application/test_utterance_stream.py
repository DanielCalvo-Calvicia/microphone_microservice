import asyncio
from array import array

import pytest

from application.services.utterance_stream import utterances_of
from domain.entities.utterance_segmenter import UtteranceSegmenter
from domain.value_objects.input_treatment import InputTreatment

RATE = 1000
LOUD = array("h", [1000, -1000] * 25).tobytes()
SILENCE = bytes(100)


def _segmenter() -> UtteranceSegmenter:
    treatment = InputTreatment(
        silence_threshold=100, silence_limit_seconds=0.1, volume_smoothing=False, noise_floor_tracking=False
    )
    return UtteranceSegmenter(treatment, RATE)


async def _chunks(*items: bytes, then_fail: bool = False):
    for item in items:
        yield item
    if then_fail:
        raise RuntimeError("device unplugged")


def _collect(chunks) -> list[bytes]:
    async def run() -> list[bytes]:
        return [utterance async for utterance in utterances_of(chunks, _segmenter())]

    return asyncio.run(run())


def test_each_finished_utterance_comes_out_of_the_live_capture():
    out = _collect(_chunks(LOUD, SILENCE, SILENCE, LOUD, SILENCE, SILENCE))

    assert out == [LOUD + SILENCE * 2, LOUD + SILENCE * 2]


def test_when_the_capture_closes_mid_utterance_that_utterance_is_still_handed_over():
    assert _collect(_chunks(LOUD, LOUD)) == [LOUD * 2]


def test_a_capture_that_fails_raises_and_does_not_hand_over_a_half_utterance():
    async def run() -> list[bytes]:
        got: list[bytes] = []
        async for utterance in utterances_of(_chunks(LOUD, SILENCE, SILENCE, LOUD, then_fail=True), _segmenter()):
            got.append(utterance)
        return got

    with pytest.raises(RuntimeError, match="device unplugged"):
        asyncio.run(run())
