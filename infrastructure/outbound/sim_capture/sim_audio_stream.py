"""Outbound adapter: the generated signal of the simulated microphone, paced like a real device."""

import asyncio
import math
import struct
import time
from collections.abc import AsyncIterator, Awaitable, Callable

from shared_logging import get_logger

from application.ports.outbound.audio_stream_port import AudioStreamPort

logger = get_logger(__name__)

TONE_HZ = 300
NOISE_AMPLITUDE = 20  # room noise: quiet, but the microphone learns its noise floor from it
TONE_AMPLITUDE = 8000  # someone speaking: far over any silence threshold


class SimAudioStream(AudioStreamPort):
    """Mono PCM16 chunks of a pattern that never repeats: room noise, a tone, then silence for good.

    The pattern is what one utterance looks like to the cutter. Chunks come out at the pace a real
    device delivers them (one chunk duration per chunk, on a fixed schedule from the moment the
    stream was opened, so a slow consumer finds the chunks that are already due and does not make
    the signal drift).
    """

    def __init__(
        self,
        sample_rate: int,
        chunk_size: int,
        quiet_chunks: int,
        tone_chunks: int,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._quiet_chunks = quiet_chunks
        self._tone_chunks = tone_chunks
        self._sleep = sleep
        self._monotonic = monotonic
        self._chunk_seconds = chunk_size / sample_rate
        self._started_at = monotonic()
        self._chunks = 0  # chunks handed over so far
        self._closed = False
        self._listener: Callable[[], None] | None = None
        self._silence = bytes(chunk_size * 2)

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self

    def on_terminated(self, callback: Callable[[], None]) -> None:
        self._listener = callback

    async def __anext__(self) -> bytes:
        if self._closed:
            raise StopAsyncIteration
        index = self._chunks
        self._chunks += 1
        try:
            delay = self._started_at + self._chunks * self._chunk_seconds - self._monotonic()
            if delay > 0:
                await self._sleep(delay)
        except asyncio.CancelledError:
            logger.info("Simulated stream was cancelled by client/server")
            self._terminate()
            raise
        if self._closed:  # closed while waiting for the chunk
            raise StopAsyncIteration
        return self._chunk(index)

    async def close(self) -> None:
        self._closed = True
        self._listener = None  # an explicit close is not a termination
        logger.info("Simulated stream closed", chunks=self._chunks)

    def _terminate(self) -> None:
        """The consumer went away: like a real stream, end and tell the listener once."""
        self._closed = True
        listener, self._listener = self._listener, None
        if listener is not None:
            listener()

    def _chunk(self, index: int) -> bytes:
        if index < self._quiet_chunks:
            amplitude = NOISE_AMPLITUDE
        elif index < self._quiet_chunks + self._tone_chunks:
            amplitude = TONE_AMPLITUDE
        else:
            return self._silence
        first = index * self._chunk_size  # the tone stays in phase from one chunk to the next
        samples = [
            int(amplitude * math.sin(2 * math.pi * TONE_HZ * (first + i) / self._sample_rate))
            for i in range(self._chunk_size)
        ]
        return struct.pack(f"<{self._chunk_size}h", *samples)
