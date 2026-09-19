"""Outbound adapter: opens an input device through ``sounddevice``.

Implements ``AudioCapturePort``. It only talks to hardware; which formats to try is decided
by ``domain.operations.format_negotiation``.
"""

import logging
from collections.abc import Sequence

import sounddevice as sd

from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.operations.format_negotiation import fallback_formats
from domain.value_objects.audio_format import AudioFormat
from infrastructure.outbound.sounddevice_capture.sounddevice_audio_stream import (
    SoundDeviceAudioStream,
)
from infrastructure.outbound.sounddevice_capture.sounddevice_error_mapper import map_open_error

logger = logging.getLogger(__name__)


class SoundDeviceAudioCapture(AudioCapturePort):
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
            "SoundDeviceAudioCapture initialized default_fallback_rate=%s target_keywords=%s",
            default_fallback_rate,
            list(self._target_keywords),
        )

    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        try:
            device_index = self._find_microphone_index()
            device_info = sd.query_devices(device_index)
            default_rate = int(device_info.get("default_samplerate", self._default_fallback_rate))
        except Exception as error:
            logger.error("Error finding microphone: %s", error)
            raise map_open_error(error) from error

        logger.info("Using microphone device index=%s info=%s", device_index, device_info)
        if audio_format.sample_rate != default_rate:
            logger.warning(
                "Requested rate %sHz may not be supported (device default: %sHz)",
                audio_format.sample_rate,
                default_rate,
            )

        last_error: Exception | None = None
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
        raise map_open_error(last_error) from last_error

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
        return int(default_input)
