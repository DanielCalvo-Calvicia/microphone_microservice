from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable


class AudioStreamPort(ABC):
    """A live stream of mono 16-bit PCM chunks coming from an opened device."""

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Sample rate actually negotiated with the device (may differ from the request)."""

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate over PCM chunks until close() is called.

        A device failure is not a clean end: it raises StreamReadFailed.
        """

    @abstractmethod
    def on_terminated(self, callback: Callable[[], None]) -> None:
        """Register a callback for when the stream ends on its own.

        Fires once, after the device has been released, when a read fails or the consumer
        goes away. It does not fire for an explicit close().
        """

    @abstractmethod
    async def close(self) -> None:
        """Release the device. Must be idempotent. Raises StreamCloseFailed on failure."""
