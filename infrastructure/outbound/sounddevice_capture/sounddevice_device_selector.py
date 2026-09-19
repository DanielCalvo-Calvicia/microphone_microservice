import logging
from collections.abc import Sequence

from infrastructure.outbound.sounddevice_capture.audio_driver import AudioDriver

logger = logging.getLogger(__name__)


class DeviceSelector:
    """Picks an input device: first keyword match, else the OS default input."""

    def __init__(self, driver: AudioDriver, target_keywords: Sequence[str] = ()) -> None:
        self._driver = driver
        self._target_keywords = tuple(target_keywords)

    def select(self) -> int:
        devices = self._driver.input_devices()
        logger.debug("Scanning for microphones; devices_found=%d", len(devices))

        for device in devices:
            if device.max_input_channels <= 0:
                continue
            logger.debug("Found input device id=%s name=%r", device.index, device.name)
            if any(key.lower() in device.name.lower() for key in self._target_keywords):
                logger.info("Auto-selected keyword match name=%r id=%s", device.name, device.index)
                return device.index

        default_input = self._driver.default_input_index()
        if default_input is None:
            raise RuntimeError("No default input device configured in OS")
        self._driver.device_info(default_input)  # raises if the default index is invalid
        logger.info("No keyword match; using OS default input index=%s", default_input)
        return default_input
