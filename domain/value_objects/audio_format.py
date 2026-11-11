from dataclasses import dataclass, replace

from domain.errors import InvalidAudioFormat


@dataclass(slots=True, frozen=True)
class AudioFormat:
    """Describes a PCM (16-bit) capture: how fast, how many channels, how big a chunk.

    Invariant: every field is strictly positive.
    """

    sample_rate: int
    channels: int
    chunk_size: int

    def __post_init__(self) -> None:
        if self.sample_rate <= 0 or self.channels <= 0 or self.chunk_size <= 0:
            raise InvalidAudioFormat("Invalid microphone stream parameters")

    def with_sample_rate(self, sample_rate: int) -> "AudioFormat":
        return replace(self, sample_rate=sample_rate)

    def with_channels(self, channels: int) -> "AudioFormat":
        return replace(self, channels=channels)
