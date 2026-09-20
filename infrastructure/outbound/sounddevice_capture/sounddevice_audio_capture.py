"""Outbound adapter: opens an input device through an ``AudioDriver``.

Implements ``AudioCapturePort``. It only talks to hardware; which formats to try is decided
by ``domain.operations.format_negotiation``, which device to use by ``DeviceSelector``.
"""

import asyncio

from shared_logging import get_logger

from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.operations.format_negotiation import fallback_formats
from domain.value_objects.audio_format import AudioFormat
from infrastructure.outbound.sounddevice_capture.audio_driver import AudioDriver
from infrastructure.outbound.sounddevice_capture.sounddevice_audio_stream import (
    SoundDeviceAudioStream,
)
from infrastructure.outbound.sounddevice_capture.sounddevice_device_selector import (
    DeviceSelector,
)
from infrastructure.outbound.sounddevice_capture.sounddevice_error_mapper import map_open_error

logger = get_logger(__name__)


class SoundDeviceAudioCapture(AudioCapturePort):
    def __init__(
        self,
        driver: AudioDriver,
        selector: DeviceSelector,
        default_fallback_rate: int = 16000,
        show_meter: bool = True,
    ) -> None:
        self._driver = driver
        self._selector = selector
        self._default_fallback_rate = default_fallback_rate
        self._show_meter = show_meter
        logger.info(
            "SoundDeviceAudioCapture initialized",
            default_fallback_rate=default_fallback_rate,
        )

    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        # Device discovery and opening block; keep them off the event loop.
        return await asyncio.to_thread(self._open_stream_blocking, audio_format)

    async def check_device(self) -> tuple[bool, str | None]:
        return await asyncio.to_thread(self._check_device_blocking)

    def _check_device_blocking(self) -> tuple[bool, str | None]:
        try:
            info = self._driver.device_info(self._selector.select())
        except Exception as error:
            return False, str(error)
        if info.max_input_channels <= 0:
            return False, "Selected device has no input channels."
        return True, None

    def _open_stream_blocking(self, audio_format: AudioFormat) -> AudioStreamPort:
        try:
            device_index = self._selector.select()
            device_info = self._driver.device_info(device_index)
        except Exception as error:
            logger.error("Error finding microphone", error=error)
            raise map_open_error(error) from error
        default_rate = device_info.default_samplerate or self._default_fallback_rate

        logger.info("Using microphone device", index=device_index, info=device_info)
        if audio_format.sample_rate != default_rate:
            logger.warning(
                "Requested sample rate may not be supported by the device",
                sample_rate=audio_format.sample_rate,
                default_rate=default_rate,
            )

        last_error: Exception | None = None
        for candidate in fallback_formats(audio_format, default_rate):
            try:
                raw_stream = self._driver.open_input(device_index, candidate)
            except Exception as error:
                logger.warning(
                    "Failed to open device with candidate format", candidate=candidate, error=error
                )
                last_error = error
                continue

            logger.info("Microphone started", device=device_index, format=candidate)
            return SoundDeviceAudioStream(
                raw_stream=raw_stream,
                chunk_size=candidate.chunk_size,
                device_channels=candidate.channels,
                sample_rate=candidate.sample_rate,
                show_meter=self._show_meter,
            )

        assert last_error is not None
        raise map_open_error(last_error) from last_error
