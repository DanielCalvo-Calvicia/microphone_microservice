"""Outbound adapter: a simulated input device (MICROPHONE_BACKEND=sim, ADR-007).

Implements ``AudioCapturePort`` without any sound hardware or PortAudio, so a machine with no
microphone (a server, a CI run, a container on Windows) can run the whole pipeline. It is a fake
*device*, not a fake service: its signal goes through the same utterance cutting as a real one.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable

from shared_logging import get_logger

from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.value_objects.audio_format import AudioFormat
from infrastructure.outbound.sim_capture.sim_audio_stream import SimAudioStream

logger = get_logger(__name__)

# What `/available` says in its `reason` (the deployment tool shows it as a warning).
SIM_NOTE = "simulated microphone (MICROPHONE_BACKEND=sim): a generated signal, not a real device"

QUIET_CHUNKS = 5  # about 0.3 s of room noise at 16 kHz with 1024-sample chunks
TONE_CHUNKS = 80  # about 5 s of tone: one utterance


class SimAudioCapture(AudioCapturePort):
    def __init__(
        self,
        quiet_chunks: int = QUIET_CHUNKS,
        tone_chunks: int = TONE_CHUNKS,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._quiet_chunks = quiet_chunks
        self._tone_chunks = tone_chunks
        self._sleep = sleep
        self._monotonic = monotonic

    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        """Always mono at the requested rate and chunk size: nothing to negotiate."""
        logger.info(
            "Using the simulated microphone",
            sample_rate=audio_format.sample_rate,
            chunk_size=audio_format.chunk_size,
        )
        return SimAudioStream(
            sample_rate=audio_format.sample_rate,
            chunk_size=audio_format.chunk_size,
            quiet_chunks=self._quiet_chunks,
            tone_chunks=self._tone_chunks,
            sleep=self._sleep,
            monotonic=self._monotonic,
        )

    async def check_device(self) -> tuple[bool, str | None]:
        return True, SIM_NOTE
