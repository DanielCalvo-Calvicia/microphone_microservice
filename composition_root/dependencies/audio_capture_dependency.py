from shared_logging import get_logger

from application.ports.outbound.audio_capture_port import AudioCapturePort
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.outbound.sim_capture.sim_audio_capture import SimAudioCapture

logger = get_logger(__name__)


def new_audio_capture(cfg: MicrophoneConfig) -> AudioCapturePort:
    """Choose the capture adapter (MICROPHONE_BACKEND, ADR-007).

    The sound-card adapter is imported only on the ``real`` branch: it imports ``sounddevice``,
    which needs PortAudio, and a machine without it must still be able to run ``sim``.
    """
    if cfg.backend == "sim":
        logger.warning("Microphone backend is simulated")
        return SimAudioCapture()
    from infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture import (
        SoundDeviceAudioCapture,
    )
    from infrastructure.outbound.sounddevice_capture.sounddevice_device_selector import (
        DeviceSelector,
    )
    from infrastructure.outbound.sounddevice_capture.sounddevice_driver import SoundDeviceDriver

    driver = SoundDeviceDriver()
    return SoundDeviceAudioCapture(
        driver=driver,
        selector=DeviceSelector(driver, cfg.target_keywords),
        default_fallback_rate=cfg.fallback_sample_rate,
        show_meter=cfg.show_meter,
    )
