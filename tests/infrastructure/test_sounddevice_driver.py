"""The real driver against a fake ``sounddevice`` module: only the mapping is under test."""

import importlib
import sys
import types

import pytest

from domain.value_objects.audio_format import AudioFormat

MODULE = "infrastructure.outbound.sounddevice_capture.sounddevice_driver"


class FakeRawInputStream:
    instances: list["FakeRawInputStream"] = []
    fail_on_start = False

    def __init__(self, samplerate, blocksize, device, channels, dtype):
        self.args = (samplerate, blocksize, device, channels, dtype)
        self.started = False
        self.closed = False
        FakeRawInputStream.instances.append(self)

    def start(self):
        if FakeRawInputStream.fail_on_start:
            raise OSError("cannot start")
        self.started = True

    def close(self):
        self.closed = True


@pytest.fixture
def driver(monkeypatch):
    FakeRawInputStream.instances = []
    FakeRawInputStream.fail_on_start = False
    fake = types.ModuleType("sounddevice")
    fake.RawInputStream = FakeRawInputStream
    fake.default = types.SimpleNamespace(device=(1, None))
    devices = [
        {"name": "Speakers", "max_input_channels": 0, "default_samplerate": 44100.0},
        {"name": "Mic", "max_input_channels": 2},
    ]
    fake.query_devices = lambda device=None: devices if device is None else devices[device]
    monkeypatch.setitem(sys.modules, "sounddevice", fake)
    monkeypatch.delitem(sys.modules, MODULE, raising=False)
    return importlib.import_module(MODULE).SoundDeviceDriver()


def test_lists_devices_with_indexes_and_optional_rate(driver):
    devices = driver.input_devices()
    assert [(d.index, d.name, d.max_input_channels, d.default_samplerate) for d in devices] == [
        (0, "Speakers", 0, 44100),
        (1, "Mic", 2, None),
    ]


def test_default_input_and_device_info(driver):
    assert driver.default_input_index() == 1
    assert driver.device_info(1).name == "Mic"


def test_open_input_starts_an_int16_stream(driver):
    raw = driver.open_input(1, AudioFormat(16000, 2, 512))
    assert raw.args == (16000, 512, 1, 2, "int16") and raw.started


def test_open_input_closes_the_stream_when_start_fails(driver):
    FakeRawInputStream.fail_on_start = True
    with pytest.raises(OSError, match="cannot start"):
        driver.open_input(1, AudioFormat(16000, 1, 512))
    assert FakeRawInputStream.instances[0].closed
