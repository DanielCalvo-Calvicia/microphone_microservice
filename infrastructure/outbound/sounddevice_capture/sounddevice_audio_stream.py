"""Outbound adapter: the live stream read from an open input device."""

import asyncio
import sys
from collections.abc import AsyncIterator, Callable

import numpy as np
from shared_logging import get_logger

from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.operations.pcm import downmix_to_mono
from infrastructure.outbound.sounddevice_capture.audio_driver import RawInput
from infrastructure.outbound.sounddevice_capture.sounddevice_error_mapper import (
    map_close_error,
    map_read_error,
)

logger = get_logger(__name__)


class SoundDeviceAudioStream(AudioStreamPort):
    """Async iterator over mono int16 PCM chunks read from an open input stream."""

    def __init__(
        self,
        raw_stream: RawInput,
        chunk_size: int,
        device_channels: int,
        sample_rate: int,
        show_meter: bool = False,
    ) -> None:
        self._raw_stream = raw_stream
        self._chunk_size = chunk_size
        self._device_channels = device_channels
        self._sample_rate = sample_rate
        self._show_meter = show_meter
        self._listener: Callable[[], None] | None = None

        self._closed = False  # iteration is over
        self._released = False  # hardware has been released

        self._chunk_count = 0
        self._total_bytes = 0
        self._overflow_count = 0

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

        try:
            data, overflowed = await asyncio.to_thread(self._raw_stream.read, self._chunk_size)
            chunk = bytes(data)

            if self._device_channels > 1:
                chunk = downmix_to_mono(chunk, self._device_channels)

            self._chunk_count += 1
            self._total_bytes += len(chunk)
            if overflowed:
                self._overflow_count += 1
            if self._show_meter:
                self._write_meter(chunk, overflowed)

            return chunk
        except asyncio.CancelledError:
            logger.info("Streaming response was cancelled by client/server")
            self._terminate()
            raise
        except Exception as error:
            logger.error("Microphone stream read failed", error=error)
            self._terminate()
            raise map_read_error(error) from error

    async def close(self) -> None:
        self._closed = True
        self._listener = None  # an explicit close is not a termination
        try:
            await asyncio.to_thread(self._release)
        except Exception as error:
            raise map_close_error(error) from error

    def _terminate(self) -> None:
        """The stream died on its own: release the device, then tell the listener."""
        self._closed = True
        try:
            self._release()
        except Exception:
            logger.exception("Failed to release the device after the stream terminated")
        listener, self._listener = self._listener, None
        if listener is not None:
            listener()

    def _release(self) -> None:
        if self._released:
            return
        self._released = True
        logger.info(
            "Stream closed",
            chunks=self._chunk_count,
            bytes=self._total_bytes,
            overflows=self._overflow_count,
        )
        try:
            if self._raw_stream.active:
                self._raw_stream.stop()
        finally:
            self._raw_stream.close()

    def _write_meter(self, chunk: bytes, overflowed: bool) -> None:
        """Overwrite one console line with a live volume meter."""
        samples = np.frombuffer(chunk, dtype=np.int16)
        rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
        rms_db = 20 * np.log10(rms / 32767) if rms > 0 else -float("inf")
        peak = int(np.max(np.abs(samples)))

        bar_len = min(30, int((rms / 32767) * 30 * 5))  # x5 gain for visibility
        bar = "█" * bar_len + "░" * (30 - bar_len)
        overflow_flag = " ⚠ OVF" if overflowed else ""

        line = (
            f"\r  🎤 #{self._chunk_count:<6}  "
            f"|{bar}|  "
            f"RMS: {rms:>7.1f} ({rms_db:>6.1f} dB)  "
            f"Peak: {peak:>5}  "
            f"{len(chunk):>5}B"
            f"{overflow_flag}"
        )
        sys.stdout.write(line.ljust(120))
        sys.stdout.flush()
