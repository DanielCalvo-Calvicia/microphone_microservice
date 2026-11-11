from dataclasses import dataclass

from fastapi import FastAPI

from application.ports.service.microphone_service_port import MicrophoneServicePort
from composition_root.dependencies.audio_capture_dependency import new_audio_capture
from composition_root.dependencies.http_app_dependency import new_http_app
from composition_root.dependencies.microphone_service_dependency import new_microphone_service
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig


@dataclass(slots=True, frozen=True)
class HttpContainer:
    app: FastAPI
    microphone: MicrophoneServicePort  # kept so main_flow can release the device on shutdown


def new_http_container(server_cfg: ServerConfig, microphone_cfg: MicrophoneConfig) -> HttpContainer:
    capture = new_audio_capture(microphone_cfg)
    service = new_microphone_service(capture, server_cfg.service_name, microphone_cfg.treatment)
    app = new_http_app(service, server_cfg.service_name)
    return HttpContainer(app=app, microphone=service)
