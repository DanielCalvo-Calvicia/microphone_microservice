"""Driven (outbound) port: what the application needs from a capture device."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from domain.value_objects.audio_format import AudioFormat


class AudioStream(ABC):
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
        """Release the device. Must be idempotent."""


class MicrophonePort(ABC):
    @abstractmethod
    async def open_stream(self, audio_format: AudioFormat) -> AudioStream:
        """Open the capture device as close to ``audio_format`` as the hardware allows.

        Raises an exception if no working device/format can be opened.
        """
