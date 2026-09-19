"""HTTP inbound adapter: decode -> call the inbound port -> encode. No business rules."""

import time

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from application.dtos.start_stream_inbound import StartStreamInboundDTO
from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from infrastructure.inbound.http.http_envelope import failure, success

_DEFAULTS = StartStreamInboundDTO()


class StartStreamBody(BaseModel):
    """HTTP transport model for ``POST /start``. Never crosses into application/."""

    sample_rate: int = _DEFAULTS.sample_rate
    channels: int = _DEFAULTS.channels
    chunk_size: int = _DEFAULTS.chunk_size


class MicrophoneHandler:
    def __init__(self, port: MicrophoneStreamingPort) -> None:
        self._port = port
        self.router = APIRouter()
        self.router.add_api_route("/start", self.handle_start, methods=["POST"])
        self.router.add_api_route("/stop", self.handle_stop, methods=["POST"])
        self.router.add_api_route("/available", self.handle_available, methods=["GET"])
        self.router.add_api_route(
            "/stream", self.handle_stream, methods=["GET"], response_model=None
        )
        self.router.add_api_route("/health", self.handle_health, methods=["GET"], tags=["Health"])

    async def handle_start(self, body: StartStreamBody) -> JSONResponse:
        try:
            result = await self._port.start_stream(
                StartStreamInboundDTO(
                    sample_rate=body.sample_rate,
                    channels=body.channels,
                    chunk_size=body.chunk_size,
                )
            )
        except Exception as error:
            return failure("start_stream", "Failed to start microphone stream", error)
        return success(
            "start_stream",
            "Microphone stream started successfully",
            {"sample_rate": result.sample_rate},
        )

    async def handle_stop(self) -> JSONResponse:
        try:
            await self._port.stop_stream()
        except Exception as error:
            return failure("stop_stream", "Failed to stop microphone stream", error)
        return success("stop_stream", "Microphone stream stopped successfully", True)

    async def handle_available(self) -> JSONResponse:
        try:
            available = self._port.is_available()
        except Exception as error:
            return failure("check_availability", "Failed to check microphone availability", error)
        return success(
            "check_availability", "Microphone availability checked successfully", available
        )

    async def handle_stream(self) -> StreamingResponse | JSONResponse:
        try:
            result = self._port.current_stream()
        except Exception as error:
            return failure("get_stream", "Failed to retrieve microphone stream", error)
        return StreamingResponse(
            result.stream,
            media_type="application/octet-stream",
            status_code=status.HTTP_200_OK,
            headers={
                "X-Sample-Rate": str(result.sample_rate),
                "X-Action": "get_stream",
                "X-Status": "success",
                "X-Message": "Microphone stream retrieved successfully",
                "X-Timestamp": str(time.time()),
            },
        )

    async def handle_health(self) -> JSONResponse:
        return success("health_check", "Service is healthy")
