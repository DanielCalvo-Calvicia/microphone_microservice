from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StartStreamCommand:
    """Input of the "start streaming" use case. Defaults are the service defaults."""

    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
