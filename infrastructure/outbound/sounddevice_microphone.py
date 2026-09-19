"""Outbound adapter: captures audio from the OS through the ``sounddevice`` library.

Implements ``application.ports.microphone_port.MicrophonePort``. It only talks to
hardware; which formats to try and when a start is allowed are decided by the
domain/application layers.
"""

import asyncio
import logging
import sys
from typing import AsyncIterator, Optional, Sequence

import numpy as np
import sounddevice as sd

from application.ports.microphone_port import AudioStream, MicrophonePort
from domain.operations.format_negotiation import fallback_formats
from domain.operations.pcm import downmix_to_mono
from domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)


class SoundDeviceAudioStream(AudioStream):
    """Async iterator over mono int16 PCM chunks read from an open ``RawInputStream``."""

    def __init__(
        self,
        raw_stream: "sd.RawInputStream",
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

        self._closed = False      # iteration is over
        self._released = False    # hardware has been released

        self._chunk_count = 0
        self._total_bytes = 0
        self._overflow_count = 0

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self

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
            self._closed = True
            raise
        except Exception as error:
            logger.error("Microphone stream read failed: %r", error)
            self._closed = True
            raise StopAsyncIteration

    async def close(self) -> None:
        self._closed = True
        if self._released:
            return
        self._released = True
        logger.info(
            "Stream closed | chunks=%d bytes=%d overflows=%d",
            self._chunk_count, self._total_bytes, self._overflow_count,
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


class SoundDeviceMicrophone(MicrophonePort):
    def __init__(
        self,
        default_fallback_rate: int = 16000,
        target_keywords: Sequence[str] = (),
        show_meter: bool = True,
    ) -> None:
        self._default_fallback_rate = default_fallback_rate
        self._target_keywords = tuple(target_keywords)
        self._show_meter = show_meter
        logger.info(
            "SoundDeviceMicrophone initialized default_fallback_rate=%s target_keywords=%s",
            default_fallback_rate, list(self._target_keywords),
        )

    async def open_stream(self, audio_format: AudioFormat) -> AudioStream:
        try:
            device_index = self._find_microphone_index()
            device_info = sd.query_devices(device_index)
            default_rate = int(device_info.get("default_samplerate", self._default_fallback_rate))
        except Exception as error:
            logger.error("Error finding microphone: %s", error)
            raise RuntimeError("No microphone devices available") from error

        logger.info("Using microphone device index=%s info=%s", device_index, device_info)
        if audio_format.sample_rate != default_rate:
            logger.warning(
                "Requested rate %sHz may not be supported (device default: %sHz)",
                audio_format.sample_rate, default_rate,
            )

        last_error: Optional[Exception] = None
        for candidate in fallback_formats(audio_format, default_rate):
            try:
                raw_stream = self._open_raw_stream(device_index, candidate)
            except Exception as error:
                logger.warning("Failed to open %s: %r", candidate, error)
                last_error = error
                continue

            logger.info("Microphone started device=%s format=%s", device_index, candidate)
            return SoundDeviceAudioStream(
                raw_stream=raw_stream,
                chunk_size=candidate.chunk_size,
                device_channels=candidate.channels,
                sample_rate=candidate.sample_rate,
                show_meter=self._show_meter,
            )

        assert last_error is not None
        raise last_error

    @staticmethod
    def _open_raw_stream(device_index: int, audio_format: AudioFormat) -> "sd.RawInputStream":
        raw_stream = sd.RawInputStream(
            samplerate=audio_format.sample_rate,
            blocksize=audio_format.chunk_size,
            device=device_index,
            channels=audio_format.channels,
            dtype="int16",
        )
        try:
            raw_stream.start()
        except Exception:
            raw_stream.close()
            raise
        return raw_stream

    def _find_microphone_index(self) -> int:
        """Pick an input device: first keyword match, else the OS default input."""
        devices = sd.query_devices()
        logger.debug("Scanning for microphones; devices_found=%d", len(devices))

        for index, info in enumerate(devices):
            if int(info.get("max_input_channels", 0)) <= 0:
                continue
            name = str(info.get("name"))
            logger.debug("Found input device id=%s name=%r", index, name)
            if any(key.lower() in name.lower() for key in self._target_keywords):
                logger.info("Auto-selected keyword match name=%r id=%s", name, index)
                return index

        default_input = sd.default.device[0]
        if default_input is None:
            raise RuntimeError("No default input device configured in OS")
        sd.query_devices(default_input)  # raises if the default index is invalid
        logger.info("No keyword match; using OS default input index=%s", default_input)
        return default_input
