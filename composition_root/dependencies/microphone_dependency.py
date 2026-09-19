from dataclasses import dataclass
from typing import Sequence

from fastapi import FastAPI

from application.ports.microphone_port import MicrophonePort
from application.ports.service_port import ServicePort
from application.services.microphone_service import MicrophoneService
from infrastructure.inbound.http.routes.microphone_routes import build_microphone_router
from infrastructure.outbound.sounddevice_microphone import SoundDeviceMicrophone


@dataclass(slots=True, frozen=True)
class MicrophoneDependency:
    service: ServicePort
    app: FastAPI


def generate_microphone_dependency(
    default_fallback_rate: int = 16000,
    target_keywords: Sequence[str] = (),
    name: str = "Microphone",
    show_meter: bool = True,
) -> MicrophoneDependency:
    """Select the concrete implementations and connect them to their ports."""
    device: MicrophonePort = SoundDeviceMicrophone(
        default_fallback_rate=default_fallback_rate,
        target_keywords=target_keywords,
        show_meter=show_meter,
    )
    service: ServicePort = MicrophoneService(device=device, name=name)

    app = FastAPI(
        title=name,
        description=f"Adapter exposing {name} via FastAPI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(build_microphone_router(service))

    return MicrophoneDependency(service=service, app=app)
