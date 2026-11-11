import pytest

from domain.entities.microphone import Microphone
from domain.errors import CaptureAlreadyActive, CaptureNotActive
from domain.value_objects.audio_format import AudioFormat

FMT = AudioFormat(16000, 1, 1024)


def test_new_microphone_is_idle():
    mic = Microphone()
    assert not mic.is_capturing
    with pytest.raises(CaptureNotActive):
        mic.active_format


def test_start_enters_capturing_state_with_format():
    mic = Microphone()
    mic.start(FMT)
    assert mic.is_capturing
    assert mic.active_format == FMT


def test_cannot_start_twice():
    mic = Microphone()
    mic.start(FMT)
    with pytest.raises(CaptureAlreadyActive):
        mic.start(FMT)
    with pytest.raises(CaptureAlreadyActive):
        mic.ensure_idle()
    assert mic.active_format == FMT


def test_stop_returns_to_idle_and_allows_restart():
    mic = Microphone()
    mic.start(FMT)
    mic.stop()
    assert not mic.is_capturing
    mic.start(FMT.with_sample_rate(48000))
    assert mic.active_format.sample_rate == 48000


def test_stop_when_idle_is_a_noop():
    mic = Microphone()
    mic.stop()
    assert not mic.is_capturing
