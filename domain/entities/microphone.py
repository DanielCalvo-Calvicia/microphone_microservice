from domain.errors import CaptureAlreadyActive, CaptureNotActive
from domain.value_objects.audio_format import AudioFormat


class Microphone:
    """The capture device as the business sees it: idle, or capturing in some format.

    Rules:
      * a microphone can only start when it is idle;
      * stopping an idle microphone is a harmless no-op.
    """

    def __init__(self) -> None:
        self._active_format: AudioFormat | None = None

    @property
    def is_capturing(self) -> bool:
        return self._active_format is not None

    @property
    def active_format(self) -> AudioFormat:
        if self._active_format is None:
            raise CaptureNotActive("Microphone stream is not active")
        return self._active_format

    def ensure_idle(self) -> None:
        if self.is_capturing:
            raise CaptureAlreadyActive("Microphone stream already started")

    def start(self, audio_format: AudioFormat) -> None:
        """Enter the capturing state with the format actually negotiated."""
        self.ensure_idle()
        self._active_format = audio_format

    def stop(self) -> None:
        self._active_format = None
