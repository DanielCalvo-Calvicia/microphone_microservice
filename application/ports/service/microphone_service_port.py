from abc import ABC, abstractmethod

from application.dtos.inbound.start_stream_inbound import StartStreamInboundDTO
from application.dtos.outbound.stream_outbound import StreamOutboundDTO


class MicrophoneServicePort(ABC):
    """The service's own port: the microphone use cases. ``MicrophoneService`` implements it; the
    inbound adapters call it (through the inbound port); nothing else in the application knows the
    concrete service."""

    @abstractmethod
    async def start_stream(self, request: StartStreamInboundDTO) -> StreamOutboundDTO:
        """Start continuous microphone streaming and return the live stream."""

    @abstractmethod
    async def stop_stream(self) -> None:
        """Stop the active stream. Does nothing if none is active."""

    @abstractmethod
    def is_available(self) -> bool:
        """True while a stream is active."""

    @abstractmethod
    def current_stream(self) -> StreamOutboundDTO:
        """The active stream. Raises CaptureNotActive if none is active."""

    async def check_device(self) -> tuple[bool, str | None]:
        """Whether a usable input device exists: ``(ok, reason if not)``."""
        return True, None
