import asyncio
from typing import AsyncIterator, Optional

import pytest

from application.dtos.stream_dtos import StartStreamCommand
from application.ports.microphone_port import AudioStream, MicrophonePort
from application.services.microphone_service import MicrophoneService
from domain.errors import CaptureAlreadyActive, CaptureNotActive, InvalidAudioFormat
from domain.value_objects.audio_format import AudioFormat


class FakeStream(AudioStream):
    def __init__(self, sample_rate: int, chunks: int = 3, fail_on_close: bool = False):
        self._sample_rate = sample_rate
        self._chunks = chunks
        self._fail_on_close = fail_on_close
        self.close_calls = 0

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def __aiter__(self) -> AsyncIterator[bytes]:
        async def gen():
            for _ in range(self._chunks):
                yield b"\x01\x00" * 4
        return gen()

    async def close(self) -> None:
        self.close_calls += 1
        if self._fail_on_close:
            raise OSError("device busy")


class FakePort(MicrophonePort):
    def __init__(self, negotiated_rate: Optional[int] = None, error: Optional[Exception] = None):
        self.negotiated_rate = negotiated_rate
        self.error = error
        self.opened: list[AudioFormat] = []
        self.streams: list[FakeStream] = []
        self.stream_kwargs: dict = {}

    async def open_stream(self, audio_format: AudioFormat) -> AudioStream:
        await asyncio.sleep(0)  # yield, like real device I/O would
        if self.error:
            raise self.error
        self.opened.append(audio_format)
        stream = FakeStream(self.negotiated_rate or audio_format.sample_rate, **self.stream_kwargs)
        self.streams.append(stream)
        return stream


def run(coro):
    return asyncio.run(coro)


def test_start_opens_device_with_requested_format_and_marks_available():
    async def scenario():
        port = FakePort()
        service = MicrophoneService(port)
        assert not service.is_available()

        stream = await service.start_stream(StartStreamCommand(8000, 1, 256))

        assert port.opened == [AudioFormat(8000, 1, 256)]
        assert stream.sample_rate == 8000
        assert service.is_available()
        assert service.current_stream() is stream

    run(scenario())


def test_start_reports_the_sample_rate_negotiated_by_the_device():
    async def scenario():
        service = MicrophoneService(FakePort(negotiated_rate=48000))
        stream = await service.start_stream(StartStreamCommand(16000, 1, 1024))
        assert stream.sample_rate == 48000

    run(scenario())


def test_invalid_parameters_are_rejected_before_touching_the_device():
    async def scenario():
        port = FakePort()
        service = MicrophoneService(port)
        with pytest.raises(InvalidAudioFormat):
            await service.start_stream(StartStreamCommand(0, 1, 1024))
        assert port.opened == []
        assert not service.is_available()

    run(scenario())


def test_second_start_is_rejected_and_device_opened_once():
    async def scenario():
        port = FakePort()
        service = MicrophoneService(port)
        await service.start_stream(StartStreamCommand())
        with pytest.raises(CaptureAlreadyActive):
            await service.start_stream(StartStreamCommand())
        assert len(port.opened) == 1

    run(scenario())


def test_concurrent_starts_only_one_wins():
    async def scenario():
        port = FakePort()
        service = MicrophoneService(port)
        results = await asyncio.gather(
            service.start_stream(StartStreamCommand()),
            service.start_stream(StartStreamCommand()),
            return_exceptions=True,
        )
        assert sum(isinstance(r, CaptureAlreadyActive) for r in results) == 1
        assert len(port.opened) == 1

    run(scenario())


def test_failed_open_leaves_service_idle_and_restartable():
    async def scenario():
        port = FakePort(error=RuntimeError("No microphone devices available"))
        service = MicrophoneService(port)
        with pytest.raises(RuntimeError):
            await service.start_stream(StartStreamCommand())
        assert not service.is_available()

        port.error = None
        await service.start_stream(StartStreamCommand())
        assert service.is_available()

    run(scenario())


def test_stop_closes_stream_and_returns_to_idle():
    async def scenario():
        port = FakePort()
        service = MicrophoneService(port)
        await service.start_stream(StartStreamCommand())

        await service.stop_stream()

        assert port.streams[0].close_calls == 1
        assert not service.is_available()
        with pytest.raises(CaptureNotActive):
            service.current_stream()

    run(scenario())


def test_stop_when_idle_is_a_noop_and_repeatable():
    async def scenario():
        service = MicrophoneService(FakePort())
        await service.stop_stream()
        await service.stop_stream()
        assert not service.is_available()

    run(scenario())


def test_stop_failure_is_reported_and_keeps_capture_active():
    async def scenario():
        port = FakePort()
        port.stream_kwargs = {"fail_on_close": True}
        service = MicrophoneService(port)
        await service.start_stream(StartStreamCommand())
        with pytest.raises(RuntimeError, match="Failed to stop microphone stream"):
            await service.stop_stream()
        assert service.is_available()

    run(scenario())


def test_can_restart_after_stop():
    async def scenario():
        port = FakePort()
        service = MicrophoneService(port)
        await service.start_stream(StartStreamCommand())
        await service.stop_stream()
        await service.start_stream(StartStreamCommand())
        assert len(port.opened) == 2

    run(scenario())
