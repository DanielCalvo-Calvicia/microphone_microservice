import asyncio
import logging

from application.dtos.start_stream_inbound import StartStreamInboundDTO
from application.dtos.stream_outbound import StreamOutboundDTO
from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.entities.microphone import Microphone
from domain.errors import CaptureNotActive
from domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)


class MicrophoneService(MicrophoneStreamingPort):
    """Orchestrates the microphone use cases. Business rules live in the domain."""

    def __init__(self, capture: AudioCapturePort, name: str = "Microphone") -> None:
        self.name = name
        self._capture = capture
        self._microphone = Microphone()
        self._stream: AudioStreamPort | None = None
        # start/stop are read-modify-write sequences that await the device.
        self._lock = asyncio.Lock()
        logger.info("MicrophoneService initialized name=%r", name)

    async def start_stream(self, request: StartStreamInboundDTO) -> StreamOutboundDTO:
        requested = AudioFormat(
            sample_rate=request.sample_rate,
            channels=request.channels,
            chunk_size=request.chunk_size,
        )
        async with self._lock:
            self._microphone.ensure_idle()
            stream = await self._capture.open_stream(requested)
            self._microphone.start(requested.with_sample_rate(stream.sample_rate))
            self._stream = stream
        logger.info("Microphone stream started sample_rate=%s", stream.sample_rate)
        return StreamOutboundDTO(sample_rate=stream.sample_rate, stream=stream)

    async def stop_stream(self) -> None:
        async with self._lock:
            if not self._microphone.is_capturing or self._stream is None:
                return
            await self._stream.close()  # StreamCloseFailed propagates; capture stays active
            self._stream = None
            self._microphone.stop()
        logger.info("Microphone stream stopped")

    def is_available(self) -> bool:
        return self._microphone.is_capturing

    def current_stream(self) -> StreamOutboundDTO:
        if self._stream is None or not self._microphone.is_capturing:
            raise CaptureNotActive("Microphone stream is not active")
        return StreamOutboundDTO(sample_rate=self._stream.sample_rate, stream=self._stream)
