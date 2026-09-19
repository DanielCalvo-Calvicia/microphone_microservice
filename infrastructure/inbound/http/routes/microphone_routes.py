"""HTTP inbound adapter: translates HTTP <-> application use cases. No business logic."""

import logging
import time
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from application.dtos.stream_dtos import StartStreamCommand
from application.ports.service_port import ServicePort

logger = logging.getLogger(__name__)

_DEFAULTS = StartStreamCommand()


class StartStreamBody(BaseModel):
    """HTTP transport model for ``POST /start``."""

    sample_rate: int = _DEFAULTS.sample_rate
    channels: int = _DEFAULTS.channels
    chunk_size: int = _DEFAULTS.chunk_size


def _success(action: str, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "action": action,
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": message,
            "timestamp": time.time(),
            "data": data,
        },
    )


def _failure(action: str, message: str, error: Exception) -> JSONResponse:
    logger.error("%s failed: %r", action, error)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "action": action,
            "status": "error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"{message}: {error}",
            "timestamp": time.time(),
            "data": str(error),
        },
    )


def build_microphone_router(service: ServicePort) -> APIRouter:
    router = APIRouter()

    @router.post("/start", status_code=status.HTTP_200_OK)
    async def start_stream(body: StartStreamBody):
        try:
            stream = await service.start_stream(
                StartStreamCommand(
                    sample_rate=body.sample_rate,
                    channels=body.channels,
                    chunk_size=body.chunk_size,
                )
            )
            return _success(
                "start_stream",
                "Microphone stream started successfully",
                {"sample_rate": stream.sample_rate},
            )
        except Exception as error:
            return _failure("start_stream", "Failed to start microphone stream", error)

    @router.post("/stop", status_code=status.HTTP_200_OK)
    async def stop_stream():
        try:
            await service.stop_stream()
            return _success("stop_stream", "Microphone stream stopped successfully", True)
        except Exception as error:
            return _failure("stop_stream", "Failed to stop microphone stream", error)

    @router.get("/available", status_code=status.HTTP_200_OK)
    async def check_availability():
        try:
            return _success(
                "check_availability",
                "Microphone availability checked successfully",
                service.is_available(),
            )
        except Exception as error:
            return _failure(
                "check_availability", "Failed to check microphone availability", error
            )

    @router.get("/stream", status_code=status.HTTP_200_OK)
    async def get_stream():
        try:
            stream = service.current_stream()
            return StreamingResponse(
                stream,
                media_type="application/octet-stream",
                status_code=status.HTTP_200_OK,
                headers={
                    "X-Sample-Rate": str(stream.sample_rate),
                    "X-Action": "get_stream",
                    "X-Status": "success",
                    "X-Message": "Microphone stream retrieved successfully",
                    "X-Timestamp": str(time.time()),
                },
            )
        except Exception as error:
            return _failure("get_stream", "Failed to retrieve microphone stream", error)

    @router.get("/health", tags=["Health"])
    async def health_check():
        return _success("health_check", "Service is healthy")

    return router
