from array import array

import pytest

from domain.entities.utterance_segmenter import UtteranceSegmenter
from domain.operations.level import samples_of
from domain.value_objects.input_treatment import InputTreatment

RATE = 1000
CHUNK = 50  # samples: 0.05 s, so a silence limit of 0.1 s is two silent chunks


def _tone(amplitude: int, samples: int = CHUNK) -> bytes:
    return array("h", [amplitude, -amplitude] * (samples // 2)).tobytes()


SILENCE = _tone(0)


def _treatment(**overrides) -> InputTreatment:
    # the plain cutting; each test switches on the treatment it is about
    settings = {
        "silence_threshold": 100,
        "silence_limit_seconds": 0.1,
        "speech_start_factor": 2.0,
        "volume_smoothing": False,
        "noise_floor_tracking": False,
        "dc_offset_removal": False,
        "preroll_seconds": 0.0,
    }
    settings.update(overrides)
    return InputTreatment(**settings)


def _feed(segmenter: UtteranceSegmenter, *chunks: bytes) -> list[bytes]:
    out: list[bytes] = []
    for chunk in chunks:
        out += segmenter.feed(chunk)
    return out


def test_silence_alone_is_never_an_utterance():
    segmenter = UtteranceSegmenter(_treatment(), RATE)

    assert _feed(segmenter, *[SILENCE] * 20) == []
    assert segmenter.flush() is None


def test_speech_then_enough_silence_is_one_utterance_with_the_silence_that_ended_it():
    segmenter = UtteranceSegmenter(_treatment(), RATE)
    loud = _tone(1000)

    out = _feed(segmenter, SILENCE, loud, loud, loud, SILENCE, SILENCE, SILENCE)

    assert out == [loud * 3 + SILENCE * 2]  # the first silence is before the speech; the third is after the end
    assert segmenter.is_speaking is False


def test_a_pause_shorter_than_the_silence_limit_stays_inside_the_utterance():
    segmenter = UtteranceSegmenter(_treatment(), RATE)
    loud = _tone(1000)

    out = _feed(segmenter, loud, SILENCE, loud, SILENCE, SILENCE)

    assert out == [loud + SILENCE + loud + SILENCE * 2]


def test_two_utterances_come_out_in_order():
    segmenter = UtteranceSegmenter(_treatment(), RATE)
    first, second = _tone(1000), _tone(2000)

    out = _feed(segmenter, first, SILENCE, SILENCE, second, SILENCE, SILENCE)

    assert out == [first + SILENCE * 2, second + SILENCE * 2]


def test_the_stream_ending_mid_utterance_hands_over_what_there_is():
    segmenter = UtteranceSegmenter(_treatment(), RATE)
    loud = _tone(1000)

    assert _feed(segmenter, loud, loud) == []
    assert segmenter.is_speaking is True
    assert segmenter.flush() == loud * 2
    assert segmenter.flush() is None


def test_speech_must_reach_the_threshold_times_the_start_factor_to_start():
    quiet_blip = _tone(150)  # over the silence threshold (100), under the start volume (200)

    assert _feed(UtteranceSegmenter(_treatment(speech_start_factor=2.0), RATE), quiet_blip, quiet_blip) == []
    started = UtteranceSegmenter(_treatment(speech_start_factor=1.0), RATE)
    _feed(started, quiet_blip)
    assert started.is_speaking is True


def test_volume_smoothing_ignores_a_single_loud_click():
    click = _tone(1500)  # smoothed with the default weight 0.1 it is only 150: under the start volume of 200

    smoothed = UtteranceSegmenter(_treatment(volume_smoothing=True), RATE)
    raw = UtteranceSegmenter(_treatment(volume_smoothing=False), RATE)
    smoothed.feed(click)
    raw.feed(click)

    assert (smoothed.is_speaking, raw.is_speaking) == (False, True)


def test_noise_floor_tracking_lifts_the_start_volume_above_the_room_noise():
    ambient, voice = _tone(80), _tone(250)  # 250 beats 3 x the floor (240); 220 only beats 100 x 2

    tracking = UtteranceSegmenter(_treatment(noise_floor_tracking=True), RATE)
    plain = UtteranceSegmenter(_treatment(noise_floor_tracking=False), RATE)
    for segmenter in (tracking, plain):
        _feed(segmenter, ambient, ambient, voice)

    assert plain.is_speaking is True
    assert tracking.is_speaking is True  # 250 > 240: a clear voice still gets through
    quiet_voice = _tone(220)
    tracking2 = UtteranceSegmenter(_treatment(noise_floor_tracking=True), RATE)
    plain2 = UtteranceSegmenter(_treatment(noise_floor_tracking=False), RATE)
    for segmenter in (tracking2, plain2):
        _feed(segmenter, ambient, ambient, quiet_voice)
    assert (tracking2.is_speaking, plain2.is_speaking) == (False, True)  # 220 is over 200 but under 3 x 80


def test_dc_offset_removal_lets_a_constant_offset_count_as_silence():
    shifted = array("h", [300] * CHUNK).tobytes()  # no sound at all, only a constant shift of the signal

    with_removal = UtteranceSegmenter(_treatment(dc_offset_removal=True), RATE)
    without = UtteranceSegmenter(_treatment(dc_offset_removal=False), RATE)
    out_with = _feed(with_removal, *[shifted] * 120)
    out_without = _feed(without, *[shifted] * 120)

    assert len(out_with) == 1  # the offset is learnt, the signal falls silent and the utterance ends
    assert out_without == []  # a constant 300 is as loud as speech and never ends
    assert without.is_speaking is True


def test_resampling_changes_the_rate_and_the_length_of_what_comes_out():
    segmenter = UtteranceSegmenter(_treatment(resample_to_hz=500), RATE)
    loud = _tone(1000)

    out = _feed(segmenter, loud, SILENCE, SILENCE)

    assert segmenter.output_sample_rate == 500
    assert len(samples_of(out[0])) == pytest.approx(3 * CHUNK / 2, abs=2)


def test_resampling_to_the_rate_it_already_has_does_nothing():
    segmenter = UtteranceSegmenter(_treatment(resample_to_hz=RATE), RATE)

    assert segmenter.output_sample_rate == RATE
    assert _feed(segmenter, _tone(1000), SILENCE, SILENCE) == [_tone(1000) + SILENCE * 2]


def test_a_rate_that_is_not_positive_is_refused():
    with pytest.raises(ValueError):
        UtteranceSegmenter(_treatment(), 0)


# --------------------------------------------------------------------------- pre-roll: the chunks heard before the utterance starts


def _numbered(n: int) -> bytes:
    """A quiet chunk of its own value, so a test can tell which chunks came out."""
    return array("h", [n] * CHUNK).tobytes()


def test_the_pre_roll_is_put_in_front_of_the_utterance():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.1), RATE)  # 0.1 s = two chunks of 50 samples
    loud = _tone(1000)
    before = [_numbered(n) for n in (1, 2, 3, 4)]

    out = _feed(segmenter, *before, loud, SILENCE, SILENCE)

    assert out == [before[2] + before[3] + loud + SILENCE * 2]  # only the last two quiet chunks: the pre-roll, not the whole past


def test_with_no_pre_roll_the_utterance_starts_at_the_chunk_that_reached_the_start_volume():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.0), RATE)
    loud = _tone(1000)

    assert _feed(segmenter, _numbered(1), _numbered(2), loud, SILENCE, SILENCE) == [loud + SILENCE * 2]


def test_the_pre_roll_is_whole_chunks_and_at_least_the_time_asked():
    # 0.06 s = 60 samples: one chunk (50) is not enough, so two are kept
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.06), RATE)
    loud = _tone(1000)
    before = [_numbered(n) for n in (1, 2, 3)]

    out = _feed(segmenter, *before, loud, SILENCE, SILENCE)

    assert out == [before[1] + before[2] + loud + SILENCE * 2]


def test_a_short_past_gives_a_short_pre_roll():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.5), RATE)  # ten chunks wanted, only one has been heard
    loud = _tone(1000)

    assert _feed(segmenter, _numbered(1), loud, SILENCE, SILENCE) == [_numbered(1) + loud + SILENCE * 2]


def test_the_silence_that_ended_an_utterance_is_not_the_pre_roll_of_the_next_one():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.1), RATE)
    first, second = _tone(1000), _tone(2000)

    out = _feed(segmenter, first, SILENCE, SILENCE, second, SILENCE, SILENCE)

    assert out == [first + SILENCE * 2, second + SILENCE * 2]  # nothing was heard between them, so nothing is prepended


def test_the_quiet_between_two_utterances_is_what_pre_rolls_the_second():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.05), RATE)
    first, second = _tone(1000), _tone(2000)
    gap = _numbered(7)

    out = _feed(segmenter, first, SILENCE, SILENCE, gap, gap, second, SILENCE, SILENCE)

    assert out == [first + SILENCE * 2, gap + second + SILENCE * 2]  # the last quiet chunk before the second utterance, once


def test_the_pre_roll_buffer_does_not_grow_with_a_long_quiet():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.1), RATE)

    _feed(segmenter, *[_numbered(n % 90) for n in range(10_000)])

    assert len(segmenter._recent) == 2  # noqa: SLF001 - the bound is the point: two chunks of 50 samples cover 0.1 s
    assert segmenter._recent_samples == 2 * CHUNK  # noqa: SLF001


def test_a_late_start_caused_by_smoothing_is_covered_by_the_pre_roll():
    # smoothed with the weight 0.1 a loud voice needs several chunks to reach the start volume; those chunks must not be lost
    voice = _tone(3000)
    smoothing = {"volume_smoothing": True, "volume_smoothing_factor": 0.1}
    without = UtteranceSegmenter(_treatment(preroll_seconds=0.0, **smoothing), RATE)
    with_pre_roll = UtteranceSegmenter(_treatment(preroll_seconds=0.25, **smoothing), RATE)
    chunks = [SILENCE, SILENCE, SILENCE, SILENCE, SILENCE] + [voice] * 12 + [SILENCE] * 80

    out_without, out_with = _feed(without, *chunks), _feed(with_pre_roll, *chunks)

    assert len(out_without) == len(out_with) == 1
    assert len(out_with[0]) > len(out_without[0])  # the pre-roll added audio
    assert out_with[0].endswith(out_without[0])  # ... in front, and nothing else changed
    first_voice = out_with[0].index(voice[:8])
    assert first_voice >= 0  # the whole voice is in the utterance, with quiet chunks before it


def test_the_pre_roll_is_resampled_with_the_utterance():
    segmenter = UtteranceSegmenter(_treatment(resample_to_hz=500, preroll_seconds=0.05), RATE)  # one chunk of pre-roll
    loud = _tone(1000)

    out = _feed(segmenter, _numbered(5), loud, SILENCE, SILENCE)

    assert len(samples_of(out[0])) == pytest.approx(4 * CHUNK / 2, abs=2)  # pre-roll + loud + two silent chunks, halved


def test_the_stream_ending_mid_utterance_hands_over_the_pre_roll_too():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.05), RATE)
    loud = _tone(1000)

    _feed(segmenter, _numbered(3), _numbered(4), loud)

    assert segmenter.flush() == _numbered(4) + loud


def test_a_pre_roll_does_not_make_silence_an_utterance():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=1.0), RATE)

    assert _feed(segmenter, *[SILENCE] * 50) == []
    assert segmenter.flush() is None


def test_a_fraction_of_a_sample_of_pre_roll_rounds_up():
    # 0.0505 s at 1000 Hz is 50.5 samples: one chunk of 50 is short of it, so two are kept
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.0505), RATE)
    loud = _tone(1000)
    before = [_numbered(n) for n in (1, 2, 3)]

    out = _feed(segmenter, *before, loud, SILENCE, SILENCE)

    assert out == [before[1] + before[2] + loud + SILENCE * 2]


def test_chunks_heard_before_one_utterance_never_leak_into_the_next_one():
    segmenter = UtteranceSegmenter(_treatment(preroll_seconds=0.05), RATE)
    first, second = _tone(1000), _tone(2000)
    x, y = _numbered(3), _numbered(4)

    out = _feed(segmenter, x, first, SILENCE, SILENCE, y, second, SILENCE, SILENCE)

    assert out == [x + first + SILENCE * 2, y + second + SILENCE * 2]
