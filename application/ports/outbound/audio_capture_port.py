from abc import ABC, abstractmethod

from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.value_objects.audio_format import AudioFormat


class AudioCapturePort(ABC):
    """What the application needs from a capture device."""

    @abstractmethod
    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        """Open the device as close to ``audio_format`` as the hardware allows.

        Raises MicrophoneUnavailable if no working device/format can be opened.
        """
