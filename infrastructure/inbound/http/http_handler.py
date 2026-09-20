"""HTTP inbound adapter: decode -> call the inbound port -> encode. No business rules."""

import time

from contracts.api.microservices.common.availability import AvailabilityResponse
from contracts.api.microservices.common.health_check import HealthCheckResponse
from contracts.api.microservices.microphone.start import MicrophoneConfig
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from application.dtos.start_stream_inbound import StartStreamInboundDTO
from application.errors import FormatMismatch
from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from infrastructure.inbound.http.http_envelope import failure, success
from infrastructure.inbound.http.ndjson_audio_events import NDJSON_MEDIA_TYPE, ndjson_audio_events

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
            MicrophoneConfig(
                sample_rate=result.sample_rate, channels=1, chunk_size=body.chunk_size
            ),  # the accepted configuration
        )

    async def handle_stop(self) -> JSONResponse:
        try:
            await self._port.stop_stream()
        except Exception as error:
            return failure("stop_stream", "Failed to stop microphone stream", error)
        return success("stop_stream", "Microphone stream stopped successfully", True)

    async def handle_available(self) -> JSONResponse:
        """Whether an input device is usable (probed without opening it)."""
        try:
            available, reason = await self._port.check_device()
        except Exception as error:
            return failure("check_availability", "Failed to check microphone availability", error)
        return success(
            "check_availability",
            "Microphone availability checked successfully",
            AvailabilityResponse(is_available=available, reason=reason),
        )

    async def handle_stream(
        self, sample_rate: int | None = None, chunk_size: int | None = None
    ) -> StreamingResponse | JSONResponse:
        """The event stream of the capture started with ``POST /start``.

        The format was fixed by ``/start``; ``sample_rate`` repeated here must match it.
        """
        try:
            result = self._port.current_stream()
            if sample_rate is not None and sample_rate != result.sample_rate:
                raise FormatMismatch(
                    f"sample_rate={sample_rate} differs from the capture's {result.sample_rate}"
                )
        except Exception as error:
            return failure("get_stream", "Failed to retrieve microphone stream", error)
        return StreamingResponse(
            ndjson_audio_events(result.stream, result.sample_rate),
            media_type=NDJSON_MEDIA_TYPE,
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
        return success("health_check", "Service is healthy", HealthCheckResponse(healthy=True))
