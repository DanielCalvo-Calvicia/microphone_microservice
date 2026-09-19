"""Adapter tests against a fake ``AudioDriver``: no hardware, no sounddevice, no monkeypatching."""

import asyncio
import struct
from typing import Any

import pytest

from application.errors import MicrophoneUnavailable, StreamCloseFailed, StreamReadFailed
from domain.value_objects.audio_format import AudioFormat
from infrastructure.outbound.sounddevice_capture.audio_driver import DeviceInfo
from infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture import (
    SoundDeviceAudioCapture,
)
from infrastructure.outbound.sounddevice_capture.sounddevice_device_selector import (
    DeviceSelector,
)

BUILT_IN = DeviceInfo(0, "Built-in Mic", 2, 48000)


class FakeRaw:
    def __init__(self, device: int, channels: int) -> None:
        self.device = device
        self.channels = channels
        self.active = True
        self.stop_calls = 0
        self.close_calls = 0
        self.payload = b""
        self.read_error: Exception | None = None
        self.stop_error: Exception | None = None

    def read(self, frames: int) -> tuple[bytes, bool]:
        if self.read_error:
            raise self.read_error
        return self.payload, False

    def stop(self) -> None:
        self.stop_calls += 1
        self.active = False
        if self.stop_error:
            raise self.stop_error

    def close(self) -> None:
        self.close_calls += 1


class FakeDriver:
    def __init__(
        self,
        devices: list[DeviceInfo] | None = None,
        default_input: int | None = 0,
        unsupported: tuple[tuple[int, int], ...] = (),
    ) -> None:
        self.devices = [BUILT_IN] if devices is None else devices
        self.default_input = default_input
        self.unsupported = set(unsupported)  # {(rate, channels)} the "hardware" rejects
        self.opened: list[tuple[int, int]] = []
        self.streams: list[FakeRaw] = []

    def input_devices(self) -> list[DeviceInfo]:
        return self.devices

    def default_input_index(self) -> int | None:
        return self.default_input

    def device_info(self, index: int) -> DeviceInfo:
        return self.devices[index]

    def open_input(self, index: int, audio_format: AudioFormat) -> FakeRaw:
        key = (audio_format.sample_rate, audio_format.channels)
        if key in self.unsupported:
            raise OSError(f"unsupported {key[0]}/{key[1]}")
        self.opened.append(key)
        raw = FakeRaw(index, audio_format.channels)
        self.streams.append(raw)
        return raw


def capture(driver: FakeDriver, keywords: tuple[str, ...] = ()) -> SoundDeviceAudioCapture:
    return SoundDeviceAudioCapture(driver, DeviceSelector(driver, keywords), show_meter=False)


def open_stream(adapter: SoundDeviceAudioCapture, fmt: AudioFormat) -> Any:
    return asyncio.run(adapter.open_stream(fmt))


def test_opens_requested_format_when_supported():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 2, 512))
    assert driver.opened == [(48000, 2)]
    assert stream.sample_rate == 48000


def test_falls_back_to_device_native_rate():
    driver = FakeDriver(unsupported=((16000, 1),))
    stream = open_stream(capture(driver), AudioFormat(16000, 1, 1024))
    assert driver.opened == [(48000, 1)]
    assert stream.sample_rate == 48000


def test_mono_request_falls_back_to_stereo_and_stream_downmixes():
    driver = FakeDriver(unsupported=((16000, 1), (48000, 1)))
    stream = open_stream(capture(driver), AudioFormat(16000, 1, 2))
    assert driver.opened == [(48000, 2)]

    driver.streams[0].payload = struct.pack("<4h", 100, 200, -3, -4)
    chunk = asyncio.run(stream.__anext__())
    assert struct.unpack("<2h", chunk) == (150, -3)


def test_mono_device_is_not_downmixed():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 1, 2))
    driver.streams[0].payload = struct.pack("<2h", 7, 9)
    assert asyncio.run(stream.__anext__()) == struct.pack("<2h", 7, 9)


def test_unknown_device_rate_uses_the_configured_fallback_rate():
    driver = FakeDriver(devices=[DeviceInfo(0, "Mic", 1, None)], unsupported=((8000, 1),))
    open_stream(capture(driver), AudioFormat(8000, 1, 256))
    assert driver.opened == [(16000, 1)]


def test_raises_unavailable_with_last_error_when_every_format_fails():
    driver = FakeDriver(unsupported=((16000, 1), (48000, 1), (48000, 2)))
    with pytest.raises(MicrophoneUnavailable, match="48000/2"):
        open_stream(capture(driver), AudioFormat(16000, 1, 1024))


def test_no_input_device_raises_unavailable():
    driver = FakeDriver(devices=[], default_input=None)
    with pytest.raises(MicrophoneUnavailable, match="Could not open"):
        open_stream(capture(driver), AudioFormat(16000, 1, 1024))


def test_close_releases_hardware_once_and_ends_iteration():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 2, 8))
    raw = driver.streams[0]

    asyncio.run(stream.close())
    asyncio.run(stream.close())

    assert (raw.stop_calls, raw.close_calls) == (1, 1)
    with pytest.raises(StopAsyncIteration):
        asyncio.run(stream.__anext__())


def test_close_error_is_translated_and_hardware_still_released():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 2, 8))
    raw = driver.streams[0]
    raw.stop_error = OSError("device gone")

    with pytest.raises(StreamCloseFailed, match="device gone"):
        asyncio.run(stream.close())
    assert raw.close_calls == 1


def test_read_failure_raises_releases_device_and_notifies_listener():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 1, 8))
    raw = driver.streams[0]
    raw.read_error = OSError("device unplugged")
    terminated: list[bool] = []
    stream.on_terminated(lambda: terminated.append(True))

    with pytest.raises(StreamReadFailed, match="device unplugged"):
        asyncio.run(stream.__anext__())

    assert terminated == [True]
    assert raw.close_calls == 1
    with pytest.raises(StopAsyncIteration):
        asyncio.run(stream.__anext__())


def test_consumer_cancellation_releases_device_and_notifies_listener():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 1, 8))
    raw = driver.streams[0]
    terminated: list[bool] = []
    stream.on_terminated(lambda: terminated.append(True))

    async def scenario() -> None:
        task = asyncio.ensure_future(stream.__anext__())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    raw.payload = b"\x00\x00"
    asyncio.run(scenario())

    assert terminated == [True]
    assert raw.close_calls == 1


def test_explicit_close_does_not_fire_the_termination_listener():
    driver = FakeDriver()
    stream = open_stream(capture(driver), AudioFormat(48000, 1, 8))
    terminated: list[bool] = []
    stream.on_terminated(lambda: terminated.append(True))

    asyncio.run(stream.close())

    assert terminated == []


def test_keyword_match_selects_device():
    driver = FakeDriver(
        devices=[
            DeviceInfo(0, "Speakers", 0, 44100),
            DeviceInfo(1, "Built-in Mic", 2, 48000),
            DeviceInfo(2, "USB Podcast Mic", 1, 44100),
        ],
        default_input=1,
    )
    open_stream(capture(driver, ("podcast",)), AudioFormat(44100, 1, 256))
    assert driver.streams[0].device == 2


def test_os_default_input_used_without_keyword_match():
    driver = FakeDriver()
    open_stream(capture(driver, ("nope",)), AudioFormat(48000, 2, 8))
    assert driver.streams[0].device == 0
