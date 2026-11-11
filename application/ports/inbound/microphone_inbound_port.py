from abc import ABC, abstractmethod

from application.dtos.inbound.start_stream_inbound import StartStreamInboundDTO
from application.dtos.outbound.stream_outbound import StreamOutboundDTO


class MicrophoneInboundPort(ABC):
    """What every inbound adapter offers, whatever its transport (HTTP today; gRPC, a CLI, ...).

    The same operations with DTOs and no transport types: an adapter decodes its own requests into
    these calls and encodes what they return. A new inbound adapter implements this port, so its
    functions are the same.
    """

    @abstractmethod
    def health(self) -> bool:
        """True while the adapter is serving."""

    @abstractmethod
    async def check_device(self) -> tuple[bool, str | None]:
        """Whether a usable input device exists (probed, not opened): ``(ok, reason if not)``."""

    @abstractmethod
    async def start_stream(self, request: StartStreamInboundDTO) -> StreamOutboundDTO:
        """Start the capture and return the live stream of utterances."""

    @abstractmethod
    async def stop_stream(self) -> None:
        """Stop the active capture. Does nothing if none is active."""

    @abstractmethod
    def current_stream(self) -> StreamOutboundDTO:
        """The stream of the active capture. Raises CaptureNotActive if none is active."""
