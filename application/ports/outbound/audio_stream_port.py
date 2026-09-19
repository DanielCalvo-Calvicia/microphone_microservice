from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class AudioStreamPort(ABC):
    """A live stream of mono 16-bit PCM chunks coming from an opened device."""

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Sample rate actually negotiated with the device (may differ from the request)."""

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate over PCM chunks until the stream is closed."""

    @abstractmethod
    async def close(self) -> None:
        """Release the device. Must be idempotent. Raises StreamCloseFailed on failure."""
