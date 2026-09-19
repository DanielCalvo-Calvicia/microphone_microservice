from dataclasses import dataclass

from fastapi import FastAPI

from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from composition_root.dependencies import microphone_dependencies as deps
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig


@dataclass(slots=True, frozen=True)
class HttpContainer:
    app: FastAPI
    microphone: MicrophoneStreamingPort  # kept so main_flow can release the device on shutdown


def new_http_container(
    server_cfg: ServerConfig, microphone_cfg: MicrophoneConfig
) -> HttpContainer:
    capture = deps.new_audio_capture(microphone_cfg)
    service = deps.new_microphone_service(capture, server_cfg.service_name)
    app = deps.new_http_app(service, server_cfg.service_name)
    return HttpContainer(app=app, microphone=service)
