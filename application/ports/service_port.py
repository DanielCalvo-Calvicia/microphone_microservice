"""Driving (inbound) port: the use cases that inbound adapters may invoke."""

from abc import ABC, abstractmethod

from application.dtos.stream_dtos import StartStreamCommand
from application.ports.microphone_port import AudioStream


class ServicePort(ABC):
    @abstractmethod
    async def start_stream(self, command: StartStreamCommand) -> AudioStream:
        """Start continuous microphone streaming and return the live stream."""

    @abstractmethod
    async def stop_stream(self) -> None:
        """Stop the active stream. Does nothing if none is active."""

    @abstractmethod
    def is_available(self) -> bool:
        """True while a stream is active."""

    @abstractmethod
    def current_stream(self) -> AudioStream:
        """The active stream. Raises if none is active."""
