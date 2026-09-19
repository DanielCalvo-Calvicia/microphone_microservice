from fastapi import FastAPI

from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.services.microphone_service import MicrophoneService
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.inbound.http.http_handler import MicrophoneHandler
from infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture import (
    SoundDeviceAudioCapture,
)
from infrastructure.outbound.sounddevice_capture.sounddevice_device_selector import DeviceSelector
from infrastructure.outbound.sounddevice_capture.sounddevice_driver import SoundDeviceDriver


def new_audio_capture(cfg: MicrophoneConfig) -> AudioCapturePort:
    driver = SoundDeviceDriver()
    return SoundDeviceAudioCapture(
        driver=driver,
        selector=DeviceSelector(driver, cfg.target_keywords),
        default_fallback_rate=cfg.fallback_sample_rate,
        show_meter=cfg.show_meter,
    )


def new_microphone_service(capture: AudioCapturePort, name: str) -> MicrophoneStreamingPort:
    return MicrophoneService(capture=capture, name=name)


def new_http_app(port: MicrophoneStreamingPort, name: str) -> FastAPI:
    app = FastAPI(
        title=name,
        description=f"HTTP adapter exposing {name}",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(MicrophoneHandler(port).router)
    return app
