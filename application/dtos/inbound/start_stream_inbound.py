from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StartStreamInboundDTO:
    """Carries the parameters of the start-streaming use case into the application layer."""

    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
