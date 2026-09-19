"""What the sounddevice adapter needs from the audio driver (the seam faked in tests)."""

from dataclasses import dataclass
from typing import Any, Protocol

from domain.value_objects.audio_format import AudioFormat


@dataclass(slots=True, frozen=True)
class DeviceInfo:
    index: int
    name: str
    max_input_channels: int
    default_samplerate: int | None


class RawInput(Protocol):
    @property
    def active(self) -> bool: ...

    def read(self, frames: int) -> tuple[Any, bool]: ...

    def stop(self) -> None: ...

    def close(self) -> None: ...


class AudioDriver(Protocol):
    def input_devices(self) -> list[DeviceInfo]:
        """Every device the driver knows, inputs and outputs."""
        ...

    def default_input_index(self) -> int | None: ...

    def device_info(self, index: int) -> DeviceInfo:
        """Raises if ``index`` is not a valid device."""
        ...

    def open_input(self, index: int, audio_format: AudioFormat) -> RawInput:
        """Open and start an int16 input stream; raises if the format is unsupported."""
        ...
