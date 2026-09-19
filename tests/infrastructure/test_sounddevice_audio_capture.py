"""Adapter tests with a fake ``sounddevice`` module: no hardware or PortAudio needed."""

import asyncio
import importlib
import struct
import sys
import types

import pytest

from application.errors import MicrophoneUnavailable, StreamCloseFailed
from domain.value_objects.audio_format import AudioFormat

MODULE = "infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture"
STREAM_MODULE = "infrastructure.outbound.sounddevice_capture.sounddevice_audio_stream"


class FakeSoundDevice(types.ModuleType):
    def __init__(self, devices=None, default_input=0, unsupported=()):
        super().__init__("sounddevice")
        self.devices = devices if devices is not None else [
            {"name": "Built-in Mic", "max_input_channels": 2, "default_samplerate": 48000.0}
        ]
        self.default = types.SimpleNamespace(device=(default_input, None))
        self.unsupported = set(unsupported)  # {(rate, channels)} the "hardware" rejects
        self.opened: list[tuple[int, int]] = []
        self.streams: list["FakeRaw"] = []
        outer = self

        class RawInputStream:
            def __init__(self, samplerate, blocksize, device, channels, dtype):
                if (samplerate, channels) in outer.unsupported:
                    raise OSError(f"unsupported {samplerate}/{channels}")
                self.samplerate, self.blocksize = samplerate, blocksize
                self.device, self.channels, self.dtype = device, channels, dtype
                self.active = False
                self.stop_calls = 0
                self.close_calls = 0
                self.payload = b""
                outer.opened.append((samplerate, channels))
                outer.streams.append(self)

            def start(self):
                self.active = True

            def stop(self):
                self.stop_calls += 1
                self.active = False

            def close(self):
                self.close_calls += 1

            def read(self, frames):
                return self.payload, False

        self.RawInputStream = RawInputStream

    def query_devices(self, device=None):
        if device is None:
            return self.devices
        return self.devices[device]


@pytest.fixture
def load(monkeypatch):
    def _load(fake: FakeSoundDevice):
        monkeypatch.setitem(sys.modules, "sounddevice", fake)
        monkeypatch.delitem(sys.modules, STREAM_MODULE, raising=False)
        monkeypatch.delitem(sys.modules, MODULE, raising=False)
        return importlib.import_module(MODULE)
    return _load


def open_stream(adapter, fmt):
    return asyncio.run(adapter.open_stream(fmt))


def test_opens_requested_format_when_supported(load):
    fake = FakeSoundDevice()
    mod = load(fake)
    stream = open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(48000, 2, 512))
    assert fake.opened == [(48000, 2)]
    assert stream.sample_rate == 48000


def test_falls_back_to_device_native_rate(load):
    fake = FakeSoundDevice(unsupported={(16000, 1)})
    mod = load(fake)
    stream = open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(16000, 1, 1024))
    assert fake.opened == [(48000, 1)]
    assert stream.sample_rate == 48000


def test_mono_request_falls_back_to_stereo_and_stream_downmixes(load):
    fake = FakeSoundDevice(unsupported={(16000, 1), (48000, 1)})
    mod = load(fake)
    stream = open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(16000, 1, 2))
    assert fake.opened == [(48000, 2)]

    fake.streams[0].payload = struct.pack("<4h", 100, 200, -3, -4)
    chunk = asyncio.run(stream.__anext__())
    assert struct.unpack("<2h", chunk) == (150, -3)


def test_mono_device_is_not_downmixed(load):
    fake = FakeSoundDevice()
    mod = load(fake)
    stream = open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(48000, 1, 2))
    fake.streams[0].payload = struct.pack("<2h", 7, 9)
    assert asyncio.run(stream.__anext__()) == struct.pack("<2h", 7, 9)


def test_raises_last_error_when_every_format_fails(load):
    fake = FakeSoundDevice(unsupported={(16000, 1), (48000, 1), (48000, 2)})
    mod = load(fake)
    with pytest.raises(MicrophoneUnavailable, match="48000/2"):
        open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(16000, 1, 1024))


def test_no_input_device_raises_clear_error(load):
    fake = FakeSoundDevice(devices=[], default_input=None)
    mod = load(fake)
    with pytest.raises(MicrophoneUnavailable, match="Could not open"):
        open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(16000, 1, 1024))


def test_keyword_match_selects_device(load):
    fake = FakeSoundDevice(
        devices=[
            {"name": "Speakers", "max_input_channels": 0, "default_samplerate": 44100.0},
            {"name": "Built-in Mic", "max_input_channels": 2, "default_samplerate": 48000.0},
            {"name": "USB Podcast Mic", "max_input_channels": 1, "default_samplerate": 44100.0},
        ],
        default_input=1,
    )
    mod = load(fake)
    open_stream(
        mod.SoundDeviceAudioCapture(target_keywords=["podcast"], show_meter=False),
        AudioFormat(44100, 1, 256),
    )
    assert fake.streams[0].device == 2


def test_os_default_input_used_without_keyword_match(load):
    fake = FakeSoundDevice()
    mod = load(fake)
    open_stream(mod.SoundDeviceAudioCapture(target_keywords=["nope"], show_meter=False), AudioFormat(48000, 2, 8))
    assert fake.streams[0].device == 0


def test_close_releases_hardware_once_and_ends_iteration(load):
    fake = FakeSoundDevice()
    mod = load(fake)
    stream = open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(48000, 2, 8))
    raw = fake.streams[0]

    asyncio.run(stream.close())
    asyncio.run(stream.close())

    assert (raw.stop_calls, raw.close_calls) == (1, 1)
    with pytest.raises(StopAsyncIteration):
        asyncio.run(stream.__anext__())


def test_close_error_is_translated_to_stream_close_failed_and_hardware_still_released(load):
    fake = FakeSoundDevice()
    mod = load(fake)
    stream = open_stream(mod.SoundDeviceAudioCapture(show_meter=False), AudioFormat(48000, 2, 8))
    raw = fake.streams[0]

    def broken_stop():
        raise OSError("device gone")

    raw.stop = broken_stop
    with pytest.raises(StreamCloseFailed, match="device gone"):
        asyncio.run(stream.close())
    assert raw.close_calls == 1
