from collections.abc import AsyncIterable
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StreamOutboundDTO:
    """A live stream handed back to an inbound adapter, plus the rate actually negotiated."""

    sample_rate: int
    stream: AsyncIterable[bytes]
