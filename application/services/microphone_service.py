import asyncio
import logging
from typing import Optional

from application.dtos.stream_dtos import StartStreamCommand
from application.ports.microphone_port import AudioStream, MicrophonePort
from application.ports.service_port import ServicePort
from domain.entities.microphone import Microphone
from domain.errors import CaptureNotActive
from domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)


class MicrophoneService(ServicePort):
    """Orchestrates the microphone use cases. Business rules live in the domain."""

    def __init__(self, device: MicrophonePort, name: str = "Microphone") -> None:
        self.name = name
        self._device = device
        self._microphone = Microphone()
        self._stream: Optional[AudioStream] = None
        # start/stop are read-modify-write sequences that await the device.
        self._lock = asyncio.Lock()
        logger.info("MicrophoneService initialized name=%r", name)

    async def start_stream(self, command: StartStreamCommand) -> AudioStream:
        requested = AudioFormat(
            sample_rate=command.sample_rate,
            channels=command.channels,
            chunk_size=command.chunk_size,
        )
        async with self._lock:
            self._microphone.ensure_idle()
            stream = await self._device.open_stream(requested)
            self._microphone.start(requested.with_sample_rate(stream.sample_rate))
            self._stream = stream
        logger.info("Microphone stream started sample_rate=%s", stream.sample_rate)
        return stream

    async def stop_stream(self) -> None:
        async with self._lock:
            if not self._microphone.is_capturing or self._stream is None:
                return
            try:
                await self._stream.close()
            except Exception as error:
                raise RuntimeError(f"Failed to stop microphone stream: {error}") from error
            self._stream = None
            self._microphone.stop()
        logger.info("Microphone stream stopped")

    def is_available(self) -> bool:
        return self._microphone.is_capturing

    def current_stream(self) -> AudioStream:
        if self._stream is None or not self._microphone.is_capturing:
            raise CaptureNotActive("Microphone stream is not active")
        return self._stream
