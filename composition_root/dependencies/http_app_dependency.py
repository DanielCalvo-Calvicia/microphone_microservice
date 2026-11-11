from fastapi import FastAPI
from shared_logging import TracingMiddleware

from application.ports.service.microphone_service_port import MicrophoneServicePort
from infrastructure.inbound.http.http_handler import MicrophoneHandler


def new_http_app(service: MicrophoneServicePort, name: str) -> FastAPI:
    app = FastAPI(
        title=name,
        description=f"HTTP adapter exposing {name}",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(MicrophoneHandler(service).router)
    app.add_middleware(TracingMiddleware)
    return app
