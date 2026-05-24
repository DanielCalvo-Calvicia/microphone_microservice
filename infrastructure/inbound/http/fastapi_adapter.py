
from typing import Any

from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse, JSONResponse

import time

from application.ports.adapter_inbound_port import AdapterInboundPort
from application.ports.service_port import ServicePort

from application.dtos.adapter_inbound_dtos import (
    StartMicrophoneStreamRequestDto,
    StartMicrophoneStreamResponseDto,
    StopMicrophoneStreamRequestDto,
    StopMicrophoneStreamResponseDto,
    MicrophoneAvailabilityRequestDto,
    MicrophoneAvailabilityResponseDto,
    GetStreamRequestDto,
    GetStreamResponseDto
)

from application.dtos.mapper.adapter_inbound_to_service import (
    map_adapter_to_service_start_request,
    map_adapter_to_service_stop_request,
    map_adapter_to_service_availability_request,
    map_adapter_to_service_get_stream_request
)

from application.dtos.mapper.service_to_adapter_inbound import (
    map_service_to_adapter_start_response,
    map_service_to_adapter_stop_response,
    map_service_to_adapter_availability_response,
    map_service_to_adapter_get_stream_response
)
from composition_root.runtime.logger import get_logger


logger = get_logger("http")

class FastApiAdapter(AdapterInboundPort):
    def __init__(self, service_port: ServicePort, app: FastAPI):
        self.service_port = service_port
        self.app = app

        logger.info("FastApiAdapter initialized")
        self.register_routes(self.app)

    def register_routes(self, app: FastAPI):
        logger.info("Registering HTTP routes")
        @app.post("/start", status_code=status.HTTP_200_OK)
        async def handle_start_stream(request: StartMicrophoneStreamRequestDto):
            logger.info(
                "POST /start received",
                sample_rate=request.sample_rate,
                channels=request.channels,
                chunk_size=request.chunk_size,
            )
            try:
                response = await self.start_stream(request)
                logger.info("POST /start succeeded", sample_rate=response.sample_rate)

                http_response = StreamingResponse(
                    response.stream,
                    media_type="application/octet-stream",
                    status_code=status.HTTP_200_OK,
                    headers={
                        "X-Sample-Rate": str(response.sample_rate),
                        "X-Action": "start_stream",
                        "X-Status": "success",
                        "X-Message": "Microphone stream started successfully",
                        "X-Timestamp": str(time.time()),
                    }
                )
                return http_response
            except Exception as e:
                logger.error("POST /start failed", error=repr(e))
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "start_stream",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to start microphone stream: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )
            
            
        @app.post("/stop", status_code=status.HTTP_200_OK)
        async def handle_stop_stream(request: StopMicrophoneStreamRequestDto):
            logger.info("POST /stop received")
            try:
                response = await self.stop_stream(request)
                logger.info("POST /stop succeeded", success=response.success)
                http_response = JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "action": "stop_stream",
                        "status": "success",
                        "status_code": status.HTTP_200_OK,
                        "message": "Microphone stream stopped successfully",
                        "timestamp": time.time(),
                        "data": response.success
                    }
                )
                return http_response
            except Exception as e:
                logger.error("POST /stop failed", error=repr(e))
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "stop_stream",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to stop microphone stream: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )

        @app.get("/available", status_code=status.HTTP_200_OK)
        async def handle_check_availability():
            logger.info("GET /available received")
            try:
                request_dto = MicrophoneAvailabilityRequestDto()
                response = await self.is_available(request_dto)
                logger.info("GET /available succeeded", is_available=response.is_available)
                http_response = JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "action": "check_availability",
                        "status": "success",
                        "status_code": status.HTTP_200_OK,
                        "message": "Microphone availability checked successfully",
                        "timestamp": time.time(),
                        "data": response.is_available
                    }
                )
                return http_response
            except Exception as e:
                logger.error("GET /available failed", error=repr(e))
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "check_availability",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to check microphone availability: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )
        @app.get("/stream", status_code=status.HTTP_200_OK)
        async def handle_get_stream():
            logger.info("GET /stream received")
            try:
                request_dto = GetStreamRequestDto()
                response = await self.mic_stream(request_dto)
                logger.info("GET /stream succeeded; returning StreamingResponse", sample_rate=response.sample_rate)
                http_response = StreamingResponse(
                    response.stream,
                    media_type="application/octet-stream",
                    status_code=status.HTTP_200_OK,
                    headers={
                        "X-Sample-Rate": str(response.sample_rate),
                        "X-Action": "get_stream",
                        "X-Status": "success",
                        "X-Message": "Microphone stream retrieved successfully",
                        "X-Timestamp": str(time.time()),
                    }
                )
                return http_response
            except Exception as e:
                logger.error("GET /stream failed", error=repr(e))
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "get_stream",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to retrieve microphone stream: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )
        @app.get("/health", tags=["Health"])
        async def health_check():
            logger.info("GET /health received")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "action": "health_check",
                    "status": "success",
                    "status_code": status.HTTP_200_OK,
                    "message": "Service is healthy",
                    "timestamp": time.time(),
                    "data": None
                }
            )
    @property
    def get_app(self) -> Any:
        logger.trace("get_app accessed")
        return self.app

    async def start_stream(self, request: StartMicrophoneStreamRequestDto) -> StartMicrophoneStreamResponseDto:
        logger.trace("Adapter start_stream mapping inbound DTO to service DTO")
        
        service_request_dto = map_adapter_to_service_start_request(request)
        
        logger.trace("Adapter start_stream calling service")
        service_response_dto = await self.service_port.start_stream(service_request_dto)

        logger.trace("Adapter start_stream mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_start_response(service_response_dto)

        logger.info("Adapter start_stream completed")
        return adapter_response_dto
    

    async def stop_stream(self, request: StopMicrophoneStreamRequestDto) -> StopMicrophoneStreamResponseDto:
        logger.trace("Adapter stop_stream mapping inbound DTO to service DTO")
        service_request_dto = map_adapter_to_service_stop_request(request)
        logger.trace("Adapter stop_stream calling service")
        service_response_dto = await self.service_port.stop_stream(service_request_dto)
        logger.trace("Adapter stop_stream mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_stop_response(service_response_dto)
        logger.info("Adapter stop_stream completed")
        return adapter_response_dto

    async def is_available(self, request: MicrophoneAvailabilityRequestDto) -> MicrophoneAvailabilityResponseDto:
        logger.trace("Adapter is_available mapping inbound DTO to service DTO")
        service_request_dto = map_adapter_to_service_availability_request(request)
        logger.trace("Adapter is_available calling service")
        service_response_dto = await self.service_port.is_available(service_request_dto)
        logger.trace("Adapter is_available mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_availability_response(service_response_dto)
        logger.info("Adapter is_available completed")
        return adapter_response_dto

    async def mic_stream(self, request: GetStreamRequestDto) -> GetStreamResponseDto:
        logger.trace("Adapter mic_stream mapping inbound DTO to service DTO")
        service_request_dto = map_adapter_to_service_get_stream_request(request)
        logger.trace("Adapter mic_stream calling service")
        service_response_dto = self.service_port.mic_stream(service_request_dto)
        logger.trace("Adapter mic_stream mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_get_stream_response(service_response_dto)
        logger.info("Adapter mic_stream completed")
        return adapter_response_dto
